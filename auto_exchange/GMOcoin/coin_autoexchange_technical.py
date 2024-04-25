# -*- coding: utf-8 -*-
import requests
import sys
import time
import datetime
import hashlib
import hmac
import codecs
import json
import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import seaborn
import gzip
import os
import math
import mplfinance as mpf
import talib as ta

args = sys.argv

#本ツール起動時、直下にAPIキーとAPIシークレットのファイルがある事。（apikey.txt、apisecret.txt）
# 第一引数：暗号資産種別、第二引数：取引余力の何%を使って注文するか
# ※nohupでprintがログに書き込まれないのでflushを付加
# ※定期メンテ時は各注文はキャンセルするが、緊急メンテ時は動作スキップだけにとどめる。

if 3 != len(args):
    print("Usage: python3 coin_autoexchange_technical.py BTC 80")
    print("para1: coinKind, para2: purchase percentage")
    sys.stdout.flush()
    sys.exit(1)

# INパラ
coinKind = args[1]
purchasePer = int(args[2])
print("IN parameter coinKind:" + coinKind + " purchasePer:" + str(purchasePer))
sys.stdout.flush()

# 固定値
PVT_ENDPOINT = 'https://api.coin.z.com/private'
PUB_ENDPOINT = 'https://api.coin.z.com/public'
AFTER_REQUEST_SLEEP_SEC = 1
#WAIT_SEC = 60 # 最終的に途中リクエストのAFTER_REQUEST_SLEEP_SEC分待機が差し引かれた値でスリープする。
WAIT_SEC = 86400 # 最終的に途中リクエストのAFTER_REQUEST_SLEEP_SEC分待機が差し引かれた値でスリープする。
MACD_FAST_PERIOD=12 # MACDで使用する短期EMAの日数
MACD_SLOW_PERIOD=26 # MACDで使用する長期EMAの日数
MACD_SIGNAL_PERIOD=9 # MACDで使用するMACDシグナルの日数
SMA_FAST_PERIOD=5 # SMA短期の日数
SMA_SLOW_PERIOD=25 # SMA長期の日数
TREND_ANAL_DURATION = ((MACD_SLOW_PERIOD + MACD_SIGNAL_PERIOD) + 2) * 24 * 60 * 60 # 買い前分析対象の期間(s) 初回はMACDの長期+シグナル+2日マージンの日数をMACD分析対象とする
DF_HOLD_DURATION = 63072000 # 分析対象レートデータフレームの保持秒数  MACD分析では2年分保持する
RATE_DF_QUEUE_MAX = ( DF_HOLD_DURATION / WAIT_SEC ) + 1 # 分析対象レートデータフレームの最大数
#BUY_THRESHOLD_TREND = 0 # 買い前、TREND_ANAL_DURATIONの期間中にどの程度の右肩上がりであれば注文するかの閾値（傾きの値）
BUY_HOLD_SEC = -1 # 買い後、傾き分析等で損切りの判断がされない間、何秒間保持しておくか。-1で無期限
LOSSCUT_THRESHOLD_TREND = 0 # 買い後、BUY_ANAL_DURATION毎の傾き分析で下り調子の場合にどの程度の右肩下がりであれば損切するかの閾値（傾きの値）
LOSSCUT_THRESHOLD_AMOUNT = 95 # 買い後、傾き分析関係なく注文時のレートからどの程度のパーセンテージとなったら損切りするかの閾値（%）
MAINTENANCE_WEEKDAY = 5 # 定期メンテナンスの曜日を設定(0が月曜日、1が火曜日、2が水曜日、3が木曜日、4が金曜日、5が土曜日、6が日曜日)
MAINTENANCE_START = "0800" # 定期メンテナンス開始前の売り処理開始時間を設定(JST)
MAINTENANCE_END = "1200" # 定期メンテナンス終了後の処理再開時間を設定(JST)


# グローバル変数
waitSec = WAIT_SEC # チェック処理のスリープ時間
dt_now = None # チェック処理の実行時間
recentRateDf = pd.DataFrame({'Close':[]}) # 分析対象レートデータフレーム
buyRate = -1 # 注文時レート。分析期間満了後、または売り後は必ず初期化すること。
buySize = 0 # 注文時数量。分析期間満了後、または売り後は必ず初期化すること。
firstTrendAnalSec = 0 # 初回分析期間の蓄積秒数カウント
orderId = -1 # 注文ID。売り後は必ず-1に初期化する事。※現物取引では使用しない
afterBuyFlg = False # 購入した状態かどうかのフラグ。売り後は必ずFalseにすること。False=未買い True=買い済み
firstTimeFlg = True # 初回フラグ。初回はklineの情報から分析する


