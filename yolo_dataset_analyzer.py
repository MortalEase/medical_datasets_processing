import os
from pathlib import Path
import argparse
import yaml
import random


def get_image_extensions():
    """返回支持的图片格式扩展名"""
    return ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp']


def find_classes_file(dataset_dir):
    """查找classes.txt文件"""
    possible_paths = [
        os.path.join(dataset_dir, 'classes.txt'),
        os.path.join(dataset_dir, 'obj.names'),
        os.path.join(dataset_dir, 'names.txt'),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None


def find_data_yaml(dataset_dir):
    """查找data.yaml文件"""
    possible_paths = [
        os.path.join(dataset_dir, 'data.yaml'),
        os.path.join(dataset_dir, 'data.yml'),
        os.path.join(dataset_dir, 'dataset.yaml'),
        os.path.join(dataset_dir, 'dataset.yml'),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None


def load_class_names(dataset_dir):
    """加载类别名称"""
    # 优先查找data.yaml
    yaml_path = find_data_yaml(dataset_dir)
    if yaml_path:
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if 'names' in data:
                    if isinstance(data['names'], list):
                        return {i: name for i, name in enumerate(data['names'])}
                    elif isinstance(data['names'], dict):
                        return data['names']
        except:
            pass
    
    # 查找classes.txt
    classes_path = find_classes_file(dataset_dir)
    if classes_path:
        try:
            with open(classes_path, 'r', encoding='utf-8') as f:
                names = [line.strip() for line in f if line.strip()]
                return {i: name for i, name in enumerate(names)}
        except:
            pass
    
    return {}


def detect_dataset_structure(dataset_dir):
    """检测数据集结构类型"""
    images_dir = os.path.join(dataset_dir, 'images')
    labels_dir = os.path.join(dataset_dir, 'labels')
    
    # 检查是否有train/val/test分层结构
    train_images = os.path.join(dataset_dir, 'train', 'images')
    train_labels = os.path.join(dataset_dir, 'train', 'labels')
    val_images = os.path.join(dataset_dir, 'val', 'images')
    val_labels = os.path.join(dataset_dir, 'val', 'labels')
    test_images = os.path.join(dataset_dir, 'test', 'images')
    test_labels = os.path.join(dataset_dir, 'test', 'labels')
    
    if (os.path.exists(train_images) and os.path.exists(train_labels)) or \
       (os.path.exists(val_images) and os.path.exists(val_labels)) or \
       (os.path.exists(test_images) and os.path.exists(test_labels)):
        return 'hierarchical'  # 分层结构
    elif os.path.exists(images_dir) and os.path.exists(labels_dir):
        return 'simple'  # 简单结构
    else:
        return 'unknown'


def get_dataset_paths(dataset_dir):
    """根据数据集结构获取所有images和labels路径"""
    structure = detect_dataset_structure(dataset_dir)
    paths = []
    
    if structure == 'hierarchical':
        # 分层结构
        for split in ['train', 'val', 'test']:
            images_dir = os.path.join(dataset_dir, split, 'images')
            labels_dir = os.path.join(dataset_dir, split, 'labels')
            if os.path.exists(images_dir) and os.path.exists(labels_dir):
                paths.append((split, images_dir, labels_dir))
    elif structure == 'simple':
        # 简单结构
        images_dir = os.path.join(dataset_dir, 'images')
        labels_dir = os.path.join(dataset_dir, 'labels')
        paths.append(('dataset', images_dir, labels_dir))
    
    return structure, paths


def check_yolo_dataset(img_dir, label_dir, img_exts=None):
    """
    检查YOLO数据集图片与标注的对应关系
    """
    if img_exts is None:
        img_exts = get_image_extensions()
    
    # 获取文件名集合（不含扩展名）
    img_stems = {Path(f).stem for f in os.listdir(img_dir)
                 if Path(f).suffix.lower() in img_exts}

    label_stems = {Path(f).stem for f in os.listdir(label_dir)
                   if Path(f).suffix.lower() == '.txt'}

    # 计算差异集合
    missing_labels = img_stems - label_stems
    redundant_labels = label_stems - img_stems

    # 生成完整文件名列表
    missing_files = []
    for stem in missing_labels:
        for ext in img_exts:
            f = Path(img_dir) / (stem + ext)
            if f.exists():
                missing_files.append(str(f))
                break

    redundant_files = [str(Path(label_dir) / (stem + '.txt'))
                       for stem in redundant_labels]

    return missing_files, redundant_files


def generate_report(split_name, missing, redundant):
    """生成检查报告"""
    print(f"\n{'=' * 20} {split_name} 检查报告 {'=' * 20}")
    print(f"缺失标注文件: {len(missing)} 个")
    print(f"冗余标注文件: {len(redundant)} 个")

    if missing:
        print("\n[ 缺失标注的图片 ]")
        for f in missing[:5]:  # 最多显示前5个
            print(f"  ! {os.path.basename(f)}")
        if len(missing) > 5: 
            print(f"  ...（还有{len(missing)-5}个）")

    if redundant:
        print("\n[ 冗余的标注文件 ]")
        for f in redundant[:5]:
            print(f"  x {os.path.basename(f)}")
        if len(redundant) > 5: 
            print(f"  ...（还有{len(redundant)-5}个）")


def analyze_annotation_statistics(img_dir, label_dir, split_name="", class_names=None):
    """分析标注统计信息"""
    img_exts = get_image_extensions()
    total_images = 0
    labeled_images = 0
    total_boxes = 0
    class_counts = {}
    box_counts_per_image = []
    
    for f in os.listdir(img_dir):
        if Path(f).suffix.lower() in img_exts:
            total_images += 1
            label_path = Path(label_dir) / (Path(f).stem + '.txt')
            
            if label_path.exists():
                labeled_images += 1
                boxes_in_image = 0
                
                try:
                    with open(label_path, 'r') as file:
                        for line in file:
                            parts = line.strip().split()
                            if len(parts) >= 5:
                                class_id = int(float(parts[0]))
                                boxes_in_image += 1
                                total_boxes += 1
                                class_counts[class_id] = class_counts.get(class_id, 0) + 1
                except:
                    continue
                
                box_counts_per_image.append(boxes_in_image)
    
    # 生成统计报告
    prefix = f"{split_name} " if split_name else ""
    print(f"\n{'='*30} {prefix}标注统计分析 {'='*30}")
    print(f"📊 图片总数: {total_images}")
    print(f"📊 有标注图片数: {labeled_images}")
    print(f"📊 背景图片数: {total_images - labeled_images}")
    print(f"📊 标注框总数: {total_boxes}")
    if labeled_images > 0:
        print(f"📊 平均每张有标注图片的标注框数: {total_boxes/labeled_images:.2f}")
    
    if box_counts_per_image:
        print(f"📊 单张图片最多标注框数: {max(box_counts_per_image)}")
        print(f"📊 单张图片最少标注框数: {min(box_counts_per_image)}")
    
    if class_counts:
        print(f"\n📈 各类别标注框分布:")
        for class_id in sorted(class_counts.keys()):
            count = class_counts[class_id]
            percentage = (count / total_boxes) * 100 if total_boxes > 0 else 0
            class_name = class_names.get(class_id, f"Class_{class_id}") if class_names else f"Class_{class_id}"
            print(f"   类别 {class_id} ({class_name}): {count} 个 ({percentage:.1f}%)")
    
    return total_images, labeled_images, total_boxes, class_counts


def analyze_dataset(dataset_dir, show_stats=False):
    """分析整个数据集"""
    print(f"🔍 开始分析数据集: {dataset_dir}")
    
    # 检测数据集结构
    structure, paths = get_dataset_paths(dataset_dir)
    
    if not paths:
        print("❌ 错误: 未找到有效的YOLO数据集结构")
        print("支持的结构:")
        print("  1. 简单结构: dataset/images/ + dataset/labels/")
        print("  2. 分层结构: dataset/train/images/ + dataset/train/labels/ 等")
        return
    
    # 加载类别名称
    class_names = load_class_names(dataset_dir)
    
    print(f"📁 检测到数据集结构: {'分层结构' if structure == 'hierarchical' else '简单结构'}")
    if class_names:
        print(f"📋 加载了 {len(class_names)} 个类别名称")
    else:
        print("⚠️  未找到类别名称文件 (classes.txt 或 data.yaml)")
    
    # 分析每个数据集分割
    total_missing = 0
    total_redundant = 0
    all_stats = {}
    
    for split_name, img_dir, label_dir in paths:
        # 检查对应关系
        missing, redundant = check_yolo_dataset(img_dir, label_dir)
        generate_report(split_name, missing, redundant)
        
        total_missing += len(missing)
        total_redundant += len(redundant)
        
        # 统计分析
        if show_stats:
            stats = analyze_annotation_statistics(img_dir, label_dir, split_name, class_names)
            all_stats[split_name] = stats
    
    # 总体摘要
    print(f"\n{'='*30} 总体摘要 {'='*30}")
    print(f"📊 数据集分割数: {len(paths)}")
    print(f"⚠️  总缺失标注: {total_missing}")
    print(f"⚠️  总冗余标注: {total_redundant}")
    
    if show_stats and all_stats:
        total_images = sum(stats[0] for stats in all_stats.values())
        total_labeled = sum(stats[1] for stats in all_stats.values())
        total_boxes = sum(stats[2] for stats in all_stats.values())
        
        print(f"📊 总图片数: {total_images}")
        print(f"📊 总有标注图片数: {total_labeled}")
        print(f"📊 总标注框数: {total_boxes}")
        
        # 合并类别统计
        combined_classes = {}
        for stats in all_stats.values():
            for class_id, count in stats[3].items():
                combined_classes[class_id] = combined_classes.get(class_id, 0) + count
        
        if combined_classes:
            print(f"\n📈 整体类别分布:")
            for class_id in sorted(combined_classes.keys()):
                count = combined_classes[class_id]
                percentage = (count / total_boxes) * 100 if total_boxes > 0 else 0
                class_name = class_names.get(class_id, f"Class_{class_id}") if class_names else f"Class_{class_id}"
                print(f"   类别 {class_id} ({class_name}): {count} 个 ({percentage:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="YOLO数据集分析工具 - 支持多种数据集结构")
    parser.add_argument('--dataset_dir', '-d', required=True, 
                       help='数据集根目录路径')
    parser.add_argument('--stats', '-s', action='store_true', 
                       help='显示详细统计信息')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.dataset_dir):
        print(f"❌ 错误: 数据集目录不存在: {args.dataset_dir}")
        return
    
    analyze_dataset(args.dataset_dir, args.stats)


if __name__ == "__main__":
    main()