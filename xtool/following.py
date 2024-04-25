# -*- coding: utf-8 -*-
import sys
import subprocess
import json
import codecs
import time

args = sys.argv

if 5 != len(args):
    print("Usage: get_followers_list.py [Bearer] [target user id] [infilename] [option(follow or unfollow)]")

follow_option = args[4]

if "follow" == follow_option:
    cmd1 = 'curl -XPOST -H "Content-type: application/json" -H "Authorization: Bearer '
    cmd2 = args[1]
    cmd3 = '" "https://api.twitter.com/2/users/'
    cmd4 = args[2]
    cmd5 = '/following" -d \'{"target_user_id": "'
    cmdend = '"}\''
else:
    cmd1 = 'curl -XDELETE -H "Authorization: Bearer '
    cmd2 = args[1]
    cmd3 = '" "https://api.twitter.com/2/users/'
    cmd4 = args[2]
    cmd5 = '/following/'
    cmdend = '"'

infilename = args[3]

infp = codecs.open(infilename, 'r', 'utf-8')
userdatalist = infp.readlines()

for userdata in userdatalist:
    userdata_json = json.loads(userdata)

    cmd = cmd1 + cmd2 + cmd3 + cmd4 + cmd5 + userdata_json.get("id") + cmdend
    print("SendURI: " + cmd) 

    result = subprocess.Popen( cmd, stdout=subprocess.PIPE,shell=True).communicate()[0]
    print("Result: " + result)

    print("Sleep 30.")
    time.sleep(30)

infp.close
