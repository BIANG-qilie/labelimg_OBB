#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格式转换器模块
集成 dataset-format-converter 库来支持多格式导出
"""

import os
import tempfile
import traceback
from typing import List, Dict, Optional, Tuple

try:
    from dataset_format_converter import FormatManager
    # 创建全局格式管理器实例
    format_manager = FormatManager()
    CONVERTER_AVAILABLE = True
except ImportError:
    CONVERTER_AVAILABLE = False
    format_manager = None
    print("警告: dataset-format-converter 未安装，高级格式转换功能不可用")
    print("安装命令: pip install dataset-format-converter")

from libs.constants import FORMAT_PASCALVOC, FORMAT_YOLO, FORMAT_YOLO_OBB, FORMAT_DOTA, FORMAT_LABELIMG_OBB


class FormatConverter:
    """格式转换器类，集成多种标注格式的转换功能"""
    
    # 格式映射：内部格式 -> dataset-format-converter格式
    FORMAT_MAPPING = {
        FORMAT_PASCALVOC: 'PASCAL-VOC',
        FORMAT_YOLO: 'YOLO-HBB', 
        FORMAT_YOLO_OBB: 'YOLO-OBB',
        FORMAT_DOTA: 'DOTA',
        FORMAT_LABELIMG_OBB: 'LabelImg-OBB'
    }
    
    # 逆向映射：dataset-format-converter格式 -> 内部格式
    REVERSE_FORMAT_MAPPING = {v: k for k, v in FORMAT_MAPPING.items()}
    
    def __init__(self):
        self.available_formats = self._get_available_formats()
        
    def _get_available_formats(self) -> List[str]:
        """获取所有可用的格式列表"""
        if not CONVERTER_AVAILABLE:
            return list(self.FORMAT_MAPPING.keys())
        
        try:
            # 获取dataset-format-converter支持的格式
            external_formats = format_manager.list_formats()
            
            # 合并内部格式和外部格式
            all_formats = list(self.FORMAT_MAPPING.keys())
            
            # 添加外部独有的格式
            for ext_format in external_formats:
                if ext_format not in self.FORMAT_MAPPING.values():
                    all_formats.append(ext_format)
                    
            return all_formats
        except Exception as e:
            print(f"获取外部格式失败: {e}")
            return list(self.FORMAT_MAPPING.keys())
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的格式列表"""
        return self.available_formats.copy()
    
    def is_converter_available(self) -> bool:
        """检查dataset-format-converter是否可用"""
        return CONVERTER_AVAILABLE
    
    def convert_file(self, 
                    input_file: str, 
                    output_file: str,
                    input_format: str,
                    output_format: str,
                    image_width: int,
                    image_height: int,
                    classes_file: Optional[str] = None,
                    class_names: Optional[List[str]] = None) -> bool:
        """
        转换单个文件
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            input_format: 输入格式
            output_format: 输出格式
            image_width: 图像宽度
            image_height: 图像高度
            classes_file: 类别文件路径（可选）
            
        Returns:
            bool: 转换是否成功
        """
        if not CONVERTER_AVAILABLE:
            print("错误: dataset-format-converter 未安装")
            return False
            
        if not os.path.exists(input_file):
            print(f"错误: 输入文件不存在: {input_file}")
            return False
            
        try:
            # 映射格式名称
            mapped_input_format = self.FORMAT_MAPPING.get(input_format, input_format)
            mapped_output_format = self.FORMAT_MAPPING.get(output_format, output_format)
            
            # 处理类别名称
            if class_names is None and classes_file and os.path.exists(classes_file):
                # 从文件读取类别名称
                with open(classes_file, 'r', encoding='utf-8') as f:
                    class_names = [line.strip() for line in f.readlines() if line.strip()]
            
            # 调用dataset-format-converter进行转换
            format_manager.convert_file(
                input_file=input_file,
                output_file=output_file,
                input_format=mapped_input_format,
                output_format=mapped_output_format,
                image_width=image_width,
                image_height=image_height,
                class_names=class_names
            )
            
            print(f"转换成功: {input_file} -> {output_file}")
            print(f"格式: {input_format} -> {output_format}")
            return True
            
        except Exception as e:
            print(f"转换失败: {e}")
            traceback.print_exc()
            return False
    
    def convert_directory(self,
                         input_dir: str,
                         output_dir: str,
                         input_format: str,
                         output_format: str,
                         image_width: int,
                         image_height: int,
                         classes_file: Optional[str] = None,
                         class_names: Optional[List[str]] = None) -> Tuple[int, int]:
        """
        批量转换目录中的文件
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            input_format: 输入格式
            output_format: 输出格式
            image_width: 图像宽度
            image_height: 图像高度
            classes_file: 类别文件路径（可选）
            
        Returns:
            Tuple[int, int]: (成功数量, 总数量)
        """
        if not CONVERTER_AVAILABLE:
            print("错误: dataset-format-converter 未安装")
            return 0, 0
            
        if not os.path.exists(input_dir):
            print(f"错误: 输入目录不存在: {input_dir}")
            return 0, 0
            
        try:
            # 映射格式名称
            mapped_input_format = self.FORMAT_MAPPING.get(input_format, input_format)
            mapped_output_format = self.FORMAT_MAPPING.get(output_format, output_format)
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 处理类别名称
            if class_names is None and classes_file and os.path.exists(classes_file):
                # 从文件读取类别名称
                with open(classes_file, 'r', encoding='utf-8') as f:
                    class_names = [line.strip() for line in f.readlines() if line.strip()]
            
            # 调用dataset-format-converter进行批量转换
            result = format_manager.convert_directory(
                input_dir=input_dir,
                output_dir=output_dir,
                input_format=mapped_input_format,
                output_format=mapped_output_format,
                image_width=image_width,
                image_height=image_height,
                class_names=class_names
            )
            
            print(f"批量转换完成: {input_dir} -> {output_dir}")
            print(f"格式: {input_format} -> {output_format}")
            
            # 统计转换结果
            if isinstance(result, dict):
                success_count = result.get('success', 0)
                total_count = result.get('total', 0)
            else:
                # 如果没有返回统计信息，手动计算
                success_count = len([f for f in os.listdir(output_dir) if os.path.isfile(os.path.join(output_dir, f))])
                total_count = len([f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))])
            
            return success_count, total_count
            
        except Exception as e:
            print(f"批量转换失败: {e}")
            traceback.print_exc()
            return 0, 0
    
    def detect_format(self, file_path: str) -> Optional[str]:
        """
        自动检测文件格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[str]: 检测到的格式，如果检测失败返回None
        """
        if not CONVERTER_AVAILABLE:
            return None
            
        if not os.path.exists(file_path):
            return None
            
        try:
            detected_format = format_manager.detect_format(file_path)
            
            # 尝试映射回内部格式
            internal_format = self.REVERSE_FORMAT_MAPPING.get(detected_format, detected_format)
            
            print(f"检测到格式: {detected_format} (映射为: {internal_format})")
            return internal_format
            
        except Exception as e:
            print(f"格式检测失败: {e}")
            return None
    
    def get_format_info(self) -> Dict[str, Dict]:
        """获取格式信息"""
        if not CONVERTER_AVAILABLE:
            return {
                FORMAT_PASCALVOC: {"name": "PASCAL VOC", "extension": ".xml", "type": "HBB"},
                FORMAT_YOLO: {"name": "YOLO", "extension": ".txt", "type": "HBB"},
                FORMAT_YOLO_OBB: {"name": "YOLO OBB", "extension": ".txt", "type": "OBB"},
                FORMAT_DOTA: {"name": "DOTA", "extension": ".txt", "type": "OBB"},
                FORMAT_LABELIMG_OBB: {"name": "LabelImg OBB", "extension": ".txt", "type": "OBB"}
            }
        
        try:
            # 构建详细的格式信息
            format_info = {}
            
            for format_name in self.available_formats:
                if format_name in self.FORMAT_MAPPING:
                    # 内部格式
                    if format_name == FORMAT_PASCALVOC:
                        format_info[format_name] = {"name": "PASCAL VOC", "extension": ".xml", "type": "HBB"}
                    elif format_name == FORMAT_YOLO:
                        format_info[format_name] = {"name": "YOLO", "extension": ".txt", "type": "HBB"}
                    elif format_name == FORMAT_YOLO_OBB:
                        format_info[format_name] = {"name": "YOLO OBB", "extension": ".txt", "type": "OBB"}
                    elif format_name == FORMAT_DOTA:
                        format_info[format_name] = {"name": "DOTA", "extension": ".txt", "type": "OBB"}
                    elif format_name == FORMAT_LABELIMG_OBB:
                        format_info[format_name] = {"name": "LabelImg OBB", "extension": ".txt", "type": "OBB"}
                else:
                    format_info[format_name] = {"name": format_name, "extension": ".txt", "type": "Unknown"}
            
            return format_info
            
        except Exception as e:
            print(f"获取格式信息失败: {e}")
            return {}


# 全局实例
format_converter = FormatConverter() 