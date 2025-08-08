import pandas as pd
import os
import cv2
import numpy as np
from pathlib import Path
from utils.logging_utils import tee_stdout_stderr
_LOG_FILE = tee_stdout_stderr('logs')
import SimpleITK as sitk
from tqdm import tqdm
import argparse

def read_mha_image(file_path):
    """读取MHA格式图像"""
    try:
        # 使用SimpleITK读取MHA文件
        image = sitk.ReadImage(file_path)
        # 转换为numpy数组
        image_array = sitk.GetArrayFromImage(image)
        
        # 如果是3D图像，取第一个切片
        if len(image_array.shape) == 3:
            image_array = image_array[0]
        
        # 归一化到0-255
        image_array = ((image_array - image_array.min()) / (image_array.max() - image_array.min()) * 255).astype(np.uint8)
        
        return image_array
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def convert_bbox_to_yolo(x, y, width, height, img_width, img_height):
    """将边界框坐标转换为YOLO格式（归一化的中心点坐标和宽高）"""
    # 计算中心点坐标
    center_x = x + width / 2
    center_y = y + height / 2
    
    # 归一化
    center_x_norm = center_x / img_width
    center_y_norm = center_y / img_height
    width_norm = width / img_width
    height_norm = height / img_height
    
    # 确保坐标在有效范围内
    center_x_norm = max(0, min(1, center_x_norm))
    center_y_norm = max(0, min(1, center_y_norm))
    width_norm = max(0, min(1, width_norm))
    height_norm = max(0, min(1, height_norm))
    
    return center_x_norm, center_y_norm, width_norm, height_norm

def convert_medical_to_yolo(input_dir, output_dir, metadata_file):
    """
    将医学图像数据集转换为YOLO格式
    
    Args:
        input_dir: 输入图像目录
        output_dir: 输出目录
        metadata_file: 元数据CSV文件路径
    """
    # 创建输出目录结构
    output_dir = Path(output_dir)
    images_dir = output_dir / "images"
    labels_dir = output_dir / "labels"
    
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    
    # 读取元数据
    print("读取元数据...")
    metadata = pd.read_csv(metadata_file)
    
    print(f"数据集统计:")
    print(f"总记录数: {len(metadata)}")
    print(f"唯一图像数: {metadata['img_name'].nunique()}")
    print(f"标签分布: {metadata['label'].value_counts()}")
    
    # 获取所有唯一的图像名称
    unique_images = metadata['img_name'].unique()
    
    # 分离有结节和无结节的图像
    images_with_nodules = metadata[metadata['label'] == 1]['img_name'].unique()
    images_without_nodules = set(unique_images) - set(images_with_nodules)
    
    print(f"\n数据分析:")
    print(f"有结节图像: {len(images_with_nodules)} 张")
    print(f"无结节图像: {len(images_without_nodules)} 张")
    
    print(f"\n开始转换 {len(unique_images)} 张图像...")
    
    converted_count = 0
    error_count = 0
    nodule_images_count = 0
    no_nodule_images_count = 0
    
    for img_name in tqdm(unique_images, desc="转换图像"):
        try:
            # 读取MHA图像
            img_path = Path(input_dir) / img_name
            if not img_path.exists():
                print(f"图像文件不存在: {img_path}")
                error_count += 1
                continue
                
            image_array = read_mha_image(str(img_path))
            if image_array is None:
                error_count += 1
                continue
            
            img_height, img_width = image_array.shape
            
            # 保存为JPG格式
            img_output_name = img_name.replace('.mha', '.jpg')
            img_output_path = images_dir / img_output_name
            cv2.imwrite(str(img_output_path), image_array)
            
            # 检查该图像是否有结节（label=1的记录）
            image_records = metadata[metadata['img_name'] == img_name]
            nodule_records = image_records[image_records['label'] == 1]
            
            if len(nodule_records) > 0:
                # 有结节，创建标签文件
                label_output_name = img_name.replace('.mha', '.txt')
                label_output_path = labels_dir / label_output_name
                
                with open(label_output_path, 'w') as f:
                    for _, row in nodule_records.iterrows():
                        # 获取边界框信息
                        x = row['x']
                        y = row['y']
                        width = row['width']
                        height = row['height']
                        
                        # 验证边界框坐标
                        if x < 0 or y < 0 or width <= 0 or height <= 0:
                            print(f"警告: 图像 {img_name} 有无效的边界框坐标: x={x}, y={y}, w={width}, h={height}")
                            continue
                        
                        # 转换为YOLO格式 (class=0 for nodule)
                        center_x, center_y, norm_width, norm_height = convert_bbox_to_yolo(
                            x, y, width, height, img_width, img_height
                        )
                        
                        # 写入标签文件 (只有一个类别: nodule = 0)
                        f.write(f"0 {center_x:.6f} {center_y:.6f} {norm_width:.6f} {norm_height:.6f}\n")
                
                nodule_images_count += 1
            else:
                # 无结节，不创建标签文件
                no_nodule_images_count += 1
            
            converted_count += 1
            
        except Exception as e:
            print(f"处理图像 {img_name} 时出错: {e}")
            error_count += 1
    
    print(f"\n转换完成!")
    print(f"成功转换: {converted_count} 张图像")
    print(f"转换失败: {error_count} 张图像")
    print(f"有结节图像(创建了标签文件): {nodule_images_count} 张")
    print(f"无结节图像(仅转换图像): {no_nodule_images_count} 张")
    
    # 创建数据集配置文件
    create_dataset_yaml(output_dir)

def create_dataset_yaml(output_dir):
    """创建YOLO数据集配置文件"""
    yaml_content = """# YOLO数据集配置文件
# NODE21胸部X光结节检测数据集

# 训练和验证数据路径（相对于此文件的路径）
train: images
val: images

# 类别数量
nc: 1

# 类别名称
names: ['nodule']
"""
    
    yaml_path = output_dir / "dataset.yaml"
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)
    
    print(f"数据集配置文件已创建: {yaml_path}")

def main():
    parser = argparse.ArgumentParser(description="医学图像数据集转YOLO格式")
    parser.add_argument('--input_dir', '-i', required=True, help='输入图像目录')
    parser.add_argument('--output_dir', '-o', required=True, help='输出YOLO数据集目录')
    parser.add_argument('--metadata_file', '-m', required=True, help='元数据CSV文件路径')
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir
    metadata_file = args.metadata_file

    print("医学图像数据集转YOLO格式转换器 (修正版)")
    print("="*60)
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print(f"元数据文件: {metadata_file}")
    print("="*60)

    # 检查输入文件是否存在
    if not os.path.exists(input_dir):
        print(f"错误: 输入目录不存在 - {input_dir}")
        return
    
    if not os.path.exists(metadata_file):
        print(f"错误: 元数据文件不存在 - {metadata_file}")
        return
    
    # 开始转换
    convert_medical_to_yolo(input_dir, output_dir, metadata_file)
    
    print("\n转换完成! ")


if __name__ == "__main__":
    main()
