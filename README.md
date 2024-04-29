# 個人で作成したツール/ソフトウェア集
Copyright(C) 2024 Kazuki Takahashi  All rights reserved in this repository files.  
本リポジトリ内のファイルは全て著作権関連法令に基づいた取り扱いをお願いいたします。  

### 目次
- Unity制作中ゲーム「Empire of Mechs」(game/empireofmechs(TBD))
- 仮想通貨自動取引プログラム(auto_exchange/GMOcoin)
- Xポスト自動削除、自動フォロー/アンフォロー(xtool)
- 楽譜スコアから自パートのみを切り抜くツール(gakuhu_part_pickup)
- ゲームのキャラクターパラメータCSV抽出ツール(gametool)
- Windows画像形式変換バッチ(windows_batch)
- ネット掲示板形式の小説作成時に各々の書込み時刻をふらすツール(shosetsu/5ch_like)

## 仮想通貨自動取引プログラム(auto_exchange/GMOcoin)
#### 概要
- coin_autoexchange.py  
GMOコインが提供しているAPIを使用して仮想通貨の値動きの波を分析して自動的に波形の谷で買い、山で売るプログラム。  
Scikit-learn機械学習の線形回帰(Linear Regression)を使用し一定期間内の値動きについて傾きを抽出する事で谷なのか山なのかを判断する。  
ビットコインを始めとする23銘柄に対応。<br><br>
参考：  
GMOコインAPI仕様書  
https://api.coin.z.com/docs/?python#  
Scikit-learn で線形回帰  
https://qiita.com/0NE_shoT_/items/08376b08783cd554b02e  
  
- coin_autoexchange_technical.py  
coin_autoexchange.pyのMACD版。  
MACDは金融テクニカル分析の一種でこちらも波形の谷で買い判断、山で売り判断をするトレンド分析手法の一種。  
分析ライブラリは「TA-Lib」を使用。<br><br>
参考：  
MACD  
https://info.monex.co.jp/technical-analysis/indicators/002.html  
【Python】【テクニカル指標】MACDの算出とローソク足への追加描画  
https://note.com/scilabcafe/n/ne7e080cad499  
  
  
#### 作成期間
5日程度


#### 使い方
```nohup python3 coin_autoexchange.py BTC 80 > coin_autoexchange-`date +%Y%m%d_%H%M%S`.log 2>&1 &```  
```nohup python3 coin_autoexchange_technical.py BTC 80 > coin_autoexchange_technical-`date +%Y%m%d_%H%M%S`.log 2>&1 &```  
※[オプション1] 銘柄種類を入力 (例：BTC)  
　[オプション2] 取引余力から何％までを購入に充てるかを入力 (例:80)  
　銘柄の種類はこちらを参照　　https://api.coin.z.com/docs/?python#parameters-ref  
※事前に直下に以下ファイルを配置する。  
　apikey.txt (GMOコイン側で発行したapikeyを記述)  
　apisecret.txt (GMOコイン側で発行したapisecretを記述)  


#### 動作確認環境
Amazon Linux 2  
Python 3.7.16  
  
また、事前に以下ライブラリをインストールする  
`pip3 install requests`  
`pip3 install --upgrade urllib3==1.26.15`　※python3.7だとrequestsが使っているurllib3の最新版(2.0.7)が参照するopenssl1.1.1が使用できない為、urllib3をダウングレードする。  
`pip3 install pandas`  
`pip3 install scikit-learn`  
`pip3 install matplotlib`  
`pip3 install seaborn`  
`pip3 install mplfinance`  
TA-Libインストール  
`sudo yum install python3-devel`  
`wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz`  
`tar -zxvf ta-lib-0.4.0-src.tar.gz`  
`cd ta-lib`  
`./configure --prefix=/usr`  
`sudo make ( 削除はsudo make clean )`  
`sudo make install ( 削除はsudo make uninstall )`  
`cd ../`  
`pip3 install TA-Lib`  
