#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""COCO 数据集分层划分脚本

输入: COCO 单一 annotations.json + images/ 目录
输出: train/val(/test)/annotations.json + 对应 images 软/硬拷贝
特性: 类别分层随机划分、比例与随机种子控制、类别统计输出
"""

import os
import json
import shutil
import random
import argparse
from utils.logging_utils import tee_stdout_stderr, log_info, log_warn, log_error
_LOG_FILE = tee_stdout_stderr('logs')

import os
import json
import shutil
import random
import argparse
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np


def get_image_extensions():
    """返回支持的图片格式扩展名"""
    return ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp']


def load_coco_annotations(annotation_file):
    """
    加载COCO格式标注文件
    
    Args:
        annotation_file (str): COCO标注文件路径
        
    Returns:
        dict: COCO格式数据
    """
    with open(annotation_file, 'r', encoding='utf-8') as f:
        coco_data = json.load(f)
    return coco_data


def analyze_dataset_distribution(coco_data):
    """
    分析数据集的类别分布
    
    Args:
        coco_data (dict): COCO格式数据
        
    Returns:
        dict: 分析结果
    """
    # 统计每个图像包含的类别
    image_to_categories = defaultdict(set)
    category_to_images = defaultdict(set)
    
    for annotation in coco_data['annotations']:
        image_id = annotation['image_id']
        category_id = annotation['category_id']
        
        image_to_categories[image_id].add(category_id)
        category_to_images[category_id].add(image_id)
    
    # 统计类别分布
    category_counts = Counter()
    for annotation in coco_data['annotations']:
        category_counts[annotation['category_id']] += 1
    
    return {
        'image_to_categories': dict(image_to_categories),
        'category_to_images': dict(category_to_images),
        'category_counts': category_counts,
        'total_images': len(coco_data['images']),
        'total_annotations': len(coco_data['annotations'])
    }


def stratified_split_images(coco_data, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1, random_state=42):
    """
    按类别分层划分图像，确保各类别在各数据集中的分布均衡
    
    Args:
        coco_data (dict): COCO格式数据
        train_ratio (float): 训练集比例
        val_ratio (float): 验证集比例  
        test_ratio (float): 测试集比例
        random_state (int): 随机种子
        
    Returns:
        dict: 划分结果 {'train': [], 'val': [], 'test': []}
    """
    random.seed(random_state)
    np.random.seed(random_state)
    
    # 分析数据集分布
    analysis = analyze_dataset_distribution(coco_data)
    image_to_categories = analysis['image_to_categories']
    category_to_images = analysis['category_to_images']
    
    # 获取所有图像ID
    all_image_ids = [img['id'] for img in coco_data['images']]
    
    # 如果没有标注，简单随机划分
    if not coco_data['annotations']:
        log_warn("数据集中没有标注，将进行简单随机划分")
        random.shuffle(all_image_ids)
        
        train_count = int(len(all_image_ids) * train_ratio)
        val_count = int(len(all_image_ids) * val_ratio)
        
        return {
            'train': all_image_ids[:train_count],
            'val': all_image_ids[train_count:train_count + val_count],
            'test': all_image_ids[train_count + val_count:]
        }
    
    # 有标注的情况下，进行分层划分
    assigned_images = set()
    train_images, val_images, test_images = [], [], []
    
    # 按类别频率排序，优先处理样本较少的类别
    sorted_categories = sorted(category_to_images.keys(), 
                             key=lambda x: len(category_to_images[x]))
    
    for category_id in sorted_categories:
        category_images = list(category_to_images[category_id])
        # 移除已分配的图像
        category_images = [img_id for img_id in category_images if img_id not in assigned_images]
        
        if not category_images:
            continue
            
        random.shuffle(category_images)
        
        # 计算该类别的划分数量
        total = len(category_images)
        train_count = max(1, int(total * train_ratio))
        val_count = max(0, int(total * val_ratio)) if total > 1 else 0
        test_count = total - train_count - val_count
        
        # 分配图像
        train_images.extend(category_images[:train_count])
        val_images.extend(category_images[train_count:train_count + val_count])
        test_images.extend(category_images[train_count + val_count:train_count + val_count + test_count])
        
        # 标记为已分配
        assigned_images.update(category_images)
    
    # 处理没有标注的图像（背景图像）
    unassigned_images = [img_id for img_id in all_image_ids if img_id not in assigned_images]
    if unassigned_images:
        log_info(f"发现 {len(unassigned_images)} 张无标注图像，进行随机分配")
        random.shuffle(unassigned_images)
        
        bg_train_count = int(len(unassigned_images) * train_ratio)
        bg_val_count = int(len(unassigned_images) * val_ratio)
        
        train_images.extend(unassigned_images[:bg_train_count])
        val_images.extend(unassigned_images[bg_train_count:bg_train_count + bg_val_count])
        test_images.extend(unassigned_images[bg_train_count + bg_val_count:])
    
    return {
        'train': train_images,
        'val': val_images,
        'test': test_images
    }


def create_split_coco_data(coco_data, image_ids, split_name):
    """
    根据图像ID列表创建对应的COCO数据子集
    
    Args:
        coco_data (dict): 原始COCO数据
        image_ids (list): 图像ID列表
        split_name (str): 数据集划分名称
        
    Returns:
        dict: 划分后的COCO数据
    """
    image_ids_set = set(image_ids)
    
    # 过滤图像
    split_images = [img for img in coco_data['images'] if img['id'] in image_ids_set]
    
    # 过滤标注
    split_annotations = [ann for ann in coco_data['annotations'] if ann['image_id'] in image_ids_set]
    
    # 重新分配ID（可选，保持原ID也可以）
    # 这里保持原ID以便于追踪
    
    # 创建新的COCO数据结构
    split_coco_data = {
        'info': coco_data.get('info', {}),
        'licenses': coco_data.get('licenses', []),
        'categories': coco_data['categories'],
        'images': split_images,
        'annotations': split_annotations
    }
    
    # 更新info中的描述
    if 'info' in split_coco_data:
        split_coco_data['info']['description'] = f"{split_coco_data['info'].get('description', '')} - {split_name} split"
    
    return split_coco_data


def copy_images(image_list, src_images_dir, dst_images_dir):
    """
    复制图像文件到目标目录
    
    Args:
        image_list (list): 图像信息列表
        src_images_dir (str): 源图像目录
        dst_images_dir (str): 目标图像目录
    """
    os.makedirs(dst_images_dir, exist_ok=True)
    
    copied_count = 0
    for image_info in image_list:
        src_path = os.path.join(src_images_dir, image_info['file_name'])
        dst_path = os.path.join(dst_images_dir, image_info['file_name'])
        
        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)
            copied_count += 1
        else:
            log_warn(f"图像文件不存在: {src_path}")
    
    log_info(f"复制了 {copied_count}/{len(image_list)} 张图像")


def print_split_statistics(splits, coco_data):
    """
    打印划分统计信息
    
    Args:
        splits (dict): 划分结果
        coco_data (dict): 原始COCO数据
    """
    analysis = analyze_dataset_distribution(coco_data)
    
    log_info("\n=== 数据集划分统计 ===")
    log_info(f"原始数据集:")
    log_info(f"  - 总图像数: {analysis['total_images']}")
    log_info(f"  - 总标注数: {analysis['total_annotations']}")
    log_info(f"  - 类别数: {len(coco_data['categories'])}")
    
    for split_name, image_ids in splits.items():
        split_annotations = [ann for ann in coco_data['annotations'] 
                           if ann['image_id'] in image_ids]

        # 统计类别分布
        category_counts = Counter(ann['category_id'] for ann in split_annotations)

        log_info(f"\n{split_name.upper()}集:")
        log_info(f"  - 图像数: {len(image_ids)} ({len(image_ids)/analysis['total_images']*100:.1f}%)")
        log_info(f"  - 标注数: {len(split_annotations)}")

        if category_counts:
            log_info(f"  - 类别分布:")
            for cat in coco_data['categories']:
                count = category_counts.get(cat['id'], 0)
                log_info(f"    * {cat['name']}: {count}")


def split_coco_dataset(input_dir, output_dir, split_ratios, random_state=42):
    """
    划分COCO格式数据集
    
    Args:
        input_dir (str): 输入数据集目录（包含images文件夹和annotations.json）
        output_dir (str): 输出数据集目录
        split_ratios (dict): 划分比例
        random_state (int): 随机种子
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # 检查输入目录结构
    images_dir = input_path / 'images'
    annotation_file = input_path / 'annotations.json'
    
    if not images_dir.exists():
        raise FileNotFoundError(f"图像目录不存在: {images_dir}")
    
    if not annotation_file.exists():
        raise FileNotFoundError(f"标注文件不存在: {annotation_file}")
    
    log_info(f"加载COCO标注文件: {annotation_file}")
    coco_data = load_coco_annotations(annotation_file)
    
    log_info(f"原始数据集包含:")
    log_info(f"  - 图像数: {len(coco_data['images'])}")
    log_info(f"  - 标注数: {len(coco_data['annotations'])}")
    log_info(f"  - 类别数: {len(coco_data['categories'])}")
    
    # 执行划分
    log_info("\n开始执行数据集划分...")
    splits = stratified_split_images(
        coco_data, 
        train_ratio=split_ratios['train'],
        val_ratio=split_ratios['val'],
        test_ratio=split_ratios['test'],
        random_state=random_state
    )
    
    # 打印统计信息
    print_split_statistics(splits, coco_data)
    
    # 创建输出目录并复制文件
    log_info(f"\n创建输出目录: {output_path}")
    output_path.mkdir(parents=True, exist_ok=True)
    
    for split_name, image_ids in splits.items():
        if not image_ids:
            log_warn(f"{split_name}集为空，跳过")
            continue

        log_info(f"\n处理 {split_name} 数据集...")

        # 创建划分目录
        split_dir = output_path / split_name
        split_images_dir = split_dir / 'images'
        split_dir.mkdir(exist_ok=True)

        # 创建划分后的COCO数据
        split_coco_data = create_split_coco_data(coco_data, image_ids, split_name)

        # 保存标注文件
        split_annotation_file = split_dir / 'annotations.json'
        with open(split_annotation_file, 'w', encoding='utf-8') as f:
            json.dump(split_coco_data, f, indent=2, ensure_ascii=False)

        # 复制图像文件
        copy_images(split_coco_data['images'], str(images_dir), str(split_images_dir))

        log_info(f"{split_name} 数据集处理完成")
    
    # 复制额外文件
    for extra_file in ['classes.txt', 'dataset_info.json']:
        src_file = input_path / extra_file
        if src_file.exists():
            dst_file = output_path / extra_file
            shutil.copy2(src_file, dst_file)
            log_info(f"复制额外文件: {extra_file}")
    
    log_info(f"\n数据集划分完成!")
    log_info(f"输出目录: {output_path}")
    
    # 显示最终目录结构
    log_info("\n最终目录结构:")
    log_info(f"{output_path.name}/")
    for split_name in ['train', 'val', 'test']:
        split_dir = output_path / split_name
        if split_dir.exists():
            image_count = len(list((split_dir / 'images').glob('*'))) if (split_dir / 'images').exists() else 0
            log_info(f"├── {split_name}/")
            log_info(f"│   ├── images/ ({image_count} 张图像)")
            log_info(f"│   └── annotations.json")
    
    # 列出额外文件
    extra_files = [f.name for f in output_path.glob('*.txt') if f.is_file()] + \
                  [f.name for f in output_path.glob('*.json') if f.is_file() and f.name not in ['train', 'val', 'test']]
    
    if extra_files:
        for i, filename in enumerate(extra_files):
            prefix = "└──" if i == len(extra_files) - 1 else "├──"
            log_info(f"{prefix} {filename}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="COCO格式数据集划分工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python coco_dataset_split.py -i RibFrac-COCO-Full -o RibFrac-COCO-Split
  
  python coco_dataset_split.py -i RibFrac-COCO-Full -o RibFrac-COCO-Split \\
                               --train_ratio 0.8 --val_ratio 0.1 --test_ratio 0.1

输入目录结构:
  RibFrac-COCO-Full/
  ├── images/           # 所有图像文件
  ├── annotations.json  # COCO格式标注文件
  ├── classes.txt       # 类别文件（可选）
  └── dataset_info.json # 数据集信息（可选）

输出目录结构:
  RibFrac-COCO-Split/
  ├── train/
  │   ├── images/
  │   └── annotations.json
  ├── val/
  │   ├── images/
  │   └── annotations.json
  ├── test/
  │   ├── images/
  │   └── annotations.json
  ├── classes.txt
  └── dataset_info.json
        """
    )
    
    parser.add_argument('-i', '--input_dir', required=True,
                        help='输入COCO数据集目录（包含images和annotations.json）')
    parser.add_argument('-o', '--output_dir', required=True,
                        help='输出划分后数据集目录')
    parser.add_argument('--train_ratio', type=float, default=0.8,
                        help='训练集比例 (默认: 0.8)')
    parser.add_argument('--val_ratio', type=float, default=0.1,
                        help='验证集比例 (默认: 0.1)')
    parser.add_argument('--test_ratio', type=float, default=0.1,
                        help='测试集比例 (默认: 0.1)')
    parser.add_argument('--seed', type=int, default=42,
                        help='随机种子 (默认: 42)')
    
    args = parser.parse_args()
    
    # 验证比例总和
    total_ratio = args.train_ratio + args.val_ratio + args.test_ratio
    if abs(total_ratio - 1.0) > 1e-6:
        log_error(f"错误: 训练、验证、测试集比例总和应为1.0，当前为{total_ratio}")
        return
    
    # 验证输入目录
    if not os.path.exists(args.input_dir):
        log_error(f"错误: 输入目录 {args.input_dir} 不存在")
        return
    
    # 构建比例字典
    split_ratios = {
        'train': args.train_ratio,
        'val': args.val_ratio,
        'test': args.test_ratio
    }
    
    log_info(f"=== COCO数据集划分工具 ===")
    log_info(f"输入目录: {args.input_dir}")
    log_info(f"输出目录: {args.output_dir}")
    log_info(f"训练集比例: {args.train_ratio}")
    log_info(f"验证集比例: {args.val_ratio}")
    log_info(f"测试集比例: {args.test_ratio}")
    log_info(f"随机种子: {args.seed}")
    log_info("-" * 50)
    
    try:
        # 执行数据集划分
        split_coco_dataset(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            split_ratios=split_ratios,
            random_state=args.seed
        )
        
    except Exception as e:
        log_error(f"划分过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
