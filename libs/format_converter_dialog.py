#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格式转换对话框
提供用户友好的格式转换界面
"""

try:
    from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                 QComboBox, QPushButton, QFileDialog, QLineEdit,
                                 QSpinBox, QCheckBox, QTextEdit, QProgressBar,
                                 QGroupBox, QGridLayout, QMessageBox)
    from PyQt5.QtCore import Qt, QThread, pyqtSignal
    from PyQt5.QtGui import QFont
except ImportError:
    from PyQt4.QtGui import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QFileDialog, QLineEdit,
                             QSpinBox, QCheckBox, QTextEdit, QProgressBar,
                             QGroupBox, QGridLayout, QMessageBox)
    from PyQt4.QtCore import Qt, QThread, pyqtSignal
    from PyQt4.QtGui import QFont

import os
import sys
from libs.format_converter import format_converter
from libs.constants import FORMAT_PASCALVOC, FORMAT_YOLO, FORMAT_YOLO_OBB, FORMAT_DOTA, FORMAT_LABELIMG_OBB


class ConvertWorker(QThread):
    """转换工作线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, input_path, output_path, input_format, output_format, 
                 image_width, image_height, classes_file=None, is_directory=False):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.input_format = input_format
        self.output_format = output_format
        self.image_width = image_width
        self.image_height = image_height
        self.classes_file = classes_file
        self.is_directory = is_directory
    
    def run(self):
        try:
            if self.is_directory:
                self.progress.emit(f"开始批量转换目录: {self.input_path}")
                success_count, total_count = format_converter.convert_directory(
                    input_dir=self.input_path,
                    output_dir=self.output_path,
                    input_format=self.input_format,
                    output_format=self.output_format,
                    image_width=self.image_width,
                    image_height=self.image_height,
                    classes_file=self.classes_file
                )
                
                if success_count > 0:
                    self.progress.emit(f"批量转换完成: {success_count}/{total_count} 个文件转换成功")
                    self.finished.emit(True, f"成功转换 {success_count}/{total_count} 个文件")
                else:
                    self.finished.emit(False, "批量转换失败")
            else:
                self.progress.emit(f"开始转换文件: {self.input_path}")
                success = format_converter.convert_file(
                    input_file=self.input_path,
                    output_file=self.output_path,
                    input_format=self.input_format,
                    output_format=self.output_format,
                    image_width=self.image_width,
                    image_height=self.image_height,
                    classes_file=self.classes_file
                )
                
                if success:
                    self.progress.emit("文件转换完成")
                    self.finished.emit(True, "文件转换成功")
                else:
                    self.finished.emit(False, "文件转换失败")
                    
        except Exception as e:
            self.finished.emit(False, f"转换过程中发生错误: {str(e)}")


