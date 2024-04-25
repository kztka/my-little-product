# -*- coding: utf-8 -*-
import sys
import json
import codecs
import datetime

args = sys.argv

# 本ツール実施前にtweets.jsの先頭行を削除して[に置き換える事
# Before : window.YTD.tweets.part0 = [
# After  : [

if 2 != len(args):
    print("Usage: tweet_listup.py [tweets.js filepath]")

infilename = args[1]
infp = codecs.open(infilename, 'r', 'utf-8')
tweetsJson = json.load(infp)

infp.close

dt_now = datetime.datetime.now()
now = dt_now.strftime('%Y%m%d-%H%M%S')
outfilename = "tweetlist_" + now + ".txt"
outfp = codecs.open(outfilename, 'w', 'utf-8')

tweetCnt = 0
tweetMaxNum = len(tweetsJson)

outfp.write("[\n")

for tweetjson in tweetsJson:
    tweetCnt += 1
    tweet = tweetjson.get("tweet")   

    full_text = tweet.get("full_text")
    created_at = tweet.get("created_at")
    tweetid = tweet.get("id")

    # full_text内の改行コードを置換する
    full_text = full_text.replace('\n','')
    full_text = full_text.replace('\"','\\"')

    print("number " + str(tweetCnt) + "/" + str(tweetMaxNum) + ": [id]" + tweetid + " [created_at]" + created_at + " [full_text]" + full_text )

    outfp.write( "{\"id\" : \"" + tweetid + "\",\"created_at\" : \"" + created_at + "\",\"full_text\" : \"" + full_text + "\"}")

    if tweetCnt != tweetMaxNum:
        outfp.write(",\n")
    else:
        outfp.write("\n")


outfp.write("]\n")
outfp.close


