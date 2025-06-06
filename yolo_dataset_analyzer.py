import os
from pathlib import Path
import argparse
import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import random
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def check_yolo_dataset(img_dir, label_dir, img_exts=['.jpg', '.png', '.jpeg']):
    """
    检查YOLO数据集图片与标注的对应关系
    :param img_dir: 图片文件夹路径
    :param label_dir: 标注文件夹路径
    :param img_exts: 支持的图片扩展名列表
    :return: 缺失标注的图片列表，冗余标注的文件列表
    """
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


def generate_report(missing, redundant):
    """生成可视化报告"""
    print(f"\n{'=' * 30} 检查报告 {'=' * 30}")
    print(f"总缺失标注文件: {len(missing)} 个")
    print(f"总冗余标注文件: {len(redundant)} 个\n")

    if missing:
        print("[ 缺失标注的图片 ]")
        for f in missing[:5]:  # 最多显示前5个
            print(f"  ! {f}")
        if len(missing) > 5: print(f"  ...（共{len(missing)}个）")

    if redundant:
        print("\n[ 冗余的标注文件 ]")
        for f in redundant[:5]:
            print(f"  x {f}")
        if len(redundant) > 5: print(f"  ...（共{len(redundant)}个）")


def visualize_dataset(img_dir, label_dir, output_dir, sample_size=5):
    """
    可视化YOLO数据集的图片和标注
    :param img_dir: 图片文件夹路径
    :param label_dir: 标注文件夹路径
    :param output_dir: 输出文件夹路径
    :param sample_size: 随机抽样的图片数量
    """
    # 获取所有图片文件
    img_files = [f for f in os.listdir(img_dir) if Path(f).suffix.lower() in ['.jpg', '.png', '.jpeg']]

    # 随机抽样
    sampled_imgs = random.sample(img_files, min(sample_size, len(img_files)))

    for img_file in sampled_imgs:
        img_path = Path(img_dir) / img_file
        label_path = Path(label_dir) / (Path(img_file).stem + '.txt')

        # 读取图片
        img = cv2.imread(str(img_path))
        h, w, _ = img.shape

        # 创建绘图对象
        fig, ax = plt.subplots(1)
        ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        # 读取并绘制标注
        if label_path.exists():
            with open(label_path, 'r') as f:
                for line in f.readlines():
                    class_id, x_center, y_center, width, height = map(float, line.strip().split())
                    # 转换为左上角坐标和右下角坐标
                    x_center, y_center, width, height = x_center * w, y_center * h, width * w, height * h
                    x1, y1, x2, y2 = int(x_center - width / 2), int(y_center - height / 2), int(x_center + width / 2), int(y_center + height / 2)

                    # 绘制矩形框
                    rect = patches.Rectangle((x1, y1), x2 - x1, y2 - y1, linewidth=2, edgecolor='red', facecolor='none')
                    ax.add_patch(rect)
                    # 绘制类别标签
                    ax.text(x1, y1, f'Class {int(class_id)}', fontsize=12, color='red', bbox=dict(facecolor='white', alpha=0.5))

        # 保存或显示图片
        output_path = Path(output_dir) / img_file
        plt.axis('off')
        plt.savefig(str(output_path), bbox_inches='tight')
        plt.close(fig)


