import math
import copy  # 添加copy模块

try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

#from PyQt4.QtOpenGL import *

from libs.shape import Shape
from libs.lib import distance
from libs.vector import Vector

CURSOR_DEFAULT = Qt.ArrowCursor
CURSOR_POINT = Qt.PointingHandCursor
CURSOR_DRAW = Qt.CrossCursor
CURSOR_MOVE = Qt.ClosedHandCursor
CURSOR_GRAB = Qt.OpenHandCursor
CURSOR_CROSS = Qt.CrossCursor

# class Canvas(QGLWidget):


class Canvas(QWidget):
    zoomRequest = pyqtSignal(int)
    scrollRequest = pyqtSignal(int, int)
    newShape = pyqtSignal()
    selectionChanged = pyqtSignal(bool)
    shapeMoved = pyqtSignal()
    drawingPolygon = pyqtSignal(bool)
    undoOperation = pyqtSignal()  # 添加撤销信号

    CREATE, EDIT = list(range(2))

    epsilon = 11.0

    def __init__(self, *args, **kwargs):
        super(Canvas, self).__init__(*args, **kwargs)
        # Initialise local state.
        self.mode = self.EDIT
        self.shapes = []
        self.current = None
        self.selectedShape = None  # save the selected shape here
        self.selectedShapeCopy = None
        self.drawingLineColor = QColor(0, 0, 255)
        self.drawingRectColor = QColor(0, 0, 255) 
        self.line = Shape(line_color=self.drawingLineColor)
        self.prevPoint = QPointF()
        self.offsets = QPointF(), QPointF()
        self.scale = 1.0
        self.pixmap = QPixmap()
        self.visible = {}
        self._hideBackround = False
        self.hideBackround = False
        self.hShape = None
        self.hVertex = None
        self._painter = QPainter()
        self._cursor = CURSOR_DEFAULT
        # Menus:
        self.menus = (QMenu(), QMenu())
        # Set widget options.
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)
        self.verified = False
        self.drawSquare = False
        
        # 添加状态历史管理
        self.history = []  # 历史状态列表
        self.historyIndex = -1  # 当前历史状态索引
        self.MAX_HISTORY = 100  # 最大历史记录数
        self.saveTimer = QTimer()  # 定时器用于键盘操作状态保存
        self.saveTimer.setSingleShot(True)
        self.saveTimer.timeout.connect(self.saveState)
        self.currentState = None  # 用于比较状态是否发生变化
        self.saveInitialState()  # 保存初始状态

    def setDrawingColor(self, qColor):
        self.drawingLineColor = qColor
        self.drawingRectColor = qColor

    def enterEvent(self, ev):
        self.overrideCursor(self._cursor)

    def leaveEvent(self, ev):
        self.restoreCursor()

    def focusOutEvent(self, ev):
        self.restoreCursor()

    def isVisible(self, shape):
        return self.visible.get(shape, True)

    def drawing(self):
        return self.mode == self.CREATE

    def editing(self):
        return self.mode == self.EDIT

    def setEditing(self, value=True):
        self.mode = self.EDIT if value else self.CREATE
        if not value:  # Create
            self.unHighlight()
            self.deSelectShape()
        self.prevPoint = QPointF()
        self.repaint()

    def unHighlight(self):
        if self.hShape:
            self.hShape.highlightClear()
        self.hVertex = self.hShape = None

    def selectedVertex(self):
        return self.hVertex is not None

    def mouseMoveEvent(self, ev):
        """Update line with last point and current coordinates."""
        pos = self.transformPos(ev.pos())

        # Update coordinates in status bar if image is opened
        window = self.parent().window()
        if window.filePath is not None:
            self.parent().window().labelCoordinates.setText(
                'X: %d; Y: %d' % (pos.x(), pos.y()))

        # Polygon drawing.
        if self.drawing():
            self.overrideCursor(CURSOR_DRAW)
            if self.current:
                color = self.drawingLineColor
                if self.outOfPixmap(pos):
                    # Don't allow the user to draw outside the pixmap.
                    # Project the point to the pixmap's edges.
                    pos = self.intersectionPoint(self.current[-1], pos)
                elif len(self.current) > 1 and self.closeEnough(pos, self.current[0]):
                    # Attract line to starting point and colorise to alert the
                    # user:
                    pos = self.current[0]
                    color = self.current.line_color
                    self.overrideCursor(CURSOR_POINT)
                    self.current.highlightVertex(0, Shape.NEAR_VERTEX)

                if self.drawSquare:
                    initPos = self.current[0]
                    minX = initPos.x()
                    minY = initPos.y()
                    min_size = min(abs(pos.x() - minX), abs(pos.y() - minY))
                    directionX = -1 if pos.x() - minX < 0 else 1
                    directionY = -1 if pos.y() - minY < 0 else 1
                    self.line[1] = QPointF(minX + directionX * min_size, minY + directionY * min_size)
                else:
                    self.line[1] = pos

                self.line.line_color = color
                self.prevPoint = QPointF()
                self.current.highlightClear()
            else:
                self.prevPoint = pos
            self.repaint()
            return

        # Polygon/Vertex moving or rotation.
        # ev.buttons is mouse buttons mask (https://doc.qt.io/qt-5/qt.html#MouseButton-enum)
        if Qt.LeftButton & ev.buttons():
            if self.selectedVertex():
                self.boundedMoveVertex(pos)
                self.shapeMoved.emit()
                self.repaint()
            elif self.selectedShape and self.prevPoint:
                self.overrideCursor(CURSOR_MOVE)
                self.boundedMoveShape(self.selectedShape, pos)
                self.shapeMoved.emit()
                self.repaint()
            return
        # ev.buttons is mouse buttons mask (https://doc.qt.io/qt-5/qt.html#MouseButton-enum)
        elif Qt.RightButton & ev.buttons():
            if self.selectedVertex():
                # 检查是否允许旋转
                if hasattr(self.hShape, 'rotation_enabled') and not self.hShape.rotation_enabled:
                    return  # 禁止旋转
                self.overrideCursor(CURSOR_CROSS)
                print("canvas line 168", pos)
                self.rotateVertex(pos)
                self.shapeMoved.emit()
                self.repaint()
            return
        
        # Polygon copy moving.
        if Qt.RightButton & ev.buttons():
            #  print("canvas line 178")
            if self.selectedShapeCopy and self.prevPoint:
                self.overrideCursor(CURSOR_MOVE)
                self.boundedMoveShape(self.selectedShapeCopy, pos)
                self.repaint()
            elif self.selectedShape:
                self.selectedShapeCopy = self.selectedShape.copy()
                self.repaint()
            return

        # Just hovering over the canvas, 2 posibilities:
        # - Highlight shapes
        # - Highlight vertex
        # Update shape/vertex fill and tooltip value accordingly.
        self.setToolTip("Image")
        for shape in reversed([s for s in self.shapes if self.isVisible(s)]):
            # Look for a nearby vertex to highlight. If that fails,
            # check if we happen to be inside a shape.
            index = shape.nearestVertex(pos, self.epsilon)
            if index is not None:
                if self.selectedVertex():
                    self.hShape.highlightClear()
                self.hVertex, self.hShape = index, shape
                shape.highlightVertex(index, shape.MOVE_VERTEX)
                self.overrideCursor(CURSOR_POINT)
                # 根据是否允许旋转显示不同的提示
                if hasattr(shape, 'rotation_enabled') and not shape.rotation_enabled:
                    self.setToolTip("Left Click & Drag point to move.")
                else:
                    self.setToolTip("Left Click & Drag point to move. Right Click & Drag points to rotate.")
                self.setStatusTip(self.toolTip())
                self.update()
                break
            elif shape.containsPoint(pos):
                if self.selectedVertex():
                    self.hShape.highlightClear()
                self.hVertex, self.hShape = None, shape
                # 根据是否允许旋转显示不同的提示
                if hasattr(shape, 'rotation_enabled') and not shape.rotation_enabled:
                    self.setToolTip("Click & Drag to move shape '%s'." % shape.label)
                else:
                    self.setToolTip("Click & Drag to move shape '%s'. Right Click points to rotate." % shape.label)
                self.setStatusTip(self.toolTip())
                self.overrideCursor(CURSOR_GRAB)
                self.update()
                break
        else:  # Nothing found, clear highlights, reset state.
            if self.hShape:
                self.hShape.highlightClear()
                self.update()
            self.hVertex, self.hShape = None, None
            self.overrideCursor(CURSOR_DEFAULT)

    def mousePressEvent(self, ev):
        pos = self.transformPos(ev.pos())

        if ev.button() == Qt.LeftButton:
            if self.drawing():
                self.handleDrawing(pos)
            else:
                self.selectShapePoint(pos)
                self.prevPoint = pos
                self.repaint()
        elif ev.button() == Qt.RightButton and self.editing() and (not self.selectedVertex()):
            self.selectShapePoint(pos)
            self.prevPoint = pos
            self.repaint()

    #  右键弹出菜单功能
    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.RightButton and (not self.selectedVertex()):
            menu = self.menus[bool(self.selectedShapeCopy)]
            self.restoreCursor()
            if not menu.exec_(self.mapToGlobal(ev.pos()))\
               and self.selectedShapeCopy:
                # Cancel the move by deleting the shadow copy.
                self.selectedShapeCopy = None
                self.repaint()
        elif ev.button() == Qt.LeftButton and self.selectedShape:  # 左键为选择标定框
            if self.selectedVertex():
                self.overrideCursor(CURSOR_POINT)
            else:
                self.overrideCursor(CURSOR_GRAB)
            # 鼠标释放后保存状态
            self.saveState()
            
        elif ev.button() == Qt.LeftButton:
            pos = self.transformPos(ev.pos())
            if self.drawing():
                self.handleDrawing(pos)
                # 绘制完成后保存状态
                if self.current is None:  # 已完成绘制
                    self.saveState()

    def endMove(self, copy=False):
        assert self.selectedShape and self.selectedShapeCopy
        shape = self.selectedShapeCopy
        #del shape.fill_color
        #del shape.line_color
        if copy:
            self.shapes.append(shape)
            self.selectedShape.selected = False
            self.selectedShape = shape
            self.repaint()
        else:
            self.selectedShape.points = [p for p in shape.points]
        self.selectedShapeCopy = None

    def hideBackroundShapes(self, value):
        self.hideBackround = value
        if self.selectedShape:
            # Only hide other shapes if there is a current selection.
            # Otherwise the user will not be able to select a shape.
            self.setHiding(True)
            self.repaint()

    def handleDrawing(self, pos):
        if self.current and self.current.reachMaxPoints() is False:
            initPos = self.current[0]
            minX = initPos.x()
            minY = initPos.y()
            targetPos = self.line[1]
            maxX = targetPos.x()
            maxY = targetPos.y()

            if minX == maxX:
                maxX = maxX + 1
            if minY == maxY:
                maxY = maxY + 1

            self.current.addPoint(QPointF(maxX, minY)) # Adding canvas points is done here
            self.current.addPoint(targetPos)
            self.current.addPoint(QPointF(minX, maxY))
            self.finalise()
        elif not self.outOfPixmap(pos):
            self.current = Shape()
            self.current.addPoint(pos)
            self.line.points = [pos, pos]
            self.setHiding()
            self.drawingPolygon.emit(True)
            self.update()

    def setHiding(self, enable=True):
        self._hideBackround = self.hideBackround if enable else False

    def canCloseShape(self):
        return self.drawing() and self.current and len(self.current) > 2

    def mouseDoubleClickEvent(self, ev):
        # We need at least 4 points here, since the mousePress handler
        # adds an extra one before this handler is called.
        if self.canCloseShape() and len(self.current) > 3:
            self.current.popPoint()
            self.finalise()

    def selectShape(self, shape):
        self.deSelectShape()
        shape.selected = True
        self.selectedShape = shape
        self.setHiding()
        self.selectionChanged.emit(True)
        self.update()

    def selectShapePoint(self, point):
        """Select the first shape created which contains this point."""
        self.deSelectShape()
        if self.selectedVertex():  # A vertex is marked for selection.
            index, shape = self.hVertex, self.hShape
            shape.highlightVertex(index, shape.MOVE_VERTEX)
            self.selectShape(shape)
            return
        for shape in reversed(self.shapes):
            if self.isVisible(shape) and shape.containsPoint(point):
                self.selectShape(shape)
                self.calculateOffsets(shape, point)
                return

    def calculateOffsets(self, shape, point):
        rect = shape.boundingRect()
        x1 = rect.x() - point.x()
        y1 = rect.y() - point.y()
        x2 = (rect.x() + rect.width()) - point.x()
        y2 = (rect.y() + rect.height()) - point.y()
        self.offsets = QPointF(x1, y1), QPointF(x2, y2)

    def boundedMoveVertex(self, pos):
        index, shape = self.hVertex, self.hShape
        point = shape[index]
        if self.outOfPixmap(pos):
            pos = self.intersectionPoint(point, pos)

        opposite_point_index = (index + 2) % 4
        o_to_pos_vector = Vector(shape[opposite_point_index], pos)
        o_to_prev_vector = Vector(shape[opposite_point_index], shape[(index + 3) % 4])
        o_to_next_vector = Vector(shape[opposite_point_index], shape[(index + 1) % 4])

        if self.drawSquare:
            opposite_point = shape[opposite_point_index]

            min_size = min(abs(pos.x() - opposite_point.x()), abs(pos.y() - opposite_point.y()))
            directionX = -1 if pos.x() - opposite_point.x() < 0 else 1
            directionY = -1 if pos.y() - opposite_point.y() < 0 else 1
            shiftPos = QPointF(opposite_point.x() + directionX * min_size - point.x(),
                               opposite_point.y() + directionY * min_size - point.y())
        else:
            o_to_pos_mag = o_to_pos_vector.magnitude()
            o_to_prev_mag = o_to_prev_vector.magnitude()
            o_to_next_mag = o_to_next_vector.magnitude()

            o_to_pos_u_vector = QPointF(o_to_pos_vector.x/o_to_pos_mag, o_to_pos_vector.y/o_to_pos_mag)
            o_to_prev_u_vector = QPointF(o_to_prev_vector.x/o_to_prev_mag, o_to_prev_vector.y/o_to_prev_mag)
            o_to_next_u_vector = QPointF(o_to_next_vector.x/o_to_next_mag, o_to_next_vector.y/o_to_next_mag)

            if o_to_pos_u_vector.x() == o_to_prev_u_vector.x() and o_to_pos_u_vector.y() == o_to_prev_u_vector.y():
                pos = pos + o_to_next_u_vector
            if o_to_pos_u_vector.x() == o_to_next_u_vector.x() and o_to_pos_u_vector.y() == o_to_next_u_vector.y():
                pos = pos + o_to_prev_u_vector

            shiftPos = pos - point

        point_to_pos_vector = Vector(point, pos)

        prev_proj = point_to_pos_vector.projection(o_to_prev_vector)
        next_proj = point_to_pos_vector.projection(o_to_next_vector)

        prev_shiftPos = QPointF(o_to_prev_vector.x * prev_proj, o_to_prev_vector.y * prev_proj)
        next_shiftPos = QPointF(o_to_next_vector.x * next_proj, o_to_next_vector.y * next_proj)

        shape.moveVertexBy(index, shiftPos)
        shape.moveVertexBy((index + 3) % 4, prev_shiftPos)
        shape.moveVertexBy((index + 1) % 4, next_shiftPos)

        
    def rotateVertex(self, pos):
        index, shape = self.hVertex, self.hShape
        point = shape[index]
        if self.outOfPixmap(pos):
            pos = self.intersectionPoint(point, pos)

        if not self.drawSquare:
            angle_target = math.atan2(pos.y() - shape.origin[1], pos.x() - shape.origin[0])
            angle_original = math.atan2(point.y() - shape.origin[1], point.x() - shape.origin[0])
            shape.rotateBy(angle_target-angle_original, self.pixmap.width(), self.pixmap.height())  # Clock-wise
            # 旋转后保存状态
            self.saveState()

    #  rotate by angle, added
    def _canRotate(self):
        """检查当前选中的形状是否允许旋转"""
        if not self.selectedShape:
            return False
        return not (hasattr(self.selectedShape, 'rotation_enabled') and not self.selectedShape.rotation_enabled)

    def rotateShape(self, angle):
        if not self._canRotate():
            return  # 禁止旋转
        self.selectedShape.rotateBy(angle, self.pixmap.width(), self.pixmap.height())  # Clock-wise
        self.shapeMoved.emit()
        self.repaint()
        # 直接保存状态而不仅仅启动计时器
        self.saveState()


    def boundedMoveShape(self, shape, pos):
        if self.outOfPixmap(pos):
            return False  # No need to move
        o1 = pos + self.offsets[0]
        if self.outOfPixmap(o1):
            pos -= QPointF(min(0, o1.x()), min(0, o1.y()))
        o2 = pos + self.offsets[1]
        if self.outOfPixmap(o2):
            pos += QPointF(min(0, self.pixmap.width() - o2.x()),
                           min(0, self.pixmap.height() - o2.y()))
        # The next line tracks the new position of the cursor
        # relative to the shape, but also results in making it
        # a bit "shaky" when nearing the border and allows it to
        # go outside of the shape's area for some reason. XXX
        #self.calculateOffsets(self.selectedShape, pos)
        dp = pos - self.prevPoint
        if dp:
            shape.moveBy(dp)
            self.prevPoint = pos
            return True
        return False

    def deSelectShape(self):
        if self.selectedShape:
            self.selectedShape.selected = False
            self.selectedShape = None
            self.setHiding(False)
            self.selectionChanged.emit(False)
            self.update()

    def deleteSelected(self):
        if self.selectedShape:
            # 删除前保存状态
            self.saveState()
            shape = self.selectedShape
            self.shapes.remove(self.selectedShape)
            self.selectedShape = None
            self.update()
            # 删除后不需要再次保存状态，因为已经在前面保存了
            return shape

    def copySelectedShape(self):
        if self.selectedShape:
            shape = self.selectedShape.copy()
            self.deSelectShape()
            self.shapes.append(shape)
            shape.selected = True
            self.selectedShape = shape
            self.boundedShiftShape(shape)
            # 复制后保存状态
            self.saveState()
            return shape

    def boundedShiftShape(self, shape):
        # Try to move in one direction, and if it fails in another.
        # Give up if both fail.
        point = shape[0]
        offset = QPointF(2.0, 2.0)
        self.calculateOffsets(shape, point)
        self.prevPoint = point
        if not self.boundedMoveShape(shape, point - offset):
            self.boundedMoveShape(shape, point + offset)

    def paintEvent(self, event):
        if not self.pixmap:
            return super(Canvas, self).paintEvent(event)

        p = self._painter
        p.begin(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.HighQualityAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        p.scale(self.scale, self.scale)
        p.translate(self.offsetToCenter())

        p.drawPixmap(0, 0, self.pixmap)
        Shape.scale = self.scale
        for shape in self.shapes:
            if (shape.selected or not self._hideBackround) and self.isVisible(shape):
                shape.fill = shape.selected or shape == self.hShape
                shape.paint(p)
        if self.current:
            self.current.paint(p)
            self.line.paint(p)
        if self.selectedShapeCopy:
            self.selectedShapeCopy.paint(p)

        # Paint rect
        if self.current is not None and len(self.line) == 2:
            leftTop = self.line[0]
            rightBottom = self.line[1]
            rectWidth = rightBottom.x() - leftTop.x()
            rectHeight = rightBottom.y() - leftTop.y()
            p.setPen(self.drawingRectColor)
            brush = QBrush(Qt.BDiagPattern)
            p.setBrush(brush)
            p.drawRect(leftTop.x(), leftTop.y(), rectWidth, rectHeight)

        if self.drawing() and not self.prevPoint.isNull() and not self.outOfPixmap(self.prevPoint):
            p.setPen(QColor(0, 0, 0))
            p.drawLine(self.prevPoint.x(), 0, self.prevPoint.x(), self.pixmap.height())
            p.drawLine(0, self.prevPoint.y(), self.pixmap.width(), self.prevPoint.y())

        self.setAutoFillBackground(True)
        if self.verified:
            pal = self.palette()
            pal.setColor(self.backgroundRole(), QColor(184, 239, 38, 128))
            self.setPalette(pal)
        else:
            pal = self.palette()
            pal.setColor(self.backgroundRole(), QColor(232, 232, 232, 255))
            self.setPalette(pal)

        p.end()

    def transformPos(self, point):
        """Convert from widget-logical coordinates to painter-logical coordinates."""
        return point / self.scale - self.offsetToCenter()

    def offsetToCenter(self):
        s = self.scale
        area = super(Canvas, self).size()
        w, h = self.pixmap.width() * s, self.pixmap.height() * s
        aw, ah = area.width(), area.height()
        x = (aw - w) / (2 * s) if aw > w else 0
        y = (ah - h) / (2 * s) if ah > h else 0
        return QPointF(x, y)

    def outOfPixmap(self, p):
        w, h = self.pixmap.width(), self.pixmap.height()
        return not (0 <= p.x() <= w and 0 <= p.y() <= h)

    def finalise(self):
        assert self.current
        if self.current.points[0] == self.current.points[-1]:
            self.current = None
            self.drawingPolygon.emit(False)
            self.update()
            return
        
        self.current.updateOBBInfo()
        self.current.close()
        self.shapes.append(self.current)
        self.current = None
        self.setHiding(False)
        self.newShape.emit()
        self.update()
        # 完成一个形状后保存状态
        self.saveState()

    def closeEnough(self, p1, p2):
        #d = distance(p1 - p2)
        #m = (p1-p2).manhattanLength()
        # print "d %.2f, m %d, %.2f" % (d, m, d - m)
        return distance(p1 - p2) < self.epsilon

    def intersectionPoint(self, p1, p2):
        # Cycle through each image edge in clockwise fashion,
        # and find the one intersecting the current line segment.
        # http://paulbourke.net/geometry/lineline2d/
        size = self.pixmap.size()
        points = [(0, 0),
                  (size.width(), 0),
                  (size.width(), size.height()),
                  (0, size.height())]
        x1, y1 = p1.x(), p1.y()
        x2, y2 = p2.x(), p2.y()
        d, i, (x, y) = min(self.intersectingEdges((x1, y1), (x2, y2), points))
        x3, y3 = points[i]
        x4, y4 = points[(i + 1) % 4]
        if (x, y) == (x1, y1):
            # Handle cases where previous point is on one of the edges.
            if x3 == x4:
                return QPointF(x3, min(max(0, y2), max(y3, y4)))
            else:  # y3 == y4
                return QPointF(min(max(0, x2), max(x3, x4)), y3)
        return QPointF(x, y)

    def intersectingEdges(self, x1y1, x2y2, points):
        """For each edge formed by `points', yield the intersection
        with the line segment `(x1,y1) - (x2,y2)`, if it exists.
        Also return the distance of `(x2,y2)' to the middle of the
        edge along with its index, so that the one closest can be chosen."""
        x1, y1 = x1y1
        x2, y2 = x2y2
        for i in range(4):
            x3, y3 = points[i]
            x4, y4 = points[(i + 1) % 4]
            denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
            nua = (x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)
            nub = (x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)
            if denom == 0:
                # This covers two cases:
                #   nua == nub == 0: Coincident
                #   otherwise: Parallel
                continue
            ua, ub = nua / denom, nub / denom
            if 0 <= ua <= 1 and 0 <= ub <= 1:
                x = x1 + ua * (x2 - x1)
                y = y1 + ua * (y2 - y1)
                m = QPointF((x3 + x4) / 2, (y3 + y4) / 2)
                d = distance(m - QPointF(x2, y2))
                yield d, i, (x, y)

    # These two, along with a call to adjustSize are required for the
    # scroll area.
    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        if self.pixmap:
            return self.scale * self.pixmap.size()
        return super(Canvas, self).minimumSizeHint()

    def wheelEvent(self, ev):
        qt_version = 4 if hasattr(ev, "delta") else 5
        if qt_version == 4:
            if ev.orientation() == Qt.Vertical:
                v_delta = ev.delta()
                h_delta = 0
            else:
                h_delta = ev.delta()
                v_delta = 0
        else:
            delta = ev.angleDelta()
            h_delta = delta.x()
            v_delta = delta.y()

        mods = ev.modifiers()
        if Qt.ControlModifier == int(mods) and v_delta:
            self.zoomRequest.emit(v_delta)
        else:
            v_delta and self.scrollRequest.emit(v_delta, Qt.Vertical)
            h_delta and self.scrollRequest.emit(h_delta, Qt.Horizontal)
        ev.accept()

    def keyPressEvent(self, ev):
        key = ev.key()
        if key == Qt.Key_Escape and self.current:
            print('ESC press')
            self.current = None
            self.drawingPolygon.emit(False)
            self.update()
        elif key == Qt.Key_Return and self.canCloseShape():
            self.finalise()
        #  translation
        elif key == Qt.Key_Left and self.selectedShape:
            self.moveOnePixel('Left')
        elif key == Qt.Key_Right and self.selectedShape:
            self.moveOnePixel('Right')
        elif key == Qt.Key_Up and self.selectedShape:
            self.moveOnePixel('Up')
        elif key == Qt.Key_Down and self.selectedShape:
            self.moveOnePixel('Down')
        # rotation - 检查是否允许旋转
        elif key == Qt.Key_O and self.selectedShape and self._canRotate():  # O
            self.rotateShape(-math.pi/1800)  # -0.1 degree
        elif key == Qt.Key_P and self.selectedShape and self._canRotate():  # P
            self.rotateShape(math.pi/1800)  # 0.1 degree
        elif key == Qt.Key_K and self.selectedShape and self._canRotate():  # K
            self.rotateShape(-math.pi/180)  # -1 degree
        elif key == Qt.Key_L and self.selectedShape and self._canRotate():  # L
            self.rotateShape(math.pi/180)  # -1 degree
        elif key == Qt.Key_M and self.selectedShape and self._canRotate():   # M
            self.rotateShape(-math.pi/36)  # -5 degree
        elif key == Qt.Key_Comma and self.selectedShape and self._canRotate():    # 逗号,
            self.rotateShape(math.pi/36)  # 5 degree
        # 添加Ctrl+Z撤销功能
        elif ev.modifiers() & Qt.ControlModifier and key == Qt.Key_Z:
            self.undo()
        '''
        #当前安装PYQT版本不识别括号 https://www.riverbankcomputing.com/static/Docs/PyQt5/search.html?q=qt.key_
        elif key == Qt.Key_BarceLeft and self.selectedShape:    # 大括号
            self.moveOnePixel('Down')
        elif key == Qt.Key_BarcketLeft and self.selectedShape:    # 中括号
            self.moveOnePixel('Down')
        elif key == Qt.Key_ParenLeft and self.selectedShape:    # 小括号
            self.moveOnePixel('Down')
        '''

    def moveOnePixel(self, direction):
        # print(self.selectedShape.points)
        moved = False
        if direction == 'Left' and not self.moveOutOfBound(QPointF(-1.0, 0)):
            # print("move Left one pixel")
            self.selectedShape.points[0] += QPointF(-1.0, 0)
            self.selectedShape.points[1] += QPointF(-1.0, 0)
            self.selectedShape.points[2] += QPointF(-1.0, 0)
            self.selectedShape.points[3] += QPointF(-1.0, 0)
            moved = True
        elif direction == 'Right' and not self.moveOutOfBound(QPointF(1.0, 0)):
            # print("move Right one pixel")
            self.selectedShape.points[0] += QPointF(1.0, 0)
            self.selectedShape.points[1] += QPointF(1.0, 0)
            self.selectedShape.points[2] += QPointF(1.0, 0)
            self.selectedShape.points[3] += QPointF(1.0, 0)
            moved = True
        elif direction == 'Up' and not self.moveOutOfBound(QPointF(0, -1.0)):
            # print("move Up one pixel")
            self.selectedShape.points[0] += QPointF(0, -1.0)
            self.selectedShape.points[1] += QPointF(0, -1.0)
            self.selectedShape.points[2] += QPointF(0, -1.0)
            self.selectedShape.points[3] += QPointF(0, -1.0)
            moved = True
        elif direction == 'Down' and not self.moveOutOfBound(QPointF(0, 1.0)):
            # print("move Down one pixel")
            self.selectedShape.points[0] += QPointF(0, 1.0)
            self.selectedShape.points[1] += QPointF(0, 1.0)
            self.selectedShape.points[2] += QPointF(0, 1.0)
            self.selectedShape.points[3] += QPointF(0, 1.0)
            moved = True
        
        if moved:
            self.shapeMoved.emit()
            self.repaint()
            # 直接保存状态而不仅仅启动计时器
            self.saveState()

    def moveOutOfBound(self, step):
        points = [p1+p2 for p1, p2 in zip(self.selectedShape.points, [step]*4)]
        return True in map(self.outOfPixmap, points)

    def setLastLabel(self, text, line_color  = None, fill_color = None):
        assert text
        self.shapes[-1].label = text
        if line_color:
            self.shapes[-1].line_color = line_color
        
        if fill_color:
            self.shapes[-1].fill_color = fill_color

        return self.shapes[-1]

    def undoLastLine(self):
        assert self.shapes
        self.current = self.shapes.pop()
        self.current.setOpen()
        self.line.points = [self.current[-1], self.current[0]]
        self.drawingPolygon.emit(True)

    def resetAllLines(self):
        assert self.shapes
        self.current = self.shapes.pop()
        self.current.setOpen()
        self.line.points = [self.current[-1], self.current[0]]
        self.drawingPolygon.emit(True)
        self.current = None
        self.drawingPolygon.emit(False)
        self.update()

    def loadPixmap(self, pixmap):
        self.pixmap = pixmap
        self.shapes = []
        # 重置历史记录
        self.history = []
        self.historyIndex = -1
        self.currentState = None
        self.repaint()
        # 加载图片后保存初始状态
        self.saveInitialState()

    def loadShapes(self, shapes):
        self.shapes = list(shapes)
        self.current = None
        # 不调用updateOBBInfo，保持形状的原始属性
        self.repaint()
        # 加载形状后保存初始状态
        self.history = []
        self.historyIndex = -1
        self.currentState = None
        self.saveInitialState()

    def setShapeVisible(self, shape, value):
        self.visible[shape] = value
        self.repaint()

    def currentCursor(self):
        cursor = QApplication.overrideCursor()
        if cursor is not None:
            cursor = cursor.shape()
        return cursor

    def overrideCursor(self, cursor):
        self._cursor = cursor
        if self.currentCursor() is None:
            QApplication.setOverrideCursor(cursor)
        else:
            QApplication.changeOverrideCursor(cursor)

    def restoreCursor(self):
        QApplication.restoreOverrideCursor()

    def resetState(self):
        self.restoreCursor()
        self.pixmap = None
        # 重置历史记录
        self.history = []
        self.historyIndex = -1
        self.currentState = None
        self.update()

    def setDrawingShapeToSquare(self, status):
        self.drawSquare = status

    # 添加以下方法用于状态管理和撤销功能
    def saveInitialState(self):
        """保存初始状态"""
        if self.pixmap:
            self.saveState()
    
    def saveState(self):
        """保存当前状态到历史记录"""
        if not self.pixmap:
            return
            
        # 创建当前状态的深拷贝
        state = {
            'shapes': [s.copy() for s in self.shapes],
            'current': self.current.copy() if self.current else None,
            'selectedShape': self.selectedShape,
            'selectedShapeIndex': -1  # 默认为-1表示没有选中形状
        }
        
        # 检查selectedShape是否在shapes列表中
        if self.selectedShape is not None:
            try:
                state['selectedShapeIndex'] = self.shapes.index(self.selectedShape)
            except ValueError:
                # 如果selectedShape不在shapes列表中，将其设为None
                state['selectedShape'] = None
                state['selectedShapeIndex'] = -1
        
        # 不调用updateOBBInfo，保持形状的原始OBB信息
        # 这样可以避免在保存时意外改变形状的属性
        
        # 判断状态是否发生变化
        if self.currentState is not None:
            # 如果形状数量不同，则状态已变化
            if len(state['shapes']) != len(self.currentState['shapes']):
                needSave = True
            else:
                # 比较每个形状的点和OBB信息是否相同
                needSave = False
                for i, shape in enumerate(state['shapes']):
                    if len(shape.points) != len(self.currentState['shapes'][i].points):
                        needSave = True
                        break
                    
                    # 检查点坐标
                    for j, point in enumerate(shape.points):
                        if (point.x() != self.currentState['shapes'][i].points[j].x() or 
                            point.y() != self.currentState['shapes'][i].points[j].y()):
                            needSave = True
                            break
                    
                    # 检查角度和尺寸
                    if (shape.angle != self.currentState['shapes'][i].angle or
                        shape.width != self.currentState['shapes'][i].width or
                        shape.height != self.currentState['shapes'][i].height):
                        needSave = True
                        break
                        
                    # 检查中心点
                    if (shape.origin[0] != self.currentState['shapes'][i].origin[0] or
                        shape.origin[1] != self.currentState['shapes'][i].origin[1]):
                        needSave = True
                        break
                        
                    if needSave:
                        break
        else:
            needSave = True
        
        # 如果状态发生变化，保存到历史记录
        if needSave:
            # 防止保存空状态（无任何形状）导致撤销后所有形状消失
            if len(state['shapes']) == 0 and len(self.history) > 0 and len(self.history[-1]['shapes']) > 0:
                # 仅当前一个状态有形状而当前状态没有形状时，跳过保存
                return
                
            # 如果当前位置不是最新历史记录，则删除之后的记录
            if self.historyIndex < len(self.history) - 1:
                self.history = self.history[:self.historyIndex + 1]
            
            # 添加新状态到历史记录
            self.history.append(state)
            self.historyIndex = len(self.history) - 1
            
            # 如果历史记录超过最大数量，删除最早的记录
            if len(self.history) > self.MAX_HISTORY:
                self.history.pop(0)
                self.historyIndex -= 1
            
            # 更新当前状态
            self.currentState = state
            
    def startSaveTimer(self):
        """启动保存定时器"""
        self.saveTimer.start(100)  # 100毫秒后保存状态
    
    def undo(self):
        """撤销到上一个状态"""
        if self.historyIndex > 0:
            # 先检查当前状态是否需要保存
            current_shapes_count = len(self.shapes)
            if current_shapes_count > 0 and self.historyIndex == len(self.history) - 1:
                # 当前可能有未保存的状态，先保存
                self.saveState()
                
            self.historyIndex -= 1
            state = self.history[self.historyIndex]
            
            # 额外检查：如果撤销会导致所有形状消失，且不是第一个状态，则跳过
            if len(state['shapes']) == 0 and self.historyIndex > 0:
                self.historyIndex -= 1
                state = self.history[self.historyIndex]
                
            self.restoreState(state)
            self.undoOperation.emit()
            return True
        return False
    
    def restoreState(self, state):
        """恢复到指定状态"""
        # 保存当前标签以便恢复
        shape_labels = {}
        for shape in self.shapes:
            if shape.label:
                shape_labels[id(shape)] = shape.label
                
        # 从状态恢复形状
        self.shapes = []
        for s in state['shapes']:
            # 完全复制形状，保持所有原始信息
            new_shape = s.copy()
            # 确保所有信息被正确复制，不重新计算
            new_shape.angle = s.angle
            new_shape.width = s.width
            new_shape.height = s.height
            new_shape.origin = [o for o in s.origin]
            new_shape.points = [QPointF(p.x(), p.y()) for p in s.points]  # 直接复制原始点位置
            new_shape.rotation_enabled = getattr(s, 'rotation_enabled', True)  # 复制旋转设置
            
            # 不调用updatePointsFromOBBInfo，直接使用保存的点位置
            # 这样可以避免意外的形状变化
            self.shapes.append(new_shape)
        
        # 尝试恢复标签
        for i, shape in enumerate(self.shapes):
            # 保持形状的属性，比如标签
            if state['shapes'][i].label:
                shape.label = state['shapes'][i].label
                
        self.current = state['current'].copy() if state['current'] else None
        
        self.selectedShape = None
        if state['selectedShapeIndex'] >= 0 and state['selectedShapeIndex'] < len(self.shapes):
            self.selectedShape = self.shapes[state['selectedShapeIndex']]
            self.selectedShape.selected = True
            
        self.update()
        
