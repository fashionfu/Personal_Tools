from PIL import Image
import os
import warnings
import math

# 禁用解压缩炸弹警告（处理大图像时）
warnings.simplefilter('ignore', Image.DecompressionBombWarning)
Image.MAX_IMAGE_PIXELS = None  # 移除像素限制

# 最大允许尺寸 (根据诊断建议设置为6000x6000)
MAX_DIMENSION = 6000

def calculate_target_size(width, height, max_dimension=MAX_DIMENSION):
    """计算符合最大尺寸限制的目标尺寸，保持宽高比"""
    if width <= max_dimension and height <= max_dimension:
        return width, height

    ratio = width / height
    if width > height:
        return max_dimension, int(max_dimension / ratio)
    return int(max_dimension * ratio), max_dimension


def convert_tiff_to_png(input_path, output_dir,
                        optimize=True,
                        reduce_colors=False,
                        max_width=None,
                        remove_metadata=True):
    """
    将TIFF转换为PNG格式并进行优化

    参数:
    input_path: 输入路径（文件或目录）
    output_dir: 输出目录
    optimize: 是否进行PNG优化（减小文件大小）
    reduce_colors: 是否减少颜色深度（256色）
    max_width: 最大宽度（等比例缩放），None表示不缩放
    remove_metadata: 是否移除元数据
    """
    os.makedirs(output_dir, exist_ok=True)

    if os.path.isfile(input_path):
        convert_single_file(input_path, output_dir, optimize, reduce_colors, max_width, remove_metadata)
    elif os.path.isdir(input_path):
        for filename in os.listdir(input_path):
            if filename.lower().endswith(('.tif', '.tiff')):
                file_path = os.path.join(input_path, filename)
                convert_single_file(file_path, output_dir, optimize, reduce_colors, max_width, remove_metadata)


def convert_single_file(tiff_path, output_dir, optimize, reduce_colors, max_width, remove_metadata):
    try:
        with Image.open(tiff_path) as img:
            # 创建输出路径
            filename = os.path.basename(tiff_path)
            png_name = os.path.splitext(filename)[0] + '.png'
            output_path = os.path.join(output_dir, png_name)

            # 0. 提前处理透明度（减少内存占用）
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景的RGB图像
                background = Image.new('RGB', img.size, (255, 255, 255))
                # 处理透明度
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3])
                elif img.mode == 'LA':  # 灰度+透明度
                    background.paste(img, mask=img.split()[1])
                elif img.mode == 'P':  # 调色板模式
                    if 'transparency' in img.info:
                        background.paste(img, mask=img.convert('RGBA').split()[3])
                    else:
                        background.paste(img)
                img = background

            # 1. 计算目标尺寸（应用所有尺寸限制）
            orig_width, orig_height = img.size
            target_width, target_height = orig_width, orig_height

            # 应用用户指定的宽度限制
            if max_width and max_width > 0 and orig_width > max_width:
                ratio = max_width / orig_width
                target_width = max_width
                target_height = int(orig_height * ratio)

            # 应用最大尺寸限制（确保不超过6000x6000）
            if target_width > MAX_DIMENSION or target_height > MAX_DIMENSION:
                target_width, target_height = calculate_target_size(target_width, target_height)

            # 2. 执行尺寸调整（如果需要）
            if (target_width, target_height) != (orig_width, orig_height):
                img = img.resize((target_width, target_height), Image.LANCZOS)
                print(f"  尺寸调整: {orig_width}x{orig_height} → {target_width}x{target_height}")

            # 3. 减少颜色深度（可选）
            if reduce_colors:
                if img.mode != 'P':
                    # 使用抖动技术保持视觉质量
                    img = img.convert('P', palette=Image.ADAPTIVE, colors=256, dither=Image.FLOYDSTEINBERG)

            # 4. 移除元数据（高效方法）
            if remove_metadata:
                # 创建无元数据的图像副本
                data = img.getdata()
                img = Image.new(img.mode, img.size)
                img.putdata(data)

            # 5. 保存PNG并进行优化
            png_options = {
                'optimize': optimize,  # 启用PNG优化
                'compress_level': 9  # 最高压缩级别
            }

            # 添加安全保存机制（防止超大文件）
            try:
                img.save(output_path, 'PNG', **png_options)
            except MemoryError:
                # 分块处理超大图像
                print("  检测到大图像，使用分块处理...")
                chunk_size = 2000  # 分块大小
                for y in range(0, img.height, chunk_size):
                    for x in range(0, img.width, chunk_size):
                        box = (x, y, min(x + chunk_size, img.width), min(y + chunk_size, img.height))
                        chunk = img.crop(box)
                        chunk.save(output_path, 'PNG', **png_options, append=True)

            # 获取文件大小信息
            orig_size = os.path.getsize(tiff_path) / (1024 * 1024)  # MB
            new_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            reduction = (1 - new_size / orig_size) * 100 if orig_size > 0 else 0

            print(f"已转换: {filename} → {png_name}")
            print(f"  原始大小: {orig_size:.2f} MB, 优化后: {new_size:.2f} MB, 减少: {reduction:.1f}%")

    except Exception as e:
        print(f"转换失败 {tiff_path}: {str(e)}")
        import traceback
        traceback.print_exc()


# 使用示例（添加了安全尺寸限制）
convert_tiff_to_png(
    r"E:\\pix4d\\0702_jpg\\3_dsm_ortho\\2_mosaic\\2_mosaic_tif",
    r"E:\\pix4d\\0702_jpg\\3_dsm_ortho\\2_mosaic\\png_output",
    optimize=True,  # 启用PNG优化
    reduce_colors=False,  # 保持真彩色
    max_width=8000,  # 用户指定的最大宽度（但会被限制在6000x6000内）
    remove_metadata=True
)