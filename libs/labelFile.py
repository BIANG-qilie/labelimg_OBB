# Copyright (c) 2016 Tzutalin
# Create by TzuTaLin <tzu.ta.lin@gmail.com>

try:
    from PyQt5.QtGui import QImage
except ImportError:
    from PyQt4.QtGui import QImage

from base64 import b64encode, b64decode
from libs.constants import TXT_EXT
from libs.format_converter import format_converter
import os.path
import sys


class LabelFileError(Exception):
    pass


class LabelFile(object):
    # It might be changed as window creates. By default, using TXT ext
    # suffix = '.lif'
    suffix = TXT_EXT

    def __init__(self, filename=None):
        self.shapes = ()
        self.imagePath = None
        self.imageData = None
        self.verified = False

    def savePascalVocFormat(self, filename, shapes, imagePath, imageData,
                            lineColor=None, fillColor=None, databaseSrc=None):
        """保存为Pascal VOC格式，使用dataset_format_converter"""
        # 先保存为LabelImg-OBB格式，然后转换
        import tempfile
        temp_fd, temp_file = tempfile.mkstemp(suffix='.txt')
        os.close(temp_fd)
        
        try:
            # 转换shapes为OBB格式
            obb_shapes = self._convert_shapes_to_obb(shapes)
            self.saveYoloOBBFormat(temp_file, obb_shapes, imagePath, imageData, [])
            
            # 使用converter转换为Pascal VOC
            image = QImage()
            image.load(imagePath)
            
            success = format_converter.convert_file(
                input_file=temp_file,
                output_file=filename,
                input_format='LabelImg-OBB',
                output_format='PASCAL-VOC',
                image_width=image.width(),
                image_height=image.height(),
                class_names=[]
            )
            
            if not success:
                print("转换为Pascal VOC格式失败")
                
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def saveYoloFormat(self, filename, shapes, imagePath, imageData, classList,
                            lineColor=None, fillColor=None, databaseSrc=None):
        """保存为YOLO格式，使用dataset_format_converter"""
        # 先保存为LabelImg-OBB格式，然后转换
        import tempfile
        temp_fd, temp_file = tempfile.mkstemp(suffix='.txt')
        os.close(temp_fd)
        
        try:
            # 转换shapes为OBB格式
            obb_shapes = self._convert_shapes_to_obb(shapes)
            self.saveYoloOBBFormat(temp_file, obb_shapes, imagePath, imageData, classList)
            
            # 使用converter转换为YOLO HBB
            image = QImage()
            image.load(imagePath)
            
            success = format_converter.convert_file(
                input_file=temp_file,
                output_file=filename,
                input_format='LabelImg-OBB',
                output_format='YOLO-HBB',
                image_width=image.width(),
                image_height=image.height(),
                class_names=classList
            )
            
            if not success:
                print("转换为YOLO格式失败")
                
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def saveYoloOBBFormat(self, filename, shapes, imagePath, imageData, classList,
                            lineColor=None, fillColor=None, databaseSrc=None):
        """保存为LabelImg-OBB格式（原YOLO_OBB格式）"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # 写入格式标识
                f.write("YOLO_OBB\n")

                # 写入所有标注
                for shape in shapes:
                    centre_x_y = shape['centre_x_y']
                    height = shape['height']
                    width = shape['width']
                    angle = shape['angle']
                    label = shape['label']
                        
                    # 获取类别索引
                    if label in classList:
                        class_index = classList.index(label)
                    else:
                        class_index = 0  # 默认类别
                    
                    # 写入标注行：class_index cx cy w h angle
                    f.write(f"{class_index} {centre_x_y[0]} {centre_x_y[1]} {width} {height} {angle}\n")
                        
        except Exception as e:
            print(f"保存LabelImg-OBB格式失败: {e}")
            return False
        
        return True
    
    def _convert_shapes_to_obb(self, shapes):
        """将普通shapes转换为OBB格式"""
        obb_shapes = []
        for shape in shapes:
            if 'centre_x_y' in shape:
                # 已经是OBB格式
                obb_shapes.append(shape)
            else:
                # 从points转换为OBB格式
                points = shape['points']
                label = shape['label']
                difficult = shape.get('difficult', False)
                
                # 计算边界框
                bndbox = LabelFile.convertPoints2BndBox(points)
                x_min, y_min, x_max, y_max = bndbox
                
                # 转换为中心点和尺寸
                cx = (x_min + x_max) / 2
                cy = (y_min + y_max) / 2
                width = x_max - x_min
                height = y_max - y_min
                angle = 0.0  # 默认角度
                
                obb_shape = {
                    'label': label,
                    'centre_x_y': (cx, cy),
                    'width': width,
                    'height': height,
                    'angle': angle,
                    'difficult': difficult,
                    'line_color': shape.get('line_color'),
                    'fill_color': shape.get('fill_color')
                }
                obb_shapes.append(obb_shape)
        
        return obb_shapes
    
    def saveWithConverter(self, filename, shapes, imagePath, imageData, 
                         input_format, output_format, classList=None,
                         lineColor=None, fillColor=None, databaseSrc=None):
        """
        使用 format_converter 进行高级格式转换
        
        Args:
            filename: 输出文件路径
            shapes: 形状数据
            imagePath: 图像路径  
            imageData: 图像数据
            input_format: 输入格式
            output_format: 输出格式
            classList: 类别列表
        """
        if not format_converter.is_converter_available():
            print("错误: dataset-format-converter 未安装，无法使用高级转换功能")
            return False
            
        try:
            # 获取图像尺寸
            image = QImage()
            image.load(imagePath)
            image_width = image.width()
            image_height = image.height()
            
            # 创建临时的输入文件
            import tempfile
            temp_dir = tempfile.mkdtemp()
            
            # 根据当前格式保存临时文件
            temp_input_file = os.path.join(temp_dir, "temp_input.txt")
            
            if input_format == 'YOLO_OBB':
                self.saveYoloOBBFormat(temp_input_file, shapes, imagePath, imageData, classList)
            elif input_format == 'YOLO':
                self.saveYoloFormat(temp_input_file, shapes, imagePath, imageData, classList)
            elif input_format == 'PascalVOC':
                temp_input_file = os.path.join(temp_dir, "temp_input.xml")
                self.savePascalVocFormat(temp_input_file, shapes, imagePath, imageData)
            else:
                print(f"不支持的输入格式: {input_format}")
                return False
            
            # 创建类别文件（如果需要）
            classes_file = None
            if classList:
                classes_file = os.path.join(temp_dir, "classes.txt")
                with open(classes_file, 'w', encoding='utf-8') as f:
                    for class_name in classList:
                        f.write(f"{class_name}\n")
            
            # 调用format_converter进行转换
            success = format_converter.convert_file(
                input_file=temp_input_file,
                output_file=filename,
                input_format=input_format,
                output_format=output_format,
                image_width=image_width,
                image_height=image_height,
                classes_file=classes_file
            )
            
            # 清理临时文件
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return success
            
        except Exception as e:
            print(f"使用转换器保存失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def toggleVerify(self):
        self.verified = not self.verified

    ''' ttf is disable
    def load(self, filename):
        import json
        with open(filename, 'rb') as f:
                data = json.load(f)
                imagePath = data['imagePath']
                imageData = b64decode(data['imageData'])
                lineColor = data['lineColor']
                fillColor = data['fillColor']
                shapes = ((s['label'], s['points'], s['line_color'], s['fill_color'])\
                        for s in data['shapes'])
                # Only replace data after everything is loaded.
                self.shapes = shapes
                self.imagePath = imagePath
                self.imageData = imageData
                self.lineColor = lineColor
                self.fillColor = fillColor

    def save(self, filename, shapes, imagePath, imageData, lineColor=None, fillColor=None):
        import json
        with open(filename, 'wb') as f:
                json.dump(dict(
                    shapes=shapes,
                    lineColor=lineColor, fillColor=fillColor,
                    imagePath=imagePath,
                    imageData=b64encode(imageData)),
                    f, ensure_ascii=True, indent=2)
    '''

    @staticmethod
    def isLabelFile(filename):
        fileSuffix = os.path.splitext(filename)[1].lower()
        return fileSuffix == LabelFile.suffix

    @staticmethod
    def convertPoints2BndBox(points):
        xmin = float('inf')
        ymin = float('inf')
        xmax = float('-inf')
        ymax = float('-inf')
        for p in points:
            x = p[0]
            y = p[1]
            xmin = min(x, xmin)
            ymin = min(y, ymin)
            xmax = max(x, xmax)
            ymax = max(y, ymax)

        # Martin Kersner, 2015/11/12
        # 0-valued coordinates of BB caused an error while
        # training faster-rcnn object detector.
        if xmin < 1:
            xmin = 1

        if ymin < 1:
            ymin = 1

        return (int(xmin), int(ymin), int(xmax), int(ymax))
