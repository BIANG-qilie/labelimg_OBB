import cv2
import os
import glob
import math
import matplotlib.pyplot as plt
import numpy as np


father_path = '/home/kid/dataset/dixia/obb'

front_files = ['seq1', 'seq3', 'seq4', 'seq5', 'seq6', 'seq8']
side_files = ['seq2', 'seq3-2', 'seq4-2', 'seq5-2', 'seq6-2', 'seq7']

bbox_coords = []
obb_coords = []

# return coords
'''
line 1: string
line 2: bbox
line 3-last: obb  
'''
def readLabels(path):
    bbox_coords.clear()
    obb_coords.clear()
    with open(path, 'r') as f:
        ls = f.readlines()
        for i in range(1, len(ls)):
            cur = ls[i].split(' ')  # label x y w h angle
            # print(i)
            x_c = float(cur[1])
            y_c = float(cur[2])
            w = float(cur[3])
            h = float(cur[4])
            a = float(cur[5])
            if i == 1:
                bbox_coords.append([x_c, y_c, w, h, a])
            elif i > 1:
                obb_coords.append([x_c, y_c, w, h, a])

# rectangle area = w * h
def calculate_area(coord):
    return float(coord[2]), float(coord[3]), float(coord[2]) * float(coord[3])

# opencv rotatedRectangleIntersection
# IOU = area1 + area2
def RRIOU(cor1, cor2):
    [xc1, yc1, w1, h1, a1] = cor1  # angle = 90 degree, not use arc
    [xc2, yc2, w2, h2, a2] = cor2

    Rotatedrect1 = ((xc1, yc1), (w1, h1), a1)  # ('center', 'size', 'angle') (2.5, 2.5), (10., 20.), 12.5
    # Rotatedrect2 = cv2.RotatedRect((xc2, yc2), (w2, h2), a2)  # ('center', 'size', 'angle') (2.5, 2.5), (10., 20.), 12.5
    Rotatedrect2 = ((xc2, yc2), (w2, h2), a2)
    res, inter = cv2.rotatedRectangleIntersection(Rotatedrect1, Rotatedrect2)
    #return cv2.rotatedRectIOU(Rotatedrect1, Rotatedrect2)  # 内部函数(static inline),仅允许nms调用, 需要自己实现计算过程
    if res == 0:
        return 0.0
    if res == 2:  # One of the rectangle is fully enclosed in the other
        return 1.0
    interArea = cv2.contourArea(inter)
    return interArea / (w1 * h1 + w2 * h2 - interArea)


def functiontest():
    plt.style.use('_mpl-gallery')

    bbox = [1.5, 0.5, 3, 1, 0]
    bboxT = [1.5, 0.5, 3, 1, 0]
    x = np.arange(0, 361, 5)
    y = []
    for i in range(0, 361, 5):
        bboxT[4] = float(i)  # * math.pi / 180.0   # 自动切换 等价
        y.append(RRIOU(tuple(bbox), tuple(bboxT)))
    y = np.asarray(y)
    #xy = np.hstack((x, y))
    print(x, y)
    #fig, ax = plt.subplots()
    #ax.scatter(x, y, s=1, vmin=0, vmax=100)
    #plt.show()

if __name__ == '__main__':
    #functiontest()
    # front view
    # fullPath = os.path.join(father_path, front_files[0])
    fullPath = os.path.join(father_path, side_files[0])
    print(fullPath)
    area_rate_list = []
    if os.path.exists(fullPath):
        files = glob.glob(fullPath+'/*.jpg')
        files.sort()
        for f in files:
            f = f.replace('.jpg', '.txt')
            readLabels(os.path.join(fullPath, f))
            #print("bbox: ", bbox_coords)
            #print("obb: ", obb_coords)
            #if float(bbox_coords[0][-1]) == 90.0 or float(bbox_coords[0][-1]) == 0.0:
            if bbox_coords[0][-1] == 90.0 or bbox_coords[0][-1] == 0.0:
                # print('correct')
                # continue
                # insert operation function
                iou = RRIOU(bbox_coords[0], obb_coords[0])
                # print(iou)
                w1, h1, bboxArea = calculate_area(bbox_coords[0])
                w2, h2, obbArea = calculate_area(obb_coords[0])
                # print("%s: bbox area = %.f, obb area = % .f" % (f, bboxArea, obbArea))
                print("%s: width rate = %.2f, height rate = %.2f, area rate = % .2f, IOU = %.2f"
                      % (f, w1 / w2, h1 / h2, bboxArea / obbArea, iou))
                area_rate_list.append(bboxArea / obbArea)
            else:
                print("problem bbox: ", float(bbox_coords[0][-1]), ', index: ', f)

    area_rate_list.sort()
    print(area_rate_list)















