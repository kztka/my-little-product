# -*- coding: utf-8 -*-
import sys
import subprocess
import json
import codecs
import time

args = sys.argv

if 4 != len(args):
    print("Usage: get_followers_list.py [Bearer] [target user id] [outfilename]")

cmd1 = 'curl -XGET -H "Authorization: Bearer '
cmd2 = args[1]
cmd3 = '" "https://api.twitter.com/2/users/'
cmd4 = args[2]
cmd5 = '/following?max_results=1000'
cmdend = '"'

cmd = cmd1 + cmd2 + cmd3 + cmd4 + cmd5 + cmdend
print("InitialSendURI: " + cmd)

outfilename = args[3]
outfp = codecs.open(outfilename, 'w', 'utf-8')

# ページネーション処理
while True:
    result = subprocess.Popen( cmd, stdout=subprocess.PIPE,shell=True).communicate()[0]

    print("Result: " + result)

    result_json = json.loads(result)

    #print("ResultJson: " + json.dumps(result_json, ensure_ascii=False) )

    # meta->next_token
    result_meta = result_json.get("meta")
    print("Meta: " + json.dumps(result_meta) )
    if "next_token" in result_meta:
        result_nexttoken = result_meta.get("next_token")
    else:
        result_nexttoken = ''

    print("NextToken: " + result_nexttoken )

    # data
    result_data = result_json.get("data")

    # data loop
    for follow_user in result_data:
        print(json.dumps(follow_user, ensure_ascii=False))
        outfp.write(json.dumps(follow_user, ensure_ascii=False) + "\n")

    # next_tokenが無い場合はbreak
    if not result_nexttoken:
        print("NONE NextToken loop end")
        break
    else:
        # next_tokenがある場合は次のURLを作成
        print("EXIST NextToken : " + result_nexttoken)
        cmd = cmd1 + cmd2 + cmd3 + cmd4 + cmd5 + '&pagination_token=' + result_nexttoken + cmdend
        print("NextSendURI: " + cmd)

    print("Sleep 60.")
    time.sleep(60)

outfp.close
