# -*- coding: utf-8 -*-
import sys
import json
import codecs
import datetime
import subprocess
import time

args = sys.argv

if 2 != len(args):
    print("Usage: tweet_listdelete.py [delete tweetlist_YYMMDD-hhmmss.txt filepath]")
    sys.stdout.flush()
    sys.exit(1)

# 実行時、直下にtweet_delete.pyが存在する事。
# ※nohupでprintがログに書き込まれないのでflushを付加

infilename = args[1]
infp = codecs.open(infilename, 'r', 'utf-8')
tweetsJson = json.load(infp)

infp.close

tweetCnt = 0
tweetMaxNum = len(tweetsJson)

# ログの標準出力時にツイート内容出力で
# UnicodeEncodeError: 'ascii' codec can't encode characters in position 140-155: ordinal not in range(128)が出るため以下実施
sys.stdout = codecs.getwriter("utf-8")(sys.stdout)

for tweetjson in tweetsJson:
    tweetCnt += 1

    full_text = tweetjson.get("full_text")
    created_at = tweetjson.get("created_at")
    tweetid = tweetjson.get("id")

    dt_now = datetime.datetime.now()
    now = dt_now.strftime('%Y/%m/%d %H:%M:%S')

    print("")
    print("[" + now + "] number " + str(tweetCnt) + "/" + str(tweetMaxNum) + " delete start: [id]" + tweetid + " [created_at]" + created_at + " [full_text]" + full_text )
    sys.stdout.flush()

    cmd = ["python","tweet_delete.py",tweetid]
    subprocess.call(cmd)

    print("[" + now + "] number " + str(tweetCnt) + "/" + str(tweetMaxNum) + " delete end: [id]" + tweetid + " [created_at]" + created_at + " [full_text]" + full_text )
    print("sleep 1800(30min) start")
    sys.stdout.flush()

    time.sleep(1800)
