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

args = sys.argv

#本ツール起動時、直下にAPIキーとAPIシークレットのファイルがある事。（apikey.txt、apisecret.txt）
# 第一引数：暗号資産種別、第二引数：取引余力の何%を使って注文するか
# ※nohupでprintがログに書き込まれないのでflushを付加
# ※定期メンテ時は各注文はキャンセルするが、緊急メンテ時は動作スキップだけにとどめる。

if 3 != len(args):
    print("Usage: python3 coin_autoexchange.py BTC 80")
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
WAIT_SEC = 60 # 最終的に途中リクエストのAFTER_REQUEST_SLEEP_SEC分待機が差し引かれた値でスリープする
TREND_ANAL_DURATION = 240 # 買い前傾き分析対象の期間(s)
BUY_THRESHOLD_TREND = 0 # 買い前、TREND_ANAL_DURATIONの期間中にどの程度の右肩上がりであれば注文するかの閾値（傾きの値）
BUY_HOLD_SEC = -1 # 買い後、傾き分析等で損切りの判断がされない間、何秒間保持しておくか。-1で無期限
AFTER_BUY_ANAL_DURATION = 240 # 買い後の傾き分析対象の期間(s)※この期間は1分、5分単位のローソク足を分析して検討する。
LOSSCUT_THRESHOLD_TREND = 0 # 買い後、BUY_ANAL_DURATION毎の傾き分析で下り調子の場合にどの程度の右肩下がりであれば損切するかの閾値（傾きの値）
LOSSCUT_THRESHOLD_AMOUNT = 95 # 買い後、傾き分析関係なく注文時のレートからどの程度のパーセンテージとなったら損切りするかの閾値（%）
MAINTENANCE_WEEKDAY = 5 # 定期メンテナンスの曜日を設定(0が月曜日、1が火曜日、2が水曜日、3が木曜日、4が金曜日、5が土曜日、6が日曜日)
MAINTENANCE_START = "0800" # 定期メンテナンス開始前の売り処理開始時間を設定(JST)
MAINTENANCE_END = "1200" # 定期メンテナンス終了後の処理再開時間を設定(JST)


# グローバル変数
waitSec = WAIT_SEC # チェック処理のスリープ時間
dt_now = None # チェック処理の実行時間
beforeBuyRateDf = pd.DataFrame({'date':[],'rate':[]}) # 買い前分析対象レートデータフレーム。分析期間満了後、または買い後は必ず初期化すること。
afterBuyRateDf = pd.DataFrame({'date':[],'rate':[]}) # 買い後分析対象レートデータフレーム。分析期間満了後、または売り後は必ず初期化すること。
buyRate = -1 # 注文時レート。分析期間満了後、または売り後は必ず初期化すること。
buySize = 0 # 注文時数量。分析期間満了後、または売り後は必ず初期化すること。
beforeBuyAnalSec = 0 # 買い前分析期間の秒数カウント。分析期間満了後に必ず初期化すること。
afterBuyAnalSec = 0 # 買い後分析期間の秒数カウント。分析機関満了後に必ず初期化すること。
orderId = -1 # 注文ID。売り後は必ず-1に初期化する事。※現物取引では使用しない
afterBuyFlg = False # 購入した状態かどうかのフラグ。売り後は必ずFalseにすること。False=未買い True=買い済み


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
        timeTotal = 0
        rateDiff = 0
        rateDiff_acc = 0
    else:
        timeTotal = int(inRateDf.iloc[-1]['time']) + int(unixDate) - int(inRateDf.iloc[-1]['unixDate'])
        rateDiff = float(recentRate.json()["data"][0]["last"]) - float(inRateDf.iloc[0]['rate'])
        rateDiff_acc = float(recentRate.json()["data"][0]["last"]) - float(inRateDf.iloc[-1]['rate'])

    newRow = {'date':recentRate.json()["data"][0]["timestamp"], 'unixDate':unixDate, 'time': timeTotal, 'rate':recentRate.json()["data"][0]["last"], 'rateDiff':rateDiff, 'rateDiff_acc':rateDiff_acc}
    print(newRow)
    sys.stdout.flush()

    inRateDf = inRateDf.append(newRow, ignore_index=True)

    print("===== appendRecentRateDf END =====")
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
    klineMin = getKLineMin(coinKind, 1)
    os.makedirs("klines", exist_ok=True)
    now = dt_now.strftime('%Y%m%d-%H%M%S')
    outfilename_kline = "klines/klines_" + now + ".txt.gz"
    with gzip.open(outfilename_kline, 'wt') as outfp:
        outfp.write(json.dumps(klineMin.json()))

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
#    if -1 == orderId:
    if not afterBuyFlg:
        # 買い前処理実施
        print("MAIN start BeforeBuy afterBuyFlg:" + str(afterBuyFlg))
        sys.stdout.flush()
        if beforeBuyAnalSec < TREND_ANAL_DURATION:
            # 買い前分析期間中処理実施
            print("MAIN start BeforeBuyAnalytics beforeBuyAnalSec:" + str(beforeBuyAnalSec) + " TREND_ANAL_DURATION:" + str(TREND_ANAL_DURATION))
            sys.stdout.flush()
            #print(beforeBuyRateDf)
            beforeBuyRateDf = appendRecentRateDf(coinKind, beforeBuyRateDf)
            print(beforeBuyRateDf)
            sys.stdout.flush()

            beforeBuyAnalSec += WAIT_SEC
            print("MAIN end BeforeBuyAnalytics")
            sys.stdout.flush()
        else:
            # 買い前分析期間満了後処理実施
            print("MAIN start BeforeBuyAnalyticsExpire beforeBuyAnalSec:" + str(beforeBuyAnalSec) + " TREND_ANAL_DURATION:" + str(TREND_ANAL_DURATION))
            sys.stdout.flush()
            beforeBuyRateDf = appendRecentRateDf(coinKind, beforeBuyRateDf)
