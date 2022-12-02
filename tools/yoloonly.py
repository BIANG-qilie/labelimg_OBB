'''
处理最开始标注的普通检测框,生成yolo标签,供darknet框架训练使用(一次性)
1. 删除第一行
2. 删除角度信息
3. 删除第三及以后的
4. 转换坐标为百分比
'''

import os
import glob
import cv2  # for checking bbox


fatherPath = '/home/kid/dataset/dixia/dixia_yolo'
seqs = ['seq1', 'seq3', 'seq4', 'seq5', 'seq6', 'seq8', 'seq2', 'seq3-2', 'seq4-2', 'seq5-2', 'seq6-2', 'seq7']
im_width = 1024.0
im_height = 768.0



def editlabel(path):
    assert os.path.exists(path)
    #print(path)
    coords = []
    label = 0  # default
    with open(path, 'r') as f:
        ls = f.readlines()
        usefulLabel = ls[1]
        usefulLabel = usefulLabel.split(' ')
        angle = float(usefulLabel[5])
        if angle == 0.0:
            coords.append(float(usefulLabel[1]))
            coords.append(float(usefulLabel[2]))
            coords.append(float(usefulLabel[3]))
            coords.append(float(usefulLabel[4]))
        if angle == 90.0:  # 有旋转错位的情况,中心不变,长宽修改
            coords.append(float(usefulLabel[1]))
            coords.append(float(usefulLabel[2]))
            coords.append(float(usefulLabel[4]))
            coords.append(float(usefulLabel[3]))

    if not len(coords) == 0:
        newLabel = '%d %f %f %f %f' % \
                   (label, coords[0] / im_width, coords[1] / im_height, coords[2] / im_width, coords[3] / im_height)

        with open(path, 'w') as f:
            f.write(newLabel)

def generatelabel():
    for seq in seqs:
        destPath = os.path.join(fatherPath, seq)
        print(destPath)
        cls = os.path.join(fatherPath, seq, 'classes.txt')
        if os.path.exists(cls):
            os.remove(cls)
        if not os.path.exists(destPath):
            continue
        # 以jpg文件为基准
        imglist = glob.glob(destPath+'/*.jpg')
        imglist.sort()
        for img in imglist:
            # print(img)
            sourceLabel = img.replace('.jpg', '.txt')
            editlabel(sourceLabel)

def checklabel():

    for seq in seqs:
        destPath = os.path.join(fatherPath, seq)
        if not os.path.exists(destPath):
            continue
        # 以jpg文件为基准
        imglist = glob.glob(destPath + '/*.jpg')
        imglist.sort()
        for img in imglist:
            print(img)
            im = cv2.imread(img)
            sourceLabel = img.replace('.jpg', '.txt')
            cord = []
            with open(sourceLabel, 'r') as f:
                ls = f.readlines()
                usefulLabel = ls[0]
                usefulLabel = usefulLabel.split(' ')
                for i in range(1, len(usefulLabel)):
                    #print(float(usefulLabel[i]))
                    cord.append(float(usefulLabel[i]))

            xmin = int((cord[0] - cord[2] / 2) * im_width)
            ymin = int((cord[1] - cord[3] / 2) * im_height)
            xmax = int((cord[0] + cord[2] / 2) * im_width)
            ymax = int((cord[1] + cord[3] / 2) * im_height)
            #print(xmin, ymin, xmax, ymax)
            cv2.rectangle(im, (xmin, ymin), (xmax, ymax), (255, 0, 0), 2)
            cv2.imshow('', im)
            cv2.waitKey()

        cv2.destroyAllWindows()

# generatelabel()  # step 1
checklabel()  # step 2