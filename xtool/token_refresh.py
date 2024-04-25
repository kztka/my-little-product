# -*- coding: utf-8 -*-
import sys
import subprocess
import json
import codecs
import time
import datetime

args = sys.argv

# アクセストークンを定期的に取得してファイルに書き込む
# ※nohupでprintがログに書き込まれないのでflushを付加

if 6 != len(args):
    print("Usage: token_refresh.py [ClientID] [ClientSecret] [code] [redirect_uri] [code_verifier]")

initCmd = ""

initCmd += 'curl --location --request POST "https://api.twitter.com/2/oauth2/token" --basic -u "'
initCmd += args[1]
initCmd += ':'
initCmd += args[2]
initCmd += '" --header "Content-Type: application/x-www-form-urlencoded" --data-urlencode "code='
initCmd += args[3]
initCmd += '" --data-urlencode "grant_type=authorization_code" --data-urlencode "client_id='
initCmd += args[1]
initCmd += '" --data-urlencode "redirect_uri='
initCmd += args[4]
initCmd += '" --data-urlencode "code_verifier='
initCmd += args[5]
initCmd += '"'

print("InitialSendURI: " + initCmd)
sys.stdout.flush()

# 初回アクセストークンを取得
initResult = subprocess.Popen( initCmd, stdout=subprocess.PIPE,shell=True).communicate()[0]
print("InitialResult: " + initResult)
sys.stdout.flush()

initResult_json = json.loads(initResult)
access_token = initResult_json.get("access_token")
refresh_token = initResult_json.get("refresh_token")

print("access_token: " + access_token)
print("refresh_token: " + refresh_token)
sys.stdout.flush()

outfilename = "access_token.txt"
outfp = codecs.open(outfilename, 'w', 'utf-8')

outfp.write(access_token)
outfp.flush()

outfp.close

refCount = 0

# リフレッシュ処理
while True:
    print("refresh wait sleep 7000.")
    sys.stdout.flush()
    time.sleep(7000)
    #time.sleep(30)

    refCmd = ""
    
    refCmd += 'curl --location --request POST "https://api.twitter.com/2/oauth2/token" --basic -u "'
    refCmd += args[1]
    refCmd += ':'
    refCmd += args[2]
    refCmd += '" --header "Content-Type: application/x-www-form-urlencoded" --data-urlencode "refresh_token='
    refCmd += refresh_token
    refCmd += '" --data-urlencode "grant_type=refresh_token" --data-urlencode "client_id='
    refCmd += args[1]
    refCmd += '"'

    print("")

    refCount += 1
    dt_now = datetime.datetime.now()
    now = dt_now.strftime('%Y/%m/%d %H:%M:%S')
    print( "[" + now + "] " + str(refCount) + " times refresh start.")
    print("refreshSendURI: " + refCmd)
    sys.stdout.flush()

    refResult = subprocess.Popen( refCmd, stdout=subprocess.PIPE,shell=True).communicate()[0]

    print("refreshResult: " + refResult)
    sys.stdout.flush()

    refResult_json = json.loads(refResult)

    #print("ResultJson: " + json.dumps(result_json, ensure_ascii=False) )

    access_token = refResult_json.get("access_token")
    refresh_token = refResult_json.get("refresh_token")

    print("refresh access_token: " + access_token)
    print("refresh refresh_token: " + refresh_token)
    sys.stdout.flush()

    outfp = codecs.open(outfilename, 'w', 'utf-8')

    outfp.write(access_token)
    outfp.flush()

    outfp.close

