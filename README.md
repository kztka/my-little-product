# 個人で作成したツール/ソフトウェア集
Copyright(C) 2024 Kazuki Takahashi  All rights reserved in this repository files.  
本リポジトリ内のファイルは全て著作権関連法令に基づいた取り扱いをお願いいたします。  

### 目次
- Unity制作中ゲーム「Empire of Mechs」(game/empireofmechs(TBD))
- 仮想通貨自動取引プログラム(auto_exchange/GMOcoin)
- Xポスト一括自動削除(xtool)
- X自動フォロー/アンフォロー(xtool)
- 楽譜スコアから自パートのみを切り抜くツール(gakuhu_part_pickup)
- ゲームのキャラクターパラメータCSV抽出ツール(gametool)
- Windows画像形式一括変換バッチ(windows_batch)
- ネット掲示板形式の小説作成時に各々の書込み時刻をふらすツール(shosetsu/5ch_like)

## Unity制作中ゲーム「Empire of Mechs」(game/empireofmechs(TBD))
#### 概要
インディーズゲームとして個人で制作しているターン制戦略シミュレーションゲーム。  
イメージとしては信長の野望のロボット版。  
その他有名SLGタイトル(ギレンの野望、Civ、Paradox社ゲーム等)の要素も足して中毒性を付加し中盤～終盤のダレも解消できるようにする。  
現時点の完成度としてはプロトタイプのごく一部を作成している程度。<br><br>
- DesignDocument  
設計資料/管理簿を格納。  
    - スタティック変数設計.xlsx  
    - データベース設計.xlsx  
    - バグ管理簿.xlsx  
    - 概要設計.xlsx  
    - 画面遷移設計.xlsx  
    - 設定ファイル設計.xlsx  

