# 脚本命令行用法简明说明

## YOLO数据集格式说明

YOLO数据集支持以下两种主要组织形式：

| 格式 | 目录结构 | 特点 |
|------|----------|------|
| **格式一** | `yolo/`<br/>`├── test/`<br/>`│   ├── images/`<br/>`│   └── labels/`<br/>`├── train/`<br/>`│   ├── images/`<br/>`│   └── labels/`<br/>`├── val/`<br/>`│   ├── images/`<br/>`│   └── labels/`<br/>`└── data.yaml` | 按数据集划分分组<br/>（train/val/test为顶级目录） |
| **格式二** | `yolo_dataset/`<br/>`├── images/`<br/>`│   ├── train/`<br/>`│   ├── val/`<br/>`│   └── test/`<br/>`├── labels/`<br/>`│   ├── train/`<br/>`│   ├── val/`<br/>`│   └── test/`<br/>`└── data.yaml` | 按文件类型分组<br/>（images/labels为顶级目录） |

---

## YOLO数据集工具

## yolo_dataset_split.py
YOLO数据集划分工具

**输入格式要求**：
- ✅ 标准结构: `dataset/images/ + dataset/labels/`
- ✅ 混合结构: 图片和txt标签文件在同一个文件夹中

**输出格式支持**：
- ✅ 格式一：`output/train/images/, output/train/labels/` 等 (默认)
- ✅ 格式二：`output/images/train/, output/labels/train/` 等

```bash
# 基础划分 (默认输出格式一，3个集合)
python yolo_dataset_split.py -i 输入数据集目录 -o 输出目录

# 划分混合结构数据集 (图片和txt文件在同一文件夹)
python yolo_dataset_split.py -i 混合结构数据集目录 -o 输出目录

# 只划分为2个集合 (train/val，不要test)
python yolo_dataset_split.py -i 输入数据集目录 -o 输出目录 --no-test --train_ratio 0.8 --val_ratio 0.2

# 3个集合自定义比例划分
python yolo_dataset_split.py -i 输入数据集目录 -o 输出目录 \
                             --train_ratio 0.8 --val_ratio 0.1 --test_ratio 0.1 \
                             --output_format 1

# 2个集合划分混合结构数据集
python yolo_dataset_split.py -i 混合结构数据集目录 -o 输出目录 \
                             --no-test --train_ratio 0.9 --val_ratio 0.1

# 设置随机种子保证可重现
python yolo_dataset_split.py -i 输入数据集目录 -o 输出目录 --seed 42 --output_format 2
```

**功能特点**：
- ✅ 确保数据完整性（输入图片数 = 输出图片数）
- ✅ 支持背景图片（无标签图片）
- ✅ 支持混合结构输入（图片和txt文件在同一文件夹）
- ✅ 智能过滤类别文件（classes.txt等）
- ✅ 自动复制类别文件到输出目录
- ✅ 支持2个集合（train/val）或3个集合（train/val/test）划分
- ✅ 详细统计报告和数据验证
- ✅ 各类别分布统计

## yolo_class_manager.py
YOLO数据集类别管理工具 - 支持删除、重命名类别和备份管理

**支持的数据集格式**：
- ✅ 标准结构：`dataset/images/ + dataset/labels/`
- ✅ 格式一：`dataset/train/images/ + dataset/train/labels/` 等 (按数据集划分分组)
- ✅ 格式二：`dataset/images/train/ + dataset/labels/train/` 等 (按文件类型分组)
- ✅ 混合结构：图片和txt标签文件在同一个文件夹中

**支持的类别文件格式**：
- ✅ 文本格式：`classes.txt`, `obj.names`, `names.txt`
- ✅ YAML格式：`data.yaml`, `data.yml`, `dataset.yaml`, `dataset.yml`

```bash
# 查看数据集类别信息
python yolo_class_manager.py -d 数据集目录 info

# 删除指定类别（支持已使用和未使用的类别）
python yolo_class_manager.py -d 数据集目录 delete -c 1 7 5

# 删除类别时不创建备份
python yolo_class_manager.py -d 数据集目录 delete -c 1 7 --no-backup

# 重命名类别名称
python yolo_class_manager.py -d 数据集目录 rename -r "old_name:new_name"

# 批量重命名多个类别
python yolo_class_manager.py -d 数据集目录 rename -r "cat:feline" "dog:canine"

# 重命名时不创建备份
python yolo_class_manager.py -d 数据集目录 rename -r "old_name:new_name" --no-backup

# 查看备份状态（演习模式）
python yolo_class_manager.py -d 数据集目录 cleanup --dry-run

# 清理旧备份，保留最新5个
python yolo_class_manager.py -d 数据集目录 cleanup --execute

# 自定义保留备份数量
python yolo_class_manager.py -d 数据集目录 cleanup --execute --keep 3

# 根据目标类别顺序重排类别ID并更新类别文件（预览模式）
python yolo_class_manager.py -d 数据集目录 reindex --to-file path/to/classes.txt --dry-run

# 实际执行重排并备份
python yolo_class_manager.py -d 数据集目录 reindex --to-classes classA classB classC --execute

# 要求当前与目标类别集合完全一致（否则中止）
python yolo_class_manager.py -d 数据集目录 reindex --to-file data.yaml --require-same-set --execute

# 按最小样本数阈值删除类别 (预览)
python yolo_class_manager.py -d 数据集目录 delete -c 5 6 --min-samples 40 --dry-run

# 按最小占比删除类别 (执行)
python yolo_class_manager.py -d 数据集目录 delete --min-percentage 2.0 --execute --yes
```

