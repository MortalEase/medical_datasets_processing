#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YOLO -> COCO 转换脚本

核心: 自动检测 YOLO 4 种结构 (format1/format2/standard/mixed) 并输出 COCO JSON
扩展: 对 standard/mixed 可选 --split 触发二次分层划分 (调用 coco_dataset_split.py)
默认: 未显式指定输出目录时按结构给出合理默认 JSON 存放路径
"""
import os
import cv2
import json
import argparse
import tempfile
import subprocess
from pathlib import Path
from tqdm import tqdm
from utils.logging_utils import tee_stdout_stderr, log_info, log_warn, log_error
_LOG_FILE = tee_stdout_stderr('logs')

IMAGE_EXTS = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp']


def detect_structure(root_dir: str):
    """检测数据集结构类型并返回结构标识与可遍历的 (split, images_dir, labels_dir) 列表。

    返回:
        structure(str): format1 | format2 | standard | mixed | unknown
        paths(list[tuple]): [(split_name, images_dir, labels_dir), ...]
    """
    root = Path(root_dir)

    # ---- 格式一: train/images, train/labels ----
    splits_found = []
    for sp in ['train', 'val', 'test']:
        if (root / sp / 'images').exists() and (root / sp / 'labels').exists():
            splits_found.append(sp)
    if splits_found:
        paths = [(sp, str(root / sp / 'images'), str(root / sp / 'labels')) for sp in splits_found]
        return 'format1', paths

    # ---- 格式二: images/train, labels/train ----
    splits_found = []
    for sp in ['train', 'val', 'test']:
        if (root / 'images' / sp).exists() and (root / 'labels' / sp).exists():
            splits_found.append(sp)
    if splits_found:
        paths = [(sp, str(root / 'images' / sp), str(root / 'labels' / sp)) for sp in splits_found]
        return 'format2', paths

    # ---- 标准结构: images + labels ----
    if (root / 'images').exists() and (root / 'labels').exists():
        return 'standard', [('dataset', str(root / 'images'), str(root / 'labels'))]

    # ---- 混合结构: 根目录下同时包含图片与 txt (非 classes.txt) ----
    has_img = False
    has_txt = False
    for f in root.iterdir():
        if f.is_file():
            suf = f.suffix.lower()
            if suf in IMAGE_EXTS:
                has_img = True
            if suf == '.txt' and f.name not in ['classes.txt', 'obj.names', 'names.txt']:
                has_txt = True
        if has_img and has_txt:
            return 'mixed', [('dataset', str(root), str(root))]

    return 'unknown', []


def load_classes(root_dir: str):
    """尝试加载类别名称(优先 classes.txt)。如果不存在则返回空列表。"""
    for name in ['classes.txt', 'obj.names', 'names.txt']:
        fp = Path(root_dir) / name
        if fp.exists():
            with open(fp, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
    return []


def iter_images(images_dir: str):
    """遍历图片文件名(保持原始顺序/稳定可排序)。"""
    files = [f for f in os.listdir(images_dir) if Path(f).suffix.lower() in IMAGE_EXTS]
    files.sort()
    return files


def build_categories(class_list):
    """根据类别名称列表构造 COCO categories。若列表为空则返回空。"""
    return [{'id': i, 'name': name, 'supercategory': 'object'} for i, name in enumerate(class_list)]


def read_label_file(label_path):
    """读取单个 YOLO 标签文件, 返回每一行的(list[str])。异常返回空。"""
    try:
        with open(label_path, 'r', encoding='utf-8') as f:
            return [ln.strip() for ln in f if ln.strip()]
    except:
        return []


def convert_split(split_name, images_dir, labels_dir, classes):
    """将一个分割(或整个数据集)转换为 COCO dict。"""
    categories = build_categories(classes)
    coco = {
        'info': {'description': f'YOLO->COCO 转换 ({split_name})'},
        'licenses': [],
        'categories': categories,
        'images': [],
        'annotations': []
    }
    class_count = len(categories) if categories else None
    ann_id = 0
    image_files = iter_images(images_dir)
    for img_id, img_name in enumerate(tqdm(image_files, desc=f'转换 {split_name}')):
        img_path = os.path.join(images_dir, img_name)
        img = cv2.imread(img_path)
        if img is None:
            log_warn(f'无法读取图片 {img_path}, 跳过。')
            continue
        h, w = img.shape[:2]
        coco['images'].append({
            'file_name': img_name,
            'id': img_id,
            'width': w,
            'height': h
        })
        # 标签文件路径(混合结构时 labels_dir == images_dir)
        stem = os.path.splitext(img_name)[0]
        label_path = os.path.join(labels_dir, stem + '.txt')
        if not os.path.exists(label_path):
            continue  # 无标签图片仍保留
        lines = read_label_file(label_path)
        for line in lines:
            parts = line.split()
            if len(parts) < 5:
                continue
            try:
                cls_id = int(float(parts[0]))
                if class_count is not None and (cls_id < 0 or cls_id >= class_count):
                    # 若类别索引越界, 仍尝试接受, 自动扩展 categories
                    while cls_id >= len(coco['categories']):
                        new_id = len(coco['categories'])
                        coco['categories'].append({'id': new_id, 'name': f'class_{new_id}', 'supercategory': 'object'})
                x, y, bw, bh = map(float, parts[1:5])
            except Exception:
                continue
            # YOLO (cx,cy,w,h) 归一化 -> COCO (x,y,width,height)
            x1 = (x - bw / 2.0) * w
            y1 = (y - bh / 2.0) * h
            box_w = max(0.0, bw * w)
            box_h = max(0.0, bh * h)
            coco['annotations'].append({
                'id': ann_id,
                'image_id': img_id,
                'category_id': cls_id,
                'bbox': [x1, y1, box_w, box_h],
                'area': box_w * box_h,
                'iscrowd': 0,
                'segmentation': [[x1, y1, x1 + box_w, y1, x1 + box_w, y1 + box_h, x1, y1 + box_h]]
            })
            ann_id += 1
    return coco


def save_coco(coco_dict, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(coco_dict, f, ensure_ascii=False)
    log_info(f'保存: {output_path}')


def maybe_split(temp_dir, output_dir, args):
    """若用户指定 --split, 调用 coco_dataset_split.py 进行再划分。"""
    ratios = [args.train_ratio, args.val_ratio, args.test_ratio]
    if abs(sum(ratios) - 1.0) > 1e-6:
        log_warn('划分比例之和需为1.0，已忽略 split 操作。')
        return
    script = Path(__file__).parent / 'coco_dataset_split.py'
    if not script.exists():
        log_warn('未找到 coco_dataset_split.py，跳过划分。')
        return
    cmd = [
        'python', str(script),
        '-i', str(temp_dir),
        '-o', str(output_dir),
        '--train_ratio', str(args.train_ratio),
        '--val_ratio', str(args.val_ratio),
        '--test_ratio', str(args.test_ratio),
        '--seed', str(args.seed)
    ]
    log_info('调用外部划分脚本: ' + ' '.join(cmd))
    subprocess.run(cmd, check=False)


def parse_args():
    parser = argparse.ArgumentParser(
        description='YOLO 转 COCO 工具 (多结构支持)',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-d', '--dataset_dir', required=True, help='数据集根目录')
    parser.add_argument('-o', '--output_dir', required=False, help='输出路径(可选):\n'
                                                           '  A) 格式一 / 格式二 且未提供 -o: 默认 <dataset_dir>/annotations/<split>.json\n'
                                                           '  B) standard/mixed 未提供 -o 且未使用 --split: 默认 <dataset_dir>/annotations.json\n'
                                                           '  C) standard/mixed 使用 --split: 必须提供 -o 作为最终划分输出目录\n'
                                                           '  若显式提供 -o: 按前述逻辑写入 (目录或单一 .json 文件)。')
    parser.add_argument('--split', action='store_true', help='当输入为标准或混合结构时, 先转换再按比例调用 coco_dataset_split 划分')
    parser.add_argument('--train_ratio', type=float, default=0.8, help='(可选) 划分训练集比例')
    parser.add_argument('--val_ratio', type=float, default=0.1, help='(可选) 划分验证集比例')
    parser.add_argument('--test_ratio', type=float, default=0.1, help='(可选) 划分测试集比例')
    parser.add_argument('--seed', type=int, default=42, help='随机种子(传递给划分脚本)')
    return parser.parse_args()


def main():
    args = parse_args()
    dataset_dir = args.dataset_dir
    if not os.path.exists(dataset_dir):
        log_error(f'数据集目录不存在: {dataset_dir}')
        return

    structure, paths = detect_structure(dataset_dir)
    if structure == 'unknown':
        log_error('无法识别的数据集结构，请确认目录组织。')
        return
    log_info(f'检测到结构: {structure}')

    classes = load_classes(dataset_dir)
    if classes:
        log_info(f'加载类别数: {len(classes)}')
    else:
        log_warn('未找到类别文件，将按标签文件动态扩展类别。')

    output = args.output_dir  # 可能为 None
    # 先检测结构再决定默认输出

    # 结构已带分割(format1/format2) -> 为每个 split 单独生成 JSON
    if structure in ['format1', 'format2']:
        if output is None:
            out_dir = Path(dataset_dir) / 'annotations'
            log_info(f'多分割结构未提供 -o，统一默认写入 {out_dir}/<split>.json')
            out_dir.mkdir(parents=True, exist_ok=True)
            for split_name, img_dir, lbl_dir in paths:
                coco_dict = convert_split(split_name, img_dir, lbl_dir, classes)
                save_coco(coco_dict, str(out_dir / f'{split_name}.json'))
            log_info('转换完成 (格式一/格式二 统一默认路径)。')
            return
        else:
            out_dir = Path(output)
            out_dir.mkdir(parents=True, exist_ok=True)
            for split_name, img_dir, lbl_dir in paths:
                coco_dict = convert_split(split_name, img_dir, lbl_dir, classes)
                save_coco(coco_dict, str(out_dir / f'{split_name}.json'))
            log_info('转换完成 (多分割自定义输出)。')
            return

    # 标准 / 混合 结构
    split_name, img_dir, lbl_dir = paths[0]
    coco_dict = convert_split(split_name, img_dir, lbl_dir, classes)

    if args.split and structure in ['standard', 'mixed']:
        if output is None:
            log_error('standard/mixed 且使用 --split 时必须指定 -o 输出目录。')
            return
        output_path = Path(output)
        # 先输出到临时目录 temp/images + annotations.json, 再调用外部划分
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # 保存 annotations.json
            save_coco(coco_dict, str(tmp_path / 'annotations.json'))
            # 拷贝图片 (COCO 划分脚本需要 images/ 目录)
            images_out = tmp_path / 'images'
            images_out.mkdir(exist_ok=True)
            for f in iter_images(img_dir):
                src = Path(img_dir) / f
                dst = images_out / f
                try:
                    if src != dst:
                        # 复制图片
                        with open(src, 'rb') as fr, open(dst, 'wb') as fw:
                            fw.write(fr.read())
                except Exception as e:
                    log_warn(f'复制图片失败: {src} -> {dst}: {e}')
            # 同时保存 classes.txt (若存在)
            if classes:
                with open(tmp_path / 'classes.txt', 'w', encoding='utf-8') as f:
                    f.write('\n'.join(classes))
            # 调用划分脚本
            maybe_split(tmp_path, output_path, args)
        log_info('转换并划分完成。')
        return

    # 不划分: 输出单一 JSON
    if output is None:
        # 默认输出到数据集根目录 annotations.json
        default_file = Path(dataset_dir) / 'annotations.json'
        log_info(f'未提供 -o，写入默认文件: {default_file}')
        save_coco(coco_dict, str(default_file))
    else:
        output_path = Path(output)
        if output_path.suffix.lower() == '.json':
            save_coco(coco_dict, str(output_path))
        else:
            output_path.mkdir(parents=True, exist_ok=True)
            save_coco(coco_dict, str(output_path / 'annotations.json'))
    log_info('转换完成 (单文件)。')


if __name__ == '__main__':
    main()