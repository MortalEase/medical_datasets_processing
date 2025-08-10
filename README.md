# 脚本命令行用法简明说明

## 脚本索引 (快速导航)

| 脚本 | 作用 | 主要输入结构 | 主要输出结构 | 关键参数 | 备注 |
|------|------|-------------|-------------|---------|------|
| yolo_dataset_analyzer.py | YOLO 数据集结构/缺失/统计分析 | format1/format2/standard/mixed | 终端输出 | -d --stats | 不修改数据 |
| yolo_dataset_split.py | YOLO 划分 train/val/test | standard/mixed | format1 或 format2 | -i -o --train_ratio | 复制图片与标签 |
| yolo_class_manager.py | YOLO 类别增删改/重排/清理 | format1/format2/standard/mixed | 就地修改 | delete/rename/reindex | 自动备份 |
| yolo_dataset_viewer.py | 可视化查看/筛选/统计 | format1/format2 | 无写出 | -d --filter-classes | Matplotlib GUI |
| yolo2coco.py | YOLO -> COCO 转换(+可分层划分) | format1/format2/standard/mixed | COCO JSON | -d -o --split | standard/mixed 可再划分 |
| coco_dataset_split.py | COCO 分层再划分 | COCO 单文件 | 多分割 COCO | -i -o --train_ratio | 类别平衡抽样 |
| coco_dataset_analyzer.py | COCO JSON 多分割统计 | COCO (annotations/*.json) | 终端输出 | -d --stats | 图片存在性检查 |
| voc2yolo.py | VOC XML -> YOLO | VOC Annotations + JPEGImages | YOLO standard/mixed | -i -o --structure | 可生成 data.yaml |
| convert_medical_to_yolo.py | MHA 医学图像转换 | MHA + metadata.csv | YOLO format2 | -i -o -m | 单类示例 |

> 统一日志: 所有脚本默认写 logs/ 时间戳日志；统一参数: 输出目录推荐使用 --output_dir / -o, 数据集根目录使用 -d/--dataset_dir。

## 推荐工作流

1. 初始数据健康检查: `yolo_dataset_analyzer.py -d ... --stats`
2. 类别清理与规范: `yolo_class_manager.py delete/rename/reindex`
3. 数据划分 (若原始未分): `yolo_dataset_split.py -i raw -o split --train_ratio ...`
4. 视觉抽样验证: `yolo_dataset_viewer.py -d split --filter-classes ...`
5. 需要 COCO 训练/评估: `yolo2coco.py -d split -o coco_dir`
6. 需要重新比例或分层: `coco_dataset_split.py -i coco_dir -o coco_split ...`
7. COCO 成品统计核对: `coco_dataset_analyzer.py -d coco_split --stats`

> 医学影像 (MHA) 场景: 先 `convert_medical_to_yolo.py` 生成 YOLO，再并入上面流程。

---

## YOLO数据集格式说明

YOLO数据集支持以下两种主要组织形式：

| 格式 | 目录结构 | 特点 |
|------|----------|------|
| **格式一** | `dataset/`<br/>`├── train/`<br/>`│   ├── images/`<br/>`│   └── labels/`<br/>`├── val/`<br/>`│   ├── images/`<br/>`│   └── labels/`<br/>`├── test/`<br/>`│   ├── images/`<br/>`│   └── labels/`<br/>`└── classes.txt(data.yaml)` | 按数据集划分分组 (train/val/test 顶级) |
| **格式二** | `dataset/`<br/>`├── images/`<br/>`│   ├── train/ val/ test/`<br/>`├── labels/`<br/>`│   ├── train/ val/ test/`<br/>`└── classes.txt(data.yaml)` | 按文件类型分组 (images 与 labels 顶级) |
| **标准** | `dataset/`<br/>`├── images/`<br/>`└── labels/`<br/>`└── classes.txt(data.yaml)` | 单一集合 (未预分割)，常用于后续再划分 |
| **混合** | `dataset/`<br/>`├── *.jpg/*.png`<br/>`├── *.txt`<br/>`└── classes.txt(data.yaml)` | 图片与标签同目录混放，快速整理或小规模数据 |

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
python yolo_dataset_split.py -i 输入数据集目录 -o 输出目录  # 仍支持 -o 但推荐 --output_dir

# 划分混合结构数据集 (图片和txt文件在同一文件夹)
python yolo_dataset_split.py -i 混合结构数据集目录 -o 输出目录

# 只划分为2个集合 (train/val，不要test)
python yolo_dataset_split.py -i 输入数据集目录 --output_dir 输出目录 --no-test --train_ratio 0.8 --val_ratio 0.2

# 3个集合自定义比例划分
python yolo_dataset_split.py -i 输入数据集目录 --output_dir 输出目录 \
                             --train_ratio 0.8 --val_ratio 0.1 --test_ratio 0.1 \
                             --output_format 1

# 2个集合划分混合结构数据集
python yolo_dataset_split.py -i 混合结构数据集目录 --output_dir 输出目录 \
                             --no-test --train_ratio 0.9 --val_ratio 0.1

# 设置随机种子保证可重现
python yolo_dataset_split.py -i 输入数据集目录 --output_dir 输出目录 --seed 42 --output_format 2
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

**支持的输入结构**：
- ✅ 格式一 (format1): `dataset/train/images/ + dataset/train/labels/` 等 (可存在 train/val/test 任意子集)
- ✅ 格式二 (format2): `dataset/images/train/ + dataset/labels/train/` 等
- ✅ 标准结构 (standard): `dataset/images/ + dataset/labels/`
- ✅ 混合结构 (mixed): 图片与标签 `.txt` 混在同一目录

**核心特性**：
- 自动检测数据集结构 (format1 / format2 / standard / mixed)
- 已带分割的结构直接输出多个 JSON (train.json / val.json / test.json)
- 单一结构(standard/mixed)可直接输出单文件或使用 `--split` 触发二次 COCO 分层划分
- `--split` 时内部先转为临时 COCO，再调用仓库现有 `coco_dataset_split.py` 完成按类别分层划分
- 支持缺失标签图片（会保留 image 条目不生成 annotation）
- 类别优先读取 `classes.txt/obj.names/names.txt`，未找到则从标签动态扩展

**命令行**：
```bash
# 1) 多分割 YOLO 结构 (格式一 / 格式二) -> 直接输出各自 JSON
python yolo2coco.py -d path/to/format1_dataset --output_dir output_coco_dir

# 2) 标准结构 / 混合结构 -> 输出单一 COCO 文件
python yolo2coco.py -d path/to/standard_dataset --output_dir coco.json
python yolo2coco.py -d path/to/mixed_dataset --output_dir out_dir          # 将生成 out_dir/annotations.json

# 3) 标准 / 混合结构并需要按比例再划分 (内部调用 coco_dataset_split.py)
python yolo2coco.py -d path/to/standard_dataset --output_dir CocoSplitDir --split \
    --train_ratio 0.8 --val_ratio 0.1 --test_ratio 0.1

# 4) 自定义随机种子 (影响后续分层划分的随机性)
python yolo2coco.py -d path/to/mixed_dataset --output_dir CocoSplitDir --split --seed 2024
```

**参数说明**：
- `-d, --dataset_dir`  数据集根目录 (必填)
- `-o, --output`       输出: 
  - 若输入为格式一/二: 目录, 生成 train.json/val.json/test.json (存在的分割才生成)
  - 若输入为 standard/mixed 且不 `--split`: 
    * 以 .json 结尾 => 直接生成该文件
    * 否则视为目录 => 生成 `目录/annotations.json`
  - 若使用 `--split`: 视为最终划分输出目录
- `--split`            对 standard / mixed 结构执行 COCO 分层划分
- `--train_ratio` `--val_ratio` `--test_ratio`  划分比例 (默认 0.8/0.1/0.1, 需和为1.0)
- `--seed`             随机种子 (传递给划分脚本)

**输出结果**：
- 已分割 YOLO 结构: `output/train.json` 等
- 单文件: `coco.json` 或 `out_dir/annotations.json`
- 分层划分: `CocoSplitDir/train/annotations.json` 等 (由 `coco_dataset_split.py` 生成)

**注意**：
- 旧版本参数 `--root_dir --save_path --random_split --split_by_file` 已废弃
- 若类别文件缺失且标签中出现超出当前类别数的ID，会自动追加占位类别 `class_N`
- `--split` 仅在输入为 standard / mixed 时生效；格式一/二自带分割不再重复划分

**快速验证**：
```bash
python yolo2coco.py -d sample_yolo --output_dir tmp.json
type tmp.json | more   # Windows 查看开头内容
```

## convert_medical_to_yolo.py
医学影像转YOLO格式转换工具

**输出格式**：生成格式二（`dataset/images/train/ + dataset/labels/train/` 等）YOLO数据集

```bash
python convert_medical_to_yolo.py -i 输入图像目录 --output_dir 输出YOLO数据集目录 -m 元数据CSV文件路径
```

## voc2yolo.py
VOC (Pascal VOC XML) 转 YOLO 标注转换工具

**输入目录假定**：
- 默认查找：`输入根/Annotations/*.xml` 与 `输入根/JPEGImages/` 中的同名图片；
- 若结构不同，可用 `--xml-dir` / `--img-dir` 明确指定；
- 也可直接将 `-i` 指向只包含 XML 的目录（会在该目录内搜索 *.xml）。

**输出结构支持**：
- `standard` (默认)：`output/images/ + output/labels/`
- `mixed`：`output/` 根目录下图片与标签混合存放（与仓库内其它脚本的 mixed 概念保持一致）

**类别来源顺序**：
1. 若提供 `--classes-file` (txt 或 yaml) 则优先使用；
2. 否则自动扫描全部 XML 中出现的 `<object><name>` 顺序去重；
3. 输出自动写入 `classes.txt` 或使用 `--save-yaml` 生成 `data.yaml`。

**关键参数**：
```bash
python voc2yolo.py -i VOC_ROOT --output_dir YOLO_OUT
python voc2yolo.py -i VOC_ROOT --output_dir YOLO_OUT --structure mixed
python voc2yolo.py -i VOC_ROOT --output_dir YOLO_OUT --classes-file classes.txt --ignore-difficult
python voc2yolo.py -i VOC_ROOT --output_dir YOLO_OUT --save-yaml --allow-new-classes
```

**常用选项说明**：
- `--structure {standard,mixed}`: 选择输出结构
- `--classes-file`: 预先存在的类别文件 (txt/yaml)
- `--allow-new-classes`: XML 中出现未在类别文件里的新类别时自动追加
- `--ignore-difficult`: 跳过 `difficult=1` 的目标
- `--save-yaml`: 输出 `data.yaml`（包含 `nc` 与 `names`）
- `--no-copy-images`: 只生成标签，不复制图片
- `--image-exts`: 自定义查找图片的扩展（不含点），默认使用内置列表

**功能特点**：
- 🔄 支持 standard / mixed 两种 YOLO 输出结构
- 🔍 自动收集或复用类别定义，支持动态追加
- 🏷️ 保留原文件名，同名图片生成同名 `.txt`
- ⚠️ 统计缺失图片数量（仍生成标签）
- 🧩 兼容 classes.txt / data.yaml 输出
- 🪵 统一日志输出（logs/ 下自动记录）

**注意**：
- VOC 坐标 (xmin,ymin,xmax,ymax) 采用直接归一化转换；若需严格 0.5 像素修正可在后续自定义脚本中再处理。
- 若同名图片不存在，仅报告警告并继续（便于先批量生成标签）。

---

## COCO数据集工具

## coco_dataset_split.py
COCO数据集划分工具

```bash
# 基础划分
python coco_dataset_split.py -i RibFrac-COCO-Full --output_dir RibFrac-COCO-Split

# 自定义比例
python coco_dataset_split.py -i RibFrac-COCO-Full --output_dir RibFrac-COCO-Split \
                             --train_ratio 0.8 --val_ratio 0.1 --test_ratio 0.1

# 自定义随机种子
python coco_dataset_split.py -i RibFrac-COCO-Full --output_dir RibFrac-COCO-Split --seed 42
```

## ribfrac_to_coco.py
RibFrac 3D CT转COCO格式目标检测

```bash
# 基础转换
python ribfrac_to_coco.py -i D:/datasets/ribFrac --output_dir D:/datasets/RibFrac-COCO

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
- **yolo_dataset_analyzer.py**: 支持格式一、格式二、简单(standard)、混合结构
- **yolo_dataset_split.py**: 输入简单结构(images/+labels/ 或混合)可输出格式一或格式二
- **yolo_class_manager.py**: 支持标准结构、格式一、格式二及混合结构
- **yolo_dataset_viewer.py**: 支持格式一、格式二
- **yolo2coco.py**: 支持格式一、格式二、标准(standard)、混合(mixed)，并可选 `--split` 调用 COCO 分层划分

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
- `YYYYMMDD_HHMMSS_脚本名.log`，例如：`20250808_143012_yolo_class_manager.log`

日志内容包含：
- 脚本启动时间与完整命令行
- 运行过程中的所有打印输出
- 错误与异常堆栈（若有）

查看与追踪（Windows PowerShell 示例）：

```powershell
# 查看最新日志文件列表
Get-ChildItem .\logs -File | Sort-Object Name -Descending | Select-Object -First 10

# 查看某个日志文件的末尾 50 行
Get-Content .\logs\20250808_143012_yolo_class_manager.log -Tail 50

# 实时追踪日志（类似 tail -f）
Get-Content .\logs\20250808_150001_yolo_dataset_split.log -Wait
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