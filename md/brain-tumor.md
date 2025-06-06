# Brain-Tumor 数据集

> **作者/来源**：Ultralytics 团队  
> **机构**：Ultralytics  
> **发布时间**：2024 年  
> **数据集地址**：[Ultralytics Hub](https://docs.ultralytics.com/datasets/detect/brain-tumor/)  
> **下载地址**：[GitHub Releases](https://github.com/ultralytics/assets/releases/download/v0.0.0/brain-tumor.zip)  

---

## 一、简介

**Brain-Tumor** 是一个专门用于脑肿瘤检测的医学影像数据集，由 Ultralytics 团队整理发布。该数据集包含 **1,116 张脑部医学影像**，专注于脑肿瘤的自动检测和分类任务。

数据集采用 **二分类目标检测** 方法，将脑部区域分为：
- **negative（阴性）**：无肿瘤区域
- **positive（阳性）**：有肿瘤区域

标注信息以 **边界框（bounding box）** 形式提供，支持脑肿瘤的自动检测与定位，适用于医学图像目标检测、辅助诊断等任务。该数据集为研究人员提供了一个标准化的脑肿瘤检测基准数据集。

---

## 二、数据组成

### 1. **元信息**
| 维度 | 模态 | 任务类型 | 解剖结构 | 解剖区域 | 类别数 | 数据量 | 文件格式 |
|------|------|----------|----------|----------|--------|--------|----------|
| 2D | MRI/CT | 目标检测（Object Detection） | 脑部 | 脑部 | 2 | 1,116 张 | JPG |

### 2. **数据集划分**
| 子集 | 图像数量 | 标签文件数量 | 总标注数量 |
|------|----------|--------------|------------|
| train | 893 | 878 | 925 |
| valid | 223 | 223 | 241 |
| test | - | - | - |
| **总计** | **1,116** | **1,101** | **1,166** |

> **说明**：训练集中有 15 张图像无标注（纯阴性样本），验证集所有图像均有标注。

### 3. **标签信息统计**
| 类别名称 | 训练集数量 | 验证集数量 | 总数量 | 占比 |
|----------|------------|------------|--------|------|
| negative（阴性） | 437 | 154 | 591 | 50.69% |
| positive（阳性） | 488 | 87 | 575 | 49.31% |
| **总计** | **925** | **241** | **1,166** | **100%** |

> **注意**：数据集在阴性和阳性样本之间保持了良好的平衡，阴性样本略多于阳性样本，有利于模型的稳定训练。

---

## 三、数据可视化

### 1. **边界框标注**
每张图像的标注包含脑肿瘤区域的 **矩形边界框（Bounding Box）**，标注文件格式为 YOLO 格式的 `.txt` 文件，每行包含：
```
<class_id> <x_center> <y_center> <width> <height>
```
其中：
- `class_id`: 0 表示 negative，1 表示 positive
- 坐标和尺寸均为相对于图像尺寸的归一化值

### 2. **图像特点**
- **输入图像**：脑部医学影像（MRI/CT扫描）
- **图像格式**：JPG 格式
- **标注精度**：专业医学标注，确保诊断准确性

---

## 四、文件结构

### 1. **整体目录结构**
基于 Ultralytics 标准的 YOLO 格式数据集目录结构：

```
brain-tumor/
├── train/                          # 训练集目录
│   ├── images/                     # 训练图像 (893张JPG)
│   └── labels/                     # 训练标签 (878个YOLO格式.txt文件)
├── valid/                          # 验证集目录
│   ├── images/                     # 验证图像 (223张JPG)
│   └── labels/                     # 验证标签 (223个YOLO格式.txt文件)
├── data.yaml                       # YOLO数据集配置文件
└── LICENSE.txt                     # 许可证文件
```

### 2. **核心文件说明**

#### **数据文件**
- **`train/images/`**: 包含 893 张训练用脑部医学影像（JPG格式）
- **`train/labels/`**: 对应的 YOLO 格式标注文件，878 个 .txt 文件包含边界框坐标和类别信息
- **`valid/images/`**: 包含 223 张验证用脑部医学影像
- **`valid/labels/`**: 验证集对应的 YOLO 格式标注文件，223 个 .txt 文件

#### **配置文件**
- **`data.yaml`**: YOLO 数据集配置文件，定义训练/验证路径和类别信息：
  ```yaml
  path: ../datasets/brain-tumor
  train: train/images
  val: valid/images
  test: 
  names:
    0: negative
    1: positive
  ```

- **`LICENSE.txt`**: 数据集许可证文件（AGPL-3.0）

### 3. **数据量统计**
| 目录 | 图像数量 | 标签文件数量 | 特殊说明 |
|------|----------|--------------|----------|
| train/images/ | 893 | - | - |
| train/labels/ | - | 878 | 15张图像无标注（纯阴性） |
| valid/images/ | 223 | - | - |
| valid/labels/ | - | 223 | 所有图像均有标注 |

### 4. **使用说明**
- **训练**: 使用 `train/` 目录进行模型训练
- **验证**: 使用 `valid/` 目录进行模型验证
- **配置**: `data.yaml` 可直接用于 YOLOv5/v8/v11 训练
- **命令示例**: `yolo train data=brain-tumor.yaml model=yolov8n.pt epochs=100`

---

## 五、数据处理与优化

### 1. **数据集特点**
- **高质量标注**：专业医学标注，确保诊断准确性
- **类别平衡**：阴性和阳性样本比例接近 1:1，有利于模型训练
- **标准格式**：采用 YOLO 标准格式，兼容主流深度学习框架

### 2. **适用场景**
- **医学影像分析**：脑肿瘤自动检测和定位
- **辅助诊断**：为医生提供初步筛查建议
- **研究基准**：用于脑肿瘤检测算法的性能评估
- **教育培训**：医学图像分析相关课程和研究

### 3. **推荐预处理**
- **图像归一化**：统一图像像素值范围
- **数据增强**：旋转、翻转、缩放等增强技术
- **尺寸统一**：建议调整到 640x640 像素进行训练

---

## 六、引用与扩展

### 1. **相关资源**
- **官方文档**：[https://docs.ultralytics.com/datasets/detect/brain-tumor/](https://docs.ultralytics.com/datasets/detect/brain-tumor/)
- **Ultralytics GitHub**：[https://github.com/ultralytics/ultralytics](https://github.com/ultralytics/ultralytics)
- **下载链接**：[https://github.com/ultralytics/assets/releases/download/v0.0.0/brain-tumor.zip](https://github.com/ultralytics/assets/releases/download/v0.0.0/brain-tumor.zip)

### 2. **许可证**
该数据集采用 **AGPL-3.0 许可证**，使用时请遵守相关许可证条款。

### 3. **推荐引用**
```bibtex
@misc{ultralytics_brain_tumor,
  title={Brain-Tumor Dataset},
  author={Ultralytics},
  year={2024},
  howpublished={\\url{https://docs.ultralytics.com/datasets/detect/brain-tumor/}},
  note={Accessed: 2024}
}
```

### 4. **扩展应用**
- 结合其他脑部疾病数据集进行多任务学习
- 应用于实时脑肿瘤检测系统开发
- 用于医学图像分割任务的预训练
- 开发移动端脑肿瘤检测应用
