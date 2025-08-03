import os
from pathlib import Path
import argparse
import yaml
import random
from prettytable import PrettyTable


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
    # 检查格式一：dataset/train/images/ + dataset/train/labels/ 等
    train_images = os.path.join(dataset_dir, 'train', 'images')
    train_labels = os.path.join(dataset_dir, 'train', 'labels')
    val_images = os.path.join(dataset_dir, 'val', 'images')
    val_labels = os.path.join(dataset_dir, 'val', 'labels')
    test_images = os.path.join(dataset_dir, 'test', 'images')
    test_labels = os.path.join(dataset_dir, 'test', 'labels')
    
    if (os.path.exists(train_images) and os.path.exists(train_labels)) or \
       (os.path.exists(val_images) and os.path.exists(val_labels)) or \
       (os.path.exists(test_images) and os.path.exists(test_labels)):
        return 'format1'  # 格式一
    
    # 检查格式二：dataset/images/train/ + dataset/labels/train/ 等
    images_train = os.path.join(dataset_dir, 'images', 'train')
    labels_train = os.path.join(dataset_dir, 'labels', 'train')
    images_val = os.path.join(dataset_dir, 'images', 'val')
    labels_val = os.path.join(dataset_dir, 'labels', 'val')
    images_test = os.path.join(dataset_dir, 'images', 'test')
    labels_test = os.path.join(dataset_dir, 'labels', 'test')
    
    if (os.path.exists(images_train) and os.path.exists(labels_train)) or \
       (os.path.exists(images_val) and os.path.exists(labels_val)) or \
       (os.path.exists(images_test) and os.path.exists(labels_test)):
        return 'format2'  # 格式二
    
    # 检查简单结构：dataset/images/ + dataset/labels/
    images_dir = os.path.join(dataset_dir, 'images')
    labels_dir = os.path.join(dataset_dir, 'labels')
    if os.path.exists(images_dir) and os.path.exists(labels_dir):
        return 'simple'  # 简单结构
    
    # 检查混合结构：所有图片和txt文件在同一个文件夹中
    img_exts = get_image_extensions()
    txt_files = []
    img_files = []
    
    try:
        for file in os.listdir(dataset_dir):
            file_path = os.path.join(dataset_dir, file)
            if os.path.isfile(file_path):
                if Path(file).suffix.lower() in img_exts:
                    img_files.append(file)
                elif Path(file).suffix.lower() == '.txt' and file not in ['classes.txt', 'obj.names', 'names.txt']:
                    txt_files.append(file)
        
        # 如果存在图片文件和txt文件，则认为是混合结构
        if img_files and txt_files:
            return 'mixed'  # 混合结构
    except:
        pass
    
    return 'unknown'


def get_dataset_paths(dataset_dir):
    """根据数据集结构获取所有images和labels路径"""
    structure = detect_dataset_structure(dataset_dir)
    paths = []
    
    if structure == 'format1':
        # 格式一：dataset/train/images/ + dataset/train/labels/ 等
        for split in ['train', 'val', 'test']:
            images_dir = os.path.join(dataset_dir, split, 'images')
            labels_dir = os.path.join(dataset_dir, split, 'labels')
            if os.path.exists(images_dir) and os.path.exists(labels_dir):
                paths.append((split, images_dir, labels_dir))
    elif structure == 'format2':
        # 格式二：dataset/images/train/ + dataset/labels/train/ 等
        for split in ['train', 'val', 'test']:
            images_dir = os.path.join(dataset_dir, 'images', split)
            labels_dir = os.path.join(dataset_dir, 'labels', split)
            if os.path.exists(images_dir) and os.path.exists(labels_dir):
                paths.append((split, images_dir, labels_dir))
    elif structure == 'simple':
        # 简单结构：dataset/images/ + dataset/labels/
        images_dir = os.path.join(dataset_dir, 'images')
        labels_dir = os.path.join(dataset_dir, 'labels')
        paths.append(('dataset', images_dir, labels_dir))
    elif structure == 'mixed':
        # 混合结构：所有图片和txt文件在同一个文件夹中
        paths.append(('dataset', dataset_dir, dataset_dir))
    
    return structure, paths


def check_yolo_dataset(img_dir, label_dir, img_exts=None):
    """
    检查YOLO数据集图片与标注的对应关系
    """
    if img_exts is None:
        img_exts = get_image_extensions()
    
    # 处理混合结构（图片和标签在同一目录）
    if img_dir == label_dir:
        all_files = os.listdir(img_dir)
        
        # 获取图片文件名集合（不含扩展名）
        img_stems = set()
        for f in all_files:
            if Path(f).suffix.lower() in img_exts:
                img_stems.add(Path(f).stem)
        
        # 获取标签文件名集合（不含扩展名），排除类别文件
        label_stems = set()
        for f in all_files:
            if (Path(f).suffix.lower() == '.txt' and 
                f not in ['classes.txt', 'obj.names', 'names.txt', 'data.yaml', 'data.yml']):
                label_stems.add(Path(f).stem)
    else:
        # 处理分离结构（图片和标签在不同目录）
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
    
    # 处理混合结构（图片和标签在同一目录）
    if img_dir == label_dir:
        all_files = os.listdir(img_dir)
        
        for f in all_files:
            if Path(f).suffix.lower() in img_exts:
                total_images += 1
                label_path = Path(img_dir) / (Path(f).stem + '.txt')
                
                # 确保不是类别文件
                if (label_path.exists() and 
                    label_path.name not in ['classes.txt', 'obj.names', 'names.txt']):
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
    else:
        # 处理分离结构（图片和标签在不同目录）
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
    
    return total_images, labeled_images, total_boxes, class_counts


