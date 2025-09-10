# Personal Tools 个人工具集

这是一个包含多个实用工具的Python工具集，主要用于图像处理、数据转换和POI数据标准化等任务。

## 工具列表

### 1. DJI热成像图像转换工具 (DJI_thermal_img_convert-main.py)

**功能描述：**
将DJI无人机拍摄的热成像图像（JPG格式）转换为TIFF格式，并提取温度数据。

**主要特性：**
- 支持批量处理JPG/PNG格式的热成像图像
- 使用DJI官方SDK进行温度数据提取
- 支持自定义测量参数（距离、湿度、发射率、反射温度）
- 自动处理EXIF数据，保留GPS信息
- 支持Windows和Linux系统

**使用方法：**
```python
from DJI_thermal_img_convert_main import run

# 基本用法
run(input_dir="输入文件夹路径", output_dir="输出文件夹路径")

# 带参数用法
run(
    input_dir="输入文件夹路径", 
    output_dir="输出文件夹路径",
    distance=25,        # 测温距离(米)
    humidity=40,        # 相对湿度(%)
    emissivity=0.95,    # 发射率
    reflection=43       # 反射温度(℃)
)
```

**参数说明：**
- `distance`: 测温距离，影响测温精度，建议根据实际拍摄高度设置
- `humidity`: 相对湿度，范围20-100%，默认70%
- `emissivity`: 发射率，不同材质有不同的发射率值
- `reflection`: 反射温度，通常设置为环境温度

**依赖库：**
- PIL (Pillow)
- piexif
- numpy
- tqdm

**注意事项：**
- 需要DJI热成像SDK (`dji_thermal_sdk_v1.4_20220929`)
- 输入文件名不能包含空格等特殊字符
- 支持的文件格式：JPG, PNG

---

### 2. POI类型映射工具 (poi_type_mapper_0908.py)

**功能描述：**
根据电子地图数据规范样式表，将POI（兴趣点）数据的类型列内容映射到标准代码，实现数据标准化。

**主要特性：**
- 支持批量处理CSV格式的POI数据文件
- 智能模糊匹配，支持多种匹配策略
- 自动处理分层级类型字符串（用分号分隔）
- 支持多种编码格式（UTF-8, GB18030, GBK等）
- 提供详细的映射统计信息

**使用方法：**
```python
from poi_type_mapper_0908 import POITypeMapper

# 创建映射器
mapper = POITypeMapper("映射文件路径.csv")

# 处理单个文件
mapper.process_poi_file("输入文件.csv", "输出文件.csv")

# 批量处理文件夹
mapper.process_all_poi_files("输入文件夹", "输出文件夹")
```

**配置说明：**
在脚本中修改以下路径配置：
```python
BASE_DIR = r"E:\demo\数据更改"
POI_FOLDER = os.path.join(BASE_DIR, "333（SJZSJ 333-2025）全国 POI 兴趣点数据分享")
MAPPING_CSV = os.path.join(BASE_DIR, "电子地图样式表0908.csv")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "POI_标准化数据_0908")
```

**输出结果：**
- `std_code`: 标准代码
- `std_name_en`: 标准英文名称
- `std_name_zh`: 标准中文名称
- `match_score`: 匹配度分数

**依赖库：**
- pandas
- difflib
- csv

---

### 3. TIFF转PNG工具 (Tiff2PngKeep6000.py)

**功能描述：**
将TIFF格式图像转换为PNG格式，并进行优化处理，支持大尺寸图像处理。

**主要特性：**
- 支持单文件和批量文件夹处理
- 自动尺寸优化，最大尺寸限制为6000x6000像素
- 透明度处理，自动转换为白色背景
- PNG优化压缩，减小文件大小
- 元数据清理，保护隐私
- 内存优化，支持超大图像处理

**使用方法：**
```python
from Tiff2PngKeep6000 import convert_tiff_to_png

# 转换单个文件
convert_tiff_to_png(
    input_path="输入文件.tiff",
    output_dir="输出文件夹",
    optimize=True,          # 启用PNG优化
    reduce_colors=False,    # 保持真彩色
    max_width=8000,         # 最大宽度限制
    remove_metadata=True    # 移除元数据
)

# 批量转换文件夹
convert_tiff_to_png(
    input_path="输入文件夹路径",
    output_dir="输出文件夹路径",
    optimize=True,
    reduce_colors=False,
    max_width=None,         # 不限制宽度
    remove_metadata=True
)
```

**参数说明：**
- `optimize`: 是否进行PNG优化（减小文件大小）
- `reduce_colors`: 是否减少颜色深度到256色
- `max_width`: 最大宽度限制，None表示不限制
- `remove_metadata`: 是否移除图像元数据

**依赖库：**
- PIL (Pillow)

**注意事项：**
- 自动处理透明度，转换为白色背景
- 大图像会自动分块处理，避免内存溢出
- 支持的文件格式：TIF, TIFF

---

## 安装依赖

```bash
pip install pillow piexif numpy tqdm pandas
```

## 系统要求

- Python 3.6+
- Windows 10+ 或 Linux
- 足够的内存处理大尺寸图像

## 注意事项

1. **DJI热成像工具**需要DJI官方SDK支持
2. **POI映射工具**需要准备标准化的映射表文件
3. **TIFF转PNG工具**会自动限制图像尺寸，避免处理过大的文件
4. 所有工具都支持中文路径，但建议避免使用特殊字符

## 作者信息

- 作者：Fu Weishun
- 邮箱：fuweishun2022@163.com

## 许可证

本项目仅供学习和个人使用。

---

*最后更新：2025年1月*