# 取引所ステータス取得関数
def getExStat():
    print("===== getExStat START =====")
    sys.stdout.flush()
    global waitSec
    ex_stat_url = PUB_ENDPOINT + '/v1/status'
    ex_stat = requests.get(ex_stat_url)
    time.sleep(AFTER_REQUEST_SLEEP_SEC)
    waitSec -= AFTER_REQUEST_SLEEP_SEC
    print("===== getExStat END =====")
    sys.stdout.flush()
    return ex_stat
    #print(ex_stat.json())

# 取引ルール取得関数
def getExRule():
    print("===== getExRule START =====")
    sys.stdout.flush()
    global waitSec
    ex_rule_url = PUB_ENDPOINT + '/v1/symbols'
    ex_rule = requests.get(ex_rule_url)
    time.sleep(AFTER_REQUEST_SLEEP_SEC)
    waitSec -= AFTER_REQUEST_SLEEP_SEC
    print("===== getExRule END =====")
    sys.stdout.flush()
    return ex_rule
    #print(ex_rule.json())

# 最新レート取得関数
def getRecentRete(inKind):
    print("===== getRecentRete START ===== symbol:" + inKind)
    sys.stdout.flush()
    global waitSec
    rate_url = PUB_ENDPOINT + '/v1/ticker?symbol=' + inKind
    recent_rate = requests.get(rate_url)
    time.sleep(AFTER_REQUEST_SLEEP_SEC)
    waitSec -= AFTER_REQUEST_SLEEP_SEC
    print("===== getRecentRete END ===== symbol:" + inKind)
    sys.stdout.flush()
    return recent_rate
    #print(recent_rate.json())

# 板情報取得関数
def getOrderBooks(inKind):
    print("===== getOrderBooks START ===== symbol:" + inKind)
    sys.stdout.flush()
    global waitSec
    orderbooks_url = PUB_ENDPOINT + '/v1/orderbooks?symbol=' + inKind
    orderbooks = requests.get(orderbooks_url)
    time.sleep(AFTER_REQUEST_SLEEP_SEC)
    waitSec -= AFTER_REQUEST_SLEEP_SEC
    print("===== getOrderBooks END ===== symbol:" + inKind)
    sys.stdout.flush()
    return orderbooks
    #print(orderbooks.json())

# 取引履歴取得関数
def getTrades(inKind, inPage, inCount):
    print("===== getTrades START ===== symbol:" + inKind + " page:" + str(inPage) + " count:" + str(inCount))
    sys.stdout.flush()
    global waitSec
    trades_url = PUB_ENDPOINT + '/v1/trades?symbol=' + inKind + '&page=' + str(inPage) + '&count=' + str(inCount)
    trades_resp = requests.get(trades_url)
    time.sleep(AFTER_REQUEST_SLEEP_SEC)
    waitSec -= AFTER_REQUEST_SLEEP_SEC
    print("===== getTrades END ===== symbol:" + inKind + " page:" + str(inPage) + " count:" + str(inCount))
    sys.stdout.flush()
    return trades_resp
    #print(trades_resp.json())

# KLine情報取得関数(min)
# inIntervalは1、5、10、15、30のいずれかを指定
def getKLineMin(inKind, inInterval):
    print("===== getKLineMin START ===== symbol:" + inKind + " interval:" + str(inInterval))
    sys.stdout.flush()
    global waitSec
    dt_now = datetime.datetime.now()
    now = dt_now.strftime('%Y%m%d')
    kline_url = PUB_ENDPOINT + '/v1/klines?symbol=' + inKind + '&interval=' + str(inInterval) + 'min&date=' + now
    kline_resp = requests.get(kline_url)
    time.sleep(AFTER_REQUEST_SLEEP_SEC)
    waitSec -= AFTER_REQUEST_SLEEP_SEC
    print("===== getKLineMin END ===== symbol:" + inKind + " interval:" + str(inInterval) + " date:" + now)
    sys.stdout.flush()
    return kline_resp

