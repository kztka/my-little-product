# -*- coding: utf-8 -*-
from PIL import Image
import sys
import datetime
import glob

args = sys.argv

if 2 != len(args):
    print("Usage: python3 gakuhu_part_pickup.py [jpg_dirpath]")
    sys.stdout.flush()
    sys.exit(1)

#本ツール使用時は、読み取り対象ディレクトリにページ番号でソート可能な画像スコアファイルが一式格納されている事。
#切り出し対象エリアは以下で指定(追加する場合はリストを増やす事)。
#貼り付けは縦に繰り返しで行い、長さが新規画像一杯になった場合は一旦画像書き出しを行い次ページに書き込む。
#x軸方向は新規作成画像の幅を超えない事。
class uc_cutarea:
    def __init__(self, left_x, upper_y, right_x, lower_y):
        self.left_x = left_x
        self.upper_y = upper_y
        self.right_x = right_x
        self.lower_y = lower_y

cutareaList = []

# 曲1
#cutareaList.append(uc_cutarea(160,240,3960,600))  #切り出しエリア1(vo1)
#cutareaList.append(uc_cutarea(160,1980,3960,2400))  #切り出しエリア2(ba1)
#cutareaList.append(uc_cutarea(160,3040,3960,3400))  #切り出しエリア3(vo2)
#cutareaList.append(uc_cutarea(160,4780,3960,5200))  #切り出しエリア4(ba2)

# 曲2
cutareaList.append(uc_cutarea(50,310,1400,430))  #切り出しエリア1(vo1)
cutareaList.append(uc_cutarea(50,1150,1400,1350))  #切り出しエリア2(ba1)


#カットエリア拡大率
# 曲1
#cutareaZoom = 1.2
# 曲2
cutareaZoom = 1

#生成先画像サイズ定義
# 曲1
#new_x = 4961    # A4サイズ
#new_y = 7016    # A4サイズ
# 曲1
new_x = 1447    # A6サイズ
new_y = 2039    # A6サイズ

#まずは切り出しエリアの総y軸長さを算出し、新規画像のy軸長さと比較して
#改ページまでの切り出しエリアリストトータルでの書き出し回数を算出する。
cutarea_total_height = 0
for cutarea in cutareaList:
    cutarea_total_height += int((cutarea.lower_y - cutarea.upper_y) * cutareaZoom)

print("cutarea_total_height:" + str(cutarea_total_height))

cutlimit_per_page = 0
cutlimit_per_page = new_y // cutarea_total_height

print("cutlimit_per_page:" + str(cutlimit_per_page))

#生成先新規画像作成
img = Image.new("L", (new_x, new_y), color=255)

dt_now = datetime.datetime.now()
now = dt_now.strftime('%Y%m%d-%H%M%S')

#スコアディレクトリからファイルを読み取り
dirname = args[1]
imgfiles = sorted(glob.glob( dirname + "/*"))

cutcount = 0
pagenum = 1
current_y = 0

for imgfilepath in imgfiles:
    print(imgfilepath + " start")
    input_img = Image.open(imgfilepath)

    # 切り出しエリア数分切り出しと貼り付け実施。
    # 長さが新規画像一杯になった場合は一旦画像書き出しを行い次ページに書き込む。
    for cutarea in cutareaList:
        input_img_crop = input_img.crop((cutarea.left_x, cutarea.upper_y, cutarea.right_x, cutarea.lower_y))
        zoom_x = int((cutarea.right_x - cutarea.left_x) * cutareaZoom)
        zoom_y = int((cutarea.lower_y - cutarea.upper_y) * cutareaZoom)
        input_img_crop_zoom = input_img_crop.resize((zoom_x, zoom_y), Image.LANCZOS )
        img.paste(input_img_crop_zoom,(0,current_y))
        current_y += zoom_y

    cutcount += 1

    if cutcount >= cutlimit_per_page:
        outfilename = 'out_gakuhu_part_' + now + '_page' + str(pagenum) + '.jpg'
        img.save(outfilename, quality=95)
        img = Image.new("L", (new_x, new_y), color=255)  #新規キャンバス作成
        pagenum += 1
        cutcount = 0
        current_y = 0

#ページとして保存されていないカットがある場合は最後のページの生成画像保存
if cutcount >= 0:
    outfilename = 'out_gakuhu_part_' + now + '_page' + str(pagenum) + '.jpg'
    img.save(outfilename, quality=95)