**功能特点**：
- 🗑️ **删除类别**: 支持删除已使用和未使用的类别，自动重新编号剩余类别
- ✏️ **重命名类别**: 修改类别文件中的类别名称，不影响标签文件中的ID
- 📊 **信息分析**: 显示类别定义、使用统计、频率排序等详细信息
- 🛡️ **安全备份**: 自动创建带时间戳的备份，避免数据丢失
- 🧹 **备份管理**: 智能清理旧备份，释放存储空间
- 🔍 **智能检测**: 自动识别数据集结构和类别文件格式
- ⚠️ **数据验证**: 验证操作前的数据完整性和有效性
 - 🎯 **阈值删除增强**: delete 命令支持最小样本数(--min-samples)与最小占比(--min-percentage)组合筛选，将阈值命中的类别与显式指定ID合并后统一删除并重新编号

**使用示例**：
```bash
# 分析医疗数据集的类别使用情况
python yolo_class_manager.py -d "D:\datasets\medical_yolo" info

# 删除未使用的类别1和7
python yolo_class_manager.py -d "D:\datasets\medical_yolo" delete -c 1 7

# 重命名医疗类别
python yolo_class_manager.py -d "D:\datasets\medical_yolo" rename -r "arco_0:normal" "arco_0_ex:normal_ex"

# 清理超过5个的旧备份
python yolo_class_manager.py -d "D:\datasets\medical_yolo" cleanup --execute --keep 5

# 按最小样本数阈值删除 (预览)
python yolo_class_manager.py -d "D:\datasets\medical_yolo" delete --min-samples 30 --dry-run

# 按最小占比删除 (执行)
python yolo_class_manager.py -d "D:\datasets\medical_yolo" delete --min-percentage 1.5 --execute --yes
```

**备份命名规则**：
- 删除操作：`dataset_backup_before_delete_20250803_142530`
- 重命名操作：`dataset_backup_before_rename_20250803_142530`
- 时间戳格式：`YYYYMMDD_HHMMSS`

注：本仓库脚本已统一复用 `utils/yolo_utils.py` 中的公共函数（如类别文件读取/写入、YOLO结构检测、图片扩展名列表等），提升一致性与复用性。

## yolo_dataset_analyzer.py
YOLO数据集分析工具 - 支持多种数据集结构

**支持的数据集格式**：
- ✅ 格式一：`dataset/train/images/ + dataset/train/labels/` 等 (按数据集划分分组)
- ✅ 格式二：`dataset/images/train/ + dataset/labels/train/` 等 (按文件类型分组)
- ✅ 简单结构：`dataset/images/ + dataset/labels/` (单一数据集)
- ✅ 混合结构：图片和txt标签文件在同一个文件夹中
- ✅ 自动检测：支持包含`data.yaml`的数据集

```bash
# 分析数据集完整性（检查图片与标签对应关系）
python yolo_dataset_analyzer.py -d 数据集根目录

# 显示详细统计信息（包含表格形式的类别分布）
python yolo_dataset_analyzer.py -d 数据集根目录 --stats
```

**功能特点**：
- 🔍 自动检测数据集结构类型 (格式一/格式二/简单结构/混合结构)
- 📊 统计图片与标签对应关系
- 📈 表格形式展示各类别在 train/val/test 中的分布
- 📋 支持从`classes.txt`或`data.yaml`加载类别名称
- ⚠️ 识别缺失标注和冗余标注文件
- 📑 紧凑表格输出，减少屏幕滚动

**使用示例**：
```bash
# 分析格式一数据集 (train/val/test 为顶级目录)
python yolo_dataset_analyzer.py -d "/path/to/format1/dataset" --stats

# 分析格式二数据集 (images/labels 为顶级目录)
python yolo_dataset_analyzer.py -d "/path/to/format2/dataset" --stats

# 分析混合结构数据集 (图片和txt文件在同一文件夹)
python yolo_dataset_analyzer.py -d "/path/to/mixed/dataset" --stats

# 快速检查数据集完整性
python yolo_dataset_analyzer.py -d "./my_dataset"
```