def create_basic_stats_table(all_stats):
    """创建基本统计信息表格"""
    table = PrettyTable()
    table.field_names = ["数据集", "总图片数", "有标注图片数", "背景图片数", "标注框总数", "平均框数/图"]
    
    total_images = 0
    total_labeled = 0
    total_boxes = 0
    
    for split_name, stats in all_stats.items():
        imgs, labeled, boxes, _ = stats
        background = imgs - labeled
        avg_boxes = boxes / labeled if labeled > 0 else 0
        
        table.add_row([
            split_name,
            imgs,
            labeled,
            background,
            boxes,
            f"{avg_boxes:.2f}"
        ])
        
        total_images += imgs
        total_labeled += labeled
        total_boxes += boxes
    
    # 添加总计行
    total_background = total_images - total_labeled
    total_avg_boxes = total_boxes / total_labeled if total_labeled > 0 else 0
    table.add_row([
        "总计",
        total_images,
        total_labeled,
        total_background,
        total_boxes,
        f"{total_avg_boxes:.2f}"
    ])
    
    print(f"\n📊 数据集基本统计信息:")
    print(table)


def create_class_distribution_table(all_stats, class_names):
    """创建类别分布表格"""
    # 收集所有类别ID
    all_class_ids = set()
    for stats in all_stats.values():
        all_class_ids.update(stats[3].keys())
    
    if not all_class_ids:
        print("\n⚠️  没有找到任何类别标注")
        return
    
    all_class_ids = sorted(all_class_ids)
    
    # 计算总体统计
    split_totals = {}
    grand_total = 0
    for split_name, stats in all_stats.items():
        split_total = sum(stats[3].values())
        split_totals[split_name] = split_total
        grand_total += split_total
    
    # 创建表格
    table = PrettyTable()
    header = ["类别ID", "类别名称"]
    
    # 为每个数据集分割添加列
    for split_name in all_stats.keys():
        header.append(f"{split_name}(数量(百分比))")
    
    header.append("总数(百分比)")
    table.field_names = header
    
    # 添加每个类别的数据
    for class_id in all_class_ids:
        class_name = class_names.get(class_id, f"Class_{class_id}") if class_names else f"Class_{class_id}"
        row = [class_id, class_name]
        
        class_total = 0
        for split_name, stats in all_stats.items():
            count = stats[3].get(class_id, 0)
            percentage = (count / split_totals[split_name]) * 100 if split_totals[split_name] > 0 else 0
            row.append(f"{count}({percentage:.1f}%)")
            class_total += count
        
        # 总计列
        total_percentage = (class_total / grand_total) * 100 if grand_total > 0 else 0
        row.append(f"{class_total}({total_percentage:.1f}%)")
        
        table.add_row(row)
    
    # 添加总计行
    total_row = ["", "总计"]
    for split_name in all_stats.keys():
        total_count = split_totals[split_name]
        total_row.append(f"{total_count}(100.0%)")
    total_row.append(f"{grand_total}(100.0%)")
    table.add_row(total_row)
    
    print(f"\n📈 类别分布统计表:")
    print(table)


def analyze_dataset(dataset_dir, show_stats=False):
    """分析整个数据集"""
    print(f"🔍 开始分析数据集: {dataset_dir}")
    
    # 检测数据集结构
    structure, paths = get_dataset_paths(dataset_dir)
    
    if not paths:
        print("❌ 错误: 未找到有效的YOLO数据集结构")
        print("支持的结构:")
        print("  1. 格式一: dataset/train/images/ + dataset/train/labels/ 等")
        print("  2. 格式二: dataset/images/train/ + dataset/labels/train/ 等")
        print("  3. 简单结构: dataset/images/ + dataset/labels/")
        print("  4. 混合结构: 图片和txt标签文件在同一个文件夹中")
        return
    
    # 加载类别名称
    class_names = load_class_names(dataset_dir)
    
    # 输出结构类型信息
    structure_name = {
        'format1': '格式一 (按数据集划分分组)',
        'format2': '格式二 (按文件类型分组)',
        'simple': '简单结构',
        'mixed': '混合结构 (图片和标签在同一文件夹)',
        'unknown': '未知格式'
    }.get(structure, '未知格式')
    
    print(f"📁 检测到数据集结构: {structure_name}")
    if class_names:
        print(f"📋 加载了 {len(class_names)} 个类别名称")
    else:
        print("⚠️  未找到类别名称文件 (classes.txt 或 data.yaml)")
    
    # 分析每个数据集分割（收集统计信息但不显示检查报告）
    total_missing = 0
    total_redundant = 0
    all_stats = {}
    missing_reports = []
    
    for split_name, img_dir, label_dir in paths:
        # 检查对应关系
        missing, redundant = check_yolo_dataset(img_dir, label_dir)
        missing_reports.append((split_name, missing, redundant))
        
        total_missing += len(missing)
        total_redundant += len(redundant)
        
        # 统计分析
        if show_stats:
            stats = analyze_annotation_statistics(img_dir, label_dir, split_name, class_names)
            all_stats[split_name] = stats
    
    # 输出顺序：1. 类别分布统计表（如果有统计）
    if show_stats and all_stats:
        create_class_distribution_table(all_stats, class_names)
        
        # 2. 数据集基本统计信息
        create_basic_stats_table(all_stats)
    
    # 3. 总体摘要
    print(f"\n{'='*30} 总体摘要 {'='*30}")
    print(f"📊 数据集分割数: {len(paths)}")
    print(f"⚠️  总缺失标注: {total_missing}")
    print(f"⚠️  总冗余标注: {total_redundant}")
    
    # 4. 检查报告（最后显示）
    for split_name, missing, redundant in missing_reports:
        generate_report(split_name, missing, redundant)


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