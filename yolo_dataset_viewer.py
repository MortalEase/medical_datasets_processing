#!/usr/bin/env python3

import os
import sys
import cv2
import argparse
from utils.logging_utils import tee_stdout_stderr
_LOG_FILE = tee_stdout_stderr('logs')
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.widgets import Button
import random

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class YOLODatasetViewer:
    """YOLO数据集查看器"""
    
    def __init__(self, dataset_path, class_names_file=None, setup_gui=True):
        self.dataset_path = Path(dataset_path)
        self.current_index = 0
        self.image_files = []
        self.class_names = {}
        self.colors = [
            'red', 'blue', 'green', 'yellow', 'purple', 'orange', 
            'cyan', 'magenta', 'brown', 'pink', 'lime', 'teal'
        ]
        
        # 加载类别名称
        self.load_class_names(class_names_file)
        
        # 扫描数据集
        self.scan_dataset()
        
        if not self.image_files:
            print("❌ 未找到任何有标注的图片文件！")
            sys.exit(1)
            
        print(f"📋 找到 {len(self.image_files)} 张有标注的图片")
        
        # 根据参数决定是否初始化matplotlib界面
        if setup_gui:
            self.setup_gui()
    
    def load_class_names(self, class_names_file=None):
        """加载类别名称文件"""
        if class_names_file and os.path.exists(class_names_file):
            try:
                with open(class_names_file, 'r', encoding='utf-8') as f:
                    for idx, line in enumerate(f):
                        class_name = line.strip()
                        if class_name:
                            self.class_names[idx] = class_name
                print(f"✅ 从指定文件加载类别名称: {class_names_file}")
                return
            except Exception as e:
                print(f"⚠️  读取指定类别文件失败: {e}")
        
        # 自动查找类别文件
        possible_names = ["classes.txt", "names.txt", "class.names", "labels.txt", "data.yaml"]
        
        for name_file in possible_names:
            class_file = self.dataset_path / name_file
            if class_file.exists():
                try:
                    if name_file.endswith('.yaml'):
                        # 处理YAML格式
                        import yaml
                        with open(class_file, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f)
                            if 'names' in data:
                                if isinstance(data['names'], list):
                                    for idx, name in enumerate(data['names']):
                                        self.class_names[idx] = name
                                elif isinstance(data['names'], dict):
                                    self.class_names = data['names']
                    else:
                        # 处理文本格式
                        with open(class_file, 'r', encoding='utf-8') as f:
                            for idx, line in enumerate(f):
                                class_name = line.strip()
                                if class_name:
                                    self.class_names[idx] = class_name
                    
                    print(f"✅ 加载类别文件: {class_file}")
                    return
                except Exception as e:
                    print(f"⚠️  读取类别文件失败: {e}")
                    continue
        
        print("⚠️  未找到类别名称文件，将显示类别ID")
    
    def scan_dataset(self):
        """扫描数据集，找到所有有标注的图片"""
        print("🔍 扫描数据集...")
        
        # 支持的图片格式
        img_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        
        # 查找所有可能的目录结构
        possible_dirs = [
            self.dataset_path,  # 根目录
            self.dataset_path / 'images',  # images目录
            self.dataset_path / 'train' / 'images',  # train/images
            self.dataset_path / 'val' / 'images',    # val/images
            self.dataset_path / 'test' / 'images',   # test/images
        ]
        
        for img_dir in possible_dirs:
            if not img_dir.exists():
                continue
                
            # 对应的标签目录
            if img_dir.name == 'images':
                label_dir = img_dir.parent / 'labels'
            else:
                label_dir = img_dir / 'labels'
                if not label_dir.exists():
                    label_dir = self.dataset_path / 'labels'
            
            if not label_dir.exists():
                continue
            
            print(f"📂 扫描目录: {img_dir}")
            print(f"📂 标签目录: {label_dir}")
            
            # 查找有标注的图片
            for img_file in img_dir.iterdir():
                if img_file.suffix.lower() in img_extensions:
                    label_file = label_dir / f"{img_file.stem}.txt"
                    
                    if label_file.exists():
                        # 检查标注文件是否非空
                        try:
                            with open(label_file, 'r') as f:
                                lines = f.readlines()
                                if lines and any(line.strip() for line in lines):
                                    self.image_files.append({
                                        'image_path': str(img_file),
                                        'label_path': str(label_file),
                                        'set_name': img_dir.parent.name if img_dir.name == 'images' else 'dataset'
                                    })
                        except Exception as e:
                            print(f"⚠️  读取标注文件失败: {label_file}, {e}")
        
        # 按路径排序
        self.image_files.sort(key=lambda x: x['image_path'])
    
    def load_annotations(self, label_path):
        """读取YOLO格式标注文件"""
        annotations = []
        try:
            with open(label_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        class_id = int(float(parts[0]))
                        x_center = float(parts[1])
                        y_center = float(parts[2])
                        width = float(parts[3])
                        height = float(parts[4])
                        annotations.append({
                            'class_id': class_id,
                            'x_center': x_center,
                            'y_center': y_center,
                            'width': width,
                            'height': height
                        })
        except Exception as e:
            print(f"❌ 读取标注失败: {e}")
        
        return annotations
    
    def draw_annotations(self, ax, image_shape, annotations):
        """在图片上绘制标注框"""
        h, w = image_shape[:2]
        
        for i, ann in enumerate(annotations):
            # YOLO格式转换为像素坐标
            x_center_px = ann['x_center'] * w
            y_center_px = ann['y_center'] * h
            box_width_px = ann['width'] * w
            box_height_px = ann['height'] * h
            
            # 计算左上角坐标
            x1 = x_center_px - box_width_px / 2
            y1 = y_center_px - box_height_px / 2
            
            # 选择颜色
            color = self.colors[ann['class_id'] % len(self.colors)]
            
            # 绘制矩形框
            rect = patches.Rectangle(
                (x1, y1), box_width_px, box_height_px,
                linewidth=2, edgecolor=color, facecolor='none'
            )
            ax.add_patch(rect)
            
            # 获取类别名称
            class_name = self.class_names.get(ann['class_id'], f"Class_{ann['class_id']}")
            
            # 添加类别标签
            label_text = f"{class_name} ({ann['class_id']})"
            ax.text(
                x1, y1 - 5, label_text,
                color=color, fontsize=10, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8)
            )
    
    def filter_by_classes(self, filter_classes):
        """根据类别筛选图片
        
        Args:
            filter_classes: 筛选的类别列表 (类别ID或名称)
        """
        if not filter_classes:
            return
            
        print(f"🔍 按类别筛选: {filter_classes}")
        
        # 解析筛选类别
        target_classes = set()
        for cls in filter_classes:
            if isinstance(cls, int) or (isinstance(cls, str) and cls.isdigit()):
                target_classes.add(int(cls))
            else:
                # 类别名称，查找对应ID
                for class_id, class_name in self.class_names.items():
                    if class_name.lower() == str(cls).lower():
                        target_classes.add(class_id)
                        break
        
        # 筛选图片
        filtered_files = []
        for img_file in self.image_files:
            annotations = self.load_annotations(img_file['label_path'])
            image_classes = {ann['class_id'] for ann in annotations}
            
            if target_classes.intersection(image_classes):
                filtered_files.append(img_file)
        
        if not filtered_files:
            print(f"❌ 未找到包含指定类别的图片！")
            return
        
        self.image_files = filtered_files
        self.current_index = 0
        print(f"✅ 筛选后找到 {len(filtered_files)} 张图片")
        
        # 如果GUI已经创建，更新窗口标题
        if hasattr(self, 'fig'):
            self.update_window_title()

    def update_window_title(self):
        """更新窗口标题"""
        dataset_name = self.dataset_path.name
        num_classes = len(self.class_names)
        title = f"YOLO数据集查看器 - {dataset_name} | {len(self.image_files)}张图片 | {num_classes}个类别"
        if hasattr(self, 'fig') and self.fig.canvas.manager:
            self.fig.canvas.manager.set_window_title(title)

    def setup_gui(self):
        """设置GUI界面"""
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        plt.subplots_adjust(bottom=0.15)
        
        # 设置窗口标题
        dataset_name = self.dataset_path.name
        num_classes = len(self.class_names)
        title = f"YOLO数据集查看器 - {dataset_name} | {len(self.image_files)}张图片 | {num_classes}个类别"
        self.fig.canvas.manager.set_window_title(title)
        
        # 计算按钮的居中位置
        button_width = 0.1
        button_height = 0.04
        button_spacing = 0.02
        total_buttons = 5
        total_width = total_buttons * button_width + (total_buttons - 1) * button_spacing
        start_x = (1 - total_width) / 2
        
        # 创建居中的按钮
        ax_prev = plt.axes([start_x, 0.05, button_width, button_height])
        ax_next = plt.axes([start_x + (button_width + button_spacing), 0.05, button_width, button_height])
        ax_random = plt.axes([start_x + 2 * (button_width + button_spacing), 0.05, button_width, button_height])
        ax_stats = plt.axes([start_x + 3 * (button_width + button_spacing), 0.05, button_width, button_height])
        ax_reset = plt.axes([start_x + 4 * (button_width + button_spacing), 0.05, button_width, button_height])
        
        # 创建按钮
        self.btn_prev = Button(ax_prev, '上一张')
        self.btn_next = Button(ax_next, '下一张')
        self.btn_random = Button(ax_random, '随机')
        self.btn_stats = Button(ax_stats, '统计')
        self.btn_reset = Button(ax_reset, '重置')
        
        # 绑定事件
        self.btn_prev.on_clicked(self.prev_image)
        self.btn_next.on_clicked(self.next_image)
        self.btn_random.on_clicked(self.random_image)
        self.btn_stats.on_clicked(self.show_class_statistics)
        self.btn_reset.on_clicked(self.reset_filter)
        
        # 键盘事件
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        # 显示第一张图片
        self.show_current_image()
    
    def show_current_image(self):
        """显示当前图片"""
        if not self.image_files:
            return
        
        current_file = self.image_files[self.current_index]
        img_path = current_file['image_path']
        label_path = current_file['label_path']
        set_name = current_file['set_name']
        
        # 读取图片
        try:
            img = cv2.imread(img_path)
            if img is None:
                print(f"❌ 无法读取图片: {img_path}")
                return
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except Exception as e:
            print(f"❌ 读取图片失败: {e}")
            return
        
        # 读取标注
        annotations = self.load_annotations(label_path)
        
        # 清空之前的图像
        self.ax.clear()
        
        # 显示图片
        self.ax.imshow(img)
        
        # 绘制标注框
        self.draw_annotations(self.ax, img.shape, annotations)
        
        # 设置标题
        img_name = Path(img_path).name
        title = f"[{self.current_index + 1}/{len(self.image_files)}] {img_name}\n"
        title += f"数据集: {set_name} | 标注框数: {len(annotations)}"
        
        self.ax.set_title(title, fontsize=12, pad=20)
        self.ax.axis('off')
        
        # 更新显示
        plt.draw()
        
        # 打印当前图片信息
        print(f"\n📸 [{self.current_index + 1}/{len(self.image_files)}] {img_name}")
        print(f"📂 路径: {img_path}")
        print(f"📊 标注框数量: {len(annotations)}")
        
        if annotations:
            print("📋 标注详情:")
            class_counts = {}
            for ann in annotations:
                class_id = ann['class_id']
                class_name = self.class_names.get(class_id, f"Class_{class_id}")
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
            
            for class_name, count in class_counts.items():
                print(f"   - {class_name}: {count} 个")
    
    def prev_image(self, event):
        """显示上一张图片"""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_image()
        else:
            print("📍 已经是第一张图片")
    
    def next_image(self, event):
        """显示下一张图片"""
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.show_current_image()
        else:
            print("📍 已经是最后一张图片")
    
    def random_image(self, event):
        """随机显示一张图片"""
        self.current_index = random.randint(0, len(self.image_files) - 1)
        self.show_current_image()
    
    def show_info(self, event):
        """显示数据集信息"""
        print(f"\n{'='*60}")
        print(f"{'数据集信息':^56}")
        print(f"{'='*60}")
        print(f"📂 数据集路径: {self.dataset_path}")
        print(f"📊 图片总数: {len(self.image_files)}")
        
        # 统计各数据集的数量
        set_counts = {}
        for img_file in self.image_files:
            set_name = img_file['set_name']
            set_counts[set_name] = set_counts.get(set_name, 0) + 1
        
        print(f"📈 数据集分布:")
        for set_name, count in set_counts.items():
            print(f"   - {set_name}: {count} 张")
        
        # 统计类别分布
        if self.class_names:
            print(f"🏷️  类别数量: {len(self.class_names)}")
            print(f"📋 类别列表:")
            for class_id, class_name in sorted(self.class_names.items()):
                print(f"   - {class_id}: {class_name}")
        else:
            print("⚠️  未加载类别名称文件")
    
    def show_class_statistics(self, event):
        """显示类别统计信息"""
        print(f"\n{'='*60}")
        print(f"{'类别统计信息':^56}")
        print(f"{'='*60}")
        
        # 统计每个类别的出现次数
        class_counts = {}
        total_annotations = 0
        
        for img_file in self.image_files:
            annotations = self.load_annotations(img_file['label_path'])
            for ann in annotations:
                class_id = ann['class_id']
                class_counts[class_id] = class_counts.get(class_id, 0) + 1
                total_annotations += 1
        
        if not class_counts:
            print("❌ 当前筛选结果中没有标注信息！")
            return
        
        print(f"📊 当前显示图片数: {len(self.image_files)}")
        print(f"📊 标注框总数: {total_annotations}")
        print(f"📊 类别数: {len(class_counts)}")
        
        print(f"\n📈 类别分布:")
        print(f"{'类别ID':<8} {'类别名称':<20} {'数量':<8} {'占比':<8}")
        print("-" * 50)
        
        # 按数量排序显示
        for class_id, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True):
            class_name = self.class_names.get(class_id, f"Class_{class_id}")
            percentage = (count / total_annotations) * 100
            print(f"{class_id:<8} {class_name:<20} {count:<8} {percentage:<8.1f}%")
    
    def reset_filter(self, event):
        """重置筛选，显示所有图片"""
        print("🔄 正在重置筛选...")
        original_count = len(self.image_files)
        
        # 重新扫描数据集
        self.scan_dataset()
        self.current_index = 0
        
        # 更新窗口标题
        self.update_window_title()
        
        self.show_current_image()
        
        print(f"✅ 筛选已重置，显示全部 {len(self.image_files)} 张图片")
        if len(self.image_files) != original_count:
            print(f"📊 筛选前: {original_count} 张 → 重置后: {len(self.image_files)} 张")

    def on_key_press(self, event):
        """处理键盘事件"""
        if event.key == 'left' or event.key == 'a':
            self.prev_image(None)
        elif event.key == 'right' or event.key == 'd':
            self.next_image(None)
        elif event.key == 'r':
            self.random_image(None)
        elif event.key == 't':
            self.show_class_statistics(None)
        elif event.key == 'c':
            self.reset_filter(None)
        elif event.key == 'q' or event.key == 'escape':
            plt.close()
    
    def start(self):
        """启动查看器"""
        print(f"\n{'='*60}")
        print(f"{'YOLO数据集查看器':^56}")
        print(f"{'='*60}")
        print("🔧 操作说明:")
        print("   • 按钮: 上一张/下一张/随机/统计/重置")
        print("   • 快捷键: ← → (A D) 切换, R 随机, T 统计, C 重置")
        print("   • 按 Q/ESC 退出程序")
        print(f"{'='*60}\n")
        
        try:
            plt.show()
        except KeyboardInterrupt:
            print("\n👋 程序已退出")