#            print(beforeBuyRateDf)
#            sys.stdout.flush()

            # 傾き分析処理
            beforeBuyTrend = analysisTrend(beforeBuyRateDf)
            #print(beforeBuyTrend)
            #sys.stdout.flush()

            # 傾き判定
            if beforeBuyTrend > BUY_THRESHOLD_TREND:
                # 買い対象
                print("MAIN BuyOrder BUY beforeBuyTrend:" + str(beforeBuyTrend) + " > BUY_THRESHOLD_TREND:" + str(BUY_THRESHOLD_TREND))
                sys.stdout.flush()

                orderId = makeBuyOrder(coinKind)
                print("MAIN BuyOrder end orderId:" + str(orderId))
                sys.stdout.flush()

                afterBuyFlg = True
                print("MAIN BuyOrder afterBuyFlg:" + str(afterBuyFlg))
                sys.stdout.flush()
            else:
                # 買い対象外(STAY)
                print("MAIN BuyOrder STAY beforeBuyTrend:" + str(beforeBuyTrend) + " <= BUY_THRESHOLD_TREND:" + str(BUY_THRESHOLD_TREND))
                sys.stdout.flush()

            beforeBuyAnalSec = 0
            beforeBuyRateDf = beforeBuyRateDf.drop(columns=['date','rate','rateDiff','rateDiff_acc','time','unixDate'])
            beforeBuyRateDf = beforeBuyRateDf.dropna(how='all')
            print(beforeBuyRateDf)
            print("MAIN end BeforeBuyAnalyticsExpire")
            sys.stdout.flush()

        print("MAIN end BeforeBuy afterBuyFlg:" + str(afterBuyFlg))
        sys.stdout.flush()
    else:
        # 買い後処理実施
        print("MAIN start AfterBuy afterBuyFlg:" + str(afterBuyFlg))
        sys.stdout.flush()

        if afterBuyAnalSec < AFTER_BUY_ANAL_DURATION:
            # 買い後分析期間中処理実施
            print("MAIN start AfterBuy afterBuyAnalSec:" + str(afterBuyAnalSec) + " AFTER_BUY_ANAL_DURATION:" + str(AFTER_BUY_ANAL_DURATION))
            sys.stdout.flush()
            #print(afterBuyRateDf)
            afterBuyRateDf = appendRecentRateDf(coinKind, afterBuyRateDf)
            print(afterBuyRateDf)
            sys.stdout.flush()

            afterBuyAnalSec += WAIT_SEC

            # 最新レートが注文時レートよりLOSSCUT_THRESHOLD_AMOUNT％以下となっていたら売却する
            if (buyRate * ( LOSSCUT_THRESHOLD_AMOUNT / 100 ) ) < float(afterBuyRateDf.iloc[-1]['rate']):
                # 売り対象外(STAY)
                print("MAIN AmountLosscut STAY buyRate:" + str(buyRate) + " LOSSCUT_THRESHOLD_AMOUNT:" + str(LOSSCUT_THRESHOLD_AMOUNT)  + " LosscutThreshold:" + str(buyRate * ( LOSSCUT_THRESHOLD_AMOUNT / 100 )) + " < RecentRate:" + afterBuyRateDf.iloc[-1]['rate'])
                sys.stdout.flush()
            else:
                # 売り対象
                print("MAIN AmountLosscut SELL buyRate:" + str(buyRate) + " LOSSCUT_THRESHOLD_AMOUNT:" + str(LOSSCUT_THRESHOLD_AMOUNT)  + " LosscutThreshold:" + str(buyRate * ( LOSSCUT_THRESHOLD_AMOUNT / 100 )) + " >= RecentRate:" + afterBuyRateDf.iloc[-1]['rate'])
                sys.stdout.flush()

                orderId_sell = makeSellOrder(coinKind)
                print("MAIN AmountLosscut end orderId_sell:" + str(orderId_sell))
                sys.stdout.flush()

                afterBuyAnalSec = 0
                afterBuyRateDf = afterBuyRateDf.drop(columns=['date','rate','rateDiff','rateDiff_acc','time','unixDate'])
                afterBuyRateDf = afterBuyRateDf.dropna(how='all')
                print(afterBuyRateDf)

                afterBuyFlg = False
                print("MAIN AmountLosscut afterBuyFlg:" + str(afterBuyFlg) + " buyRate:" + str(buyRate))
                sys.stdout.flush()

            print("MAIN end AfterBuy")
            sys.stdout.flush()
        else:
            # 買い後分析期間満了後処理実施
            print("MAIN start AfterBuyExpire afterBuyAnalSec:" + str(afterBuyAnalSec) + " AFTER_BUY_ANAL_DURATION:" + str(AFTER_BUY_ANAL_DURATION))
            sys.stdout.flush()
            afterBuyRateDf = appendRecentRateDf(coinKind, afterBuyRateDf)
