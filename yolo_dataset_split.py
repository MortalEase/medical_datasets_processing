#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YOLO 数据集划分脚本

输入: standard(images/+labels/) 或 mixed(同目录混合) 结构
输出: 可选 format1(train/val/test 子目录) 或 format2(images/train, labels/train)
特性: 支持 2/3 集合比例、随机种子、类别文件复制与统计报告
"""
import os
import shutil
import random
import argparse
from utils.logging_utils import tee_stdout_stderr, log_info, log_warn, log_error
_LOG_FILE = tee_stdout_stderr('logs')
from collections import defaultdict
from utils.yolo_utils import (
    get_image_extensions,
    list_possible_class_files,
    read_class_names,
    discover_class_names,
)


def get_image_extensions_local():
    return get_image_extensions()


def find_corresponding_image(label_file, images_dir, structure='standard'):
    """根据标签文件找到对应的图片文件"""
    base_name = os.path.splitext(label_file)[0]
    image_extensions = get_image_extensions()
    
    if structure == 'mixed':
        # 混合结构：图片和标签在同一目录
        for ext in image_extensions:
            image_file = base_name + ext
            image_path = os.path.join(images_dir, image_file)
            if os.path.exists(image_path):
                return image_file
    else:
        # 标准结构：图片和标签在不同目录
        for ext in image_extensions:
            image_file = base_name + ext
            image_path = os.path.join(images_dir, image_file)
            if os.path.exists(image_path):
                return image_file
    return None


def find_class_files(base_dir):
    return list_possible_class_files(base_dir)


def detect_input_structure(base_dir):
    """检测输入数据集结构类型"""
    # 检查标准结构：dataset/images/ + dataset/labels/
    images_dir = os.path.join(base_dir, "images")
    labels_dir = os.path.join(base_dir, "labels")
    if os.path.exists(images_dir) and os.path.exists(labels_dir):
        return 'standard', images_dir, labels_dir
    
    # 检查混合结构：所有图片和txt文件在同一个文件夹中
    img_exts = get_image_extensions()
    txt_files = []
    img_files = []
    
    try:
        for file in os.listdir(base_dir):
            file_path = os.path.join(base_dir, file)
            if os.path.isfile(file_path):
                if os.path.splitext(file)[1].lower() in img_exts:
                    img_files.append(file)
                elif file.endswith('.txt') and file not in ['classes.txt', 'obj.names', 'names.txt']:
                    txt_files.append(file)
        
        # 如果存在图片文件和txt文件，则认为是混合结构
        if img_files and txt_files:
            return 'mixed', base_dir, base_dir
    except:
        pass
    
    return 'unknown', None, None


def split_dataset(base_dir, output_dir, split_ratios, output_format=1, use_test=True):
    """
    按指定比例划分数据集，确保各类别在训练、验证、测试集中尽可能均衡

    Args:
        base_dir (str): 数据集的根目录，支持标准结构(images/+labels/)或混合结构(图片和txt在同一文件夹)
        output_dir (str): 输出数据集的根目录
        split_ratios (dict): 数据集划分比例，例如 {"train": 0.8, "val": 0.2} 或 {"train": 0.8, "val": 0.1, "test": 0.1}
        output_format (int): 输出格式，1为格式一，2为格式二 (默认: 1)
        use_test (bool): 是否使用测试集，False时只划分为train/val两个集合 (默认: True)
    """
    # 检测输入结构
    structure, images_dir, labels_dir = detect_input_structure(base_dir)
    
    if structure == 'unknown':
        log_error("错误: 未找到有效的数据集结构")
        log_info("支持的输入结构:")
        log_info("  1. 标准结构: dataset/images/ + dataset/labels/")
        log_info("  2. 混合结构: 图片和txt标签文件在同一个文件夹中")
        return
    
    structure_name = {
        'standard': '标准结构 (images/ + labels/)',
        'mixed': '混合结构 (图片和标签在同一文件夹)'
    }.get(structure, '未知结构')
    
    log_info(f"检测到输入结构: {structure_name}")
    
    # 查找类别文件
    class_files = find_class_files(base_dir)
    if class_files:
        log_info(f"找到类别文件: {', '.join(class_files)}")
    
    # 确定要创建的分割集合
    splits = ["train", "val"]
    if use_test:
        splits.append("test")
    
    log_info(f"划分模式: {len(splits)}个集合 ({', '.join(splits)})")

    if output_format == 1:
        # 格式一: yolo/train/images/, yolo/train/labels/, etc.
        # 创建输出目录
        for split in splits:
            split_dir = os.path.join(output_dir, split)
            os.makedirs(os.path.join(split_dir, "images"), exist_ok=True)
            os.makedirs(os.path.join(split_dir, "labels"), exist_ok=True)
    else:
        # 格式二: yolo_dataset/images/train/, yolo_dataset/labels/train/, etc.
        # 创建输出目录
        for data_type in ["images", "labels"]:
            for split in splits:
                os.makedirs(os.path.join(output_dir, data_type, split), exist_ok=True)
    
    # 复制类别文件到输出目录根目录（优先根目录，缺失则尝试 labels/）
    labels_dir_for_copy = None
    if structure == 'standard':
        labels_dir_for_copy = labels_dir
    copied_set = set()
    for class_file in class_files:
        src_class_path = os.path.join(base_dir, class_file)
        dst_class_path = os.path.join(output_dir, class_file)
        if os.path.exists(src_class_path):
            shutil.copy(src_class_path, dst_class_path)
            copied_set.add(class_file)
            log_info(f"复制类别文件: {class_file}")
    # 若根目录未包含但 labels/ 下存在类别文件，则也复制一份到输出根目录
    if labels_dir_for_copy and os.path.isdir(labels_dir_for_copy):
        for candidate in ['classes.txt', 'obj.names', 'names.txt', 'data.yaml', 'data.yml', 'dataset.yaml', 'dataset.yml']:
            if candidate in copied_set:
                continue
            p = os.path.join(labels_dir_for_copy, candidate)
            if os.path.isfile(p):
                shutil.copy(p, os.path.join(output_dir, candidate))
                log_info(f"复制类别文件: {candidate}")

    # 获取所有标签文件
    if structure == 'mixed':
        # 混合结构：排除类别文件
        all_files = os.listdir(labels_dir)
        label_files = [
            f for f in all_files
            if f.endswith(".txt") and f not in ['classes.txt', 'obj.names', 'names.txt']
        ]
    else:
        # 标准结构：labels目录下的所有txt文件
        label_files = [
            f for f in os.listdir(labels_dir)
            if f.endswith(".txt") and f not in ['classes.txt', 'obj.names', 'names.txt']
        ]
        
    # 构建图片-类别映射
    image_to_classes = {}  # {image_file: [class1, class2, ...]}
    class_to_images = defaultdict(list)  # {class: [image_files]}

    for label_file in label_files:
        label_path = os.path.join(labels_dir, label_file)
        with open(label_path, "r") as f:
            lines = f.readlines()
            classes = set(int(line.split()[0]) for line in lines)  # 提取所有类别
            
            # 查找对应的图片文件
            corresponding_image = find_corresponding_image(label_file, images_dir, structure)
            if corresponding_image is None:
                log_warn(f"找不到标签文件 {label_file} 对应的图片文件")
                continue
        image_to_classes[corresponding_image] = classes
        for c in classes:
            class_to_images[c].append(corresponding_image)

    # 获取所有图片文件（包括有标签和无标签的）
    if structure == 'mixed':
        # 混合结构：从同一目录获取图片文件
        all_image_files = [
            f for f in os.listdir(images_dir)
            if os.path.splitext(f)[1].lower() in get_image_extensions()
        ]
    else:
        # 标准结构：从images目录获取图片文件
        all_image_files = [
            f for f in os.listdir(images_dir)
            if os.path.splitext(f)[1].lower() in get_image_extensions()
        ]
    
    # 随机打乱所有图片
    random.shuffle(all_image_files)
    
    # 按比例划分
    total_files = len(all_image_files)
    
    if use_test:
        # 三个集合：train/val/test
        train_count = int(total_files * split_ratios["train"])
        val_count = int(total_files * split_ratios["val"])
        test_count = total_files - train_count - val_count  # 剩余归为测试集
        
        train_files = all_image_files[:train_count]
        val_files = all_image_files[train_count:train_count + val_count]
        test_files = all_image_files[train_count + val_count:]
        
        split_files = {
            "train": train_files,
            "val": val_files,
            "test": test_files
        }
    else:
        # 两个集合：train/val
        train_count = int(total_files * split_ratios["train"])
        val_count = total_files - train_count  # 剩余归为验证集
        
        train_files = all_image_files[:train_count]
        val_files = all_image_files[train_count:]
        
        split_files = {
            "train": train_files,
            "val": val_files
        }

    # 复制文件到对应目录
    def copy_files(file_list, split):
        for image_file in file_list:
            # 图片文件路径
            src_image_path = os.path.join(images_dir, image_file)
            
            # 标签文件路径
            label_file = os.path.splitext(image_file)[0] + ".txt"  # 获取对应的标签文件名
            src_label_path = os.path.join(labels_dir, label_file)
            
            # 对于混合结构，需要检查标签文件是否为类别文件
            if (structure == 'mixed' and 
                label_file in ['classes.txt', 'obj.names', 'names.txt']):
                # 跳过类别文件
                continue
            
            if output_format == 1:
                # 格式一: yolo/train/images/, yolo/train/labels/
                dst_image_path = os.path.join(output_dir, split, "images", image_file)
                dst_label_path = os.path.join(output_dir, split, "labels", label_file)
            else:
                # 格式二: yolo_dataset/images/train/, yolo_dataset/labels/train/
                dst_image_path = os.path.join(output_dir, "images", split, image_file)
                dst_label_path = os.path.join(output_dir, "labels", split, label_file)
            
            if os.path.exists(src_image_path):  # 确保图片存在
                shutil.copy(src_image_path, dst_image_path)
            if os.path.exists(src_label_path):  # 只复制有标签的图片的标签
                shutil.copy(src_label_path, dst_label_path)

    # 复制所有分割的文件
    for split in splits:
        copy_files(split_files[split], split)

    # 统计信息
    total_original = len(all_image_files)
    total_split = sum(len(split_files[split]) for split in splits)
    
    format_desc = "格式一 (train/images/, train/labels/)" if output_format == 1 else "格式二 (images/train/, labels/train/)"
    log_info(f"数据集划分完成！输出格式: {format_desc}")
    log_info(f"原始总图片数: {total_original}")
    log_info(f"划分后总数: {total_split}")
    
    # 显示各集合的统计
    for split in splits:
        files_count = len(split_files[split])
        percentage = files_count / total_original * 100 if total_original > 0 else 0
        log_info(f"{split}集: {files_count} 张图片 ({percentage:.1f}%)")
    
    # 验证数据完整性
    if total_original == total_split:
        log_info("数据完整性验证通过")
    else:
        log_warn(f"数据不完整，丢失了 {total_original - total_split} 张图片")
    
    # 统计各集合中有标签的图片数量
    print()
    log_info(f"标签图片分布:")
    for split in splits:
        labeled_count = sum(1 for img in split_files[split] if img in image_to_classes)
        log_info(f"{split}集标签图片: {labeled_count}")
    log_info(f"总标签图片: {len(image_to_classes)}")
    
    # 统计各类别在不同集合中的分布
    if image_to_classes:
        print()
        log_info(f"类别分布统计:")
        all_classes = set()
        for classes in image_to_classes.values():
            all_classes.update(classes)
        
        for class_id in sorted(all_classes):
            class_stats = []
            total_class_count = 0
            
            for split in splits:
                count = sum(1 for img in split_files[split] if img in image_to_classes and class_id in image_to_classes[img])
                class_stats.append(f"{split}集{count}")
                total_class_count += count
            
            total_class = len(class_to_images[class_id])
            class_stats.append(f"总计{total_class}")
            log_info(f"类别 {class_id}: {', '.join(class_stats)}")

    # 生成标准 data.yaml
    try:
        # 构造 paths（相对于输出根目录）
        if output_format == 1:
            train_rel = 'train/images'
            val_rel = 'val/images'
            test_rel = 'test/images'
        else:  # format 2
            train_rel = 'images/train'
            val_rel = 'images/val'
            test_rel = 'images/test'

        data_yaml = {
            'path': os.path.normpath(output_dir).replace('\\', '/'),
            'train': train_rel,
            'val': val_rel,
        }
        if use_test:
            data_yaml['test'] = test_rel

        # 推断/读取类别名（统一工具）
        names, _src = discover_class_names(base_dir, structure=structure, labels_dir=labels_dir)

        # 若仍无 names，则根据出现的类别ID生成占位名
        if not names:
            if image_to_classes:
                all_ids = set()
                for s in image_to_classes.values():
                    all_ids.update(s)
                max_id = max(all_ids) if all_ids else -1
                names = [f"Class_{i}" for i in range(max_id + 1)]
            else:
                names = []

        data_yaml['nc'] = len(names)
        data_yaml['names'] = names

        out_yaml_path = os.path.join(output_dir, 'data.yaml')
        # 手写 YAML，避免依赖外部库
        def q(s: str) -> str:
            s = str(s).replace('\\', '/')
            if any(ch in s for ch in [':', '#', '"', '\'', ',', '[', ']', '{', '}', ' ']):
                return '"' + s.replace('"', '\\"') + '"'
            return s
        lines = []
        lines.append(f"path: {q(data_yaml['path'])}")
        lines.append(f"train: {q(data_yaml['train'])}")
        lines.append(f"val: {q(data_yaml['val'])}")
        if 'test' in data_yaml:
            lines.append(f"test: {q(data_yaml['test'])}")
        lines.append(f"nc: {len(names)}")
        if names:
            names_quoted = ', '.join(q(n) for n in names)
            lines.append(f"names: [{names_quoted}]")
        else:
            lines.append("names: []")
        with open(out_yaml_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        log_info(f"已生成标准 data.yaml -> {out_yaml_path}")
    except Exception as e:
        log_warn(f"生成 data.yaml 失败: {e}")


def main():
    parser = argparse.ArgumentParser(description="YOLO数据集划分工具")
    parser.add_argument("--input_dir", "-i", required=True, 
                       help="输入数据集目录 (支持images/+labels/结构或混合结构)")
    parser.add_argument("--output_dir", "-o", required=True,
                       help="输出数据集目录")
    parser.add_argument("--train_ratio", type=float, default=0.8,
                       help="训练集比例 (默认: 0.8)")
    parser.add_argument("--val_ratio", type=float, default=0.1,
                       help="验证集比例 (默认: 0.1)")
    parser.add_argument("--test_ratio", type=float, default=0.1,
                       help="测试集比例 (默认: 0.1，当--no-test时此参数被忽略)")
    parser.add_argument("--seed", type=int, default=42,
                       help="随机种子 (默认: 42)")
    parser.add_argument("--output_format", type=int, choices=[1, 2], default=1,
                       help="输出格式: 1=格式一(train/images/), 2=格式二(images/train/) (默认: 1)")
    parser.add_argument("--no-test", action="store_true",
                       help="只划分为train/val两个集合，不创建test集合")
    
    args = parser.parse_args()
    
    use_test = not args.no_test
    
    # 验证比例总和
    if use_test:
        total_ratio = args.train_ratio + args.val_ratio + args.test_ratio
        if abs(total_ratio - 1.0) > 1e-6:
            log_error(f"错误: 训练、验证、测试集比例总和应为1.0，当前为{total_ratio}")
            return
        split_ratios = {
            "train": args.train_ratio,
            "val": args.val_ratio,
            "test": args.test_ratio
        }
    else:
        total_ratio = args.train_ratio + args.val_ratio
        if abs(total_ratio - 1.0) > 1e-6:
            log_error(f"错误: 训练、验证集比例总和应为1.0，当前为{total_ratio}")
            return
        split_ratios = {
            "train": args.train_ratio,
            "val": args.val_ratio
        }
    
    # 验证输入目录
    if not os.path.exists(args.input_dir):
        log_error(f"错误: 输入目录 {args.input_dir} 不存在")
        return
    
    # 检测输入结构
    structure, images_dir, labels_dir = detect_input_structure(args.input_dir)
    
    if structure == 'unknown':
        log_error(f"错误: 输入目录 {args.input_dir} 不是有效的数据集结构")
        log_info("支持的输入结构:")
        log_info("  1. 标准结构: dataset/images/ + dataset/labels/")
        log_info("  2. 混合结构: 图片和txt标签文件在同一个文件夹中")
        return
    
    # 设置随机种子
    random.seed(args.seed)
    
    structure_name = {
        'standard': '标准结构 (images/ + labels/)',
        'mixed': '混合结构 (图片和标签在同一文件夹)'
    }.get(structure, '未知结构')
    
    log_info("开始划分数据集...")
    log_info(f"输入目录: {args.input_dir}")
    log_info(f"输入结构: {structure_name}")
    log_info(f"输出目录: {args.output_dir}")
    log_info(f"输出格式: {args.output_format} ({'格式一' if args.output_format == 1 else '格式二'})")
    log_info(f"划分模式: {'2个集合 (train/val)' if args.no_test else '3个集合 (train/val/test)'}")
    
    if use_test:
        log_info(f"训练集比例: {args.train_ratio}")
        log_info(f"验证集比例: {args.val_ratio}")
        log_info(f"测试集比例: {args.test_ratio}")
    else:
        log_info(f"训练集比例: {args.train_ratio}")
        log_info(f"验证集比例: {args.val_ratio}")
    
    log_info(f"随机种子: {args.seed}")
    log_info("-" * 50)
    
    # 执行数据集划分
    split_dataset(args.input_dir, args.output_dir, split_ratios, args.output_format, use_test)


if __name__ == "__main__":
    main()
