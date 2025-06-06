import os
from collections import Counter
import argparse

def load_class_names(dataset_path):
    """加载类别名称文件"""
    class_names = {}
    
    # 常见的类别名称文件名
    possible_names = ["classes.txt", "names.txt", "class.names", "labels.txt"]
    
    for name_file in possible_names:
        name_file_path = os.path.join(dataset_path, name_file)
        if os.path.exists(name_file_path):
            try:
                with open(name_file_path, "r", encoding="utf-8") as f:
                    for idx, line in enumerate(f):
                        class_name = line.strip()
                        if class_name:
                            class_names[str(idx)] = class_name
                print(f"加载类别名称文件: {name_file_path}")
                return class_names
            except Exception as e:
                print(f"读取类别文件失败: {e}")
                continue
    
    print("未找到类别名称文件，将只显示类别ID")
    return {}

def main():
    parser = argparse.ArgumentParser(description="统计YOLO数据集各集合标签分布")
    parser.add_argument("--dataset_path", "-d", required=True, help="数据集根目录 (包含train/val/test子目录)")
    parser.add_argument("--class_file", "-c", help="类别名称文件路径 (可选)")
    args = parser.parse_args()
    dataset_path = args.dataset_path

    # 加载类别名称
    if args.class_file:
        class_names = {}
        try:
            with open(args.class_file, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    class_name = line.strip()
                    if class_name:
                        class_names[str(idx)] = class_name
            print(f"从指定文件加载类别名称: {args.class_file}")
        except Exception as e:
            print(f"读取指定类别文件失败: {e}")
            class_names = load_class_names(dataset_path)
    else:
        class_names = load_class_names(dataset_path)

    # 要统计的子目录
    sub_dirs = ["train", "val", "test"]

    # 初始化字典用于存储每个子目录的类别计数
    subdir_label_counts = {sub_dir: Counter() for sub_dir in sub_dirs}    # 遍历每个子目录
    for sub_dir in sub_dirs:
        labels_path = os.path.join(dataset_path, sub_dir, "labels")

        # 确保路径存在
        if not os.path.exists(labels_path):
            print(f"路径不存在: {labels_path}")
            continue        # 遍历当前目录下的所有标签文件
        for label_file in os.listdir(labels_path):
            if label_file.endswith(".txt"):
                label_file_path = os.path.join(labels_path, label_file)
                # 读取标签文件内容
                with open(label_file_path, "r") as f:
                    for line in f:
                        # 每行的第一个数字是类别
                        label = line.strip().split()[0]
                        subdir_label_counts[sub_dir][label] += 1

    # 按顺序打印统计结果
    overall_counts = Counter()
    
    for sub_dir, label_counter in subdir_label_counts.items():
        print(f"\n{sub_dir} 中的标签统计:")
        total_count = sum(label_counter.values())  # 总计
        print(f"  总数量: {total_count}")
        for label, count in sorted(label_counter.items(), key=lambda x: int(x[0])):  # 按类别ID排序输出
            class_name = class_names.get(label, f"未知_{label}")
            percentage = count / total_count if total_count > 0 else 0
            print(f"  类别 {label} ({class_name}): {count} ({percentage:.2%})")
        
        # 累加到总体计数
        for label, count in label_counter.items():
            overall_counts[label] += count
    
    # 打印总体统计
    if overall_counts:
        print(f"\n{'='*50}")
        print("整体数据集统计:")
        overall_total = sum(overall_counts.values())
        print(f"  总数量: {overall_total}")
        for label, count in sorted(overall_counts.items(), key=lambda x: int(x[0])):
            class_name = class_names.get(label, f"未知_{label}")
            percentage = count / overall_total if overall_total > 0 else 0
            print(f"  类别 {label} ({class_name}): {count} ({percentage:.2%})")

if __name__ == "__main__":
    main()