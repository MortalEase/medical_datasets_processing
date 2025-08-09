#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""VOC (Pascal VOC XML) -> YOLO 标注转换工具

支持将典型 VOC 目录下的 XML 标注文件转换为 YOLO txt 标注，输出为：
- standard 结构: output/images/, output/labels/
- mixed 结构: output/ 目录下图片与 txt 混合（不再额外分 labels/）

类别来源策略：
1) 优先使用 --classes-file 指定的类别文件 (txt 或 yaml)
2) 未指定时自动扫描全部 XML 中出现的 object/name，按出现顺序去重
3) 默认将生成的类别文件写入 output/classes.txt（或 data.yaml 若使用 --save-yaml）

示例：
    python voc2yolo.py -i VOC_ROOT -o YOLO_OUT
    python voc2yolo.py -i VOC_ROOT -o YOLO_OUT --structure mixed
    python voc2yolo.py -i VOC_ROOT -o YOLO_OUT --classes-file classes.txt --ignore-difficult
    python voc2yolo.py -i VOC_ROOT -o YOLO_OUT --save-yaml --allow-new-classes

注意：脚本会复制图片文件 (常见扩展) 并为每个 XML 生成同名 .txt。未找到匹配图片将发出警告。
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Tuple, Set

from utils.logging_utils import tee_stdout_stderr
from utils.yolo_utils import (
    read_class_names,
    write_class_names,
    get_image_extensions,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="将 VOC XML 标注转换为 YOLO txt 标注 (standard 或 mixed 输出结构)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("-i", "--input", required=True, help="输入 VOC 根目录 (包含 Annotations/ JPEGImages/ 或自定义) 或存放 XML 的目录")
    p.add_argument("-o", "--output", required=True, help="输出 YOLO 数据集根目录")
    p.add_argument("--xml-dir", default=None, help="若 XML 不在 input/Annotations 下，可显式指定")
    p.add_argument("--img-dir", default=None, help="若图片不在 input/JPEGImages 下，可显式指定")
    p.add_argument("--structure", choices=["standard", "mixed"], default="standard", help="输出 YOLO 结构")
    p.add_argument("--classes-file", default=None, help="预先存在的类别文件 (txt 或 yaml)，若提供则以此为准")
    p.add_argument("--allow-new-classes", action="store_true", help="当 XML 中出现 classes-file 里未定义的类别时，自动追加")
    p.add_argument("--ignore-difficult", action="store_true", help="跳过 difficult=1 的目标对象")
    p.add_argument("--save-yaml", action="store_true", help="将输出类别写为 data.yaml (含 names/nc)")
    p.add_argument("--overwrite", action="store_true", help="若输出目录已存在允许继续写入 (不清空)")
    p.add_argument("--image-exts", nargs="*", default=None, help="限定可复制的图片扩展 (不含点). 默认=内置列表")
    p.add_argument("--no-copy-images", action="store_true", help="仅生成 labels，不复制图片 (需自行保证 images/ 可访问)")
    p.add_argument("--verbose", action="store_true", help="打印更多调试信息")
    return p.parse_args()


def collect_xml_files(xml_dir: Path) -> List[Path]:
    xmls = [p for p in xml_dir.iterdir() if p.is_file() and p.suffix.lower() == ".xml"]
    return sorted(xmls)


def parse_voc_xml(path: Path, ignore_difficult: bool) -> Tuple[str, int, int, List[Dict]]:
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception as e:
        raise RuntimeError(f"解析 XML 失败: {path}: {e}")

    def _text(node, name, default="0"):
        el = node.find(name)
        return el.text.strip() if el is not None and el.text else default

    filename = root.findtext("filename", default="")
    size = root.find("size")
    if size is None:
        raise RuntimeError(f"XML 缺少 size 节点: {path}")
    w = int(_text(size, "width", "0"))
    h = int(_text(size, "height", "0"))
    if w <= 0 or h <= 0:
        raise RuntimeError(f"无效的图像尺寸 w={w} h={h} in {path}")

    objects: List[Dict] = []
    for obj in root.findall("object"):
        name = obj.findtext("name")
        if not name:
            continue
        difficult = obj.findtext("difficult", default="0")
        if ignore_difficult and difficult == "1":
            continue
        bnd = obj.find("bndbox")
        if bnd is None:
            continue
        try:
            xmin = float(bnd.findtext("xmin"))
            ymin = float(bnd.findtext("ymin"))
            xmax = float(bnd.findtext("xmax"))
            ymax = float(bnd.findtext("ymax"))
        except Exception:
            continue
        # VOC 坐标通常是 1-based 且包含像素；这里直接采用数值，不做 -1 修正，作为近似。
        # 保证范围在图像内
        xmin = max(0.0, min(xmin, w - 1))
        ymin = max(0.0, min(ymin, h - 1))
        xmax = max(0.0, min(xmax, w - 1))
        ymax = max(0.0, min(ymax, h - 1))
        if xmax <= xmin or ymax <= ymin:
            continue
        objects.append({
            "name": name,
            "bbox": (xmin, ymin, xmax, ymax),
        })
    return filename, w, h, objects


def voc_bbox_to_yolo(xmin: float, ymin: float, xmax: float, ymax: float, w: int, h: int) -> Tuple[float, float, float, float]:
    cx = (xmin + xmax) / 2.0 / w
    cy = (ymin + ymax) / 2.0 / h
    bw = (xmax - xmin) / w
    bh = (ymax - ymin) / h
    return cx, cy, bw, bh


def ensure_output_dirs(base: Path, structure: str, overwrite: bool) -> Tuple[Path, Path]:
    if base.exists() and not overwrite:
        # 如果已有 images/labels 结构且不是覆盖，则允许继续写
        pass
    if structure == "standard":
        (base / "images").mkdir(parents=True, exist_ok=True)
        (base / "labels").mkdir(parents=True, exist_ok=True)
        return base / "images", base / "labels"
    else:  # mixed
        base.mkdir(parents=True, exist_ok=True)
        return base, base  # images 与 labels 在同一路径


def load_or_collect_classes(args: argparse.Namespace, xml_files: List[Path]) -> List[str]:
    classes: List[str] = []
    if args.classes_file:
        classes = read_class_names(args.classes_file)
        if not classes:
            print(f"[WARN] 指定 classes 文件为空或读取失败: {args.classes_file}")
    if not classes:  # 自动收集
        seen: List[str] = []
        seen_set: Set[str] = set()
        for xp in xml_files:
            try:
                _, _, _, objs = parse_voc_xml(xp, args.ignore_difficult)
            except Exception:
                continue
            for o in objs:
                nm = o["name"].strip()
                if nm and nm not in seen_set:
                    seen.append(nm)
                    seen_set.add(nm)
        classes = seen
    return classes


def main():
    args = parse_args()
    tee_stdout_stderr(script_basename=Path(sys.argv[0]).stem)

    in_root = Path(args.input)
    if not in_root.exists():
        print(f"[ERROR] 输入目录不存在: {in_root}")
        sys.exit(1)

    # 推断 XML 与 图片目录
    xml_dir = Path(args.xml_dir) if args.xml_dir else (in_root / "Annotations")
    img_dir = Path(args.img_dir) if args.img_dir else (in_root / "JPEGImages")
    if not xml_dir.exists():
        # 若指定目录不存在，尝试直接把 input 当作 xml 存放目录
        if args.xml_dir:
            print(f"[ERROR] XML 目录不存在: {xml_dir}")
            sys.exit(1)
        else:
            xml_dir = in_root
    if not img_dir.exists():
        # 不强制存在 (可能用户只想要 labels)
        print(f"[WARN] 图片目录不存在: {img_dir}")

    xml_files = collect_xml_files(xml_dir)
    if not xml_files:
        print(f"[ERROR] 未找到任何 XML: {xml_dir}")
        sys.exit(1)
    print(f"发现 XML 标注文件: {len(xml_files)}")

    classes = load_or_collect_classes(args, xml_files)
    if not classes:
        print("[ERROR] 未能获取类别集合 (classes)；请显式提供 --classes-file")
        sys.exit(1)
    print(f"类别数: {len(classes)} -> {classes}")
    cls_to_id = {c: i for i, c in enumerate(classes)}

    out_root = Path(args.output)
    img_out_dir, lbl_out_dir = ensure_output_dirs(out_root, args.structure, args.overwrite)
    print(f"输出结构: {args.structure}; images -> {img_out_dir}; labels -> {lbl_out_dir}")

    image_exts = [e.lower() for e in (args.image_exts if args.image_exts else [x[1:] for x in get_image_extensions()])]
    image_exts = [f".{e}" if not e.startswith('.') else e for e in image_exts]

    copied = 0
    converted = 0
    missing_image = 0
    new_classes: List[str] = []

    for idx, xp in enumerate(xml_files, 1):
        try:
            filename, w, h, objects = parse_voc_xml(xp, args.ignore_difficult)
        except Exception as e:
            print(f"[WARN] 跳过无法解析的 XML: {xp.name}: {e}")
            continue
        stem = Path(filename).stem if filename else xp.stem
        # 查找图片 (同名，不同扩展)
        img_path = None
        if img_dir.exists():
            for ext in image_exts:
                cand = img_dir / f"{stem}{ext}"
                if cand.is_file():
                    img_path = cand
                    break
        if img_path is None:
            missing_image += 1
            if args.verbose:
                print(f"[WARN] 未找到匹配图片: {stem}.* (跳过图片复制，但仍生成标注)")

        yolo_lines: List[str] = []
        for obj in objects:
            name = obj["name"].strip()
            if name not in cls_to_id:
                if args.allow_new_classes:
                    cls_to_id[name] = len(cls_to_id)
                    classes.append(name)
                    new_classes.append(name)
                else:
                    if args.verbose:
                        print(f"[WARN] 未知类别 {name} (未启用 --allow-new-classes), 已跳过")
                    continue
            xmin, ymin, xmax, ymax = obj["bbox"]
            cx, cy, bw, bh = voc_bbox_to_yolo(xmin, ymin, xmax, ymax, w, h)
            yolo_lines.append(f"{cls_to_id[name]} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")

        # 写 label
        lbl_fp = lbl_out_dir / f"{stem}.txt"
        with open(lbl_fp, "w", encoding="utf-8") as f:
            f.write("\n".join(yolo_lines) + ("\n" if yolo_lines else ""))
        converted += 1

        # 复制图片
        if img_path and not args.no_copy_images:
            target_img = img_out_dir / img_path.name
            if not target_img.exists():  # 简单避免重复复制
                try:
                    # 使用二进制复制
                    with open(img_path, "rb") as rf, open(target_img, "wb") as wf:
                        wf.write(rf.read())
                    copied += 1
                except Exception as e:
                    print(f"[WARN] 复制图片失败 {img_path} -> {target_img}: {e}")

        if args.verbose and idx % 100 == 0:
            print(f"进度: {idx}/{len(xml_files)} 已转换 {converted} 个标签")

    # 写类别文件
    cls_out = out_root / ("data.yaml" if args.save_yaml else "classes.txt")
    write_class_names(cls_out, classes)
    print(f"已写入类别文件: {cls_out} (共 {len(classes)} 类)")
    if new_classes:
        uniq_new = sorted(set(new_classes), key=new_classes.index)
        print(f"新增类别 (allow-new-classes): {uniq_new}")

    print("===== 转换完成 =====")
    print(f"XML 数: {len(xml_files)}")
    print(f"生成标签: {converted}")
    print(f"复制图片: {copied}")
    print(f"缺失图片(未复制): {missing_image}")
    print(f"类别数: {len(classes)}")


if __name__ == "__main__":
    main()