def visualize_yolo_annotations(img_dir, label_dir, num_samples=6, img_exts=['.jpg', '.png', '.jpeg']):
    """
    可视化YOLO数据集中的图片和标注框
    :param img_dir: 图片文件夹路径
    :param label_dir: 标注文件夹路径
    :param num_samples: 要显示的样本数量
    :param img_exts: 支持的图片扩展名列表
    """
    # 获取所有有标注的图片文件（过滤掉背景图）
    img_files = []
    for f in os.listdir(img_dir):
        if Path(f).suffix.lower() in img_exts:
            img_path = Path(img_dir) / f
            label_path = Path(label_dir) / (Path(f).stem + '.txt')
            
            # 检查标注文件是否存在且非空
            if label_path.exists():
                try:
                    with open(label_path, 'r') as file:
                        lines = file.readlines()                        # 只选择有实际标注内容的图片
                        if lines and any(line.strip() for line in lines):
                            img_files.append((str(img_path), str(label_path)))
                except:
                    continue
    
    if not img_files:
        print("❌ 没有找到有标注的图片！所有图片都是背景图。")
        return
    
    print(f"📋 找到 {len(img_files)} 张有标注的图片（过滤掉了背景图）")
    
    # 随机选择样本
    samples = random.sample(img_files, min(num_samples, len(img_files)))
    
    # 创建子图
    cols = 3
    rows = (len(samples) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(15, 5*rows))
    if len(samples) == 1:
        axes = [axes]
    elif rows == 1:
        axes = [axes]
    else:
        axes = axes.flatten()
    
    for idx, (img_path, label_path) in enumerate(samples):
        # 读取图片
        img = cv2.imread(img_path)
        if img is None:
            continue
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]
        
        # 读取YOLO标注
        boxes = []
        try:
            with open(label_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        class_id, x_center, y_center, width, height = map(float, parts[:5])
                        boxes.append((class_id, x_center, y_center, width, height))
        except:
            continue
        
        # 显示图片
        axes[idx].imshow(img)
        axes[idx].set_title(f'{Path(img_path).name}\n标注框数量: {len(boxes)}', fontsize=10)
        axes[idx].axis('off')
        
        # 绘制标注框
        colors = ['red', 'blue', 'green', 'yellow', 'purple', 'orange', 'cyan', 'magenta']
        for i, (class_id, x_center, y_center, box_width, box_height) in enumerate(boxes):
            # YOLO格式转换为像素坐标
            x_center_px = x_center * w
            y_center_px = y_center * h
            box_width_px = box_width * w
            box_height_px = box_height * h
            
            # 计算左上角坐标
            x1 = x_center_px - box_width_px / 2
            y1 = y_center_px - box_height_px / 2
            
            # 绘制矩形框
            color = colors[int(class_id) % len(colors)]
            rect = patches.Rectangle((x1, y1), box_width_px, box_height_px, 
                                   linewidth=2, edgecolor=color, facecolor='none')
            axes[idx].add_patch(rect)
            
            # 添加类别标签
            axes[idx].text(x1, y1-5, f'Class {int(class_id)}', 
                         color=color, fontsize=8, fontweight='bold',
                         bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.7))
    
    # 隐藏多余的子图
    for idx in range(len(samples), len(axes)):
        axes[idx].axis('off')
    
    plt.tight_layout()
    plt.show()
    
    print(f"✅ 已展示 {len(samples)} 个样本的可视化结果")


def analyze_annotation_statistics(img_dir, label_dir, img_exts=['.jpg', '.png', '.jpeg']):
    """
    分析标注统计信息
    """
    total_images = 0
    total_boxes = 0
    class_counts = {}
    box_counts_per_image = []
    
    for f in os.listdir(img_dir):
        if Path(f).suffix.lower() in img_exts:
            img_path = Path(img_dir) / f
            label_path = Path(label_dir) / (Path(f).stem + '.txt')
            
            if label_path.exists():
                total_images += 1
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
    print(f"\n{'='*40} 标注统计分析 {'='*40}")
    print(f"📊 图片总数: {total_images}")
    print(f"📊 标注框总数: {total_boxes}")
    print(f"📊 平均每张图片的标注框数: {total_boxes/total_images:.2f}" if total_images > 0 else "📊 平均每张图片的标注框数: 0")
    
    if box_counts_per_image:
        print(f"📊 单张图片最多标注框数: {max(box_counts_per_image)}")
        print(f"📊 单张图片最少标注框数: {min(box_counts_per_image)}")
    
    print(f"\n📈 各类别标注框分布:")
    for class_id, count in sorted(class_counts.items()):
        percentage = (count / total_boxes) * 100 if total_boxes > 0 else 0
        print(f"   类别 {class_id}: {count} 个 ({percentage:.1f}%)")
    
    return total_images, total_boxes, class_counts


def main():
    parser = argparse.ArgumentParser(description="检查YOLO数据集图片与标签对应关系")
    parser.add_argument('--img_dir', '-i', required=True, help='图片文件夹路径')
    parser.add_argument('--label_dir', '-l', required=True, help='标签文件夹路径')
    parser.add_argument('--visualize', '-v', action='store_true', help='显示图片和检测框可视化')
    parser.add_argument('--samples', '-s', type=int, default=6, help='可视化样本数量 (默认6)')
    parser.add_argument('--stats', action='store_true', help='显示详细统计信息')
    args = parser.parse_args()
    IMAGE_DIR = args.img_dir
    LABEL_DIR = args.label_dir

    # 检查图片与标签对应关系
    missing, redundant = check_yolo_dataset(IMAGE_DIR, LABEL_DIR)
    generate_report(missing, redundant)
    
    # 显示统计信息
    if args.stats or args.visualize:
        analyze_annotation_statistics(IMAGE_DIR, LABEL_DIR)
    
    # 可视化
    if args.visualize:
        print(f"\n🖼️  准备显示 {args.samples} 个随机样本的可视化...")
        try:
            visualize_yolo_annotations(IMAGE_DIR, LABEL_DIR, args.samples)
        except Exception as e:
            print(f"❌ 可视化失败: {e}")
            print("请确保安装了 matplotlib: pip install matplotlib")

    # 交互式确认
    if missing or redundant or args.visualize:
        input("\n按Enter键退出...")


if __name__ == "__main__":
    main()