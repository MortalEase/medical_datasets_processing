# 脚本命令行用法简明说明

## yolo_dataset_split.py
YOLO数据集划分：
```bash
python yolo_dataset_split.py -i 输入数据集目录 -o 输出目录
# 可选参数：--train_ratio 0.8 --val_ratio 0.1 --test_ratio 0.1 --seed 42
```

## coco_dataset_split.py
COCO数据集划分：
```bash
# 基础划分
python coco_dataset_split.py -i RibFrac-COCO-Full -o RibFrac-COCO-Split

# 自定义比例
python coco_dataset_split.py -i RibFrac-COCO-Full -o RibFrac-COCO-Split \
                             --train_ratio 0.8 --val_ratio 0.1 --test_ratio 0.1

# 自定义随机种子
python coco_dataset_split.py -i RibFrac-COCO-Full -o RibFrac-COCO-Split --seed 42
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

## yolo_dataset_viewer.py
YOLO数据集交互式遍历查看器：
```bash
# 交互式查看模式
python yolo_dataset_viewer.py -d 数据集根目录

# 指定类别文件
python yolo_dataset_viewer.py -d 数据集根目录 -c classes.txt

# 交互式查看特定类别的图片
python yolo_dataset_viewer.py -d 数据集根目录 --filter-classes 0,1,2
python yolo_dataset_viewer.py -d 数据集根目录 --filter-classes person,car,bicycle

# 批量查看模式（一次显示多张图片）
python yolo_dataset_viewer.py -d 数据集根目录 --batch -n 12

# 批量查看特定类别的图片
python yolo_dataset_viewer.py -d 数据集根目录 --batch --filter-classes 0,1,2
python yolo_dataset_viewer.py -d 数据集根目录 --batch --filter-classes person,car,bicycle
```

**交互式模式功能**：
- 🖼️ **图片浏览**: 上一张/下一张切换图片
- � **随机查看**: 随机显示任意一张图片
- 📊 **统计分析**: 显示当前数据集的类别分布统计
- 🔄 **数据重置**: 重新扫描数据集，重置所有状态
- � **程序退出**: 安全退出查看器

**快捷键说明**：
- `← →` 或 `A D`: 切换图片（上一张/下一张）
- `R`: 随机显示图片
- `T`: 显示统计信息
- `C`: 重置数据集状态
- `Q` 或 `ESC`: 退出程序

**支持的数据集结构**：
```
# 结构1: 简单结构
dataset/
├── images/
├── labels/
└── classes.txt

# 结构2: 分层结构（推荐）
dataset/
├── train/images + train/labels
├── val/images + val/labels
├── test/images + test/labels
├── classes.txt
└── data.yaml

# 结构3: 混合结构
dataset/
├── images/
├── labels/
└── data.yaml
```

**使用示例**：
```bash
# 查看医疗数据集
python yolo_dataset_viewer.py -d "D:\datasets\medical_yolo"

# 查看自定义数据集
python yolo_dataset_viewer.py -d "/path/to/yolo/dataset" -c custom_classes.txt

# 按类别筛选查看（窗口标题会显示筛选状态）
python yolo_dataset_viewer.py -d "D:\datasets\gugutoudata" --filter-classes 0
```

## clean_gynecology_dataset.py
gynecology-mri数据集专用清理工具：
```bash
python clean_gynecology_dataset.py 数据集根目录 --min_samples 10
# 清理gynecology-mri数据集，移除标注过少的类别
```

## ribfrac_to_coco.py
RibFrac 3D CT转COCO格式目标检测：
```bash
# 基础转换
python ribfrac_to_coco.py -i D:/datasets/ribFrac -o D:/datasets/RibFrac-COCO

# 自定义窗宽窗位
python ribfrac_to_coco.py -i D:/datasets/ribFrac -o D:/datasets/RibFrac-COCO \
                          --window_center 400 --window_width 1500

# 自定义最小边界框面积（过滤小目标）
python ribfrac_to_coco.py -i D:/datasets/ribFrac -o D:/datasets/RibFrac-COCO \
                          --min_area 50

# 完整参数示例
python ribfrac_to_coco.py -i D:/datasets/ribFrac -o D:/datasets/RibFrac-COCO \
                          --window_center 400 --window_width 1500 --min_area 100
```

**参数说明**：
- `--min_area`: 最小边界框面积阈值（单位：像素），默认100像素
  - 小于此面积的骨折区域将被过滤掉
  - 建议值：50-200像素，根据数据集特点调整
  - 值越小，保留的小目标越多，但可能包含噪声
  - 值越大，过滤掉的小目标越多，但可能丢失真实骨折

---
使用 `-h` 或 `--help` 查看详细参数说明。