- Assets  
スクリプトやリソースファイル等を格納したディレクトリ。  
    - Data  
      DBに格納する各種ゲームデータ
    - Image  
      ゲームで使用する各種画像  
    - Packages  
      スクリプトで使用する外部DLL  
    - Plugins  
      Unityの機能を拡張する外部DLL  
    - Scenes  
      ゲームの各画面データ  
    - Script  
      ゲームの制御スクリプト(C#)  
    - StreamingAssets  
      ビルドバイナリに含まずターゲットのマシンに直接格納するファイル  
    - TextMesh Pro  
      ゲーム上でのテキスト表示プラグイン  
    - Tilemap  
      タイルマップ(画像をタイル状に配置)のデータ  


#### 規模 / 作成期間
約1.2kL / 90人時程度 ※2024/4/30時点
#### 使い方
Unity Hubでエディターバージョン2022.3.12f1で新規プロジェクトを作成し、そのプロジェクトのAssetsを本リポジトリのAssetsに差し替える
#### 動作確認環境
Windows 11  
Unity Hub 3.8.0  
Unity Editor 2022.3.12f1  
その他使用している外部パッケージは「概要設計.xlsx」の「使用OSS」シートを参照

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
  
  
#### 規模 / 作成期間
約0.9kL / 50人時程度  
※2ファイル合計は1.3kLだがcoin_autoexchange_technical.pyはマイナーチェンジ版の為変更部分のみ加算


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

## Xポスト一括自動削除(xtool)
#### 概要
ユーザがリストアップした削除対象Xポストリストを元に一括で自動削除を行うツール。  
通常、業者に費用を払って業者サイト/アプリ経由で行う作業を無料で実施できる。<br><br>

- tweet_listup.py  
エクスポートしたポスト履歴内のdata->tweets.jsから純粋な内容(ID,投稿日時,本文)のみを抜き出したリストを抽出する。  
ポスト履歴のエクスポート方法は以下サポートページを参照。  
https://help.twitter.com/ja/managing-your-account/how-to-download-your-x-archive  
- token_refresh.py  
XへのAPIアクセスに必要なアクセストークンを自動的にリフレッシュする  
- tweet_listdelete.py  
tweet_listup.pyで抽出したリストからユーザが必要なポストのみを削除したリスト（削除対象ポストリスト）を元に一括で削除処理を行う。  
※月間APIアクセス数制限(月間1500アクセス)の為30分に1ポストの削除となる。  
- tweet_delete.py  
tweet_listdelete.pyから実行されるサブツール。指定されたIDのポストを削除する。単独での実行も可能。  

#### 規模 / 作成期間
約0.2kL / 20人時程度
#### 使い方
1. 以下サポートページを参考にポスト履歴を取得する(申請してから大体24hで取得できる)  
https://help.twitter.com/ja/managing-your-account/how-to-download-your-x-archive  
2. 取得したポスト履歴を解凍しdataフォルダにあるtweets.jsをtweet_listup.pyのある環境に転送する  
3. tweets.jsからポストリストを抽出する  
     1. tweets.jsを一部手動で加工(先頭行を削除して[に置き換える)  
        Before : window.YTD.tweets.part0 = [  
        After  : [  
     2. tweet_listup.pyを実行して直下にポストリストが出力されている事を確認  
        `python tweet_listup.py [tweets.js filepath]`  
        →直下にtweetlist_YYYYMMDD-hhmmss.txtが出力  
4. ポストリストを編集して**削除不要な**ポストをリストから削除
`vi tweetlist_YYYYMMDD-hhmmss.txt`
5. Twitter Developer Portalに対してAppの認証をOauth2.0で行う。  
以下をブラウザのURLに打ち込む  
`https://twitter.com/i/oauth2/authorize?response_type=code&client_id=[Client ID]&redirect_uri=https://127.0.0.1:3000/cb&scope=tweet.read%20tweet.write%20users.read%20follows.write%20offline.access&state=abc&code_challenge=[計算したcode_challengeの値]&code_challenge_method=s256`
承認すると以下がリダイレクトされるのでcodeの値を保存しておく。  
`https://127.0.0.1:3000/cb?state=abc&code=[codeの値]`  
※事前にポスト削除対象アカウントのTwitter Developer Accountを開設しClient IDとClient Secretを取得しておくこと。以下参考  
  Twitter APIのKeyやSecretの取得・確認手順※2023年10月最新  
　https://programming-zero.net/twitter-api-process/  
※事前にTwitter Developer Portalの今回使用App->User authentication settingsの設定を行っておくこと。  
  「Type of App」-> Native App  
  「App info」-> Callback URI / Redirect URL (※認証完了時にリダイレクトされるURL。今回は認証結果の値が欲しいだけなので適当なURLを設定) :  
                 https://127.0.0.1:3000/cb  
                 http://127.0.0.1:3000/cb  
                 Website URL :  
                 https://twitter.com/[ポスト削除対象アカウントID]  
                 他は入力不要  
※事前に以下を参考にcode_verifierとcode_challengeの値を計算しておくこと  
  【Python】OAuth2.0認証を利用してTwitter APIと連携し、認証されたTwitter IDを得る方法  
  https://zenn.dev/yuk6ra/articles/0874eac6336c40  
  ````
  code_verifier = hashlib.sha256(os.urandom(128)).hexdigest()
  code_challenge_sha256 = hashlib.sha256(code_verifier.encode()).digest()
  code_challenge = base64.urlsafe_b64encode(code_challenge_sha256).decode().rstrip("=")
  ````
6. アクセストークンを取得/自動リフレッシュ  
`nohup python token_refresh.py [ClientID] [ClientSecret] [code] [redirect_uri] [code_verifier] > token_refresh-`date +%Y%m%d_%H%M%S`.log 2>&1 &`  
→直下にaccess_token.txtが生成される。  
7. ツイート削除実行  
`nohup python tweet_listdelete.py [4.で作成した削除対象ポストリスト] > tweet_listdelete-`date +%Y%m%d_%H%M%S`.log 2>&1 &`  

#### 動作確認環境
Amazon Linux 2  
Python 2.7.18  

## X自動フォロー/アンフォロー(xtool)
#### 概要
#### 規模 / 作成期間
#### 使い方
#### 動作確認環境

## 楽譜スコアから自パートのみを切り抜くツール(gakuhu_part_pickup)
#### 概要
#### 規模 / 作成期間
#### 使い方
#### 動作確認環境

## ゲームのキャラクターパラメータCSV抽出ツール(gametool)
#### 概要
#### 規模 / 作成期間
#### 使い方
#### 動作確認環境

## Windows画像形式一括変換バッチ(windows_batch)
#### 概要
#### 規模 / 作成期間
#### 使い方
#### 動作確認環境

## ネット掲示板形式の小説作成時に各々の書込み時刻をふらすツール(shosetsu/5ch_like)
#### 概要
#### 規模 / 作成期間
#### 使い方
#### 動作確認環境
