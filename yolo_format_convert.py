#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YOLO 格式重排工具: format1 <-> format2

功能：不修改任何文件内容；支持复制(默认)或移动(--move).
备注：可通过 --to 指定目标结构(1 或 2)，不指定则自动选择相反结构.
"""
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

from utils.logging_utils import tee_stdout_stderr, log_info, log_warn, log_error
from utils.yolo_utils import (
    get_image_extensions,
    list_possible_class_files,
    detect_yolo_structure,
)

_LOG_FILE = tee_stdout_stderr('logs')


SPLITS = ["train", "val", "test"]
CLASS_TXT_NAMES = {"classes.txt", "obj.names", "names.txt"}
CLASS_YAML_NAMES = {"data.yaml", "data.yml", "dataset.yaml", "dataset.yml"}


def detect_splits_format1(root: Path) -> list[str]:
    """返回 format1 下存在的 splits 列表。"""
    found = []
    for sp in SPLITS:
        if (root / sp / 'images').exists() and (root / sp / 'labels').exists():
            found.append(sp)
    return found


def detect_splits_format2(root: Path) -> list[str]:
    """返回 format2 下存在的 splits 列表。"""
    found = []
    for sp in SPLITS:
        if (root / 'images' / sp).exists() and (root / 'labels' / sp).exists():
            found.append(sp)
    return found


def ensure_format2_dirs(out_root: Path, splits: list[str]) -> tuple[Path, Path]:
    """创建 format2 目录结构，返回 (images_root, labels_root)"""
    images_root = out_root / 'images'
    labels_root = out_root / 'labels'
    for sp in splits:
        (images_root / sp).mkdir(parents=True, exist_ok=True)
        (labels_root / sp).mkdir(parents=True, exist_ok=True)
    return images_root, labels_root


def ensure_format1_dirs(out_root: Path, splits: list[str]) -> list[Path]:
    """创建 format1 目录结构，返回每个 split 的根路径列表"""
    roots = []
    for sp in splits:
        sp_root = out_root / sp
        (sp_root / 'images').mkdir(parents=True, exist_ok=True)
        (sp_root / 'labels').mkdir(parents=True, exist_ok=True)
        roots.append(sp_root)
    return roots


def copy_or_move(src: Path, dst: Path, move: bool) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if move:
        shutil.move(str(src), str(dst))
    else:
        shutil.copy2(str(src), str(dst))


def _copy_class_and_config_files(src_dirs: list[Path], out_root: Path) -> None:
    """从若干可能目录拷贝 classes.txt / data.yaml 等到输出根目录(存在则覆盖)"""
    candidates_txt = CLASS_TXT_NAMES
    candidates_yaml = CLASS_YAML_NAMES
    seen = set()
    # 先尝试根目录快捷发现
    for src_base in src_dirs:
        for name in list_possible_class_files(src_base):
            p = src_base / name
            if p.is_file() and name not in seen:
                try:
                    shutil.copy2(str(p), str(out_root / name))
                    log_info(f"复制类别/配置: {name}")
                    seen.add(name)
                except Exception as e:
                    log_warn(f"复制类别/配置失败: {p} -> {out_root/name}: {e}")
    # 再显式扫描常见文件名
    for src_base in src_dirs:
        for name in sorted(candidates_txt | candidates_yaml):
            p = src_base / name
            if name in seen:
                continue
            if p.is_file():
                try:
                    shutil.copy2(str(p), str(out_root / name))
                    log_info(f"复制类别/配置: {name}")
                    seen.add(name)
                except Exception as e:
                    log_warn(f"复制类别/配置失败: {p} -> {out_root/name}: {e}")


def convert_format1_to_format2(in_root: Path, out_root: Path, move: bool = False, overwrite: bool = False) -> None:
    # 安全检查
    if not in_root.exists():
        log_error(f"输入目录不存在: {in_root}")
        return
    if in_root.resolve() == out_root.resolve():
        log_error("不支持在同一目录就地重排，请指定不同的 --output_dir；如确需原地移动，请先指定新的输出后再手动替换。")
        return
    if out_root.exists() and any(out_root.iterdir()) and not overwrite:
        log_error(f"输出目录已存在且非空: {out_root}，若要覆盖，请添加 --overwrite")
        return
    out_root.mkdir(parents=True, exist_ok=True)

    splits = detect_splits_format1(in_root)
    if not splits:
        log_error("未检测到格式一结构 (train/val/test 下含 images 与 labels)。")
        return
    log_info(f"检测到分割集合: {', '.join(splits)}")

    # 创建目标结构
    images_root, labels_root = ensure_format2_dirs(out_root, splits)

    img_exts = set(get_image_extensions())
    copied_imgs = 0
    copied_lbls = 0

    for sp in splits:
        src_img_dir = in_root / sp / 'images'
        src_lbl_dir = in_root / sp / 'labels'
        dst_img_dir = images_root / sp
        dst_lbl_dir = labels_root / sp

        # 图片
        for name in sorted(os.listdir(src_img_dir)):
            p = src_img_dir / name
            if p.is_file() and p.suffix.lower() in img_exts:
                copy_or_move(p, dst_img_dir / name, move)
                copied_imgs += 1

        # 标签（排除类别/配置文件）
        for name in sorted(os.listdir(src_lbl_dir)):
            p = src_lbl_dir / name
            if not p.is_file():
                continue
            if p.suffix.lower() != '.txt':
                continue
            if name in CLASS_TXT_NAMES:
                continue
            copy_or_move(p, dst_lbl_dir / name, move)
            copied_lbls += 1

    # 复制类别/配置文件到输出根目录（若存在）
    src_dirs = [in_root]
    # 也尝试各 split/labels 目录（有些数据集把 classes.txt 放在其中一个 split 下）
    for sp in splits:
        p = in_root / sp / 'labels'
        if p.exists():
            src_dirs.append(p)
    _copy_class_and_config_files(src_dirs, out_root)

    log_info("===== 重排完成 =====")
    log_info(f"图片: {copied_imgs} | 标签: {copied_lbls}")
    log_info(f"输出: {out_root}")


def convert_format2_to_format1(in_root: Path, out_root: Path, move: bool = False, overwrite: bool = False) -> None:
    # 安全检查
    if not in_root.exists():
        log_error(f"输入目录不存在: {in_root}")
        return
    if in_root.resolve() == out_root.resolve():
        log_error("不支持在同一目录就地重排，请指定不同的 --output_dir；如确需原地移动，请先指定新的输出后再手动替换。")
        return
    if out_root.exists() and any(out_root.iterdir()) and not overwrite:
        log_error(f"输出目录已存在且非空: {out_root}，若要覆盖，请添加 --overwrite")
        return
    out_root.mkdir(parents=True, exist_ok=True)

    splits = detect_splits_format2(in_root)
    if not splits:
        log_error("未检测到格式二结构 (images/labels 下含 train/val/test)。")
        return
    log_info(f"检测到分割集合: {', '.join(splits)}")

    # 创建目标结构
    ensure_format1_dirs(out_root, splits)

    img_exts = set(get_image_extensions())
    copied_imgs = 0
    copied_lbls = 0

    for sp in splits:
        src_img_dir = in_root / 'images' / sp
        src_lbl_dir = in_root / 'labels' / sp
        dst_img_dir = out_root / sp / 'images'
        dst_lbl_dir = out_root / sp / 'labels'

        # 图片
        for name in sorted(os.listdir(src_img_dir)):
            p = src_img_dir / name
            if p.is_file() and p.suffix.lower() in img_exts:
                copy_or_move(p, dst_img_dir / name, move)
                copied_imgs += 1

        # 标签（排除类别/配置文件）
        for name in sorted(os.listdir(src_lbl_dir)):
            p = src_lbl_dir / name
            if not p.is_file():
                continue
            if p.suffix.lower() != '.txt':
                continue
            if name in CLASS_TXT_NAMES:
                continue
            copy_or_move(p, dst_lbl_dir / name, move)
            copied_lbls += 1

    # 复制类别/配置文件到输出根目录（若存在）
    src_dirs = [in_root, in_root / 'labels']
    _copy_class_and_config_files(src_dirs, out_root)

    log_info("===== 重排完成 =====")
    log_info(f"图片: {copied_imgs} | 标签: {copied_lbls}")
    log_info(f"输出: {out_root}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="YOLO 格式重排: format1 -> format2 (复制或移动)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument('-d', '--dataset_dir', required=True, help='输入数据集根目录 (格式一或格式二)')
    p.add_argument('-o', '--output_dir', required=True, help='输出数据集根目录 (目标结构)')
    p.add_argument('--to', choices=['1', '2', 'auto'], default='auto', help='目标结构: 1=format1, 2=format2, auto=与输入相反')
    p.add_argument('--move', action='store_true', help='移动文件而非复制 (默认复制)')
    p.add_argument('--overwrite', action='store_true', help='允许写入已存在的非空输出目录')
    return p.parse_args()


def main():
    args = parse_args()
    in_root = Path(args.dataset_dir)
    out_root = Path(args.output_dir)

    log_info("YOLO 格式重排 (format1 <-> format2)")
    log_info(f"输入:  {in_root}")
    log_info(f"输出:  {out_root}")
    log_info(f"模式:  {'移动' if args.move else '复制'}")
    if args.overwrite:
        log_info("覆盖:  已开启 --overwrite")

    # 检测输入结构
    structure, _img, _lbl = detect_yolo_structure(in_root)
    if structure not in ('format1', 'format2'):
        log_error(f"仅支持 format1/format2 互转，检测到结构: {structure}")
        return

    # 解析目标结构
    to = args.to
    if to == 'auto':
        target = 'format2' if structure == 'format1' else 'format1'
    else:
        target = 'format1' if to == '1' else 'format2'

    if structure == target:
        log_error(f"输入已是目标结构: {target}，无需转换")
        log_info("若需复制到新目录，请指定与输入相反的 --to 或使用文件系统复制")
        return

    if structure == 'format1' and target == 'format2':
        convert_format1_to_format2(in_root, out_root, move=args.move, overwrite=args.overwrite)
    elif structure == 'format2' and target == 'format1':
        convert_format2_to_format1(in_root, out_root, move=args.move, overwrite=args.overwrite)


if __name__ == '__main__':
    main()
