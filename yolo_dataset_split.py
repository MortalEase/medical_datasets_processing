import os
import shutil
import random
import argparse
from collections import defaultdict


def get_image_extensions():
    """返回支持的图片格式扩展名"""
    return ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp']


def find_corresponding_image(label_file, images_dir):
    """根据标签文件找到对应的图片文件"""
    base_name = os.path.splitext(label_file)[0]
    image_extensions = get_image_extensions()
    
    for ext in image_extensions:
        image_file = base_name + ext
        image_path = os.path.join(images_dir, image_file)
        if os.path.exists(image_path):
            return image_file
    return None


def split_dataset(base_dir, output_dir, split_ratios):
    """
    按指定比例划分数据集，确保各类别在训练、验证、测试集中尽可能均衡。

    Args:
        base_dir (str): 数据集的根目录，需包含 images 和 labels 文件夹。
        output_dir (str): 输出数据集的根目录。
        split_ratios (dict): 数据集划分比例，例如 {"train": 0.8, "val": 0.1, "test": 0.1}。
    """
    images_dir = os.path.join(base_dir, "images")
    labels_dir = os.path.join(base_dir, "labels")

    train_dir = os.path.join(output_dir, "train")
    val_dir = os.path.join(output_dir, "val")
    test_dir = os.path.join(output_dir, "test")

    # 创建输出目录
    for split in [train_dir, val_dir, test_dir]:
        os.makedirs(os.path.join(split, "images"), exist_ok=True)
        os.makedirs(os.path.join(split, "labels"), exist_ok=True)

    # 获取所有标签文件
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
            corresponding_image = find_corresponding_image(label_file, images_dir)
            if corresponding_image is None:
                print(f"警告: 找不到标签文件 {label_file} 对应的图片文件")
                continue
        image_to_classes[corresponding_image] = classes
        for c in classes:
            class_to_images[c].append(corresponding_image)

    # 将每个类别的图片按比例划分
    train_files, val_files, test_files = [], [], []

    for c, images in class_to_images.items():
        random.shuffle(images)
        total_files = len(images)
        train_count = int(total_files * split_ratios["train"])
        val_count = int(total_files * split_ratios["val"])
        test_count = total_files - train_count - val_count  # 剩余归为测试集

        train_files.extend(images[:train_count])
        val_files.extend(images[train_count:train_count + val_count])
        test_files.extend(images[train_count + val_count:])

    # 处理背景图片（无标签图片）
    all_image_files = [f for f in os.listdir(images_dir) if os.path.splitext(f)[1].lower() in get_image_extensions()]
    labeled_images = set(image_to_classes.keys())
    background_images = [f for f in all_image_files if f not in labeled_images]
    random.shuffle(background_images)
    total_bg = len(background_images)
    train_bg = int(total_bg * split_ratios["train"])
    val_bg = int(total_bg * split_ratios["val"])
    test_bg = total_bg - train_bg - val_bg
    train_files.extend(background_images[:train_bg])
    val_files.extend(background_images[train_bg:train_bg + val_bg])
    test_files.extend(background_images[train_bg + val_bg:])

    # 去重并保持数据分布均衡
    train_files = list(set(train_files))
    val_files = list(set(val_files))
    test_files = list(set(test_files))

    # 复制文件到对应目录
    def copy_files(file_list, split):
        for image_file in file_list:
            # 图片文件路径
            src_image_path = os.path.join(images_dir, image_file)
            dst_image_path = os.path.join(output_dir, split, "images", image_file)
            if os.path.exists(src_image_path):  # 确保图片存在
                shutil.copy(src_image_path, dst_image_path)
            # 标签文件路径
            label_file = os.path.splitext(image_file)[0] + ".txt"  # 获取对应的标签文件名
            src_label_path = os.path.join(labels_dir, label_file)
            dst_label_path = os.path.join(output_dir, split, "labels", label_file)
            if os.path.exists(src_label_path):  # 只复制有标签的图片的标签
                shutil.copy(src_label_path, dst_label_path)

    copy_files(train_files, "train")
    copy_files(val_files, "val")
    copy_files(test_files, "test")

    print(f"数据集划分完成！")
    print(f"训练集: {len(train_files)} 张图片")
    print(f"验证集: {len(val_files)} 张图片")
    print(f"测试集: {len(test_files)} 张图片")


def main():
    parser = argparse.ArgumentParser(description="YOLO数据集划分工具")
    parser.add_argument("--input_dir", "-i", required=True, 
                       help="输入数据集目录 (包含images和labels文件夹)")
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
        
    images_dir = os.path.join(args.input_dir, "images")
    labels_dir = os.path.join(args.input_dir, "labels")
    
    if not os.path.exists(images_dir):
        print(f"错误: 图片目录 {images_dir} 不存在")
        return
        
    if not os.path.exists(labels_dir):
        print(f"错误: 标签目录 {labels_dir} 不存在")
        return
    
    # 设置随机种子
    random.seed(args.seed)
    
    # 构建比例字典
    split_ratios = {
        "train": args.train_ratio,
        "val": args.val_ratio,
        "test": args.test_ratio
    }
    
    print(f"开始划分数据集...")
    print(f"输入目录: {args.input_dir}")
    print(f"输出目录: {args.output_dir}")
    print(f"训练集比例: {args.train_ratio}")
    print(f"验证集比例: {args.val_ratio}")
    print(f"测试集比例: {args.test_ratio}")
    print(f"随机种子: {args.seed}")
    print("-" * 50)
    
    # 执行数据集划分
    split_dataset(args.input_dir, args.output_dir, split_ratios)


if __name__ == "__main__":
    main()
