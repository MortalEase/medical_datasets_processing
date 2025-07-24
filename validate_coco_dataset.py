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
    
    dataset_path = Path(dataset_path)
    
    # 检查两种可能的数据集结构
    # 结构1: 新格式 - train/val/test 子目录，每个包含 images/ 和 annotations.json
    # 结构2: 传统格式 - annotations/ 目录包含多个JSON文件
    
    # 先检查新格式
    splits = ['train', 'val', 'test']
    new_format_splits = []
    
    for split in splits:
        split_dir = dataset_path / split
        if split_dir.exists():
            annotation_file = split_dir / 'annotations.json'
            images_dir = split_dir / 'images'
            if annotation_file.exists() and images_dir.exists():
                new_format_splits.append(split)
    
    if new_format_splits:
        print(f"✅ 检测到新格式COCO数据集，找到{len(new_format_splits)}个数据划分")
        return validate_coco_new_format(dataset_path, new_format_splits)
    
    # 检查传统格式
    annotations_dir = dataset_path / 'annotations'
    if annotations_dir.exists():
        json_files = list(annotations_dir.glob('*.json'))
        if json_files:
            print(f"✅ 检测到传统格式COCO数据集，找到{len(json_files)}个标注文件")
            return validate_coco_traditional_format(dataset_path, json_files)
    
    print(f"❌ 未找到有效的COCO数据集结构")
    print(f"期望结构1 (新格式):")
    print(f"  {dataset_path}/train/annotations.json")
    print(f"  {dataset_path}/train/images/")
    print(f"期望结构2 (传统格式):")
    print(f"  {dataset_path}/annotations/*.json")
    return False


def validate_coco_new_format(dataset_path, splits):
    """验证新格式COCO数据集 (train/val/test结构)"""
    
    total_images = 0
    total_annotations = 0
    all_categories = set()
    
    for split in splits:
        split_dir = dataset_path / split
        annotation_file = split_dir / 'annotations.json'
        images_dir = split_dir / 'images'
        
        print(f"\n📋 验证数据划分: {split}")
        
        try:
            with open(annotation_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ 读取标注文件失败: {e}")
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
        
        # 验证图像目录
        if images_dir.exists():
            print(f"  ✅ 找到对应图像目录: {images_dir.name}")
            
            # 统计图像文件
            image_files = list(images_dir.glob('*.png')) + \
                         list(images_dir.glob('*.jpg')) + \
                         list(images_dir.glob('*.jpeg'))
            
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
            print(f"  ❌ 未找到对应图像目录: {images_dir}")
        
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
    
    # 检查额外文件
    print(f"\n📄 检查额外文件:")
    classes_file = dataset_path / 'classes.txt'
    info_file = dataset_path / 'dataset_info.json'
    
    if classes_file.exists():
        print(f"  ✅ 找到类别文件: classes.txt")
        try:
            with open(classes_file, 'r', encoding='utf-8') as f:
                class_names = [line.strip() for line in f if line.strip()]
            print(f"    包含 {len(class_names)} 个类别: {', '.join(class_names)}")
        except Exception as e:
            print(f"    ⚠️ 读取失败: {e}")
    else:
        print(f"  ⚠️ 未找到类别文件: classes.txt")
    
    if info_file.exists():
        print(f"  ✅ 找到数据集信息文件: dataset_info.json")
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                info_data = json.load(f)
            print(f"    数据集名称: {info_data.get('name', '未知')}")
            print(f"    描述: {info_data.get('description', '无')}")
        except Exception as e:
            print(f"    ⚠️ 读取失败: {e}")
    else:
        print(f"  ⚠️ 未找到数据集信息文件: dataset_info.json")
    
    # 总体统计
    print_summary(total_images, total_annotations, all_categories)
    return True


def validate_coco_traditional_format(dataset_path, json_files):
    """验证传统格式COCO数据集 (annotations目录结构)"""
    
    total_images = 0
    total_annotations = 0
    all_categories = set()
    
    for json_file in json_files:
        print(f"\n📋 验证标注文件: {json_file.name}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
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
        
        img_dir_path = dataset_path / img_dir_name
        
        if img_dir_path.exists():
            print(f"  ✅ 找到对应图像目录: {img_dir_name}")
            
            # 统计图像文件
            image_files = list(img_dir_path.glob('*.png')) + \
                         list(img_dir_path.glob('*.jpg')) + \
                         list(img_dir_path.glob('*.jpeg'))
            
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
    print_summary(total_images, total_annotations, all_categories)
    return True


def print_summary(total_images, total_annotations, all_categories):
    """打印总体统计信息"""
    print(f"\n{'='*60}")
    print(f"📋 总体统计:")
    print(f"  总图像数: {total_images}")
    print(f"  总标注数: {total_annotations}")
    print(f"  所有类别: {len(all_categories)}")
    for cat in sorted(all_categories):
        print(f"    {cat}")
    print(f"{'='*60}")

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
