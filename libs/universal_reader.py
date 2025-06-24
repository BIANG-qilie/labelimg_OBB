#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import tempfile
from typing import List, Tuple, Optional
from libs.format_converter import format_converter
from libs.constants import *

class UniversalReader:
    """统一的标注文件读取器，使用dataset_format_converter"""
    
    def __init__(self, file_path: str, image_size: Tuple[int, int], class_names: Optional[List[str]] = None):
        """
        初始化读取器
        
        Args:
            file_path: 标注文件路径
            image_size: 图像尺寸 (width, height)
            class_names: 类别名称列表
        """
        self.file_path = file_path
        self.image_width, self.image_height = image_size
        self.class_names = class_names or []
        self.shapes = []
        self.verified = False
        
    def get_shapes(self) -> List[Tuple]:
        """
        获取标注形状列表
        
        Returns:
            List[Tuple]: 形状列表，每个元素为 (label, x, y, w, h, angle, ...)
        """
        if not self.shapes:
            self._parse_file()
        return self.shapes
    
    def _parse_file(self):
        """解析标注文件"""
        if not os.path.exists(self.file_path):
            return
            
        try:
            # 检测文件格式
            detected_format = format_converter.detect_format(self.file_path)
            if not detected_format:
                # 如果检测失败，尝试根据文件扩展名和内容判断
                detected_format = self._fallback_format_detection()
            
            print(f"检测到格式: {detected_format}")
            
            # 根据格式解析文件
            if detected_format == FORMAT_PASCALVOC:
                self._parse_pascal_voc()
            elif detected_format == FORMAT_YOLO:
                self._parse_yolo_hbb()
            elif detected_format == FORMAT_YOLO_OBB:
                self._parse_yolo_obb()
            elif detected_format == FORMAT_LABELIMG_OBB:
                self._parse_labelimg_obb()
            elif detected_format == FORMAT_DOTA:
                self._parse_dota()
            else:
                # 默认尝试LabelImg-OBB格式
                self._parse_labelimg_obb()
                
        except Exception as e:
            print(f"解析文件失败: {e}")
            # 尝试回退方法
            self._fallback_parse()
    
    def _fallback_format_detection(self) -> str:
        """回退格式检测"""
        file_ext = os.path.splitext(self.file_path)[1].lower()
        
        if file_ext == '.xml':
            return FORMAT_PASCALVOC
        elif file_ext == '.txt':
            # 尝试读取第一行判断格式
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line == "YOLO_OBB":
                        return FORMAT_LABELIMG_OBB
                    elif first_line.startswith('<annotation'):
                        return FORMAT_PASCALVOC
                    else:
                        # 尝试解析数字来判断格式
                        parts = first_line.split()
                        if len(parts) == 5:  # class x y w h
                            return FORMAT_YOLO
                        elif len(parts) >= 8:  # class + 8个坐标或更多
                            return FORMAT_YOLO_OBB
                        else:
                            return FORMAT_LABELIMG_OBB
            except:
                return FORMAT_LABELIMG_OBB
        
        return FORMAT_LABELIMG_OBB
    
    def _parse_pascal_voc(self):
        """解析PASCAL VOC格式"""
        try:
            # 使用dataset_format_converter转换为LabelImg-OBB格式
            temp_file = self._convert_to_labelimg_obb(FORMAT_PASCALVOC)
            if temp_file:
                self._parse_labelimg_obb_file(temp_file)
                os.unlink(temp_file)
        except Exception as e:
            print(f"解析PASCAL VOC失败: {e}")
    
    def _parse_yolo_hbb(self):
        """解析YOLO HBB格式"""
        try:
            # 使用dataset_format_converter转换为LabelImg-OBB格式
            temp_file = self._convert_to_labelimg_obb(FORMAT_YOLO)
            if temp_file:
                self._parse_labelimg_obb_file(temp_file)
                os.unlink(temp_file)
        except Exception as e:
            print(f"解析YOLO HBB失败: {e}")
    
    def _parse_yolo_obb(self):
        """解析YOLO OBB格式"""
        try:
            # 使用dataset_format_converter转换为LabelImg-OBB格式
            temp_file = self._convert_to_labelimg_obb(FORMAT_YOLO_OBB)
            if temp_file:
                self._parse_labelimg_obb_file(temp_file)
                os.unlink(temp_file)
        except Exception as e:
            print(f"解析YOLO OBB失败: {e}")
    
    def _parse_dota(self):
        """解析DOTA格式"""
        try:
            # 使用dataset_format_converter转换为LabelImg-OBB格式
            temp_file = self._convert_to_labelimg_obb(FORMAT_DOTA)
            if temp_file:
                self._parse_labelimg_obb_file(temp_file)
                os.unlink(temp_file)
        except Exception as e:
            print(f"解析DOTA失败: {e}")
    
    def _parse_labelimg_obb(self):
        """解析LabelImg-OBB格式"""
        self._parse_labelimg_obb_file(self.file_path)
    
    def _convert_to_labelimg_obb(self, source_format: str) -> Optional[str]:
        """将其他格式转换为LabelImg-OBB格式"""
        try:
            # 创建临时文件
            temp_fd, temp_file = tempfile.mkstemp(suffix='.txt')
            os.close(temp_fd)
            
            # 使用format_converter进行转换
            success = format_converter.convert_file(
                input_file=self.file_path,
                output_file=temp_file,
                input_format=source_format,
                output_format=FORMAT_LABELIMG_OBB,
                image_width=self.image_width,
                image_height=self.image_height,
                class_names=self.class_names
            )
            
            if success:
                return temp_file
            else:
                os.unlink(temp_file)
                return None
                
        except Exception as e:
            print(f"格式转换失败: {e}")
            return None
    
    def _parse_labelimg_obb_file(self, file_path: str):
        """解析LabelImg-OBB格式文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 跳过第一行如果是格式标识
            start_line = 1 if lines and lines[0].strip() == "YOLO_OBB" else 0
            
            for line in lines[start_line:]:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    parts = line.split()
                    if len(parts) >= 6:
                        # LabelImg-OBB格式: class_index cx cy w h angle
                        class_index = int(parts[0])
                        cx = float(parts[1])
                        cy = float(parts[2])
                        w = float(parts[3])
                        h = float(parts[4])
                        angle = float(parts[5]) if len(parts) > 5 else 0.0
                        
                        # 获取类别名称
                        if class_index < len(self.class_names):
                            label = self.class_names[class_index]
                        else:
                            label = f"class_{class_index}"
                        
                        # 添加到形状列表
                        # 格式: (label, cx, cy, h, w, angle, None, None, False) - 保持与文件中w h的顺序一致
                        shape = (label, cx, cy, w, h, angle, None, None, False)
                        self.shapes.append(shape)
                        
                        print(f"已加载标注: {label} - 中心点({cx}, {cy}), 尺寸({w}x{h}), 角度{angle}度")
                        
                except ValueError as e:
                    print(f"解析行失败: {line}, 错误: {e}")
                    continue
                    
        except Exception as e:
            print(f"读取文件失败: {e}")
    
    def _fallback_parse(self):
        """回退解析方法"""
        try:
            # 尝试直接解析为LabelImg-OBB格式
            self._parse_labelimg_obb_file(self.file_path)
        except Exception as e:
            print(f"回退解析也失败: {e}") 