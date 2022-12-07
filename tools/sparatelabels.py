'''
观测上,属于bbox最上方的点在最前面,但是看文档描述并没有对四个点的顺序进行强调.
也就是需要将第二个label抽离出来,变成4个角点的形式,并且加上类别,难度默认为0
184 2875 193 2923 146 2932 137 2885 plane 0
A[0:8]: Polygons with format (x1, y1, x2, y2, x3, y3, x4, y4).
A[8]: Category.
A[9]: Difficulty.
需要将所有图像合并, 6位,前2位为序列,后四位为帧号.
合并后imgs和labels各一个子目录, 图像和标签都需要统一命名
mergeddate|
          |-imgs
          |-labels
    ...候选补充目标分割
    ...候选补充语义分割(本体,太阳帆,喷嘴三小类)
'''
import os
import shutil
import glob
import cv2
import math

fatherPath = '/home/kid/dataset/dixia/obb'  # source
DesPath = '/home/kid/dataset/dixia/obb/mergeddata'  # destination
seqs = ['seq1', 'seq3', 'seq4', 'seq5', 'seq6', 'seq8']  # train, 'seq2', 'seq3-2', 'seq4-2', 'seq5-2', 'seq6-2', 'seq7']
# seqs = ['seq1']

bbox_coords = []
obb_coords = []

im_width = 1024.0
im_height = 768.0

def checkSubFolder(path):
    if os.path.exists(path):
        return True
    else:
        os.mkdir(path)

'''
line 1: string
line 2: bbox
line 3-last: obb  
每次更新并将目标label读取到两个数组
'''
def readLabels(path):
    bbox_coords.clear()
    obb_coords.clear()
    with open(path, 'r') as f:
        ls = f.readlines()
        is_rotated = False
        smallest_coord = []
        smallest_area = 9999999999.0
        for i in range(1, len(ls)):  # line-1: string
            cur = ls[i].split(' ')
            # print(i)
            x_c = float(cur[1])
            y_c = float(cur[2])
            w = float(cur[3])
            h = float(cur[4])
            a = float(cur[5])
            label = cur[0]
            if i == 1:
                cur_area = w * h
                if cur_area < smallest_area:
                    smallest_area = cur_area
                    smallest_coord = [x_c, y_c, w, h, a, label]
                bbox_coords.append([x_c, y_c, w, h, a, label])

            elif i > 1:
                #if i > 3:  # line 4 is missing
                #    print(path)
                cur_area = w * h
                if cur_area < smallest_area:
                    smallest_area = cur_area
                    is_rotated = True
                    smallest_coord = [x_c, y_c, w, h, a, label]
                # obb_coords.append([x_c, y_c, w, h, a, label])
    # only involve the smallest case as obb
    obb_coords.append(smallest_coord)
        # if not is_rotated:
        #    print(path, 'obb is larger than bbox.')


# return a list of class str
def readclasses(path):
    fpath = os.path.join(path, "classes.txt")
    clist = []
    with open(fpath, 'r') as f:
        ls = f.readlines()
        for c in ls:
            clist.append(c.strip('\n'))
    return clist

# yolo format use percentage center and width height
def operateBbox(dpath, clist, cname):
    assert len(bbox_coords) != 0
    # a txt of class strings, yolo only use index in per frame label file.
    namefile = os.path.join(dpath, 'classes.names')
    labelfile = os.path.join(dpath, cname)
    print(labelfile)
    with open(namefile, 'w') as f:
        for c in clist:
            f.write(c)
    # write labels
    # format <class-id> <x> <y> <width> <height>
    for bbox in bbox_coords:
        a = bbox[4]
        if a == 90 or a == 0:  # to percentage
            clabel = "%s %f %f %f %f" % (bbox[5], bbox[0] / im_width, bbox[1] / im_height, bbox[2] / im_width, bbox[3] / im_height)  # remove angle
            # print(clabel)
            with open(labelfile, 'w') as f:
                f.write(clabel + '\n')

'''
0-------------------> x (0 rad)
|  A-------------B
|  |             |
|  |     box     h
|  |   angle=0   |
|  D------w------C
v
y (pi/2 rad)

xmin ymin xmax ymax

'''
def getRotatedCoord(c):
    new_xs = []
    new_ys = []
    x_c = c[0]
    y_c = c[1]
    w = c[2]
    h = c[3]
    angle = -c[4] * math.pi / 180.0  # current - destination = 0 - angle

    xmin = int(x_c - w / 2.0)
    ymin = int(y_c - h / 2.0)
    xmax = int(x_c + w / 2.0)
    ymax = int(y_c + h / 2.0)
    # 0-1-2-3 clockwise A-B-C-D
    p_x = [xmin, xmax, xmax, xmin]
    p_y = [ymin, ymin, ymax, ymax]
    for i in range(4):  # refer lib/shape.py  rotateBy()
        point_x = p_x[i]
        point_y = p_y[i]
        new_xs.append(int(x_c + math.cos(angle) * (point_x - x_c) - math.sin(angle) * (point_y - y_c)))
        new_ys.append(int(y_c + math.sin(angle) * (point_x - x_c) + math.cos(angle) * (point_y - y_c)))
    # 越界判断
    if all((0 <= new_xs[i] <= im_width and 0 <= new_ys[i] <= im_height) for i in range(4)):
        return new_xs, new_ys

# add area compare, and select the smallest one
# add bbox as candidates
# x1 y1 x2 y2 x3 y3 x4 y4 class dif=0
def operateObb(dpath, clist, cname):
    assert len(obb_coords) != 0
    labelfile = os.path.join(dpath, cname)
    for bbox in obb_coords:
        labelStr = clist[int(bbox[5])]  # label string
        # coord calculate
        dif = 0  # default
        cor = [bbox[0], bbox[1], bbox[2], bbox[3], bbox[4]]
        p_x, p_y = getRotatedCoord(cor)
        clabel = "%d %d %d %d %d %d %d %d %s %d" \
                 % (p_x[0], p_y[0], p_x[1], p_y[1], p_x[2], p_y[2], p_x[3], p_y[3], labelStr, dif)  # remove angle
        # print(clabel)
        # 写文本
        with open(labelfile, 'w') as f:
            f.write(clabel + '\n')

for seq in seqs:

    source_Path = os.path.join(fatherPath, seq)

    if not os.path.exists(source_Path):
        continue
    print(source_Path)
    imgPath = os.path.join(DesPath, 'imgs')
    # bboxPath = os.path.join(source_Path, 'bbox')
    obbPath = os.path.join(DesPath, 'obb')
    checkSubFolder(imgPath)
    # checkSubFolder(bboxPath)
    checkSubFolder(obbPath)

    # 以jpg文件为基准
    imglist = glob.glob(source_Path+'/*.jpg')
    classList = readclasses(source_Path)

    imglist.sort()
    for img in imglist:
        #print(img)
        destImg = os.path.join(imgPath, seq+"_"+img.split('/')[-1])

        shutil.copy(img, destImg)  # copy to dest
        # read and create bbox/obb
        sourceLabel = img.replace('.jpg', '.txt')
        destLabel = os.path.join(obbPath, seq+"_"+sourceLabel.split('/')[-1])
        # print(sourceLabel)
        readLabels(sourceLabel)  # label-> bbox_coords & obb_coords
        # operateBbox(bboxPath, classList, img.split('/')[-1].replace('.jpg', '.txt'))
        operateObb(obbPath, classList, destLabel)













