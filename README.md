# 脚本命令行用法简明说明

## yolo_dataset_split.py
YOLO数据集划分：
```bash
python yolo_dataset_split.py -i 输入数据集目录 -o 输出目录
# 可选参数：--train_ratio 0.8 --val_ratio 0.1 --test_ratio 0.1 --seed 42
```

## convert_medical_to_yolo.py
医学影像转YOLO格式：
```bash
python convert_medical_to_yolo.py -i 输入图像目录 -o 输出YOLO数据集目录 -m 元数据CSV文件路径
```

## validate_coco_dataset.py
验证COCO格式数据集：
```bash
python validate_coco_dataset.py -d 数据集根目录
# 验证COCO格式数据集的标注文件与图像文件对应关系
```

## validate_yolo_dataset.py
统计YOLO数据集各集合标签分布：
```bash
python validate_yolo_dataset.py -d 数据集根目录
# 统计YOLO格式数据集中各个集合的标签分布情况
```

## yolo_dataset_analyzer.py
检查图片和标签对应关系 + 可视化功能：
```bash
# 基础检查
python yolo_dataset_analyzer.py -i 图片文件夹路径 -l 标签文件夹路径

# 显示详细统计信息
python yolo_dataset_analyzer.py -i 图片文件夹路径 -l 标签文件夹路径 --stats

# 可视化图片和检测框（过滤背景图）
python yolo_dataset_analyzer.py -i 图片文件夹路径 -l 标签文件夹路径 --visualize --samples 9

# 完整分析（统计+可视化）
python yolo_dataset_analyzer.py -i 图片文件夹路径 -l 标签文件夹路径 --stats --visualize
```

## yolo2coco.py
YOLO转COCO格式：
```bash
python yolo2coco.py --root_dir 数据集根目录 --save_path 输出json文件路径
# 可选参数：--random_split (随机划分) --split_by_file (按文件划分)
```

## universal_label_cleaner.py
通用YOLO数据集标签清理工具：
```bash
# 交互式清理（推荐）
python universal_label_cleaner.py 数据集根目录

# 自动清理 - 删除少于50个样本的类别
python universal_label_cleaner.py 数据集根目录 --auto-clean min_samples:50

# 自动清理 - 删除少于2%的类别
python universal_label_cleaner.py 数据集根目录 --auto-clean min_percentage:2.0

# 不创建备份
python universal_label_cleaner.py 数据集根目录 --no-backup

# 静默模式
python universal_label_cleaner.py 数据集根目录 --quiet

# 指定类别文件
python universal_label_cleaner.py 数据集根目录 --class-file custom_classes.txt
```

## clean_gynecology_dataset.py
gynecology-mri数据集专用清理工具：
```bash
python clean_gynecology_dataset.py 数据集根目录 --min_samples 10
# 清理gynecology-mri数据集，移除标注过少的类别
```

---
使用 `-h` 或 `--help` 查看详细参数说明。
