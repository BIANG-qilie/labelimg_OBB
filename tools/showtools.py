import os
import numpy as np
import cv2
import math

imgpath = '/home/kid/camera_ws/src/ROS_spinnaker/data/seq1/000050.jpg'
labelpath = '/home/kid/camera_ws/src/ROS_spinnaker/data/seq1/000050.txt'

def DOTAFormateTest():
    red = (0, 0, 255)
    data = [(184, 875),
    (193, 923),
    (146, 932),
    (137, 885)]
    data1 = [(66, 95),
             (75, 142),
             (21, 154),
             (11, 107)]
    img = np.ones((1000, 1000, 3), np.uint8)
    img.fill(255)
    img = cv2.line(img, data[0], data[1], red, 2)
    img = cv2.line(img, data[1], data[2], red, 2)
    img = cv2.line(img, data[2], data[3], red, 2)
    img = cv2.line(img, data[3], data[0], red, 2)


    img = cv2.line(img, data1[0], data1[1], red, 2)
    img = cv2.line(img, data1[1], data1[2], red, 2)
    img = cv2.line(img, data1[2], data1[3], red, 2)
    img = cv2.line(img, data1[3], data1[0], red, 2)
    cv2.imshow("", img)
    cv2.waitKey()
    cv2.destroyAllWindows()



def readtxt(path):
    coords = []
    with open(path, 'r') as f:
        ls = f.readlines()
        for i in ls[1:]:
            i = i.split(' ')
            #print(i)
            x_c = float(i[1])
            y_c = float(i[2])
            w = float(i[3])
            h = float(i[4])
            a = float(i[5])
            coords.append([x_c, y_c, w, h, a])
    return coords
# coords = [[cx, cy, w, h, a], ...]
def getRotatedCoord(coords, img):
    height, width, _ = img.shape
    print(height, width)

    new_coords = []
    for c in coords:
        new_xs = []
        new_ys = []
        x_c = c[0]
        y_c = c[1]
        w = c[2]
        h = c[3]
        # pi
        angle = -c[4]/180*math.pi  # current - destination = 0 - angle
        xmin = int(x_c - w / 2)
        ymin = int(y_c - h / 2)
        xmax = int(x_c + w / 2)
        ymax = int(y_c + h / 2)
        # 0-1-2-3 clockwise
        p_x = [xmin, xmax, xmax, xmin]
        p_y = [ymin, ymin, ymax, ymax]
        for i in range(4):  #  refer lib/shape.py  rotateBy()
            point_x = p_x[i]
            point_y = p_y[i]
            #new_xs.append(self.origin[0] + math.cos(angle) * (point_x - self.origin[0]) - math.sin(angle) * (point_y - self.origin[1]))
            #new_ys.append(self.origin[1] + math.sin(angle) * (point_x - self.origin[0]) + math.cos(angle) * (point_y - self.origin[1]))
            new_xs.append(x_c + math.cos(angle) * (point_x - x_c) - math.sin(angle) * (point_y - y_c))
            new_ys.append(y_c + math.sin(angle) * (point_x - x_c) + math.cos(angle) * (point_y - y_c))
        # 越界判断
        if all((0 <= new_xs[i] <= width and 0 <= new_ys[i] <= height) for i in range(4)):
            new_coords.append([new_xs, new_ys])
    return new_coords

def drawRotatedRect(co, im):  # co= [4points, 4points, ...]
    red = (0, 0, 255)
    for c in co:  # each bbox in box list
        x_ps = c[0]
        y_ps = c[1]
        pt0 = (int(x_ps[0]), int(y_ps[0]))
        pt1 = (int(x_ps[1]), int(y_ps[1]))
        pt2 = (int(x_ps[2]), int(y_ps[2]))
        pt3 = (int(x_ps[3]), int(y_ps[3]))
        cv2.line(im, pt0, pt1, red, 2)
        cv2.line(im, pt1, pt2, red, 2)
        cv2.line(im, pt2, pt3, red, 2)
        cv2.line(im, pt3, pt0, red, 2)
    return im

def vis():
    co = readtxt(labelpath)
    x_c = co[0][0]
    y_c = co[0][1]
    w = co[0][2]
    h = co[0][3]
    a = co[0][4]
    xmin, ymin = int(x_c - w / 2), int(y_c - h / 2)
    xmax, ymax = int(x_c + w / 2), int(y_c + h / 2)
    print((xmin, ymin), (xmax, ymax), a)
    im = cv2.imread(imgpath)
    im = cv2.rectangle(im, (xmin, ymin), (xmax, ymax), (255, 0, 0), 2)  # (B,G,R)
    # rotatedrect = cv2.RotatedRect((x_c, y_c), (w, h), a)  # only cpp
    #print(rotatedrect)
    new_co = getRotatedCoord(co, im)
    im = drawRotatedRect(new_co, im)
    cv2.imshow("", im)
    cv2.waitKey()
    cv2.destroyAllWindows()

vis()
# DOTAFormateTest()