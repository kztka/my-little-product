# -*- coding: utf-8 -*-
import os
import sys
import glob
import codecs
import configparser
import csv
import datetime

modpass = "D:\\Steam\\steamapps\\workshop\\content\\1468720"
moddirs = glob.glob( modpass + "\\*")

print(modpass)

#ヘッダー書き出し
headerlist = ["name","modnumber","animset","hp","dmg","attrange","splashdmg","splashdmgrng","impactforce","meleeblock","rangeblock","rangeblockforce","meleearmor","rangearmor","rangearmorforce","attacktime","attackbreak","projectile","projectilespeed","burstamount","burstrate","unitheight","unitwidth","soundpres","human","accuracy"]

dt_now = datetime.datetime.now()
now = dt_now.strftime('%Y%m%d-%H%M%S')
outfilename = "UEBS2_unitdata_" + now + ".csv"
outfp = codecs.open(outfilename, 'w', 'utf-8')

writer = csv.writer(outfp)
writer.writerow(headerlist)

#modfile読み込み＆csv書き出し
for moddir in moddirs:
    print(moddir + " start")
    modfiles = glob.glob( moddir + "\\*" )
    modnumber = os.path.basename(os.path.normpath(moddir))
    for modfile in modfiles:
        if modfile.endswith('.bgmod'):
            # modfile設定値読み込み
            print("    " + modfile)
            modfilename = os.path.splitext(os.path.basename(modfile))[0]
            #print("    " + modfilename)
            
            infp = codecs.open(modfile, 'r', 'utf-8')
            modfile_string = '[dummy_section]\n' + infp.read()
            infp.close
            
            config = configparser.ConfigParser()
            config.read_string(modfile_string)
            dummy_section = config['dummy_section']
            #print(dict(dummy_section))
            
            # csv書き出し
            rowlist = []
            rowlist.append(modfilename)
            rowlist.append(modnumber)
            rowlist.append(dummy_section.get('animset','None'))
            rowlist.append(dummy_section.get('hp','None'))
            rowlist.append(dummy_section.get('dmg','None'))
            rowlist.append(dummy_section.get('attrange','None'))
            rowlist.append(dummy_section.get('splashdmg','None'))
            rowlist.append(dummy_section.get('splashdmgrng','None'))
            rowlist.append(dummy_section.get('impactforce','None'))
            rowlist.append(dummy_section.get('meleeblock','None'))
            rowlist.append(dummy_section.get('rangeblock','None'))
            rowlist.append(dummy_section.get('rangeblockforce','None'))
            rowlist.append(dummy_section.get('meleearmor','None'))
            rowlist.append(dummy_section.get('rangearmor','None'))
            rowlist.append(dummy_section.get('rangearmorforce','None'))
            rowlist.append(dummy_section.get('attacktime','None'))
            rowlist.append(dummy_section.get('attackbreak','None'))
            rowlist.append(dummy_section.get('projectile','None'))
            rowlist.append(dummy_section.get('projectilespeed','None'))
            rowlist.append(dummy_section.get('burstamount','None'))
            rowlist.append(dummy_section.get('burstrate','None'))
            rowlist.append(dummy_section.get('unitheight','None'))
            rowlist.append(dummy_section.get('unitwidth','None'))
            rowlist.append(dummy_section.get('soundpres','None'))
            rowlist.append(dummy_section.get('human','None'))
            rowlist.append(dummy_section.get('accuracy','None'))
            writer.writerow(rowlist)