# KLine情報取得関数(day)
# 今年分と昨年分を取得
def getKLineDay(inKind):
    print("===== getKLineDay START ===== symbol:" + inKind)
    sys.stdout.flush()
    global waitSec
    dt_now = datetime.datetime.now()
    now = dt_now.strftime('%Y')
    dt_lastyear = dt_now - datetime.timedelta(days=365)
    lastyear = dt_lastyear.strftime('%Y')

    kline_url = PUB_ENDPOINT + '/v1/klines?symbol=' + inKind + '&interval=1day&date=' + now
    kline_resp = requests.get(kline_url)
    time.sleep(AFTER_REQUEST_SLEEP_SEC)
    waitSec -= AFTER_REQUEST_SLEEP_SEC
    print("1st request symbol:" + inKind + " interval:1day date:" + now)
    sys.stdout.flush()

    kline_url_ly = PUB_ENDPOINT + '/v1/klines?symbol=' + inKind + '&interval=1day&date=' + lastyear
    kline_resp_ly = requests.get(kline_url_ly)
    time.sleep(AFTER_REQUEST_SLEEP_SEC)
    waitSec -= AFTER_REQUEST_SLEEP_SEC
    print("===== getKLineDay END ===== symbol:" + inKind + " interval:1day date:" + lastyear)
    sys.stdout.flush()
    return kline_resp, kline_resp_ly

# privateAPI実行関数
def submitPrivateAPI(inMethod, inPath, inReqBody):
    print("===== submitPrivateAPI START =====")
    sys.stdout.flush()
    global waitSec
    # 認証情報作成
    nowUnixTime = '{0}000'.format(int(time.mktime(datetime.datetime.now().timetuple())))
    apikey_file = "apikey.txt"
    apisec_file = "apisecret.txt"

    infp = codecs.open(apikey_file, 'r', 'utf-8')
    apikey_list = infp.readlines()
    infp.close
    apikey = apikey_list[0].rstrip()
    #print("apikey: " + apikey)

    infp2 = codecs.open(apisec_file, 'r', 'utf-8')
    apisec_list = infp2.readlines()
    infp2.close
    apisec = apisec_list[0].rstrip()
    #print("apisecret: " + apisec)

    # API実行
    if ("GET" == inMethod) or (inReqBody is None):
        hmac_text = nowUnixTime + inMethod + inPath
        print("GET or hmac noparams hmac_text:" + hmac_text)
    else:
        hmac_text = nowUnixTime + inMethod + inPath + json.dumps(inReqBody)
        #hmac_text = nowUnixTime + inMethod + inPath
        print("POST and hmac params exist hmac_text:" + hmac_text)

    sign = hmac.new(bytes(apisec.encode('ascii')), bytes(hmac_text.encode('ascii')), hashlib.sha256).hexdigest()

    headers = {
        "API-KEY": apikey,
        "API-TIMESTAMP": nowUnixTime,
        "API-SIGN": sign
    }

    print("execute: " + inMethod + " " + inPath )
    sys.stdout.flush()

    if "GET" == inMethod:
        if inReqBody is None:
            print("GET noparams")
            sys.stdout.flush()
            retBody = requests.get(PVT_ENDPOINT + inPath, headers=headers)
        else:
            print("GET params:")
            print(inReqBody)
            sys.stdout.flush()
            retBody = requests.get(PVT_ENDPOINT + inPath, headers=headers, params=inReqBody)
    elif "POST" == inMethod:
        if inReqBody is None:
            print("POST noparams")
            sys.stdout.flush()
            retBody = requests.post(PVT_ENDPOINT + inPath, headers=headers)
        else:
            print("POST params:")
            print(json.dumps(inReqBody))
            sys.stdout.flush()
            retBody = requests.post(PVT_ENDPOINT + inPath, headers=headers, data=json.dumps(inReqBody))

    time.sleep(AFTER_REQUEST_SLEEP_SEC)
    waitSec -= AFTER_REQUEST_SLEEP_SEC

    print("responseCode:")
    print(retBody)
    print("response:")
    print(retBody.json())
    print("===== submitPrivateAPI END =====")
    sys.stdout.flush()
    return retBody

