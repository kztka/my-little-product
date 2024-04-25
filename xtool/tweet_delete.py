# -*- coding: utf-8 -*-
import sys
import subprocess
import json
import codecs
import time

# 本ツール連続実行は少なくとも30分間隔を置く事。
# User rate limit (User context): 50 requests per 24 hours window per each authenticated user

# 本ツール実行前にtoken_refresh.pyを使用してaccess_token.txtが直下に生成されていること
# ※nohupでprintがログに書き込まれないのでflushを付加

args = sys.argv

if 2 != len(args):
    print("Usage: tweet_delete.py [target tweet id]")
    sys.stdout.flush()
    sys.exit(1)

infilename = "access_token.txt"
infp = codecs.open(infilename, 'r', 'utf-8')
access_token_list = infp.readlines()

infp.close

access_token = access_token_list[0].rstrip()

print("access_token: " + access_token)

cmd1 = 'curl -XDELETE -H "Content-type: application/json" -H "Authorization: Bearer '
cmd2 = access_token
cmd3 = '" "https://api.twitter.com/2/tweets/'
cmd4 = args[1]
cmdend = '"'

cmd = cmd1 + cmd2 + cmd3 + cmd4 + cmdend
print("SendURI: " + cmd) 
sys.stdout.flush()

result = subprocess.Popen( cmd, stdout=subprocess.PIPE,shell=True).communicate()[0]
print("Result: " + result)
sys.stdout.flush()
