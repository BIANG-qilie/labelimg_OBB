# LabelImg OBB (Oriented Bounding Box)

一个用于创建和标注旋转边界框(OBB)的图形化标注工具。本项目基于 [labelImg_OBB](https://github.com/heshameraqi/labelImg_OBB) 修改，增加了快捷键操作和中文支持。

## 功能特点

- 支持旋转边界框(OBB)标注
- 支持多语言界面(英语、简体中文、繁体中文)
- 丰富的快捷键操作
- 实时显示边界框面积和角度
- 支持标注历史记录(最多100步)
- 支持YOLO OBB格式导出
- **🆕 集成多格式转换器** - 支持DOTA、LabelImg-OBB等多种格式互转
- **🆕 批量格式转换** - 支持整个目录的批量格式转换
- **🆕 智能格式检测** - 自动识别标注文件格式

## 安装说明

### 环境安装
1. 使用 conda 创建环境:
```bash
conda env create -f requirement/labelimgOBB.yml
```

2. 激活环境:
```bash
conda activate labelimgOBB
```

3. 安装格式转换依赖 (可选):
```bash
pip install dataset-format-converter
```

4. 启动程序:
```bash
python labelImg.py
```

5. 测试格式转换功能:
```bash
python test_format_converter.py
```

## 快捷键说明

### 基本操作
- `W` - 创建新的旋转边界框
- `Ctrl+J` - 切换编辑模式
- `Ctrl+Z` - 撤销上一步操作
- 方向键 - 移动选中的边界框

### 旋转操作
- `O` - 顺时针旋转 0.1 度
- `P` - 逆时针旋转 0.1 度
- `K` - 顺时针旋转 1 度
- `L` - 逆时针旋转 1 度
- `M` - 顺时针旋转 5 度
- `,` - 逆时针旋转 5 度

### 图像导航
- `D` - 下一张图片
- `A` - 上一张图片
- `Space` - 验证当前图片

### 视图控制
- `Ctrl++` - 放大
- `Ctrl+-` - 缩小
- `Ctrl+=` - 原始大小
- `Ctrl+F` - 适应窗口
- `Ctrl+Shift+F` - 适应宽度

## 格式转换功能

### 支持的格式

| 格式 | 类型 | 描述 |
|------|------|------|
| YOLO-HBB | 水平框 | 标准YOLO格式 |
| YOLO-OBB | 旋转框 | YOLO旋转边界框格式 |
| PASCAL VOC | 水平框 | XML格式 |
| DOTA | 旋转框 | 多边形旋转框格式 |
| LabelImg-OBB | 旋转框 | 带角度的旋转框格式 |

### 使用方法

1. **图形界面转换**：
   - 在主菜单中选择"工具" → "格式转换器"
   - 选择输入/输出路径和格式
   - 支持单文件和批量转换

2. **API调用**：
```python
from libs.format_converter import format_converter

# 单文件转换
success = format_converter.convert_file(
    input_file='input.txt',
    output_file='output.txt',
    input_format='YOLO_OBB',
    output_format='DOTA',
    image_width=1920,
    image_height=1080
)

# 批量转换
success_count, total_count = format_converter.convert_directory(
    input_dir='./labels',
    output_dir='./converted',
    input_format='YOLO_OBB',
    output_format='DOTA',
    image_width=1920,
    image_height=1080
)
```

## 注意事项

1. 对于小规模数据集，使用1度/3度/5度的旋转标注通常已经足够(可在 `libs/canvas_shortcut.py` 中修改)。
2. 界面直接显示当前边界框的面积和角度，而不是宽度和高度，这有助于创建最小面积的标注框。
3. 标注历史记录最多保存30步，可以通过修改 `libs/canvas.py` 中的 `MAX_HISTORY` 值来调整。
4. 语言设置修改后需要重启程序才能生效。
5. **格式转换功能需要安装 `dataset-format-converter` 库才能使用。**

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 致谢

- [labelImg_OBB](https://github.com/heshameraqi/labelImg_OBB) - 原始项目
- [labelImg](https://github.com/tzutalin/labelImg) - 基础框架
