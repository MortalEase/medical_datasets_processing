# gynecology-mri 数据集

> **作者/来源**：Yuanyu Anpei, Francesco Zuppichini  
> **机构**：Roboflow 100  
> **发布时间**：2022 年 5 月  
> **数据集地址**：[Roboflow Universe](https://universe.roboflow.com/roboflow-100/gynecology-mri)  
> **GitHub 地址**：[RF100 Github repo](https://github.com/roboflow-ai/roboflow-100-benchmark)  

---

## 一、简介

**gynecology-mri** 是一个用于妇产科MRI影像目标检测的医学影像数据集，属于RF100基准测试项目的一部分。该数据集包含**3类主要检测目标**，通过众包方式完成标注，专注于通过MRI图像进行对象检测以提高妇产科疾病的诊断准确性。

检测类别包括：
- **6W**：6周胎儿
- **7W**：7周胎儿  
- **EH**：子宫内膜增生

标注信息以**边界框（bounding box）**形式提供，支持妇产科MRI影像的自动检测与分析，适用于医学图像分割、目标检测等任务。

---

## 二、数据组成

### 1. **元信息**
| 维度 | 模态 | 任务类型 | 解剖结构 | 解剖区域 | 类别数 | 数据量 | 文件格式 |
|------|------|----------|----------|----------|--------|--------|----------|
| 2D | MRI | 目标检测（Object Detection） | 妇产科 | 子宫、胎儿 | 3 | 1K-10K | JPG |

### 2. **图像尺寸统计**
- **标准尺寸**：`[640, 640]`
- **实际尺寸**：变长，根据原始MRI图像调整
- **颜色模式**：RGB

### 3. **标签信息统计**
| 类别名称 | 类别ID | 描述 |
|----------|--------|------|
| 6W | 1 | 6周胎儿 |
| 7W | 2 | 7周胎儿 |
| EH | 3 | 子宫内膜增生 |

---

## 三、数据可视化

### 1. **边界框标注**
每张图像的标注包含目标区域的**矩形边界框（Bounding Box）**，标注格式为COCO格式，包含：
- 边界框坐标 `[x, y, width, height]`
- 目标类别ID
- 边界框面积
- 标注ID

### 2. **数据示例**
```json
{
  "image_id": 15,
  "image": "<PIL.JpegImagePlugin.JpegImageFile image mode=RGB size=640x640>",
  "width": 964043,
  "height": 640,
  "objects": {
    "id": [114, 115, 116, 117],
    "area": [3796, 1596, 152768, 81002],
    "bbox": [
      [302.0, 109.0, 73.0, 52.0],
      [810.0, 100.0, 57.0, 28.0],
      [160.0, 31.0, 248.0, 616.0],
      [741.0, 68.0, 202.0, 401.0]
    ],
    "category": [4, 4, 0, 0]
  }
}
```

---

## 四、文件结构

### 1. **整体目录结构**
```
gynecology-mri/
├── train/                          # 训练集目录
│   ├── images/                     # 训练图像
│   └── labels/                     # 训练标签 (YOLO格式.txt文件)
├── valid/                          # 验证集目录
│   ├── images/                     # 验证图像
│   └── labels/                     # 验证标签 (YOLO格式.txt文件)
├── test/                           # 测试集目录
│   ├── images/                     # 测试图像
│   └── labels/                     # 测试标签 (YOLO格式.txt文件)
├── classes.txt                     # 类别名称文件 (3个类别)
├── data.yaml                       # YOLO数据集配置文件
```

### 2. **核心文件说明**

#### **配置文件**
- **`classes.txt`**: 包含3种妇产科MRI检测类别：
  ```
  6W
  7W
  EH
  ```
  
- **`data.yaml`**: YOLO数据集配置文件，定义训练/验证/测试路径和类别信息

### 3. **数据特征**
- **图像格式**：PIL.Image.Image对象，RGB模式
- **标注格式**：COCO格式边界框
- **数据规模**：1K-10K图像范围
- **标注质量**：众包标注，精确度89.5%

---

## 五、数据处理与优化

### 1. **数据集特点**
- **专业性强**：专注于妇产科MRI影像分析
- **标注详细**：包含完整的边界框元数据
- **高分辨率**：保持MRI图像的诊断质量
- **标准化格式**：支持主流深度学习框架

### 2. **使用建议**
- **索引访问**：建议使用索引方式访问图像，避免大量解码影响性能
- **数据增强**：考虑旋转、翻转等医学影像适用的增强方法
- **类别平衡**：注意处理类别不平衡问题
- **隐私保护**：遵循医学数据使用的伦理规范

---

## 六、引用与扩展

### 1. **相关资源**
- **Roboflow Universe**：[https://universe.roboflow.com/roboflow-100/gynecology-mri](https://universe.roboflow.com/roboflow-100/gynecology-mri)
- **RF100 Github**：[https://github.com/roboflow-ai/roboflow-100-benchmark](https://github.com/roboflow-ai/roboflow-100-benchmark)

### 2. **推荐引用**
```bibtex
@misc{
gynecology-mri_dataset,
title = { gynecology MRI Dataset },
type = { Open Source Dataset },
author = { Roboflow 100 },
howpublished = { \url{ https://universe.roboflow.com/roboflow-100/gynecology-mri } },
url = { https://universe.roboflow.com/roboflow-100/gynecology-mri },
journal = { Roboflow Universe },
publisher = { Roboflow },
year = { 2023 },
month = { may },
note = { visited on 2025-06-05 },
}
```