## yolo_dataset_viewer.py
YOLO数据集交互式遍历查看器

**支持的数据集格式**：
- ✅ 格式一：`dataset/train/images/ + dataset/train/labels/` 等
- ✅ 格式二：`dataset/images/train/ + dataset/labels/train/` 等

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
- 🎲 **随机查看**: 随机显示任意一张图片
- 📊 **统计分析**: 显示当前数据集的类别分布统计
- 🔄 **数据重置**: 重新扫描数据集，重置所有状态
- 🚪 **程序退出**: 安全退出查看器

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

## yolo2coco.py
YOLO转COCO格式转换工具

**支持的数据集格式**：
- ✅ 格式一：`dataset/train/images/ + dataset/train/labels/` 等
- ✅ 格式二：`dataset/images/train/ + dataset/labels/train/` 等

```bash
python yolo2coco.py --root_dir 数据集根目录 --save_path 输出json文件路径
# 可选参数：--random_split (随机划分) --split_by_file (按文件划分)
```

## convert_medical_to_yolo.py
医学影像转YOLO格式转换工具

**输出格式**：生成格式二（`dataset/images/train/ + dataset/labels/train/` 等）YOLO数据集

```bash
python convert_medical_to_yolo.py -i 输入图像目录 -o 输出YOLO数据集目录 -m 元数据CSV文件路径
```

---

## COCO数据集工具

## coco_dataset_split.py
COCO数据集划分工具

```bash
# 基础划分
python coco_dataset_split.py -i RibFrac-COCO-Full -o RibFrac-COCO-Split

# 自定义比例
python coco_dataset_split.py -i RibFrac-COCO-Full -o RibFrac-COCO-Split \
                             --train_ratio 0.8 --val_ratio 0.1 --test_ratio 0.1

# 自定义随机种子
python coco_dataset_split.py -i RibFrac-COCO-Full -o RibFrac-COCO-Split --seed 42
```

## ribfrac_to_coco.py
RibFrac 3D CT转COCO格式目标检测

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

## 数据集专用清理工具

## clean_gynecology_dataset.py
gynecology-mri数据集专用清理工具

```bash
python clean_gynecology_dataset.py 数据集根目录 --min_samples 10
# 清理gynecology-mri数据集，移除标注过少的类别
```

---

## 工具说明

### YOLO数据集格式支持情况
- **yolo_dataset_analyzer.py**: 支持格式一、格式二及混合结构
- **yolo_dataset_split.py**: 输入简单结构(images/+labels/)，可输出格式一或格式二
- **yolo_class_manager.py**: 支持标准结构、格式一、格式二及混合结构
- **yolo_dataset_viewer.py**: 支持格式一、格式二
- **yolo2coco.py**: 支持格式一、格式二

### 推荐工作流程
1. 使用 `yolo_dataset_analyzer.py` 分析现有数据集
2. 使用 `yolo_class_manager.py info` 查看类别使用情况
3. 使用 `yolo_class_manager.py delete/rename` 管理类别（如需要）
4. 使用 `yolo_dataset_split.py` 划分数据集（如需要）
5. 使用 `yolo_dataset_analyzer.py` 验证划分结果（使用--stats参数）
6. 使用 `yolo_dataset_viewer.py` 可视化检查数据集
7. 使用 `yolo_class_manager.py cleanup` 定期清理备份文件

使用 `-h` 或 `--help` 查看详细参数说明

---

## 日志输出说明

本仓库的所有入口脚本已统一启用日志重定向。每次运行脚本时，标准输出与标准错误会同时：
- 原样打印到控制台；
- 复制写入到项目根目录下的 `logs/` 目录中的日志文件。

日志文件命名：
- `脚本名_YYYYMMDD_HHMMSS.log`，例如：`yolo_class_manager_20250808_143012.log`

日志内容包含：
- 脚本启动时间与完整命令行
- 运行过程中的所有打印输出
- 错误与异常堆栈（若有）

查看与追踪（Windows PowerShell 示例）：

```powershell
# 查看最新日志文件列表
Get-ChildItem .\logs -File | Sort-Object LastWriteTime -Descending | Select-Object -First 10

# 查看某个日志文件的末尾 50 行
Get-Content .\logs\yolo_class_manager_20250808_143012.log -Tail 50

# 实时追踪日志（类似 tail -f）
Get-Content .\logs\yolo_dataset_split_20250808_150001.log -Wait
```

清理建议：

```powershell
# 仅保留最近 100 个日志，其余删除
Get-ChildItem .\logs -File |
  Sort-Object LastWriteTime -Descending |
  Select-Object -Skip 100 |
  Remove-Item
```

高级定制：
- 日志逻辑位于 `utils/logging_utils.py` 的 `tee_stdout_stderr`，默认输出到 `logs/` 目录；
- 如需调整日志目录/命名规则或增加自动清理策略，可在该文件中扩展实现。