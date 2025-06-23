#!/usr/bin/python
# -*- coding: utf-8 -*-

import math
import numpy as np

from turtledemo import paint
from audioop import minmax

try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

from libs.lib import distance
import sys

DEFAULT_LINE_COLOR = QColor(0, 255, 0, 128)
DEFAULT_FILL_COLOR = QColor(255, 0, 0, 128)
DEFAULT_SELECT_LINE_COLOR = QColor(255, 255, 255)
DEFAULT_SELECT_FILL_COLOR = QColor(0, 128, 255, 155)
DEFAULT_VERTEX_FILL_COLOR = QColor(0, 255, 0, 255)
DEFAULT_HVERTEX_FILL_COLOR = QColor(255, 0, 0)
DEFAULT_ORIGIN_FILL_COLOR = QColor(0, 0, 0)
MIN_Y_LABEL = 10


class Shape(object):
    P_SQUARE, P_ROUND = range(2)

    MOVE_VERTEX, NEAR_VERTEX = range(2)

    # The following class variables influence the drawing
    # of _all_ shape objects.
    line_color = DEFAULT_LINE_COLOR
    fill_color = DEFAULT_FILL_COLOR
    select_line_color = DEFAULT_SELECT_LINE_COLOR
    select_fill_color = DEFAULT_SELECT_FILL_COLOR
    vertex_fill_color = DEFAULT_VERTEX_FILL_COLOR
    hvertex_fill_color = DEFAULT_HVERTEX_FILL_COLOR
    origin_fill_color = DEFAULT_ORIGIN_FILL_COLOR
    
    point_type = P_ROUND
    point_size = 8
    scale = 1.0

    def __init__(self, label=None, line_color=None, difficult=False, paintLabel=False):
        self.label = label
        self.points = []
        self.origin = [0, 0]
        self.angle = 0
        self.height = 0
        self.width = 0
        self.fill = False
        self.selected = False
        self.difficult = difficult
        self.paintLabel = paintLabel

        self._highlightIndex = None
        self._highlightMode = self.NEAR_VERTEX
        self._highlightSettings = {
            self.NEAR_VERTEX: (4, self.P_ROUND),
            self.MOVE_VERTEX: (1.5, self.P_SQUARE),
        }

        self._closed = False

        if line_color is not None:
            # Override the class line_color attribute
            # with an object attribute. Currently this
            # is used for drawing the pending line a different color.
            self.line_color = line_color

    def close(self):
        self._closed = True

    def reachMaxPoints(self):
        if len(self.points) >= 4:
            return True
        return False

    def addPoint(self, point):
        if not self.reachMaxPoints():
            self.points.append(point)

    def popPoint(self):
        if self.points:
            return self.points.pop()
        return None

    def isClosed(self):
        return self._closed

    def setOpen(self):
        self._closed = False

    def paint(self, painter):
        if self.points:
            color = self.select_line_color if self.selected else self.line_color
            pen = QPen(color)
            # Try using integer sizes for smoother drawing(?)
            pen.setWidth(max(1, int(round(2.0 / self.scale))))
            painter.setPen(pen)

            line_path = QPainterPath()
            vrtx_path = QPainterPath()
            originPoint_path = QPainterPath()

            line_path.moveTo(self.points[0])
            # Uncommenting the following line will draw 2 paths
            # for the 1st vertex, and make it non-filled, which
            # may be desirable.
            #self.drawVertex(vrtx_path, 0)

            for i, p in enumerate(self.points):
                line_path.lineTo(p)
                self.drawVertex(vrtx_path, i)
            self.drawOrigin(originPoint_path)  # Draw object origin (centre)
            
            if self.isClosed():
                line_path.lineTo(self.points[0])

            painter.drawPath(line_path)
            painter.drawPath(vrtx_path)
            painter.drawPath(originPoint_path)
            #painter.fillPath(vrtx_path, self.vertex_fill_color)
            #painter.fillPath(originPoint_path, self.origin_fill_color)
            painter.fillPath(vrtx_path, QColor(0, 0, 255))
            painter.fillPath(originPoint_path, QColor(0, 0, 255))

            # Print debug info
            min_x = sys.maxsize
            min_y = sys.maxsize
            for point in self.points:
                min_x = min(min_x, point.x())
                min_y = min(min_y, point.y())
            if min_x != sys.maxsize and min_y != sys.maxsize:
                font = QFont()
                font.setPointSize(8)
                font.setBold(True)
                painter.setFont(font)
                if self.label == None:
                    self.label = ""
                if min_y < MIN_Y_LABEL:
                    min_y += MIN_Y_LABEL
                painter.drawText(min_x, min_y,
                                 "s={0:.1f} , \u03F4={1:.1f}".format(self.width * self.height, self.angle))

                #painter.drawText(min_x, min_y, "h={0:.1f}, w={1:.1f}, s={2:.1f} , \u03F4={3:.1f}".format(self.height, self.width, self.width*self.height, self.angle))

            # Draw label at the top-left
            if self.paintLabel:
                min_x = sys.maxsize
                min_y = sys.maxsize
                for point in self.points:
                    min_x = min(min_x, point.x())
                    min_y = min(min_y, point.y())
                if min_x != sys.maxsize and min_y != sys.maxsize:
                    font = QFont()
                    font.setPointSize(8)
                    font.setBold(True)
                    painter.setFont(font)
                    if(self.label == None):
                        self.label = ""
                    if(min_y < MIN_Y_LABEL):
                        min_y += MIN_Y_LABEL
                    painter.drawText(min_x, min_y+10, self.label)

            if self.fill:
                color = self.select_fill_color if self.selected else self.fill_color
                painter.fillPath(line_path, color)

    def drawVertex(self, path, i):
        d = self.point_size / self.scale
        shape = self.point_type
        point = self.points[i]
        if i == self._highlightIndex:
            size, shape = self._highlightSettings[self._highlightMode]
            d *= size
        if self._highlightIndex is not None:
            self.vertex_fill_color = self.hvertex_fill_color
        else:
            self.vertex_fill_color = Shape.vertex_fill_color
        if shape == self.P_SQUARE:
            path.addRect(point.x() - d / 2, point.y() - d / 2, d, d)
        elif shape == self.P_ROUND:
            path.addEllipse(point, d / 2.0, d / 2.0)
        else:
            assert False, "unsupported vertex shape"
            
    def drawOrigin(self, path):
        d = self.point_size / self.scale
        path.addEllipse(QPoint(self.origin[0], self.origin[1]), d / 2.0, d / 2.0)

    def nearestVertex(self, point, epsilon):
        for i, p in enumerate(self.points):
            if distance(p - point) <= epsilon:
                return i
        return None

    def containsPoint(self, point):
        return self.makePath().contains(point)

    def makePath(self):
        path = QPainterPath(self.points[0])
        for p in self.points[1:]:
            path.lineTo(p)
        return path

    def boundingRect(self):
        return self.makePath().boundingRect()

    def moveBy(self, offset):
        self.points = [p + offset for p in self.points]
        self.updateOBBInfo()

    def moveVertexBy(self, i, offset):
        self.points[i] = self.points[i] + offset
        self.updateOBBInfo()
        
    def rotateBy(self, angle, pixmap_width, pixmap_height):  # Clock-wise
        # 先记录当前角度
        current_angle = self.angle
        
        # 计算新的点坐标
        new_xs = []
        new_ys = []
        for i in range(4):
            point_x = self.points[i].x()
            point_y = self.points[i].y()
            new_xs.append(self.origin[0] + math.cos(angle) * (point_x - self.origin[0]) - math.sin(angle) * (point_y - self.origin[1]))
            new_ys.append(self.origin[1] + math.sin(angle) * (point_x - self.origin[0]) + math.cos(angle) * (point_y - self.origin[1]))
            
        # 检查是否超出图片边界
        if all((0 <= new_xs[i] <= pixmap_width and 0 <= new_ys[i] <= pixmap_height) for i in range(4)):
            # 更新点坐标
            for j in range(4):
                self.points[j].setX(new_xs[j])
                self.points[j].setY(new_ys[j])
            
            # 手动更新角度信息
            new_angle = current_angle - math.degrees(angle)
            # 标准化角度到 -90 到 90 之间
            while new_angle > 90:
                new_angle -= 180
            while new_angle < -90:
                new_angle += 180
            
            # 更新中心点
            minX = min([self.points[i].x() for i in range(4)])
            maxX = max([self.points[i].x() for i in range(4)])
            minY = min([self.points[i].y() for i in range(4)])
            maxY = max([self.points[i].y() for i in range(4)])
            self.origin[0] = minX + (maxX-minX)/2.0
            self.origin[1] = minY + (maxY-minY)/2.0
            
            # 计算宽高
            val1 = math.sqrt( ((self.points[1].x()-self.points[0].x())**2) + 
                             ((self.points[1].y()-self.points[0].y())**2) )
            val2 = math.sqrt( ((self.points[2].x()-self.points[1].x())**2) + 
                             ((self.points[2].y()-self.points[1].y())**2) )
            self.height = max([val1, val2])
            self.width = min([val1, val2])
            
            # 最后设置角度，避免被updateOBBInfo覆盖
            self.angle = new_angle
            
            return True
        return False

    def updateOBBInfo(self):
        if (self.reachMaxPoints()):
            # Update Origin (Centre info)
            minX = min([self.points[i].x() for i in range(4)])
            maxX = max([self.points[i].x() for i in range(4)])
            minY = min([self.points[i].y() for i in range(4)])
            maxY = max([self.points[i].y() for i in range(4)])
            self.origin[0] = minX + (maxX-minX)/2.0
            self.origin[1] = minY + (maxY-minY)/2.0
            
            val1 = math.sqrt( ((self.points[1].x()-self.points[0].x())**2) + 
                              ((self.points[1].y()-self.points[0].y())**2) )
            val2 = math.sqrt( ((self.points[2].x()-self.points[1].x())**2) + 
                              ((self.points[2].y()-self.points[1].y())**2) )
            self.height = max([val1, val2])
            self.width = min([val1, val2])
            if (np.argmax([val1, val2]) == 0): # Height is point[0] to point[1]
                self.angle = math.degrees( math.atan2( math.fabs(self.points[0].y()-self.points[1].y()), 
                                                       math.fabs(self.points[0].x()-self.points[1].x()) ) )
                # Check if box is slanted like West-North to East-South
                larger_x_point_id = np.argmax([self.points[0].x(), self.points[1].x()])
                if (    self.points[larger_x_point_id].y()>self.points[1 if (larger_x_point_id==0) else 0].y()   ):
                    self.angle = -self.angle
            else: # Height is point[1] to point[2]
                self.angle = math.degrees( math.atan2( math.fabs(self.points[1].y()-self.points[2].y()), 
                                                       math.fabs(self.points[1].x()-self.points[2].x()) ) )
                # Check if box is slanted like West-North to East-South
                larger_x_point_id = np.argmax([self.points[1].x(), self.points[2].x()]) + 1
                if (self.points[larger_x_point_id].y() > self.points[2 if (larger_x_point_id==1) else 1].y()):
                    self.angle = -self.angle
    
    def updatePointsFromOBBInfo(self, canvas_width, canvas_height):
        # 计算原始顶点
        p = []
        p.append(self.origin[0] + self.height*math.cos(math.radians(self.angle))/2.0 + self.width*math.cos(math.radians(90+self.angle))/2.0)
        p.append(self.origin[1] - self.height*math.sin(math.radians(self.angle))/2.0 - self.width*math.sin(math.radians(90+self.angle))/2.0)
        
        p.append(self.origin[0] - self.height*math.cos(math.radians(self.angle))/2.0 + self.width*math.cos(math.radians(90+self.angle))/2.0)
        p.append(self.origin[1] + self.height*math.sin(math.radians(self.angle))/2.0 - self.width*math.sin(math.radians(90+self.angle))/2.0)
        
        p.append(self.origin[0] - self.height*math.cos(math.radians(self.angle))/2.0 - self.width*math.cos(math.radians(90+self.angle))/2.0)
        p.append(self.origin[1] + self.height*math.sin(math.radians(self.angle))/2.0 + self.width*math.sin(math.radians(90+self.angle))/2.0)
        
        p.append(self.origin[0] + self.height*math.cos(math.radians(self.angle))/2.0 - self.width*math.cos(math.radians(90+self.angle))/2.0)
        p.append(self.origin[1] - self.height*math.sin(math.radians(self.angle))/2.0 + self.width*math.sin(math.radians(90+self.angle))/2.0)
        
        # 检查是否有顶点超出边界
        out_of_bounds = False
        for i in range(0, 8, 2):
            if p[i] < 0 or p[i] > canvas_width or p[i+1] < 0 or p[i+1] > canvas_height:
                out_of_bounds = True
                break
        
        if out_of_bounds:
            # 如果超出边界，调整中心点位置和边长
            # 计算当前中心点
            center_x = sum(p[i] for i in range(0, 8, 2)) / 4
            center_y = sum(p[i+1] for i in range(0, 8, 2)) / 4
            
            # 计算需要移动的距离
            dx = 0
            dy = 0
            
            if center_x < 0:
                dx = -center_x
            elif center_x > canvas_width:
                dx = canvas_width - center_x
                
            if center_y < 0:
                dy = -center_y
            elif center_y > canvas_height:
                dy = canvas_height - center_y
                
            # 移动中心点
            self.origin[0] += dx
            self.origin[1] += dy
            
            # 计算最大可用边长
            max_width = min(canvas_width - self.origin[0], self.origin[0]) * 2
            max_height = min(canvas_height - self.origin[1], self.origin[1]) * 2
            
            # 根据角度调整边长
            angle_rad = math.radians(self.angle)
            cos_angle = abs(math.cos(angle_rad))
            sin_angle = abs(math.sin(angle_rad))
            
            # 计算在当前角度下可用的最大边长
            # 添加对除零的检查
            if sin_angle == 0:  # 角度为0或180度
                max_available_width = max_width / cos_angle
                max_available_height = float('inf')  # 无限制
            elif cos_angle == 0:  # 角度为90度
                max_available_width = float('inf')  # 无限制
                max_available_height = max_height / sin_angle
            else:
                max_available_width = min(max_width / cos_angle, max_height / sin_angle)
                max_available_height = min(max_width / sin_angle, max_height / cos_angle)
            
            # 保持宽高比调整边长
            aspect_ratio = self.width / self.height
            if aspect_ratio > 1:  # 宽度大于高度
                self.width = min(self.width, max_available_width)
                self.height = self.width / aspect_ratio
            else:  # 高度大于宽度
                self.height = min(self.height, max_available_height)
                self.width = self.height * aspect_ratio
            
            # 重新计算顶点
            p = []
            p.append(self.origin[0] + self.height*math.cos(math.radians(self.angle))/2.0 + self.width*math.cos(math.radians(90+self.angle))/2.0)
            p.append(self.origin[1] - self.height*math.sin(math.radians(self.angle))/2.0 - self.width*math.sin(math.radians(90+self.angle))/2.0)
            
            p.append(self.origin[0] - self.height*math.cos(math.radians(self.angle))/2.0 + self.width*math.cos(math.radians(90+self.angle))/2.0)
            p.append(self.origin[1] + self.height*math.sin(math.radians(self.angle))/2.0 - self.width*math.sin(math.radians(90+self.angle))/2.0)
            
            p.append(self.origin[0] - self.height*math.cos(math.radians(self.angle))/2.0 - self.width*math.cos(math.radians(90+self.angle))/2.0)
            p.append(self.origin[1] + self.height*math.sin(math.radians(self.angle))/2.0 + self.width*math.sin(math.radians(90+self.angle))/2.0)
            
            p.append(self.origin[0] + self.height*math.cos(math.radians(self.angle))/2.0 - self.width*math.cos(math.radians(90+self.angle))/2.0)
            p.append(self.origin[1] - self.height*math.sin(math.radians(self.angle))/2.0 + self.width*math.sin(math.radians(90+self.angle))/2.0)
        
        # 添加点
        self.points = []  # 清空现有点
        self.addPoint(QPointF(p[0], p[1]))
        self.addPoint(QPointF(p[2], p[3]))
        self.addPoint(QPointF(p[4], p[5]))
        self.addPoint(QPointF(p[6], p[7]))
        
        # 保存原始角度，避免被updateOBBInfo覆盖
        original_angle = self.angle
        
        # 更新OBB信息（但不更新角度）
        self.updateOBBInfo()
        
        # 恢复原始角度
        self.angle = original_angle
        return True
        
    def highlightVertex(self, i, action):
        self._highlightIndex = i
        self._highlightMode = action

    def highlightClear(self):
        self._highlightIndex = None

    def copy(self):
        shape = Shape("%s" % self.label)
        shape.points = [p for p in self.points]
        shape.origin = [p for p in self.origin]
        shape.angle = self.angle
        shape.width = self.width
        shape.height = self.height
        shape.fill = self.fill
        shape.selected = self.selected
        shape._closed = self._closed
        if self.line_color != Shape.line_color:
            shape.line_color = self.line_color
        if self.fill_color != Shape.fill_color:
            shape.fill_color = self.fill_color
        shape.difficult = self.difficult
        shape.paintLabel = self.paintLabel
        return shape

    def __len__(self):
        return len(self.points)

    def __getitem__(self, key):
        return self.points[key]

    def __setitem__(self, key, value):
        self.points[key] = value
