# RibFrac 数据集

> **作者/来源**：Shanghai Jiao Tong University & Huadong Hospital  
> **机构**：上海交通大学、复旦大学附属华东医院  
> **发布时间**：2020年6月  
> **数据集地址**：[RibFrac官方](https://ribfrac.grand-challenge.org/)  
> **任务类型**：肋骨骨折检测与分类挑战赛  

---

## 一、简介

**RibFrac 2020** 是一个大规模的CT图像肋骨骨折检测与分类数据集，来源于RibFrac挑战赛。该数据集包含**660张CT图像的约5000个肋骨骨折**，专注于肋骨骨折的检测、分割与分类。

检测类别：
- **Buckle**：塌陷性骨折/凹陷性骨折（Buckle fracture）
- **Nondisplaced**：非移位骨折（Nondisplaced fracture）
- **Displaced**：移位骨折（Displaced fracture）
- **Segmental**：节段性骨折/多节段骨折（Segmental fracture）

标注信息以**像素级掩模（segmentation mask）**形式提供，采用NIfTI格式存储，支持肋骨骨折自动检测与诊断辅助系统的开发，适用于医学图像实例分割、计算机辅助诊断等任务。

---

## 二、数据组成

### 1. **元信息**
| 维度 | 模态 | 任务类型 | 解剖结构 | 解剖区域 | 类别数 | 数据量 | 文件格式 |
|------|------|----------|----------|----------|--------|--------|----------|
| 3D | CT | 检测;分类 | 肋骨骨折 | 胸部 | 4 | 660 | .nii.gz |

### 2. **图像尺寸统计**
- **Spacing范围**：(0.56, 0.56, 0.63) - (0.98, 0.98, 1.5) mm
- **Spacing中值**：(0.74, 0.74, 1.25) mm
- **尺寸范围**：(512, 512, 74) - (512, 512, 721) 像素
- **尺寸中值**：(512, 512, 357) 像素
- **颜色模式**：单通道灰度
- **总二维切片数**：180,547

### 3. **标签信息统计**
| 类别名称 | 类别ID | 描述 | 标注数量 | 受影响患者数 |
|----------|--------|------|----------|-------------|
| Buckle | 1 | 塌陷性骨折/凹陷性骨折 | 687 | 270 |
| Nondisplaced | 2 | 非移位骨折 | 630 | 246 |
| Displaced | 3 | 移位骨折 | 321 | 152 |
| Segmental | 4 | 节段性骨折/多节段骨折 | 209 | 76 |
| Undefined | -1 | 无法明确定型的肋骨骨折 | 2575 | 431 |

### 4. **数据分布**

#### **原始NIfTI格式分布**
| 数据集 | CT图像数 | 有标注图像 | 无标注图像 | 标注数量 | 平均每图标注 |
|--------|----------|-----------|-----------|----------|-------------|
| 训练集 (train) | 420 | 420 | 0 | 4422 | 10.53 |
| 验证集 (val) | 80 | 60 | 20 | 578 | 7.23 |
| 评估集 (eval) | 160 | - | - | - | - |
| **总计** | **660** | **480** | **20** | **5000** | **10.42** |

#### **转换后COCO格式分布（建议8:1:1划分）**
| 数据集 | 图像数量 | 有标注图像 | 无标注图像 | 标注数量 | 平均每图标注 |
|--------|----------|-----------|-----------|----------|-------------|
| 训练集 (train) | 384 | 384 | 0 | 3770 | 9.82 |
| 验证集 (val) | 48 | 48 | 0 | 471 | 9.81 |
| 测试集 (test) | 48 | 48 | 0 | 181 | 3.77 |
| **总计** | **480** | **480** | **0** | **4422** | **9.21** |

> **注意事项**：
> - 原始评估集仅提供图像，无标注信息
> - COCO格式转换需要将3D体积分割转换为2D边界框
> - 建议仅使用有标注的480张CT图像进行转换
> - 类别分布不均匀，建议使用分层抽样

---

## 三、数据可视化

### 1. **分割掩模标注**
每张CT图像的标注包含肋骨骨折区域的**像素级分割掩模（Segmentation Mask）**，标注格式为NIfTI格式，包含：
- 3D体素级分割标注
- 骨折类型标签（1-4，-1）
- 患者信息和病例ID
- 解剖结构信息

### 2. **标注特征统计**
- **骨折分布**：主要集中在4种明确类型
- **患者覆盖**：涉及431名患者的肋骨骨折
- **标注密度**：平均每个CT包含10+个骨折标注
- **解剖覆盖**：完整的胸部肋骨区域

---

## 四、文件结构

### 1. **原始NIfTI格式目录结构**
```
RibFrac/
├── ribfrac-train-images/              # 训练图像目录
│   ├── RibFrac1-image.nii.gz         # 420张训练CT图像
│   ├── RibFrac2-image.nii.gz
│   └── ...
├── ribfrac-train-labels/              # 训练标签目录
│   ├── RibFrac1-label.nii.gz         # 对应分割标签
│   ├── RibFrac2-label.nii.gz
│   └── ...
├── ribfrac-train-info.csv            # 训练集信息文件
├── ribfrac-val-images/               # 验证图像目录
│   ├── RibFrac421-image.nii.gz      # 80张验证CT图像
│   ├── RibFrac422-image.nii.gz
│   └── ...
├── ribfrac-val-labels/               # 验证标签目录
│   ├── RibFrac421-label.nii.gz      # 对应分割标签
│   ├── RibFrac422-label.nii.gz
│   └── ...
└── ribfrac-val-info.csv             # 验证集信息文件
```

### 2. **转换后COCO格式目录结构**
```
RibFrac-COCO/
├── train/                            # 训练集 (384张CT, 80%)
│   ├── images/                       # 训练图像（2D切片）
│   │   ├── RibFrac1_slice_001.jpg
│   │   ├── RibFrac1_slice_002.jpg
│   │   └── ...
│   └── annotations.json              # COCO格式标注
├── val/                              # 验证集 (48张CT, 10%)
│   ├── images/                       # 验证图像
│   └── annotations.json              # COCO格式标注
├── test/                             # 测试集 (48张CT, 10%)
│   ├── images/                       # 测试图像
│   └── annotations.json              # COCO格式标注
├── classes.txt                       # 类别文件
└── dataset_info.json                 # 数据集元信息
```

> **数据集转换说明**：
> - 3D CT图像需要转换为2D切片用于COCO格式
> - 3D分割掩模需要转换为2D边界框
> - 转换过程需要保持骨折类型标签信息
> - 建议按患者级别进行数据划分以避免数据泄露

### 3. **核心文件说明**

#### **NIfTI格式文件（原始）**
- **`ribfrac-train-info.csv`**: 训练集信息文件
  - 包含420张CT的患者信息
  - 骨折类型和位置信息
  - 解剖结构详细描述
  
- **`ribfrac-val-info.csv`**: 验证集信息文件
  - 包含80张CT的患者信息
  - 其中20张为正常CT（无骨折）

#### **COCO格式文件（转换后）**
- **`annotations.json`**: COCO格式标注文件
  ```json
  {
    "categories": [
      {"id": 1, "name": "Buckle", "supercategory": "fracture"},
      {"id": 2, "name": "Nondisplaced", "supercategory": "fracture"},
      {"id": 3, "name": "Displaced", "supercategory": "fracture"},
      {"id": 4, "name": "Segmental", "supercategory": "fracture"}
    ]
  }
  ```

- **`classes.txt`**: 类别文件
  ```
  Buckle
  Nondisplaced
  Displaced
  Segmental
  ```

- **边界框格式**: 从3D分割掩模提取的2D边界框
  ```json
  {
    "id": 1,
    "image_id": 1,
    "category_id": 1,
    "bbox": [x, y, width, height],  # 绝对坐标
    "area": 12345.0,
    "iscrowd": 0
  }
  ```

#### **图像文件**
- **原始格式**: 660张3D CT图像（.nii.gz格式）
- **COCO格式**: 转换为2D切片图像（.jpg/.png格式）

### 4. **标注格式说明**

#### **NIfTI格式（原始）**
```python
# 3D分割掩模，每个体素值代表类别
# 0: 背景
# 1: 塌陷性骨折
# 2: 非移位骨折  
# 3: 移位骨折
# 4: 节段性骨折
# -1: 无法明确定型的骨折
```

#### **COCO格式（转换后）**
```json
{
    "categories": [
        {"id": 1, "name": "Buckle", "supercategory": "fracture"},
        {"id": 2, "name": "Nondisplaced", "supercategory": "fracture"},
        {"id": 3, "name": "Displaced", "supercategory": "fracture"},
        {"id": 4, "name": "Segmental", "supercategory": "fracture"}
    ],
    "images": [
        {
            "file_name": "RibFrac1_slice_001.jpg",
            "height": 512,
            "width": 512,
            "id": 1,
            "patient_id": "RibFrac1",
            "slice_index": 1
        }
    ],
    "annotations": [
        {
            "id": 1,
            "image_id": 1,
            "category_id": 1,
            "iscrowd": 0,
            "area": 2156.8,
            "bbox": [x, y, width, height],  # 绝对坐标
            "segmentation": []  # 可选：多边形分割
        }
    ]
}
```

**转换流程**：
1. **3D切片提取**：将3D CT图像按轴向切片提取为2D图像
2. **掩模转边界框**：从3D分割掩模提取每个切片的2D边界框
3. **类别映射**：保持原始类别标签（1-4）
4. **坐标转换**：确保边界框坐标正确对应2D切片

---

## 五、数据处理与优化

### 1. **数据集特点**
- **高分辨率**：保持CT图像的诊断质量
- **3D结构**：完整的胸部CT体积数据
- **专业标注**：由放射科专业人员完成像素级标注
- **多类别**：涵盖4种主要肋骨骨折类型
- **临床相关**：反映真实临床骨折分布

### 2. **使用建议**

#### **格式选择**
- **NIfTI格式**：适用于3D分割和体积分析
- **COCO格式**：适用于2D检测模型训练
- **数据划分**：建议按患者级别划分避免数据泄露

#### **数据预处理**
- **窗宽窗位**：使用骨窗（窗宽: 1500-2000 HU, 窗位: 300-500 HU）
- **重采样**：标准化体素间距为1mm×1mm×1mm
- **切片提取**：提取包含骨折的有效切片
- **数据增强**：旋转、翻转、缩放、弹性变形

#### **模型训练策略**
- **3D分割模型**：
  ```python
  # 使用3D U-Net等模型直接处理原始NIfTI数据
  model = UNet3D(in_channels=1, out_channels=5)  # 4类+背景
  ```
- **2D检测模型**：
  ```python
  # 使用转换后的COCO格式训练检测模型
  python train.py --data RibFrac-COCO/annotations.json --epochs 100
  ```
- **损失函数**：使用focal loss处理类别不平衡
- **多尺度训练**：处理不同大小的骨折
- **集成学习**：结合3D和2D模型提高性能

#### **评估与验证**
- **关键指标**：
  - Sensitivity（敏感性）：检测召回率，临床关键指标
  - PPV（阳性预测值）：精确率，控制假阳性
  - F1-Score：平衡精确率和召回率
  - FROC曲线：医学影像检测标准评估
- **数据集使用**：
  - 训练集：用于模型训练和参数优化
  - 验证集：用于超参数调优和模型选择
  - 测试集：用于最终性能评估

---

## 六、应用场景

### 1. **临床应用**
- **急诊诊断**：快速识别肋骨骨折，辅助急诊医师诊断
- **创伤评估**：全面评估胸部创伤严重程度
- **法医鉴定**：为法医学提供客观的骨折检测工具
- **保险理赔**：为保险索赔提供影像学依据

### 2. **研究应用**
- **算法开发**：开发新的3D医学图像分割算法
- **基准测试**：作为肋骨骨折检测模型的标准基准
- **多模态研究**：结合X线、CT等多模态影像
- **临床验证**：验证AI系统在实际临床环境中的表现

### 3. **技术挑战**
- **3D-2D转换**：在保持信息完整性的同时进行维度转换
- **类别不平衡**：处理不同骨折类型的样本不均衡问题
- **小目标检测**：准确检测相对较小的骨折区域
- **解剖变异**：处理不同患者的解剖结构差异

---

## 七、相关研究与扩展

### 1. **相关数据集**
- **LUNA16**：肺结节检测数据集
- **LiTS**：肝脏肿瘤分割数据集
- **KiTS19**：肾脏肿瘤分割数据集
- **VerSe**：脊椎分割数据集

### 2. **技术发展方向**
- **3D深度学习**：直接处理3D体积数据的深度学习模型
- **弱监督学习**：减少对精确像素级标注的依赖
- **多任务学习**：同时进行检测、分割和分类
- **联邦学习**：在保护隐私的前提下利用多中心数据

### 3. **评估标准**
- **FROC分析**：Free-Response Operating Characteristic
- **DSC系数**：Dice Similarity Coefficient（分割任务）
- **敏感性分析**：不同骨折类型的检测敏感性
- **临床一致性**：与放射科医师诊断的一致性评估

---

## 八、引用与参考

### 1. **数据集引用**
```bibtex
@article{ribfracchallenge2024,
    title={Deep Rib Fracture Instance Segmentation and Classification from CT on the RibFrac Challenge},
    author={Yang, Jiancheng and Shi, Rui and Jin, Liang and Huang, Xiaoyang and Kuang, Kaiming and Wei, Donglai and Gu, Shixuan and Liu, Jianying and Liu, Pengfei and Chai, Zhizhong and Xiao, Yongjie and Chen, Hao and Xu, Liming and Du, Bang and Yan, Xiangyi and Tang, Hao and Alessio, Adam and Holste, Gregory and Zhang, Jiapeng and Wang, Xiaoming and He, Jianye and Che, Lixuan and Pfister, Hanspeter and Li, Ming and Ni, Bingbing},
    journal={arXiv Preprint},
    year={2024}
}

@article{ribfracclinical2020,
    title={Deep-Learning-Assisted Detection and Segmentation of Rib Fractures from CT Scans: Development and Validation of FracNet},
    author={Jin, Liang and Yang, Jiancheng and Kuang, Kaiming and Ni, Bingbing and Gao, Yiyi and Sun, Yingli and Gao, Pan and Ma, Weiling and Tan, Mingyu and Kang, Hui and Chen, Jiajun and Li, Ming},
    journal={eBioMedicine},
    year={2020},
    publisher={Elsevier}
}
```

### 2. **相关资源**
- **官方网站**：[https://ribfrac.grand-challenge.org/](https://ribfrac.grand-challenge.org/)
- **论文地址**：[https://arxiv.org/pdf/2402.09372.pdf](https://arxiv.org/pdf/2402.09372.pdf)
- **下载链接**：[https://ribfrac.grand-challenge.org/dataset/](https://ribfrac.grand-challenge.org/dataset/)
- **COCO格式文档**：[https://cocodataset.org/](https://cocodataset.org/)

---

## 九、使用许可与声明

本数据集用于学术研究和教育目的。使用时请：
- 遵循医学数据使用的伦理规范
- 尊重患者隐私和数据安全
- 引用原始数据来源和相关论文
- 遵循RibFrac挑战赛的使用条款
- 不得将数据用于商业用途（如有需要请联系原作者）
