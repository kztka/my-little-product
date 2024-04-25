# -*- coding: utf-8 -*-
import sys
import datetime
import time
import random

args = sys.argv

if 5 != len(args):
    print("Usage: createWriteTimes.py [startTime as YYYY/mm/dd-HH:MM:SS] [interval(sec)] [randrange[sec]] [count]")
    sys.stdout.flush()
    sys.exit(1)

startTime = args[1]
intervalSec = int(args[2])
randRange = int(args[3])
createCnt = int(args[4])

splitTime = startTime.split('-')
inputDate = splitTime[0].split('/')
inputTime = splitTime[1].split(':')

#print(splitTime)
#print(inputTime)
#print(inputDate)

dt_input = datetime.datetime( int(inputDate[0]), int(inputDate[1]), int(inputDate[2]), int(inputTime[0]), int(inputTime[1]), int(inputTime[2]) )
#print(dt_input)
#print(dt_input.second)

print("入力時刻:")
print(dt_input.strftime('%Y/%m/%d %H:%M:%S'))
print("作成時刻:")

# 指定数の書き込み時刻を作成。間隔はintervalの秒数の間でランダムにふらす
dt_current = dt_input
for currentCnt in range(createCnt):
    # ランダムのふらす時刻を作成
    random_sec = random.randint(0, randRange)
    #print(random_sec)
    dt_future = dt_current + datetime.timedelta(seconds=random_sec)
    print(dt_future.strftime('%Y/%m/%d %H:%M:%S'))
    # 次回ループの時刻を作成
    dt_current = dt_current + datetime.timedelta(seconds=intervalSec)

