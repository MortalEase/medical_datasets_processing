# FracAtlas 数据集

> **作者/来源**：Imran Abedeen, Md. Ashiqur Rahman, Farzana Zia Prottyasha, Tasnim Ahmed, Tareque Mohmud Chowdhury, Swakkhar Shatabda  
> **机构**：United International University, Bangladesh  
> **发布时间**：2023 年  
> **数据集地址**：[Hugging Face Dataset](https://hf-mirror.com/datasets/yh0701/FracAtlas_dataset)  
> **论文地址**：[Scientific Data - Nature](https://doi.org/10.1038/s41597-023-02432-4)  

---

## 一、简介

**FracAtlas** 是一个用于肌肉骨骼放射影像中骨折检测的医学影像数据集，包含 **4,083 张 X 射线图像**。该数据集由两名专业放射科医师手动标注，后经整形外科医生验证，专门用于骨折区域的目标检测任务。数据集采用YOLO格式进行标注，包含：

- 训练集：2,858 张图像（648 个骨折标注）
- 验证集：816 张图像（159 个骨折标注） 
- 测试集：409 张图像（115 个骨折标注）

标注信息采用YOLO格式提供，专门用于骨折区域的目标检测，适用于医学图像中的骨折自动识别与定位任务。
![数据集标注](./images/FracAtlas_labels.png "数据集标注")

---

## 二、数据组成

### 1. **元信息**
| 维度 | 模态 | 任务类型 | 解剖结构 | 解剖区域 | 类别数 | 数据量 | 文件格式 |
|------|------|----------|----------|----------|--------|--------|----------|
| 2D | X-ray | 目标检测 | 肌肉骨骼 | 手、腿、髋部、肩部 | 1 | 4,083 张 | JPG |

### 2. **图像尺寸统计**
- **格式**：JPG格式
- **来源**：DICOM转换而来，保护患者隐私
> 图像尺寸因原始扫描设备而异，建议预处理时统一调整。

### 3. **标签信息统计**
| 数据集 | 图像数量 | 标注数量 |
|--------|----------|----------|
| 训练集 | 2,858 | 648 |
| 验证集 | 816 | 159 |
| 测试集 | 409 | 115 |
| **总计** | **4,083** | **922** |

> **注意**：数据集中只包含有骨折的图像标注，采用YOLO格式进行边界框标注。

---

## 三、数据可视化

### 1. **YOLO格式标注**
数据集采用YOLO格式进行标注，每张图像对应一个同名的.txt标注文件，包含骨折区域的边界框信息。标注格式为：
```
class_id center_x center_y width height
```
其中所有坐标值都已归一化到[0,1]范围内。

### 2. **原始图像示例**
- **输入图像**：JPG格式的肌肉骨骼 X 光图像
- **标注信息**：YOLO格式的边界框标注，标识骨折区域位置

---

## 四、文件结构

### 1. **整体目录结构**
基于实际的FracAtlas数据集的完整目录结构：

```
FracAtlas/
├── train/                          # 训练集
│   ├── images/                     # 训练图像 (2,858张JPG)
│   └── labels/                     # 训练标注 (648个TXT文件)
├── val/                            # 验证集
│   ├── images/                     # 验证图像 (816张JPG)
│   └── labels/                     # 验证标注 (159个TXT文件)
├── test/                           # 测试集
│   ├── images/                     # 测试图像 (409张JPG)
│   └── labels/                     # 测试标注 (115个TXT文件)
├── classes.txt                     # 类别名称文件
└── data.yaml                      # YOLO配置文件
```

### 2. **核心文件说明**

#### **数据文件**
- **`train/images/`**: 包含2,858张训练用X光图像（JPG格式）
- **`train/labels/`**: 包含648个训练标注文件（TXT格式，YOLO格式）
- **`val/images/`**: 包含816张验证用X光图像（JPG格式）
- **`val/labels/`**: 包含159个验证标注文件（TXT格式，YOLO格式）
- **`test/images/`**: 包含409张测试用X光图像（JPG格式）
- **`test/labels/`**: 包含115个测试标注文件（TXT格式，YOLO格式）

#### **配置文件**
- **`classes.txt`**: 包含类别名称信息：
  ```
  fracture
  ```
- **`data.yaml`**: YOLO训练配置文件，包含数据集路径和类别信息

#### **工具脚本**
- **YOLO训练**: 数据集已按YOLO格式组织，可直接用于YOLOv5/YOLOv8等模型训练
- **数据验证**: 所有图像与标注文件完全对应，无缺失或冗余文件

### 3. **数据量统计**
| 目录 | 图像数量 | 标注文件数量 | 总大小(约) |
|------|----------|--------------|------------|
| train/ | 2,858 | 648 | ~1.2GB |
| val/ | 816 | 159 | ~350MB |
| test/ | 409 | 115 | ~180MB |

### 4. **使用说明**
- **目标检测**: 使用YOLO格式进行骨折区域检测训练
- **数据加载**: 通过`data.yaml`配置文件加载数据集
- **类别信息**: `classes.txt`包含单一类别"fracture"
- **标注格式**: 每个TXT文件包含归一化的边界框坐标

---

## 五、引用与扩展

### 1. **相关资源**
- **Hugging Face Dataset**: [https://hf-mirror.com/datasets/yh0701/FracAtlas_dataset](https://hf-mirror.com/datasets/yh0701/FracAtlas_dataset)
- **Figshare 原始数据**: [https://figshare.com/articles/dataset/FracAtlas/19440050](https://figshare.com/articles/dataset/FracAtlas/19440050)

### 2. **推荐引用**
```bibtex
@article{abedeen2023fracatlas,
  title={FracAtlas: A Dataset for Fracture Classification, Localization and Segmentation of Musculoskeletal Radiographs},
  author={Abedeen, Imran and Rahman, Md. Ashiqur and Prottyasha, Farzana Zia and Ahmed, Tasnim and Chowdhury, Tareque Mohmud and Shatabda, Swakkhar},
  journal={Scientific Data},
  volume={10},
  number={1},
  pages={521},
  year={2023},
  publisher={Nature Publishing Group},
  doi={10.1038/s41597-023-02432-4}
}
```
