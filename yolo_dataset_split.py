import os
import shutil
import random
import argparse
from collections import defaultdict


def get_image_extensions():
    """返回支持的图片格式扩展名"""
    return ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp']


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


def split_dataset(base_dir, output_dir, split_ratios, output_format=1):
    """
    按指定比例划分数据集，确保各类别在训练、验证、测试集中尽可能均衡

    Args:
        base_dir (str): 数据集的根目录，支持标准结构(images/+labels/)或混合结构(图片和txt在同一文件夹)
        output_dir (str): 输出数据集的根目录
        split_ratios (dict): 数据集划分比例，例如 {"train": 0.8, "val": 0.1, "test": 0.1}
        output_format (int): 输出格式，1为格式一，2为格式二 (默认: 1)
    """
    # 检测输入结构
    structure, images_dir, labels_dir = detect_input_structure(base_dir)
    
    if structure == 'unknown':
        print("❌ 错误: 未找到有效的数据集结构")
        print("支持的输入结构:")
        print("  1. 标准结构: dataset/images/ + dataset/labels/")
        print("  2. 混合结构: 图片和txt标签文件在同一个文件夹中")
        return
    
    structure_name = {
        'standard': '标准结构 (images/ + labels/)',
        'mixed': '混合结构 (图片和标签在同一文件夹)'
    }.get(structure, '未知结构')
    
    print(f"📁 检测到输入结构: {structure_name}")

    if output_format == 1:
        # 格式一: yolo/train/images/, yolo/train/labels/, etc.
        train_dir = os.path.join(output_dir, "train")
        val_dir = os.path.join(output_dir, "val")
        test_dir = os.path.join(output_dir, "test")
        
        # 创建输出目录
        for split in [train_dir, val_dir, test_dir]:
            os.makedirs(os.path.join(split, "images"), exist_ok=True)
            os.makedirs(os.path.join(split, "labels"), exist_ok=True)
    else:
        # 格式二: yolo_dataset/images/train/, yolo_dataset/labels/train/, etc.
        train_dir = output_dir
        val_dir = output_dir
        test_dir = output_dir
        
        # 创建输出目录
        for data_type in ["images", "labels"]:
            for split in ["train", "val", "test"]:
                os.makedirs(os.path.join(output_dir, data_type, split), exist_ok=True)

    # 获取所有标签文件
    if structure == 'mixed':
        # 混合结构：排除类别文件
        all_files = os.listdir(labels_dir)
        label_files = [f for f in all_files if f.endswith(".txt") and 
                      f not in ['classes.txt', 'obj.names', 'names.txt']]
    else:
        # 标准结构：labels目录下的所有txt文件
        label_files = [f for f in os.listdir(labels_dir) if f.endswith(".txt")]
        
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
                print(f"警告: 找不到标签文件 {label_file} 对应的图片文件")
                continue
        image_to_classes[corresponding_image] = classes
        for c in classes:
            class_to_images[c].append(corresponding_image)

    # 获取所有图片文件（包括有标签和无标签的）
    if structure == 'mixed':
        # 混合结构：从同一目录获取图片文件
        all_image_files = [f for f in os.listdir(images_dir) 
                          if os.path.splitext(f)[1].lower() in get_image_extensions()]
    else:
        # 标准结构：从images目录获取图片文件
        all_image_files = [f for f in os.listdir(images_dir) 
                          if os.path.splitext(f)[1].lower() in get_image_extensions()]
    
    # 随机打乱所有图片
    random.shuffle(all_image_files)
    
    # 按比例划分
    total_files = len(all_image_files)
    train_count = int(total_files * split_ratios["train"])
    val_count = int(total_files * split_ratios["val"])
    test_count = total_files - train_count - val_count  # 剩余归为测试集
    
    train_files = all_image_files[:train_count]
    val_files = all_image_files[train_count:train_count + val_count]
    test_files = all_image_files[train_count + val_count:]

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

    copy_files(train_files, "train")
    copy_files(val_files, "val")
    copy_files(test_files, "test")

    # 统计信息
    total_original = len(all_image_files)
    total_split = len(train_files) + len(val_files) + len(test_files)
    
    format_desc = "格式一 (train/images/, train/labels/)" if output_format == 1 else "格式二 (images/train/, labels/train/)"
    print(f"数据集划分完成！输出格式: {format_desc}")
    print(f"原始总图片数: {total_original}")
    print(f"划分后总数: {total_split}")
    print(f"训练集: {len(train_files)} 张图片 ({len(train_files)/total_original*100:.1f}%)")
    print(f"验证集: {len(val_files)} 张图片 ({len(val_files)/total_original*100:.1f}%)")
    print(f"测试集: {len(test_files)} 张图片 ({len(test_files)/total_original*100:.1f}%)")
    
    # 验证数据完整性
    if total_original == total_split:
        print("✓ 数据完整性验证通过")
    else:
        print(f"✗ 警告: 数据不完整，丢失了 {total_original - total_split} 张图片")
    
    # 统计各集合中有标签的图片数量
    labeled_in_train = sum(1 for img in train_files if img in image_to_classes)
    labeled_in_val = sum(1 for img in val_files if img in image_to_classes)
    labeled_in_test = sum(1 for img in test_files if img in image_to_classes)
    
    print(f"\n标签图片分布:")
    print(f"训练集标签图片: {labeled_in_train}")
    print(f"验证集标签图片: {labeled_in_val}")
    print(f"测试集标签图片: {labeled_in_test}")
    print(f"总标签图片: {len(image_to_classes)}")
    
    # 统计各类别在不同集合中的分布
    if image_to_classes:
        print(f"\n类别分布统计:")
        all_classes = set()
        for classes in image_to_classes.values():
            all_classes.update(classes)
        
        for class_id in sorted(all_classes):
            train_count = sum(1 for img in train_files if img in image_to_classes and class_id in image_to_classes[img])
            val_count = sum(1 for img in val_files if img in image_to_classes and class_id in image_to_classes[img])
            test_count = sum(1 for img in test_files if img in image_to_classes and class_id in image_to_classes[img])
            total_class = len(class_to_images[class_id])
            print(f"类别 {class_id}: 训练集{train_count}, 验证集{val_count}, 测试集{test_count}, 总计{total_class}")


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
                       help="测试集比例 (默认: 0.1)")
    parser.add_argument("--seed", type=int, default=42,
                       help="随机种子 (默认: 42)")
    parser.add_argument("--output_format", type=int, choices=[1, 2], default=1,
                       help="输出格式: 1=格式一(train/images/), 2=格式二(images/train/) (默认: 1)")
    
    args = parser.parse_args()
    
    # 验证比例总和
    total_ratio = args.train_ratio + args.val_ratio + args.test_ratio
    if abs(total_ratio - 1.0) > 1e-6:
        print(f"错误: 训练、验证、测试集比例总和应为1.0，当前为{total_ratio}")
        return
    
    # 验证输入目录
    if not os.path.exists(args.input_dir):
        print(f"错误: 输入目录 {args.input_dir} 不存在")
        return
    
    # 检测输入结构
    structure, images_dir, labels_dir = detect_input_structure(args.input_dir)
    
    if structure == 'unknown':
        print(f"错误: 输入目录 {args.input_dir} 不是有效的数据集结构")
        print("支持的输入结构:")
        print("  1. 标准结构: dataset/images/ + dataset/labels/")
        print("  2. 混合结构: 图片和txt标签文件在同一个文件夹中")
        return
    
    # 设置随机种子
    random.seed(args.seed)
    
    # 构建比例字典
    split_ratios = {
        "train": args.train_ratio,
        "val": args.val_ratio,
        "test": args.test_ratio
    }
    
    structure_name = {
        'standard': '标准结构 (images/ + labels/)',
        'mixed': '混合结构 (图片和标签在同一文件夹)'
    }.get(structure, '未知结构')
    
    print(f"开始划分数据集...")
    print(f"输入目录: {args.input_dir}")
    print(f"输入结构: {structure_name}")
    print(f"输出目录: {args.output_dir}")
    print(f"输出格式: {args.output_format} ({'格式一' if args.output_format == 1 else '格式二'})")
    print(f"训练集比例: {args.train_ratio}")
    print(f"验证集比例: {args.val_ratio}")
    print(f"测试集比例: {args.test_ratio}")
    print(f"随机种子: {args.seed}")
    print("-" * 50)
    
    # 执行数据集划分
    split_dataset(args.input_dir, args.output_dir, split_ratios, args.output_format)


if __name__ == "__main__":
    main()
