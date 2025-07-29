# 脚本命令行用法简明说明

## yolo_dataset_split.py
YOLO数据集划分工具（仅支持简单结构）：
```bash
# 基础划分
python yolo_dataset_split.py -i 输入数据集目录 -o 输出目录

# 自定义比例划分
python yolo_dataset_split.py -i 输入数据集目录 -o 输出目录 \
                             --train_ratio 0.8 --val_ratio 0.1 --test_ratio 0.1

# 设置随机种子保证可重现
python yolo_dataset_split.py -i 输入数据集目录 -o 输出目录 --seed 42
```

**输入要求**：
- 输入数据集必须为简单结构：`dataset/images/ + dataset/labels/`
- 输出为分层结构：`output/train/, output/val/, output/test/`

**功能特点**：
- ✅ 确保数据完整性（输入图片数 = 输出图片数）
- ✅ 支持背景图片（无标签图片）
- ✅ 详细统计报告和数据验证
- ✅ 各类别分布统计

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
YOLO数据集分析工具 - 支持多种数据集结构：
```bash
# 分析数据集完整性（检查图片与标签对应关系）
python yolo_dataset_analyzer.py -d 数据集根目录

# 显示详细统计信息
python yolo_dataset_analyzer.py -d 数据集根目录 --stats
```

**支持的数据集结构**：
- **简单结构**: `dataset/images/ + dataset/labels/`
- **分层结构**: `dataset/train/images/ + dataset/train/labels/` 等
- **混合结构**: 自动检测并支持包含`data.yaml`的数据集

**功能特点**：
- 🔍 自动检测数据集结构类型
- 📊 统计图片与标签对应关系
- 📈 分析各类别标注框分布
- 📋 支持从`classes.txt`或`data.yaml`加载类别名称
- ⚠️ 识别缺失标注和冗余标注文件

**使用示例**：
```bash
# 分析分层结构数据集
python yolo_dataset_analyzer.py -d "/path/to/hierarchical/dataset" --stats

# 快速检查数据集完整性
python yolo_dataset_analyzer.py -d "./my_dataset"
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

## 工具说明

### 多格式支持
- **yolo_dataset_analyzer.py**: 支持所有三种YOLO数据集结构
- **yolo_dataset_split.py**: 仅支持简单结构输入，输出分层结构
- **其他工具**: 大部分支持简单结构，部分支持分层结构

### 推荐工作流程
1. 使用 `yolo_dataset_analyzer.py` 分析现有数据集
2. 使用 `yolo_dataset_split.py` 划分数据集（如需要）
3. 使用 `validate_yolo_dataset.py` 验证划分结果
4. 使用 `yolo_dataset_viewer.py` 可视化检查数据集

使用 `-h` 或 `--help` 查看详细参数说明。