# MACD分析処理
def analysisMACD(inRateDf):
    print("===== analysisMACD START =====")
    sys.stdout.flush()

    # MACD分析実行
    macd, macdsignal, macdhist = ta.MACD(inRateDf['Close'], fastperiod=MACD_FAST_PERIOD, slowperiod=MACD_SLOW_PERIOD, signalperiod=MACD_SIGNAL_PERIOD)
    print("executed MACD")
    sys.stdout.flush()

    inRateDf['macd'] = macd
    inRateDf['macdsignal'] = macdsignal
    inRateDf['macdhist'] = macdhist

    # 移動平均
    smaFastLabel = "ma" + str(SMA_FAST_PERIOD)
    smaSlowLabel = "ma" + str(SMA_SLOW_PERIOD)
    inRateDf[smaFastLabel] = ta.SMA(inRateDf['Close'], SMA_FAST_PERIOD)
    inRateDf[smaSlowLabel] = ta.SMA(inRateDf['Close'], SMA_SLOW_PERIOD)
    print("executed SMA")
    print(inRateDf)
    sys.stdout.flush()

    os.makedirs("technicalAnalysis", exist_ok=True)
    outfilename_tech = "technicalAnalysis/MACD_SMA_" + now + ".txt.gz"
    with gzip.open(outfilename_tech, 'wt') as outfp:
        outfp.write(inRateDf.to_string())

    apd = [
        # 5日移動平均線
        mpf.make_addplot(inRateDf[smaFastLabel], color='blue', panel=0, width=0.5),
        # 25日移動平均線
        mpf.make_addplot(inRateDf[smaSlowLabel], color='green', panel=0, width=0.5),
        # MACD
        mpf.make_addplot(inRateDf['macd'], panel=1, width=0.5, color='red'),
        # シグナル
        mpf.make_addplot(inRateDf['macdsignal'], panel=1, width=0.5, color='blue'),
        # ヒストグラム
        mpf.make_addplot(inRateDf['macdhist'], panel=2, type='bar')
    ]

    # ラベルをつけてチャートを表示
    fig, axes = mpf.plot(inRateDf, type='candle', addplot=apd, returnfig=True)

    # ラベルを追加
    axes[0].legend([smaFastLabel, smaSlowLabel])
    axes[2].legend(['MACD', 'SIGNAL'])

    # チャートを保存
    outfilename_chart = "technicalAnalysis/MACD_SMA_" + now + ".jpg"
    fig.savefig(outfilename_chart, dpi=300)

    print("===== analysisMACD END =====")
    sys.stdout.flush()
    return inRateDf

# 傾き分析処理
def analysisTrend(inRateDf):
    print("===== analysisTrend START =====")

    os.makedirs("analysisTrend", exist_ok=True)
    now = dt_now.strftime('%Y%m%d-%H%M%S')
    outfilename_txt = "analysisTrend/analysisTrend_" + now + ".txt.gz"
    outfp = gzip.open(outfilename_txt, 'wt')
    print(inRateDf)
    sys.stdout.flush()
    outfp.write(inRateDf.to_string())

    time = inRateDf[['time']]
    rate = inRateDf[['rate']]

    # 回帰分析
    model_lr = LinearRegression()
    model_lr.fit(time, rate)

    print('y(rate)= %.3fx(time) + %.3f' % (model_lr.coef_ , model_lr.intercept_))
    print('score: ' + str(model_lr.score(time, rate)))
    sys.stdout.flush()
    outfp.write("\n")
    outfp.write('function: y(rate)= %.3fx(time) + %.3f' % (model_lr.coef_ , model_lr.intercept_))
    outfp.write("\n")
    outfp.write('score: ' + str(model_lr.score(time, rate)))
    outfp.close()

    # グラフ出力
#    outfilename = "analysisTrend_" + now + ".jpg"

#    date_plot = inRateDf['date']
#    rate_plot = inRateDf['rate']

#    plt.plot(date_plot, rate_plot, 'o')
#    plt.plot(date_plot, model_lr.predict(time), linestyle="solid")
#    plt.savefig(outfilename)
#    plt.clf()

    print("===== analysisTrend END =====")
    sys.stdout.flush()

    return model_lr.coef_[0][0]

