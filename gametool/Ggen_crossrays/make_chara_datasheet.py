# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import sys
import datetime
import csv
import re
import codecs

args = sys.argv

if 1 != len(args):
    print("Usage: python3 make_chara_datasheet.py")
    sys.stdout.flush()
    sys.exit(1)

# キャラクターLv99ステータス取得関数
def CharaLv99StatusGet(chara_soap):
    ret_list = []
    # tbodyが2重にある箇所を抽出 
    chara_soap_tbodys = chara_soap.find_all("tbody")
    for chara_soap_tbody in chara_soap_tbodys:
        if chara_soap_tbody.find("tbody") is not None:
            sample_tbody =chara_soap_tbody.find("tbody")
            # Lv99のステータスを抽出
            sample_trs = sample_tbody.find_all("tr")
            for sample_tr in sample_trs:
                #print(sample_tr)
                sample_tds = sample_tr.find_all("td")
                sample_td_count = 0
                lv99_flg = False
                for sample_td in sample_tds:
                    sample_td_count += 1
                    #print(sample_td.text.replace('\n', ''))
                    # tdの最初が99であればステータス抽出
                    # tdの初回で名前にリンクがある場合はその先のlv99のステータスデータを取得
                    if lv99_flg and (sample_td_count != 1):
                        #print(sample_td.text)
                        ret_list.append(sample_td.text.replace('\n', ''))
                    elif (sample_td_count == 1) and (sample_td.text.replace('\n', '') == "99"):
                        lv99_flg = True
                    else:
                        break
    return ret_list

# リスト作成
chara_list = []

# キャラクター一覧解析
list_url = "https://w.atwiki.jp/generation-crossrays/pages/32.html"  # atwikiのキャラクター一覧のページのURL
list_html = requests.get(list_url)
list_soup = BeautifulSoup(list_html.content, "html.parser")

list_soup_a = list_soup.find_all("a", string=re.compile('^キャラクター/'))
# print(list_soup_a)

for soup_a in list_soup_a:
    print("LOOP1 START :" + str(soup_a))
    series_href = "https:" + soup_a.get("href")
    series_name = soup_a.text
    #print(series_href)
    # 各シリーズ毎キャラクター一覧解析
    series_html = requests.get(series_href)
    series_soap = BeautifulSoup(series_html.content, "html.parser")
    ## テーブル取得
    series_soap_tbodys = series_soap.find_all("tbody")
    # print(series_soap_tbodys)
    for series_soap_tbody in series_soap_tbodys:
        series_soap_trs = series_soap_tbody.find_all("tr")
        tr_count = 0
        for series_soap_tr in series_soap_trs:
            tr_count += 1
            # trの初回はヘッダーなのでスキップ
            if tr_count == 1:
                continue
            series_soap_tds = series_soap_tr.find_all("td")
            para_list = []
            chara_lv99_statlist = []
            td_count = 0
            for series_soap_td in series_soap_tds:
                td_count += 1
                # tdの初回で名前にリンクがある場合はその先のlv99のステータスデータを取得
                if (td_count == 1) and (series_soap_td.find("a") is not None):
                    #print(series_soap_td)
                    chara_href = "https:" + series_soap_td.find("a").get("href")
                    chara_html = requests.get(chara_href)
                    chara_soap = BeautifulSoup(chara_html.content, "html.parser")
                    chara_lv99_statlist = CharaLv99StatusGet(chara_soap)
                # パラメータリストへインプット
                para_list.append(series_soap_td.text.replace('\n', ''))
                #print(series_soap_td.text.replace('\n', ''))
            # lv99ステータスデータがある場合はパラメータリストへ追加
            for chara_lv99_stat in chara_lv99_statlist:
                para_list.append(chara_lv99_stat)
            para_list.append(series_name)
            # キャラクターリストへインプット
            chara_list.append(para_list)

#print(chara_list)
# CSV出力
## ヘッダー書き出し
header_list = ["名前","COST","EXP","性格","","指揮","射撃","格闘","守備","反応","覚醒","","補佐","通信","操舵","整備","魅力","初期アビリティ","初期スキル","指揮(Lv99)","射撃(Lv99)","格闘(Lv99)","守備(Lv99)","反応(Lv99)","覚醒(Lv99)","","補佐(Lv99)","通信(Lv99)","操舵(Lv99)","整備(Lv99)","魅力(Lv99)","登場作品"]

dt_now = datetime.datetime.now()
now = dt_now.strftime('%Y%m%d-%H%M%S')
outfilename = "Ggen_crossrays_charadata_" + now + ".csv"
outfp = codecs.open(outfilename, 'w', 'utf-8')

writer = csv.writer(outfp)
writer.writerow(header_list)

for chara_para_list in chara_list:
    writer.writerow(chara_para_list)

outfp.close