def batch_view_mode(dataset_path, class_names_file=None, num_samples=9, filter_classes=None):
    """批量查看模式 - 在一个窗口显示多张图片
    
    Args:
        dataset_path: 数据集路径
        class_names_file: 类别文件路径
        num_samples: 显示样本数量
        filter_classes: 筛选的类别列表 (类别ID或名称)
    """
    print(f"🔍 批量查看模式: 显示 {num_samples} 张图片")
    
    # 创建临时查看器来扫描数据集（不创建GUI）
    viewer = YOLODatasetViewer(dataset_path, class_names_file, setup_gui=False)
    
    if len(viewer.image_files) == 0:
        print("❌ 未找到任何有标注的图片！")
        return
    
    # 如果指定了类别筛选
    if filter_classes:
        viewer.filter_by_classes(filter_classes)
    
    # 随机选择样本
    samples = random.sample(viewer.image_files, min(num_samples, len(viewer.image_files)))
    
    # 计算子图布局
    cols = 3
    rows = (len(samples) + cols - 1) // cols
    
    # 增加图片尺寸和间距，彻底解决重叠问题
    fig, axes = plt.subplots(rows, cols, figsize=(18, 8 * rows))
    if len(samples) == 1:
        axes = [axes]
    elif rows == 1:
        axes = axes
    else:
        axes = axes.flatten()
    
    # 设置窗口标题
    dataset_name = viewer.dataset_path.name
    num_classes = len(viewer.class_names)
    window_title = f"YOLO批量查看器 - {dataset_name} | {len(viewer.image_files)}张图片 | {num_classes}个类别"
    if filter_classes:
        window_title += f" | 筛选: {filter_classes}"
    fig.canvas.manager.set_window_title(window_title)
    
    # 设置总标题
    title = f"YOLO数据集批量查看 ({len(samples)} 张图片)"
    if filter_classes:
        title += f" - 筛选类别: {filter_classes}"
    fig.suptitle(title, fontsize=14, y=0.95)
    
    for idx, sample in enumerate(samples):
        img_path = sample['image_path']
        label_path = sample['label_path']
        
        # 读取图片
        try:
            img = cv2.imread(img_path)
            if img is None:
                continue
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except:
            continue
        
        # 读取标注
        annotations = viewer.load_annotations(label_path)
        
        # 显示图片
        axes[idx].imshow(img)
        
        # 绘制标注框
        viewer.draw_annotations(axes[idx], img.shape, annotations)
        
        # 设置标题 - 显示类别信息
        img_name = Path(img_path).name
        class_info = []
        class_counts = {}
        for ann in annotations:
            class_id = ann['class_id']
            class_name = viewer.class_names.get(class_id, f"Class_{class_id}")
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        class_info = [f"{name}({count})" for name, count in class_counts.items()]
        
        # 简化文件名和类别信息
        if len(img_name) > 25:
            display_name = img_name[:22] + "..."
        else:
            display_name = img_name
            
        if class_info:
            class_text = ', '.join(class_info)
            if len(class_text) > 30:
                class_text = class_text[:27] + "..."
            title = f"{display_name}\n{class_text}"
        else:
            title = f"{display_name}\n无标注"
        
        axes[idx].set_title(title, fontsize=8, pad=10)
        axes[idx].axis('off')
    
    # 隐藏多余的子图
    for idx in range(len(samples), len(axes)):
        axes[idx].axis('off')
    
    # 设置合适的布局间距
    plt.tight_layout(pad=2.0, h_pad=3.5, w_pad=2.0)
    plt.subplots_adjust(top=0.92)  # 为总标题留出空间
    plt.show()
    
    print(f"✅ 已展示 {len(samples)} 个样本的可视化结果")


