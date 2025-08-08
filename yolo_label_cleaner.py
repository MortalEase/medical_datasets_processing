#!/usr/bin/env python3

import os
import shutil
import json
from pathlib import Path
import argparse
from collections import Counter, defaultdict
import yaml
from utils.logging_utils import tee_stdout_stderr
_LOG_FILE = tee_stdout_stderr('logs')

# 设置中文字体
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class YOLODatasetCleaner:
    """YOLO数据集清理器"""
    
    def __init__(self, dataset_path, backup=True, verbose=True):
        """
        初始化清理器
        
        Args:
            dataset_path: 数据集根目录路径
            backup: 是否创建备份
            verbose: 是否显示详细信息
        """
        self.dataset_path = Path(dataset_path)
        self.backup = backup
        self.verbose = verbose
        self.splits = ['train', 'val', 'test']  # 支持的数据集划分
        self.img_exts = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        
        # 统计信息
        self.class_counts = defaultdict(int)
        self.total_annotations = 0
        self.total_images = 0
        
        # 检测数据集格式
        self.dataset_format = self.detect_dataset_format()
    
    def detect_dataset_format(self):
        """
        检测YOLO数据集格式
        返回: 1 为格式一, 2 为格式二
        """
        # 检查格式一: dataset/train/images/, dataset/train/labels/
        format1_exists = any((self.dataset_path / split / 'images').exists() and 
                           (self.dataset_path / split / 'labels').exists() 
                           for split in self.splits)
        
        # 检查格式二: dataset/images/train/, dataset/labels/train/
        format2_exists = ((self.dataset_path / 'images').exists() and 
                         (self.dataset_path / 'labels').exists() and
                         any((self.dataset_path / 'images' / split).exists() for split in self.splits))
        
        if format1_exists and not format2_exists:
            self.log("🔍 检测到格式一: train/images/, train/labels/")
            return 1
        elif format2_exists and not format1_exists:
            self.log("🔍 检测到格式二: images/train/, labels/train/")
            return 2
        elif format1_exists and format2_exists:
            self.log("⚠️  检测到混合格式，优先使用格式一")
            return 1
        else:
            self.log("❌ 未检测到有效的YOLO数据集格式")
            return None
    
    def get_split_paths(self, split):
        """根据数据集格式获取分割的路径"""
        if self.dataset_format == 1:
            # 格式一: dataset/train/images/, dataset/train/labels/
            images_dir = self.dataset_path / split / 'images'
            labels_dir = self.dataset_path / split / 'labels'
        else:
            # 格式二: dataset/images/train/, dataset/labels/train/
            images_dir = self.dataset_path / 'images' / split
            labels_dir = self.dataset_path / 'labels' / split
        
        return images_dir, labels_dir
        
    def log(self, message):
        """输出日志信息"""
        if self.verbose:
            print(message)
    
    def load_class_names(self):
        """加载类别名称"""
        class_names = {}
        
        # 尝试不同的类别文件名
        possible_files = ["classes.txt", "names.txt", "class.names", "labels.txt"]
        
        for filename in possible_files:
            class_file = self.dataset_path / filename
            if class_file.exists():
                try:
                    with open(class_file, 'r', encoding='utf-8') as f:
                        for idx, line in enumerate(f):
                            class_name = line.strip()
                            if class_name:
                                class_names[idx] = class_name
                    self.log(f"📂 加载类别文件: {class_file}")
                    return class_names
                except Exception as e:
                    self.log(f"⚠️  读取类别文件失败: {e}")
        
        self.log("⚠️  未找到类别文件，将使用类别ID")
        return {}
    
    def analyze_dataset(self):
        """分析数据集的类别分布"""
        self.log("🔍 分析数据集...")
        
        if self.dataset_format is None:
            self.log("❌ 无法分析数据集：未检测到有效格式")
            return {}
        
        split_stats = {}
        
        for split in self.splits:
            images_dir, labels_dir = self.get_split_paths(split)
            
            if not labels_dir.exists():
                self.log(f"⚠️  跳过不存在的目录: {labels_dir}")
                continue
            
            split_class_counts = defaultdict(int)
            split_images = 0
            split_annotations = 0
            
            # 分析标签文件
            for label_file in labels_dir.glob('*.txt'):
                split_images += 1
                try:
                    with open(label_file, 'r') as f:
                        for line in f:
                            parts = line.strip().split()
                            if len(parts) >= 5:
                                class_id = int(float(parts[0]))
                                split_class_counts[class_id] += 1
                                self.class_counts[class_id] += 1
                                split_annotations += 1
                                self.total_annotations += 1
                except Exception as e:
                    self.log(f"❌ 读取标签文件失败: {label_file}, 错误: {e}")
            
            self.total_images += split_images
            split_stats[split] = {
                'images': split_images,
                'annotations': split_annotations,
                'class_counts': dict(split_class_counts)
            }
        
        return split_stats
    
    def display_analysis(self, split_stats, class_names):
        """显示分析结果"""
        self.log(f"\n{'='*60}")
        self.log(f"{'数据集分析报告':^56}")
        self.log(f"{'='*60}")
        
        # 总体统计
        self.log(f"📊 总图片数: {self.total_images}")
        self.log(f"📊 总标注数: {self.total_annotations}")
        self.log(f"📊 类别数: {len(self.class_counts)}")
        
        # 各split统计
        for split, stats in split_stats.items():
            if stats['images'] > 0:
                self.log(f"\n📂 {split.upper()} 集:")
                self.log(f"   图片数: {stats['images']}")
                self.log(f"   标注数: {stats['annotations']}")
        
        # 类别分布
        self.log(f"\n📈 类别分布:")
        sorted_classes = sorted(self.class_counts.items(), key=lambda x: x[1], reverse=True)
        
        for class_id, count in sorted_classes:
            class_name = class_names.get(class_id, f"Class_{class_id}")
            percentage = (count / self.total_annotations) * 100 if self.total_annotations > 0 else 0
            self.log(f"   类别 {class_id} ({class_name}): {count} 个 ({percentage:.1f}%)")
    
    def get_cleaning_strategy(self, class_names):
        """获取用户的清理策略"""
        self.log(f"\n{'='*60}")
        self.log(f"{'选择清理策略':^56}")
        self.log(f"{'='*60}")
        
        print("请选择清理策略:")
        print("1. 按最小样本数清理 (删除样本数少于阈值的类别)")
        print("2. 按百分比清理 (删除占比少于阈值的类别)")
        print("3. 手动选择要保留的类别")
        print("4. 手动选择要删除的类别")
        print("5. 自定义清理规则")
        print("0. 取消清理")
        
        while True:
            try:
                choice = input("\n请输入选择 (0-5): ").strip()
                if choice in ['0', '1', '2', '3', '4', '5']:
                    break
                else:
                    print("❌ 无效选择，请输入 0-5")
            except KeyboardInterrupt:
                print("\n👋 用户取消操作")
                return None
        
        if choice == '0':
            return None
        
        strategy = {'type': choice}
        
        if choice == '1':
            # 按最小样本数清理
            while True:
                try:
                    min_samples = int(input("请输入最小样本数阈值: "))
                    strategy['min_samples'] = min_samples
                    break
                except ValueError:
                    print("❌ 请输入有效的整数")
        
        elif choice == '2':
            # 按百分比清理
            while True:
                try:
                    min_percentage = float(input("请输入最小百分比阈值 (例如: 1.0 表示1%): "))
                    strategy['min_percentage'] = min_percentage
                    break
                except ValueError:
                    print("❌ 请输入有效的数字")
        
        elif choice == '3':
            # 手动选择保留的类别
            print(f"\n当前类别列表:")
            for class_id, count in sorted(self.class_counts.items()):
                class_name = class_names.get(class_id, f"Class_{class_id}")
                print(f"  {class_id}: {class_name} ({count} 个样本)")
            
            while True:
                try:
                    keep_input = input("请输入要保留的类别ID (用逗号分隔): ").strip()
                    keep_classes = [int(x.strip()) for x in keep_input.split(',') if x.strip()]
                    
                    # 验证类别ID
                    invalid_ids = [cid for cid in keep_classes if cid not in self.class_counts]
                    if invalid_ids:
                        print(f"❌ 无效的类别ID: {invalid_ids}")
                        continue
                    
                    strategy['keep_classes'] = keep_classes
                    break
                except ValueError:
                    print("❌ 请输入有效的类别ID")
        
        elif choice == '4':
            # 手动选择删除的类别
            print(f"\n当前类别列表:")
            for class_id, count in sorted(self.class_counts.items()):
                class_name = class_names.get(class_id, f"Class_{class_id}")
                print(f"  {class_id}: {class_name} ({count} 个样本)")
            
            while True:
                try:
                    remove_input = input("请输入要删除的类别ID (用逗号分隔): ").strip()
                    remove_classes = [int(x.strip()) for x in remove_input.split(',') if x.strip()]
                    
                    # 验证类别ID
                    invalid_ids = [cid for cid in remove_classes if cid not in self.class_counts]
                    if invalid_ids:
                        print(f"❌ 无效的类别ID: {invalid_ids}")
                        continue
                    
                    strategy['remove_classes'] = remove_classes
                    break
                except ValueError:
                    print("❌ 请输入有效的类别ID")
        
        elif choice == '5':
            # 自定义清理规则
            print("\n自定义清理规则:")
            print("1. 组合条件 (最小样本数 AND 最小百分比)")
            print("2. 保留前N个最多样本的类别")
            print("3. 删除特定范围的类别")
            
            sub_choice = input("请选择自定义规则 (1-3): ").strip()
            strategy['custom_type'] = sub_choice
            
            if sub_choice == '1':
                min_samples = int(input("请输入最小样本数: "))
                min_percentage = float(input("请输入最小百分比: "))
                strategy['min_samples'] = min_samples
                strategy['min_percentage'] = min_percentage
            
            elif sub_choice == '2':
                top_n = int(input("请输入要保留的类别数量: "))
                strategy['top_n'] = top_n
            
            elif sub_choice == '3':
                min_id = int(input("请输入要删除的类别ID最小值: "))
                max_id = int(input("请输入要删除的类别ID最大值: "))
                strategy['id_range'] = (min_id, max_id)
        
        return strategy
    
    def determine_classes_to_remove(self, strategy, class_names):
        """根据策略确定要删除的类别"""
        if not strategy:
            return []
        
        classes_to_remove = []
        
        if strategy['type'] == '1':
            # 按最小样本数
            min_samples = strategy['min_samples']
            classes_to_remove = [class_id for class_id, count in self.class_counts.items() 
                               if count < min_samples]
        
        elif strategy['type'] == '2':
            # 按百分比
            min_percentage = strategy['min_percentage']
            min_count = (min_percentage / 100.0) * self.total_annotations
            classes_to_remove = [class_id for class_id, count in self.class_counts.items() 
                               if count < min_count]
        
        elif strategy['type'] == '3':
            # 手动选择保留
            keep_classes = strategy['keep_classes']
            classes_to_remove = [class_id for class_id in self.class_counts.keys() 
                               if class_id not in keep_classes]
        
        elif strategy['type'] == '4':
            # 手动选择删除
            classes_to_remove = strategy['remove_classes']
        
        elif strategy['type'] == '5':
            # 自定义规则
            custom_type = strategy['custom_type']
            
            if custom_type == '1':
                # 组合条件
                min_samples = strategy['min_samples']
                min_percentage = strategy['min_percentage']
                min_count = (min_percentage / 100.0) * self.total_annotations
                classes_to_remove = [class_id for class_id, count in self.class_counts.items() 
                                   if count < min_samples or count < min_count]
            
            elif custom_type == '2':
                # 保留前N个
                top_n = strategy['top_n']
                sorted_classes = sorted(self.class_counts.items(), key=lambda x: x[1], reverse=True)
                keep_classes = [class_id for class_id, _ in sorted_classes[:top_n]]
                classes_to_remove = [class_id for class_id in self.class_counts.keys() 
                                   if class_id not in keep_classes]
            
            elif custom_type == '3':
                # ID范围删除
                min_id, max_id = strategy['id_range']
                classes_to_remove = [class_id for class_id in self.class_counts.keys() 
                                   if min_id <= class_id <= max_id]
        
        return classes_to_remove
    
    def preview_cleaning(self, classes_to_remove, class_names):
        """预览清理结果"""
        if not classes_to_remove:
            self.log("✅ 没有需要删除的类别!")
            return False
        
        classes_to_keep = [class_id for class_id in self.class_counts.keys() 
                          if class_id not in classes_to_remove]
        
        self.log(f"\n{'='*60}")
        self.log(f"{'清理预览':^56}")
        self.log(f"{'='*60}")
        
        # 要删除的类别
        self.log(f"❌ 将删除的类别 ({len(classes_to_remove)} 个):")
        removed_samples = 0
        for class_id in sorted(classes_to_remove):
            class_name = class_names.get(class_id, f"Class_{class_id}")
            count = self.class_counts[class_id]
            percentage = (count / self.total_annotations) * 100
            removed_samples += count
            self.log(f"   类别 {class_id} ({class_name}): {count} 个 ({percentage:.1f}%)")
        
        # 要保留的类别
        self.log(f"\n✅ 将保留的类别 ({len(classes_to_keep)} 个):")
        kept_samples = 0
        for class_id in sorted(classes_to_keep):
            class_name = class_names.get(class_id, f"Class_{class_id}")
            count = self.class_counts[class_id]
            percentage = (count / self.total_annotations) * 100
            kept_samples += count
            self.log(f"   类别 {class_id} ({class_name}): {count} 个 ({percentage:.1f}%)")
        
        # 统计信息
        self.log(f"\n📊 清理统计:")
        self.log(f"   删除样本数: {removed_samples} ({(removed_samples/self.total_annotations)*100:.1f}%)")
        self.log(f"   保留样本数: {kept_samples} ({(kept_samples/self.total_annotations)*100:.1f}%)")
        
        # 用户确认
        while True:
            confirm = input(f"\n是否确认执行清理? (y/n): ").strip().lower()
            if confirm in ['y', 'yes', 'n', 'no']:
                return confirm in ['y', 'yes']
            print("❌ 请输入 y 或 n")
    
    def create_backup(self):
        """创建数据集备份"""
        if not self.backup:
            return None
        
        backup_path = self.dataset_path.parent / f"{self.dataset_path.name}_backup_{self.get_timestamp()}"
        
        if backup_path.exists():
            self.log(f"⚠️  备份目录已存在: {backup_path}")
            return backup_path
        
        self.log(f"💾 创建备份: {backup_path}")
        try:
            shutil.copytree(self.dataset_path, backup_path)
            self.log(f"✅ 备份创建成功")
            return backup_path
        except Exception as e:
            self.log(f"❌ 备份创建失败: {e}")
            return None
    
    def get_timestamp(self):
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def clean_dataset(self, classes_to_remove, class_names):
        """执行数据集清理"""
        if not classes_to_remove:
            return
        
        classes_to_keep = [class_id for class_id in self.class_counts.keys() 
                          if class_id not in classes_to_remove]
        
        self.log(f"\n🧹 开始清理数据集...")
        
        # 创建类别ID映射
        id_mapping = {old_id: new_id for new_id, old_id in enumerate(sorted(classes_to_keep))}
        
        # 统计信息
        removed_files = []
        updated_files = []
        
        for split in self.splits:
            images_dir, labels_dir = self.get_split_paths(split)
            
            if not labels_dir.exists():
                continue
            
            self.log(f"🔧 处理 {split} 集...")
            
            for label_file in labels_dir.glob('*.txt'):
                try:
                    # 读取并过滤标签
                    valid_lines = []
                    with open(label_file, 'r') as f:
                        for line in f:
                            parts = line.strip().split()
                            if len(parts) >= 5:
                                class_id = int(float(parts[0]))
                                if class_id in classes_to_keep:
                                    # 重新映射类别ID
                                    new_class_id = id_mapping[class_id]
                                    parts[0] = str(new_class_id)
                                    valid_lines.append(' '.join(parts))
                    
                    # 如果没有有效标注，删除文件
                    if not valid_lines:
                        # 删除标签文件
                        label_file.unlink()
                        removed_files.append(str(label_file))
                        
                        # 删除对应的图片文件
                        img_stem = label_file.stem
                        for ext in self.img_exts:
                            img_file = images_dir / f"{img_stem}{ext}"
                            if img_file.exists():
                                img_file.unlink()
                                removed_files.append(str(img_file))
                                break
                    else:
                        # 更新标签文件
                        with open(label_file, 'w') as f:
                            f.write('\n'.join(valid_lines) + '\n')
                        updated_files.append(str(label_file))
                
                except Exception as e:
                    self.log(f"❌ 处理文件失败: {label_file}, 错误: {e}")
        
        # 更新配置文件
        self.update_config_files(classes_to_keep, class_names, id_mapping)
        
        # 显示结果
        self.log(f"\n📊 清理完成:")
        self.log(f"   🗑️  删除文件数: {len(removed_files)}")
        self.log(f"   ✏️  更新文件数: {len(updated_files)}")
        
        return {
            'removed_files': removed_files,
            'updated_files': updated_files,
            'id_mapping': id_mapping
        }
    
    def update_config_files(self, classes_to_keep, class_names, id_mapping):
        """更新配置文件"""
        # 更新classes.txt
        classes_file = self.dataset_path / 'classes.txt'
        if classes_file.exists() or class_names:
            new_class_names = []
            for new_id in range(len(classes_to_keep)):
                old_id = sorted(classes_to_keep)[new_id]
                class_name = class_names.get(old_id, f"Class_{old_id}")
                new_class_names.append(class_name)
            
            with open(classes_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_class_names))
            self.log(f"📝 更新 classes.txt: {new_class_names}")
        
        # 更新data.yaml
        data_yaml = self.dataset_path / 'data.yaml'
        if data_yaml.exists():
            try:
                with open(data_yaml, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                # 更新类别数和名称
                data['nc'] = len(classes_to_keep)
                if 'names' in data:
                    new_names = []
                    for new_id in range(len(classes_to_keep)):
                        old_id = sorted(classes_to_keep)[new_id]
                        if isinstance(data['names'], list) and old_id < len(data['names']):
                            new_names.append(data['names'][old_id])
                        else:
                            class_name = class_names.get(old_id, f"Class_{old_id}")
                            new_names.append(class_name)
                    data['names'] = new_names
                
                with open(data_yaml, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)
                self.log(f"📝 更新 data.yaml")
                
            except Exception as e:
                self.log(f"⚠️  更新 data.yaml 失败: {e}")
    
    def generate_report(self, strategy, classes_removed, cleaning_result, class_names, backup_path):
        """生成清理报告"""
        report_path = self.dataset_path / f"cleaning_report_{self.get_timestamp()}.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# YOLO数据集清理报告\n\n")
            f.write(f"**清理日期**: {self.get_timestamp()}\n")
            f.write(f"**数据集路径**: `{self.dataset_path}`\n")
            if backup_path:
                f.write(f"**备份路径**: `{backup_path}`\n")
            f.write(f"\n## 清理前统计\n\n")
            f.write(f"- **总图片数**: {self.total_images}\n")
            f.write(f"- **总标注数**: {self.total_annotations}\n")
            f.write(f"- **类别数**: {len(self.class_counts)}\n\n")
            
            f.write(f"### 原始类别分布\n\n")
            f.write("| 类别ID | 类别名称 | 标注数 | 占比 |\n")
            f.write("|--------|----------|--------|------|\n")
            
            for class_id, count in sorted(self.class_counts.items()):
                class_name = class_names.get(class_id, f"Class_{class_id}")
                percentage = (count / self.total_annotations) * 100
                f.write(f"| {class_id} | {class_name} | {count} | {percentage:.1f}% |\n")
            
            f.write(f"\n## 清理策略\n\n")
            f.write(f"**策略类型**: {strategy['type']}\n")
            # 根据策略类型添加详细信息
            
            if classes_removed:
                f.write(f"\n## 清理结果\n\n")
                f.write(f"- **删除类别数**: {len(classes_removed)}\n")
                f.write(f"- **删除文件数**: {len(cleaning_result['removed_files'])}\n")
                f.write(f"- **更新文件数**: {len(cleaning_result['updated_files'])}\n")
        
        self.log(f"📋 生成清理报告: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="YOLO数据集标签清理工具")
    parser.add_argument('dataset_path', help='数据集根目录路径')
    parser.add_argument('--no-backup', action='store_true', help='不创建备份')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式')
    parser.add_argument('--class-file', help='指定类别名称文件路径')
    parser.add_argument('--auto-clean', help='自动清理模式 (min_samples:N 或 min_percentage:N)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.dataset_path):
        print(f"❌ 数据集路径不存在: {args.dataset_path}")
        return
    
    # 初始化清理器
    cleaner = YOLODatasetCleaner(
        dataset_path=args.dataset_path,
        backup=not args.no_backup,
        verbose=not args.quiet
    )
    
    try:
        # 加载类别名称
        if args.class_file:
            class_names = {}
            with open(args.class_file, 'r', encoding='utf-8') as f:
                for idx, line in enumerate(f):
                    class_name = line.strip()
                    if class_name:
                        class_names[idx] = class_name
        else:
            class_names = cleaner.load_class_names()
        
        # 分析数据集
        split_stats = cleaner.analyze_dataset()
        cleaner.display_analysis(split_stats, class_names)
        
        # 获取清理策略
        if args.auto_clean:
            # 自动模式
            if args.auto_clean.startswith('min_samples:'):
                min_samples = int(args.auto_clean.split(':')[1])
                strategy = {'type': '1', 'min_samples': min_samples}
            elif args.auto_clean.startswith('min_percentage:'):
                min_percentage = float(args.auto_clean.split(':')[1])
                strategy = {'type': '2', 'min_percentage': min_percentage}
            else:
                print("❌ 无效的自动清理参数")
                return
        else:
            # 交互模式
            strategy = cleaner.get_cleaning_strategy(class_names)
        
        if not strategy:
            cleaner.log("👋 用户取消清理操作")
            return
        
        # 确定要删除的类别
        classes_to_remove = cleaner.determine_classes_to_remove(strategy, class_names)
        
        # 预览并确认
        if not cleaner.preview_cleaning(classes_to_remove, class_names):
            cleaner.log("👋 用户取消清理操作")
            return
        
        # 创建备份
        backup_path = cleaner.create_backup()
        
        # 执行清理
        cleaning_result = cleaner.clean_dataset(classes_to_remove, class_names)
        
        # 生成报告
        cleaner.generate_report(strategy, classes_to_remove, cleaning_result, class_names, backup_path)
        
        cleaner.log(f"\n🎉 数据集清理完成!")
        
    except KeyboardInterrupt:
        cleaner.log(f"\n👋 用户中断操作")
    except Exception as e:
        cleaner.log(f"\n❌ 清理过程中发生错误: {e}")


if __name__ == "__main__":
    main()