# 最新レートデータフレーム追加処理
def appendRecentRateDf(inCoinKind, inRateDf):
    print("===== appendRecentRateDf START =====")
    sys.stdout.flush()

    # 最新レート取得(日時はunix時間に変換)
    recentRate = getRecentRete(inCoinKind)
    print(recentRate.json())
    sys.stdout.flush()

    unixDate = datetime.datetime.strptime(recentRate.json()["data"][0]["timestamp"], '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()
    if len(inRateDf) <= 0:
        rateDiff_acc = 0
    else:
        rateDiff_acc = float(recentRate.json()["data"][0]["last"]) - float(inRateDf.iloc[-1]['rate'])

    newRow = {'date':recentRate.json()["data"][0]["timestamp"], 'time': unixDate, 'rate':recentRate.json()["data"][0]["last"], 'rateDiff_acc':rateDiff_acc}
    print(newRow)
    sys.stdout.flush()

    inRateDf = inRateDf.append(newRow, ignore_index=True)

    # キューが満杯の場合先頭データを消去
    if len(inRateDf) > RATE_DF_QUEUE_MAX:
        inRateDf = inRateDf[1:]

    print("===== appendRecentRateDf END =====")
    sys.stdout.flush()

    return inRateDf

# 日毎kline抽出処理
# 取得した昨年と今年の日毎klinesから指定期間中の値を抽出し時系列データフレームを作成し応答する
def extractFromDayKlines( inRecentUnixTime, inPastUnixTime, inKLine, inLYKline, inRateDf ):
    print("===== extractFromDayKlines START =====")
    sys.stdout.flush()

    # 昨年分のkline情報処理
    for inLYKlineData in inLYKline.json()["data"]:
        if (( inRecentUnixTime >= int(inLYKlineData["openTime"])) and ( int(inLYKlineData["openTime"]) >= inPastUnixTime )):
            # 指定期間内のデータの場合は時刻と終値をデータフレームに追加する
            datestr = datetime.datetime.fromtimestamp(int(inLYKlineData["openTime"]) / 1000).strftime('%Y-%m-%d')
            newRow = {'Date':datestr, 'Open':int(inLYKlineData["open"]), 'High':int(inLYKlineData["high"]), 'Low':int(inLYKlineData["low"]), 'Close':int(inLYKlineData["close"]), 'Volume':float(inLYKlineData["volume"])}

            print("LastYear extract")
            #print(newRow)
            sys.stdout.flush()

            tempDf = pd.DataFrame(newRow, index=[datestr])
            tempDf["Date"] = pd.to_datetime(tempDf['Date'])
            tempDf = tempDf.set_index("Date")
            print(tempDf)
            sys.stdout.flush()
            inRateDf = pd.concat([inRateDf, tempDf])

    # 今年分のkline情報処理
    for inKLineData in inKLine.json()["data"]:
        if (( inRecentUnixTime >= int(inKLineData["openTime"])) and ( int(inKLineData["openTime"]) >= inPastUnixTime )):
            # 指定期間内のデータの場合は時刻と終値をデータフレームに追加する
            datestr = datetime.datetime.fromtimestamp(int(inKLineData["openTime"]) / 1000).strftime('%Y-%m-%d')
            newRow = {'Date':datestr, 'Open':int(inKLineData["open"]), 'High':int(inKLineData["high"]), 'Low':int(inKLineData["low"]), 'Close':int(inKLineData["close"]), 'Volume':float(inKLineData["volume"])}

            print("CurrentYear extract")
            #print(newRow)
            sys.stdout.flush()

            tempDf = pd.DataFrame(newRow, index=[datestr])
            tempDf["Date"] = pd.to_datetime(tempDf['Date'])
            tempDf = tempDf.set_index("Date")
            print(tempDf)
            sys.stdout.flush()
            inRateDf = pd.concat([inRateDf, tempDf])

    print("len(inRateDf): " + str(len(inRateDf)))
    print("RATE_DF_QUEUE_MAX: " + str(RATE_DF_QUEUE_MAX))

    # キューが満杯の場合先頭データを消去
    if len(inRateDf) > RATE_DF_QUEUE_MAX:
        deleteLength = len(inRateDf) - RATE_DF_QUEUE_MAX
        inRateDf = inRateDf[deleteLength:]

    print("===== extractFromDayKlines END =====")
    sys.stdout.flush()

    return inRateDf

# 買い注文処理
def makeBuyOrder(inCoinKind):
    print("===== makeBuyOrder START =====")
    sys.stdout.flush()

    global buyRate
    global buySize
    outOrderId = -1
    minOrderSize = 0
    maxOrderSize = 0

    # 買い付け数量算出
    # 取引ルール取得
    exRule = getExRule()
    os.makedirs("exRule", exist_ok=True)
    now = dt_now.strftime('%Y%m%d-%H%M%S')
    outfilename_exRule = "exRule/exRule_" + now + ".txt.gz"
    with gzip.open(outfilename_exRule, 'wt') as outfp:
        outfp.write(json.dumps(exRule.json()))

    for exRuleData in exRule.json()["data"]:
        if inCoinKind == exRuleData["symbol"]:
            print(inCoinKind + " rule exist")
            print(exRuleData)
            sys.stdout.flush()
            minOrderSize = float(exRuleData["minOrderSize"])
            maxOrderSize = float(exRuleData["maxOrderSize"])
            break

    print("coinKind:" + inCoinKind + " minOrderSize:" + str(minOrderSize) + " maxOrderSize:" + str(maxOrderSize))
    sys.stdout.flush()

    # 最小注文数量の小数点以降の桁数を取得。小数点が無い場合は0
    dot_index = 0
    minOrderSize_digit = 0
    minOrderSize_str = str(minOrderSize)
    dot_index = minOrderSize_str.find(".")
    if dot_index > 0:
        minOrderSize_digit = (len(minOrderSize_str) - (dot_index+1))
    print("minOrderSize_digit:" + str(minOrderSize_digit))

    # 余力情報取得
    margin = submitPrivateAPI("GET","/v1/account/margin",None)

    availAmount = int(margin.json()["data"]["availableAmount"])
    purchaseAmount = availAmount * ( purchasePer / 100 )
    print("availAmount:" + str(availAmount) + " purchaseAmount(availAmount * (" + str(purchasePer) + " / 100)):" + str(purchaseAmount) )
    sys.stdout.flush()

    # 最新レート取得
    recentRate = getRecentRete(inCoinKind)
    print(recentRate.json())
    sys.stdout.flush()

    recentRate_last = int(recentRate.json()["data"][0]["last"])
    print("recentRate(last):" + str(recentRate_last) )
    sys.stdout.flush()

    # 数量算出
    buySize_tmp = (purchaseAmount / (recentRate_last * minOrderSize)) * minOrderSize
    print("buySize_tmp((purchaseAmount / (recentRate_last * minOrderSize)) * minOrderSize):" + str(buySize_tmp) )
    sys.stdout.flush()
    
    # 最小注文数量以下の桁数の切り捨て実行
    buySize = math.floor(buySize_tmp * (10 ** minOrderSize_digit)) / (10 ** minOrderSize_digit)
    print("buySize(remove under " + str(minOrderSize_digit)  + " digits):" + str(buySize) )
    sys.stdout.flush()

    # 最大注文数量より大きい場合は最大注文数量を設定
    if (maxOrderSize < buySize):
        print("maxOrderSize(" + str(maxOrderSize) + ") < buySize(" + str(buySize) + ") execute round")
        buySize = maxOrderSize

    if (maxOrderSize >= buySize) and (buySize >= minOrderSize):
        print("EXECUTE buyOrder (maxOrderSize(" + str(maxOrderSize) + ") >= buySize(" + str(buySize) + ") >= minOrderSize(" + str(minOrderSize)  + "))")
        sys.stdout.flush()
        # 買い注文実行
        buyOrderParams = {
        "symbol": inCoinKind,
        "side": "BUY",
        "executionType": "MARKET",
        "size": str(buySize)
        }
        print(buyOrderParams)
        sys.stdout.flush()

        outOrderId = submitPrivateAPI("POST","/v1/order",buyOrderParams)

        buyRate = recentRate_last
        print("buyRate:" + str(buyRate))
        sys.stdout.flush()
    else:
        # 買い実行不可
        print("SKIP buyOrder !(maxOrderSize(" + str(maxOrderSize) + ") >= buySize(" + str(buySize) + ") >= minOrderSize(" + str(minOrderSize)  + "))")
        sys.stdout.flush()

    print("===== makeBuyOrder END ===== outOrderId:" + str(outOrderId))
    sys.stdout.flush()

    return outOrderId

# 売り注文処理
def makeSellOrder(inCoinKind):
    print("===== makeSellOrder START =====")
    sys.stdout.flush()

    global buySize
    global buyRate
    outOrderId = -1

    # 売り注文実行
    sellOrderParams = {
    "symbol": inCoinKind,
    "side": "SELL",
    "executionType": "MARKET",
    "size": str(buySize)
    }
    print(sellOrderParams)
    sys.stdout.flush()

    outOrderId = submitPrivateAPI("POST","/v1/order",sellOrderParams)

    buySize = 0
    buyRate = -1
    print("buySize:" + str(buySize) + " buyRate:" + str(buyRate))
    sys.stdout.flush()

    print("===== makeSellOrder END ===== outOrderId:" + str(outOrderId))
    sys.stdout.flush()

    return outOrderId

# メイン処理。ループで相場、残高チェック。売買注文実施
# 割り込み時は事後処理をして終了
while True:
    waitSec = WAIT_SEC

    dt_now = datetime.datetime.now()
    now = dt_now.strftime('%Y/%m/%d %H:%M:%S')

    print("")
    print("MAIN [" + now + "] check loop start" )
    sys.stdout.flush()

    # 取引所ステータス取得
    exStat = getExStat()
    print(exStat.json())
    sys.stdout.flush()

    # KLine情報取得
#    klineMin = getKLineMin(coinKind, 1)
#    os.makedirs("klines", exist_ok=True)
#    now = dt_now.strftime('%Y%m%d-%H%M%S')
#    outfilename_kline = "klines/klines_" + now + ".txt.gz"
#    with gzip.open(outfilename_kline, 'wt') as outfp:
#        outfp.write(json.dumps(klineMin.json()))

    klineDay, klineDay_ly = getKLineDay(coinKind)
    os.makedirs("klines_day", exist_ok=True)
    now = dt_now.strftime('%Y%m%d-%H%M%S')
    outfilename_kline_d = "klines_day/klines_day_" + now + ".txt.gz"
    outfilename_kline_dly = "klines_day/klines_day_ly_" + now + ".txt.gz"
    with gzip.open(outfilename_kline_d, 'wt') as outfp:
        outfp.write(json.dumps(klineDay.json()))
    with gzip.open(outfilename_kline_dly, 'wt') as outfp:
        outfp.write(json.dumps(klineDay_ly.json()))

    # 板情報取得
    orderBooks = getOrderBooks(coinKind)
    os.makedirs("orderBooks", exist_ok=True)
    now = dt_now.strftime('%Y%m%d-%H%M%S')
    outfilename_ob = "orderBooks/orderBooks_" + now + ".txt.gz"
    with gzip.open(outfilename_ob, 'wt') as outfp:
        outfp.write(json.dumps(orderBooks.json()))

    # 取引履歴取得
    trades = getTrades(coinKind, 1, 30)
    os.makedirs("trades", exist_ok=True)
    now = dt_now.strftime('%Y%m%d-%H%M%S')
    outfilename_trade = "trades/trades_" + now + ".txt.gz"
    with gzip.open(outfilename_trade, 'wt') as outfp:
        outfp.write(json.dumps(trades.json()))

    # 余力情報取得
    margin_out = submitPrivateAPI("GET","/v1/account/margin",None)
    os.makedirs("margin", exist_ok=True)
    now = dt_now.strftime('%Y%m%d-%H%M%S')
    outfilename_margin = "margin/margin_" + now + ".txt.gz"
    with gzip.open(outfilename_margin, 'wt') as outfp:
        outfp.write(json.dumps(margin_out.json()))

    # 資産残高取得
    assets_out = submitPrivateAPI("GET","/v1/account/assets",None)
    os.makedirs("assets", exist_ok=True)
    now = dt_now.strftime('%Y%m%d-%H%M%S')
    outfilename_assets = "assets/assets_" + now + ".txt.gz"
    with gzip.open(outfilename_assets, 'wt') as outfp:
        outfp.write(json.dumps(assets_out.json()))

    # 有効注文一覧取得
#    AO_parameters = {
#    "symbol": coinKind,
#    "page": 1,
#    }
#    activeOrders = submitPrivateAPI("GET","/v1/activeOrders",AO_parameters)
#    print(activeOrders.json())
#    sys.stdout.flush()

#    ※現物取引では以下処理は使用しない
#    if 0 == len(activeOrders.json()["data"]):
#        orderId = -1
#        print("MAIN beforeCheck activeOrders 0 orderId:" + orderId)
#        sys.stdout.flush()
#    else:
#        orderId = activeOrders.json()["data"][0]["orderId"]
#        print("MAIN beforeCheck activeOrders exist orderId:" + orderId)
#        sys.stdout.flush()

    ### 買い前、買い後処理
    # TODO: 初回のみklinesでMACD実施。それ以降は1日毎の最新レートでMACD実施。
#    if -1 == orderId:
    if firstTimeFlg:
        # 初回処理実施
        print("MAIN start first firstTimeFlg:" + str(firstTimeFlg))
        sys.stdout.flush()
        # 日毎kline情報から分析対象データフレーム作成
        dt_past = dt_now - datetime.timedelta(seconds=TREND_ANAL_DURATION)
        recentRateDf = extractFromDayKlines( int(dt_now.timestamp() * 1000), int(dt_past.timestamp() * 1000), klineDay, klineDay_ly, recentRateDf)
#        print(recentRateDf)
#        sys.stdout.flush()

        firstTimeFlg = False

        print("MAIN end first firstTimeFlg:" + str(firstTimeFlg))
        sys.stdout.flush()

    else:
        # 初回以降処理実施
        print("MAIN start regular firstTimeFlg:" + str(firstTimeFlg))
        sys.stdout.flush()

        # 日毎kline情報から分析対象データフレーム作成
        dt_past = dt_now - datetime.timedelta(days=1)
        recentRateDf = extractFromDayKlines( int(dt_now.timestamp() * 1000), int(dt_past.timestamp() * 1000), klineDay, klineDay_ly, recentRateDf)
#        print(recentRateDf)
#        sys.stdout.flush()

        print("MAIN end regular firstTimeFlg:" + str(firstTimeFlg))
        sys.stdout.flush()

    # MACD分析実行
    recentRateDf = analysisMACD(recentRateDf)
    print("MAIN execute MACD")
    sys.stdout.flush()

    # 買い済みか売り済みかで分岐
    if not afterBuyFlg:
        # 売り済み（未買い）時処理
        print("MAIN start BeforeBuy afterBuyFlg:" + str(afterBuyFlg))
        sys.stdout.flush()

        # 買判定 ※一旦ゴールデンクロス部分のみを判定する（0基準の追随売り、買いは判定しない）
        # 最後尾のデータ           MACDシグナル <= MACD
        # 最後尾から1個前のデータ  MACDシグナル >= MACD
        # 両方の条件を満たす場合は買い対象とする
        if (float(recentRateDf.iloc[-2]['macdsignal']) >= float(recentRateDf.iloc[-2]['macd'])) and (float(recentRateDf.iloc[-1]['macdsignal']) <= float(recentRateDf.iloc[-1]['macd'])):
            # 買い対象
            print("MAIN BuyOrder BUY MACD signal[-2]:" + str(recentRateDf.iloc[-2]['macdsignal']) + " MACD[-2]:" + str(recentRateDf.iloc[-2]['macd']) + " MACD signal[-1]:" + str(recentRateDf.iloc[-1]['macdsignal']) + " MACD[-1]:" + str(recentRateDf.iloc[-1]['macd']))
            sys.stdout.flush()

            orderId = makeBuyOrder(coinKind)
            afterBuyFlg = True
            print("MAIN BuyOrder end orderId:" + str(orderId) + " afterBuyFlg:" + str(afterBuyFlg))
            sys.stdout.flush()
        else:
            # 買い対象外(STAY)
            print("MAIN BuyOrder STAY MACD signal[-2]:" + str(recentRateDf.iloc[-2]['macdsignal']) + " MACD[-2]:" + str(recentRateDf.iloc[-2]['macd']) + " MACD signal[-1]:" + str(recentRateDf.iloc[-1]['macdsignal']) + " MACD[-1]:" + str(recentRateDf.iloc[-1]['macd']))
            sys.stdout.flush()

    else:
        # 買い済み時処理
        print("MAIN start AfterBuy afterBuyFlg:" + str(afterBuyFlg))
        sys.stdout.flush()

        # 売判定 ※一旦ゴールデンクロス部分のみを判定する（0基準の追随売り、買いは判定しない）
        # 最後尾のデータ           MACDシグナル >= MACD
        # 最後尾から1個前のデータ  MACDシグナル <= MACD
        # 両方の条件を満たす場合は売り対象とする
        if (float(recentRateDf.iloc[-2]['macdsignal']) <= float(recentRateDf.iloc[-2]['macd'])) and (float(recentRateDf.iloc[-1]['macdsignal']) >= float(recentRateDf.iloc[-1]['macd'])):
            # 売り対象
            print("MAIN SellOrder SELL MACD signal[-2]:" + str(recentRateDf.iloc[-2]['macdsignal']) + " MACD[-2]:" + str(recentRateDf.iloc[-2]['macd']) + " MACD signal[-1]:" + str(recentRateDf.iloc[-1]['macdsignal']) + " MACD[-1]:" + str(recentRateDf.iloc[-1]['macd']))
            sys.stdout.flush()

            orderId_sell = makeSellOrder(coinKind)
            print("MAIN SellOrder end orderId_sell:" + str(orderId_sell))
            sys.stdout.flush()

            afterBuyFlg = False
            print("MAIN SellOrder afterBuyFlg:" + str(afterBuyFlg) + " buyRate:" + str(buyRate))
            sys.stdout.flush()
        else:
            # 売り対象外(STAY)
            print("MAIN SellOrder STAY MACD signal[-2]:" + str(recentRateDf.iloc[-2]['macdsignal']) + " MACD[-2]:" + str(recentRateDf.iloc[-2]['macd']) + " MACD signal[-1]:" + str(recentRateDf.iloc[-1]['macdsignal']) + " MACD[-1]:" + str(recentRateDf.iloc[-1]['macd']))
            sys.stdout.flush()

    print("")
    print("MAIN wait " + str(waitSec) + "(sec) start" )
    sys.stdout.flush()
    time.sleep(waitSec)