#            print(afterBuyRateDf)
#            sys.stdout.flush()

            # 傾き分析処理
            afterBuyTrend = analysisTrend(afterBuyRateDf)
            #print(afterBuyTrend)
            #sys.stdout.flush()

            # 傾き判定
            if ( afterBuyTrend >= LOSSCUT_THRESHOLD_TREND ) and ((buyRate * ( LOSSCUT_THRESHOLD_AMOUNT / 100 ) ) < float(afterBuyRateDf.iloc[-1]['rate'])) :
                # 売り対象外(STAY)
                print("MAIN SellOrder STAY afterBuyTrend:" + str(afterBuyTrend) + " >= LOSSCUT_THRESHOLD_TREND:" + str(LOSSCUT_THRESHOLD_TREND))
                print("MAIN AmountLosscut STAY buyRate:" + str(buyRate) + " LOSSCUT_THRESHOLD_AMOUNT:" + str(LOSSCUT_THRESHOLD_AMOUNT)  + " LosscutThreshold:" + str(buyRate * ( LOSSCUT_THRESHOLD_AMOUNT / 100 )) + " < RecentRate:" + afterBuyRateDf.iloc[-1]['rate'])
                sys.stdout.flush()
            else:
                # 売り対象
                print("MAIN SellOrder SELL afterBuyTrend:" + str(afterBuyTrend) + " < LOSSCUT_THRESHOLD_TREND:" + str(LOSSCUT_THRESHOLD_TREND))
                print("MAIN AmountLosscut SELL buyRate:" + str(buyRate) + " LOSSCUT_THRESHOLD_AMOUNT:" + str(LOSSCUT_THRESHOLD_AMOUNT)  + " LosscutThreshold:" + str(buyRate * ( LOSSCUT_THRESHOLD_AMOUNT / 100 )) + " >= RecentRate:" + afterBuyRateDf.iloc[-1]['rate'])
                sys.stdout.flush()

                orderId_sell = makeSellOrder(coinKind)
                print("MAIN SellOrder end orderId_sell:" + str(orderId_sell))
                sys.stdout.flush()

                afterBuyFlg = False
                print("MAIN SellOrder afterBuyFlg:" + str(afterBuyFlg) + " buyRate:" + str(buyRate))
                sys.stdout.flush()

            afterBuyAnalSec = 0
            afterBuyRateDf = afterBuyRateDf.drop(columns=['date','rate','rateDiff','rateDiff_acc','time','unixDate'])
            afterBuyRateDf = afterBuyRateDf.dropna(how='all')
            print(afterBuyRateDf)
            print("MAIN end AfterBuyExpire")
            sys.stdout.flush()

        print("MAIN end AfterBuy afterBuyFlg:" + str(afterBuyFlg))
        sys.stdout.flush()

    print("")
    print("MAIN wait " + str(waitSec) + "(sec) start" )
    sys.stdout.flush()
    time.sleep(waitSec)



