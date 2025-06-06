#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COCO格式数据集验证脚本
用于验证COCO格式数据集的标签和图像对应关系
"""

import os
import json
import argparse
from pathlib import Path
from collections import Counter

def validate_coco_dataset(dataset_path):
    """验证COCO格式数据集"""
    print(f"验证COCO数据集: {dataset_path}")
    
    # 查找annotations目录
    annotations_dir = os.path.join(dataset_path, 'annotations')
    if not os.path.exists(annotations_dir):
        print(f"❌ 未找到annotations目录: {annotations_dir}")
        return False
    
    # 查找所有JSON标注文件
    json_files = list(Path(annotations_dir).glob('*.json'))
    if not json_files:
        print(f"❌ annotations目录中未找到JSON文件")
        return False
    
    print(f"✅ 找到{len(json_files)}个标注文件")
    
    total_images = 0
    total_annotations = 0
    all_categories = set()
    
    for json_file in json_files:
        print(f"\n📋 验证标注文件: {json_file.name}")
        
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ 读取JSON文件失败: {e}")
            continue
        
        # 基本信息
        images = data.get('images', [])
        annotations = data.get('annotations', [])
        categories = data.get('categories', [])
        
        print(f"  📊 图像数量: {len(images)}")
        print(f"  📊 标注数量: {len(annotations)}")
        print(f"  📊 类别数量: {len(categories)}")
        
        # 累计统计
        total_images += len(images)
        total_annotations += len(annotations)
        
        # 类别信息
        for cat in categories:
            cat_info = f"ID{cat['id']}:{cat['name']}"
            all_categories.add(cat_info)
            print(f"    类别 {cat['id']}: {cat['name']}")
          # 验证对应的图像目录
        # 推断图像目录名 (去掉instances_前缀和.json后缀)
        img_dir_name = json_file.stem.replace('instances_', '')
        
        # 特殊处理：如果是full，对应full2017目录
        if img_dir_name == 'full':
            img_dir_name = 'full2017'
        
        img_dir_path = os.path.join(dataset_path, img_dir_name)
        
        if os.path.exists(img_dir_path):
            print(f"  ✅ 找到对应图像目录: {img_dir_name}")
            
            # 统计图像文件
            image_files = list(Path(img_dir_path).glob('*.png')) + \
                         list(Path(img_dir_path).glob('*.jpg')) + \
                         list(Path(img_dir_path).glob('*.jpeg'))
            
            print(f"  📁 实际图像文件数: {len(image_files)}")
            
            # 检查图像-标注对应关系
            json_image_names = {img['file_name'] for img in images}
            actual_image_names = {img_file.name for img_file in image_files}
            
            missing_images = json_image_names - actual_image_names
            extra_images = actual_image_names - json_image_names
            
            if missing_images:
                print(f"  ⚠️  标注中有{len(missing_images)}个图像在目录中不存在")
                for img in list(missing_images)[:3]:
                    print(f"    缺失: {img}")
                if len(missing_images) > 3:
                    print(f"    ...还有{len(missing_images)-3}个")
            
            if extra_images:
                print(f"  ⚠️  目录中有{len(extra_images)}个图像未在标注中")
                for img in list(extra_images)[:3]:
                    print(f"    多余: {img}")
                if len(extra_images) > 3:
                    print(f"    ...还有{len(extra_images)-3}个")
            
            if not missing_images and not extra_images:
                print(f"  ✅ 图像-标注完全对应")
        
        else:
            print(f"  ❌ 未找到对应图像目录: {img_dir_name}")
        
        # 标注统计
        if annotations:
            category_counts = Counter(ann['category_id'] for ann in annotations)
            areas = [ann['area'] for ann in annotations if 'area' in ann]
            
            print(f"  📈 标注分布:")
            for cat_id, count in category_counts.items():
                cat_name = next((cat['name'] for cat in categories if cat['id'] == cat_id), f"未知_{cat_id}")
                percentage = count / len(annotations) * 100
                print(f"    类别 {cat_id} ({cat_name}): {count} ({percentage:.1f}%)")
            
            if areas:
                print(f"  📦 边界框面积: 最小{min(areas):.1f}, 最大{max(areas):.1f}, 平均{sum(areas)/len(areas):.1f}")
    
    # 总体统计
    print(f"\n{'='*60}")
    print(f"📋 总体统计:")
    print(f"  总图像数: {total_images}")
    print(f"  总标注数: {total_annotations}")
    print(f"  所有类别: {len(all_categories)}")
    for cat in sorted(all_categories):
        print(f"    {cat}")
    print(f"{'='*60}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="验证COCO格式数据集")
    parser.add_argument("-d", "--dataset", required=True, help="COCO数据集根目录路径")
    
    args = parser.parse_args()
    dataset_path = args.dataset
    
    print("=" * 70)
    print("          COCO格式数据集验证工具")
    print("=" * 70)
    
    validate_coco_dataset(dataset_path)

if __name__ == "__main__":
    main()