def main():
    parser = argparse.ArgumentParser(
        description="YOLO数据集遍历查看器 - 显示图片标注框和类名",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 交互式查看模式
  python yolo_dataset_viewer.py -d /path/to/yolo/dataset
  
  # 指定类别文件
  python yolo_dataset_viewer.py -d /path/to/dataset -c classes.txt
  
  # 批量查看模式
  python yolo_dataset_viewer.py -d /path/to/dataset --batch -n 12
  
  # 按类别筛选批量查看
  python yolo_dataset_viewer.py -d /path/to/dataset --batch --filter-classes 0,1,2
  python yolo_dataset_viewer.py -d /path/to/dataset --batch --filter-classes person,car
  
  # 支持的数据集结构:
  # 1. dataset/images + dataset/labels
  # 2. dataset/train/images + dataset/train/labels  
  # 3. dataset/val/images + dataset/val/labels
  # 4. dataset/test/images + dataset/test/labels
        """
    )
    
    parser.add_argument(
        '-d', '--dataset', required=True,
        help='YOLO数据集根目录路径'
    )
    parser.add_argument(
        '-c', '--classes', 
        help='类别名称文件路径 (可选，支持 .txt 和 .yaml 格式)'
    )
    parser.add_argument(
        '--batch', action='store_true',
        help='批量查看模式：在一个窗口显示多张图片'
    )
    parser.add_argument(
        '-n', '--num-samples', type=int, default=9,
        help='批量模式下显示的图片数量 (默认: 9)'
    )
    parser.add_argument(
        '--filter-classes',
        help='筛选指定类别的图片，用逗号分隔 (支持类别ID或名称，如: 0,1,2 或 person,car)'
    )
    
    args = parser.parse_args()
    
    # 检查数据集路径
    if not os.path.exists(args.dataset):
        print(f"❌ 数据集路径不存在: {args.dataset}")
        sys.exit(1)
    
    # 解析筛选类别
    filter_classes = None
    if args.filter_classes:
        filter_classes = [cls.strip() for cls in args.filter_classes.split(',')]
        print(f"🔍 将筛选类别: {filter_classes}")
    
    try:
        if args.batch:
            # 批量查看模式
            batch_view_mode(args.dataset, args.classes, args.num_samples, filter_classes)
        else:
            # 交互式查看模式
            viewer = YOLODatasetViewer(args.dataset, args.classes)
            
            # 如果指定了类别筛选，应用筛选
            if filter_classes:
                viewer.filter_by_classes(filter_classes)
                if viewer.image_files:  # 确保筛选后还有图片
                    viewer.show_current_image()
            
            viewer.start()
    
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