class FormatConverterDialog(QDialog):
    """格式转换对话框"""
    
    def __init__(self, parent=None):
        super(FormatConverterDialog, self).__init__(parent)
        self.parent = parent
        self.setupUI()
        self.setup_connections()
        self.load_formats()
        
    def setupUI(self):
        """设置用户界面"""
        self.setWindowTitle("格式转换器 - 多格式标注转换")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("多格式标注转换工具")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 状态提示
        if not format_converter.is_converter_available():
            warning_label = QLabel("⚠️ dataset-format-converter 未安装，请先安装: pip install dataset-format-converter")
            warning_label.setStyleSheet("color: red; font-weight: bold;")
            layout.addWidget(warning_label)
        
        # 输入设置组
        input_group = QGroupBox("输入设置")
        input_layout = QGridLayout()
        
        # 输入模式选择
        input_layout.addWidget(QLabel("转换模式:"), 0, 0)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["单文件转换", "批量目录转换"])
        input_layout.addWidget(self.mode_combo, 0, 1)
        
        # 输入路径
        input_layout.addWidget(QLabel("输入路径:"), 1, 0)
        self.input_path_edit = QLineEdit()
        input_layout.addWidget(self.input_path_edit, 1, 1)
        
        self.input_browse_btn = QPushButton("浏览...")
        input_layout.addWidget(self.input_browse_btn, 1, 2)
        
        # 输入格式
        input_layout.addWidget(QLabel("输入格式:"), 2, 0)
        self.input_format_combo = QComboBox()
        input_layout.addWidget(self.input_format_combo, 2, 1)
        
        self.detect_format_btn = QPushButton("自动检测")
        input_layout.addWidget(self.detect_format_btn, 2, 2)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 输出设置组
        output_group = QGroupBox("输出设置")
        output_layout = QGridLayout()
        
        # 输出路径
        output_layout.addWidget(QLabel("输出路径:"), 0, 0)
        self.output_path_edit = QLineEdit()
        output_layout.addWidget(self.output_path_edit, 0, 1)
        
        self.output_browse_btn = QPushButton("浏览...")
        output_layout.addWidget(self.output_browse_btn, 0, 2)
        
        # 输出格式
        output_layout.addWidget(QLabel("输出格式:"), 1, 0)
        self.output_format_combo = QComboBox()
        output_layout.addWidget(self.output_format_combo, 1, 1)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # 图像尺寸设置组
        size_group = QGroupBox("图像尺寸设置")
        size_layout = QGridLayout()
        
        size_layout.addWidget(QLabel("图像宽度:"), 0, 0)
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(1, 9999)
        self.width_spinbox.setValue(1920)
        size_layout.addWidget(self.width_spinbox, 0, 1)
        
        size_layout.addWidget(QLabel("图像高度:"), 0, 2)
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(1, 9999)
        self.height_spinbox.setValue(1080)
        size_layout.addWidget(self.height_spinbox, 0, 3)
        
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)
        
        # 类别文件设置组
        classes_group = QGroupBox("类别设置")
        classes_layout = QGridLayout()
        
        self.use_classes_checkbox = QCheckBox("使用类别文件")
        classes_layout.addWidget(self.use_classes_checkbox, 0, 0)
        
        self.classes_path_edit = QLineEdit()
        self.classes_path_edit.setEnabled(False)
        classes_layout.addWidget(self.classes_path_edit, 0, 1)
        
        self.classes_browse_btn = QPushButton("浏览...")
        self.classes_browse_btn.setEnabled(False)
        classes_layout.addWidget(self.classes_browse_btn, 0, 2)
        
        classes_group.setLayout(classes_layout)
        layout.addWidget(classes_group)
        
        # 进度显示
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        layout.addWidget(self.log_text)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.setEnabled(format_converter.is_converter_available())
        
        self.cancel_btn = QPushButton("取消")
        
        button_layout.addStretch()
        button_layout.addWidget(self.convert_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def setup_connections(self):
        """设置信号连接"""
        self.input_browse_btn.clicked.connect(self.browse_input_path)
        self.output_browse_btn.clicked.connect(self.browse_output_path)
        self.classes_browse_btn.clicked.connect(self.browse_classes_file)
        self.detect_format_btn.clicked.connect(self.detect_input_format)
        self.use_classes_checkbox.toggled.connect(self.toggle_classes_file)
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        self.convert_btn.clicked.connect(self.start_conversion)
        self.cancel_btn.clicked.connect(self.reject)
        
    def load_formats(self):
        """加载格式列表"""
        formats = format_converter.get_supported_formats()
        
        self.input_format_combo.addItems(formats)
        self.output_format_combo.addItems(formats)
        
        # 设置默认值
        if FORMAT_YOLO_OBB in formats:
            self.input_format_combo.setCurrentText(FORMAT_YOLO_OBB)
        if FORMAT_DOTA in formats:
            self.output_format_combo.setCurrentText(FORMAT_DOTA)
            
    def on_mode_changed(self, mode):
        """模式切换"""
        if mode == "单文件转换":
            self.input_browse_btn.setText("选择文件")
            self.output_browse_btn.setText("保存文件")
        else:
            self.input_browse_btn.setText("选择目录")
            self.output_browse_btn.setText("选择目录")
            
    def browse_input_path(self):
        """浏览输入路径"""
        if self.mode_combo.currentText() == "单文件转换":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择输入文件", "", "标注文件 (*.txt *.xml);;所有文件 (*)")
            if file_path:
                self.input_path_edit.setText(file_path)
        else:
            dir_path = QFileDialog.getExistingDirectory(self, "选择输入目录")
            if dir_path:
                self.input_path_edit.setText(dir_path)
                
    def browse_output_path(self):
        """浏览输出路径"""
        if self.mode_combo.currentText() == "单文件转换":
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存输出文件", "", "标注文件 (*.txt *.xml);;所有文件 (*)")
            if file_path:
                self.output_path_edit.setText(file_path)
        else:
            dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
            if dir_path:
                self.output_path_edit.setText(dir_path)
                
    def browse_classes_file(self):
        """浏览类别文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择类别文件", "", "文本文件 (*.txt);;所有文件 (*)")
        if file_path:
            self.classes_path_edit.setText(file_path)
            
    def toggle_classes_file(self, checked):
        """切换类别文件使用"""
        self.classes_path_edit.setEnabled(checked)
        self.classes_browse_btn.setEnabled(checked)
        
    def detect_input_format(self):
        """自动检测输入格式"""
        input_path = self.input_path_edit.text().strip()
        if not input_path:
            QMessageBox.warning(self, "警告", "请先选择输入文件")
            return
            
        if not os.path.exists(input_path):
            QMessageBox.warning(self, "警告", "输入文件不存在")
            return
            
        detected_format = format_converter.detect_format(input_path)
        if detected_format:
            self.input_format_combo.setCurrentText(detected_format)
            self.log_text.append(f"检测到格式: {detected_format}")
        else:
            QMessageBox.information(self, "信息", "无法自动检测格式，请手动选择")
            
    def start_conversion(self):
        """开始转换"""
        # 验证输入
        input_path = self.input_path_edit.text().strip()
        output_path = self.output_path_edit.text().strip()
        
        if not input_path or not output_path:
            QMessageBox.warning(self, "警告", "请选择输入和输出路径")
            return
            
        if not os.path.exists(input_path):
            QMessageBox.warning(self, "警告", "输入路径不存在")
            return
            
        input_format = self.input_format_combo.currentText()
        output_format = self.output_format_combo.currentText()
        
        if input_format == output_format:
            QMessageBox.warning(self, "警告", "输入和输出格式相同，无需转换")
            return
            
        # 获取参数
        image_width = self.width_spinbox.value()
        image_height = self.height_spinbox.value()
        classes_file = self.classes_path_edit.text().strip() if self.use_classes_checkbox.isChecked() else None
        is_directory = self.mode_combo.currentText() == "批量目录转换"
        
        # 开始转换
        self.convert_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        
        self.worker = ConvertWorker(
            input_path, output_path, input_format, output_format,
            image_width, image_height, classes_file, is_directory
        )
        
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
        
    def on_progress(self, message):
        """进度更新"""
        self.log_text.append(message)
        
    def on_finished(self, success, message):
        """转换完成"""
        self.convert_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            QMessageBox.information(self, "成功", message)
            self.log_text.append(f"✅ {message}")
        else:
            QMessageBox.critical(self, "失败", message)
            self.log_text.append(f"❌ {message}") 