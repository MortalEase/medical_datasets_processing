import os
from pathlib import Path
import yaml
from typing import List, Tuple, Iterable

IMG_EXTS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp']
CLASS_FILES = ['classes.txt', 'obj.names', 'names.txt']
YAML_FILES = ['data.yaml', 'data.yml', 'dataset.yaml', 'dataset.yml']


def get_image_extensions() -> List[str]:
    return IMG_EXTS.copy()


def list_possible_class_files(base_dir: str | Path) -> List[str]:
    files = []
    base = Path(base_dir)
    for n in CLASS_FILES + YAML_FILES:
        if (base / n).is_file():
            files.append(n)
    return files


def read_class_names(path: str | Path) -> List[str]:
    path = str(path)
    if path.endswith(('.yaml', '.yml')):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            names = data.get('names')
            if isinstance(names, list):
                return names
            if isinstance(names, dict):
                return [names[i] for i in sorted(names.keys())]
        except Exception:
            return []
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return [ln.strip() for ln in f if ln.strip()]
    except Exception:
        return []


def write_class_names(path: str | Path, names: List[str]) -> None:
    path = str(path)
    if path.endswith(('.yaml', '.yml')):
        try:
            data = {}
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
            data['nc'] = len(names)
            data['names'] = names
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        except Exception:
            pass
        return
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(names) + ('\n' if names else ''))
    except Exception:
        pass


def detect_yolo_structure(base_dir: str | Path) -> Tuple[str, str | None, str | None]:
    base = Path(base_dir)

    # 先检测已分割结构，避免 format2 被误判为 standard
    if (base / 'train' / 'images').exists() and (base / 'train' / 'labels').exists():
        return 'format1', str(base), str(base)

    if (base / 'images' / 'train').exists() and (base / 'labels' / 'train').exists():
        return 'format2', str(base), str(base)

    # 再检测标准结构（未分割）
    if (base / 'images').exists() and (base / 'labels').exists():
        return 'standard', str(base / 'images'), str(base / 'labels')

    try:
        files = list(base.iterdir())
        img = any(p.is_file() and p.suffix.lower() in IMG_EXTS for p in files)
        txt = any(p.is_file() and p.suffix.lower() == '.txt' and p.name not in CLASS_FILES for p in files)
        if img and txt:
            return 'mixed', str(base), str(base)
    except Exception:
        pass
    return 'unknown', None, None


def yolo_label_dirs(base_dir: str | Path, structure: str) -> List[str]:
    base = Path(base_dir)
    res: List[str] = []
    if structure == 'standard':
        p = base / 'labels'
        if p.exists():
            res.append(str(p))
    elif structure == 'format1':
        for sp in ['train', 'val', 'test']:
            p = base / sp / 'labels'
            if p.exists():
                res.append(str(p))
    elif structure == 'format2':
        p = base / 'labels'
        if p.exists():
            for sp in p.iterdir():
                if sp.is_dir():
                    res.append(str(sp))
    elif structure == 'mixed':
        res.append(str(base))
    return res


def iter_label_files(label_dir: str | Path, structure: str) -> Iterable[str]:
    for f in os.listdir(label_dir):
        # 仅遍历 .txt 标签文件，并在任何结构下都跳过类别/配置文件
        if not f.endswith('.txt'):
            continue
        if f in CLASS_FILES or f in YAML_FILES:
            continue
        yield f


def get_folder_size(path: str | Path) -> float:
    total = 0
    try:
        for dirpath, _, filenames in os.walk(path):
            for fn in filenames:
                fp = os.path.join(dirpath, fn)
                if os.path.exists(fp):
                    total += os.path.getsize(fp)
    except Exception:
        pass
    return total / (1024 * 1024)


def discover_class_names(
    base_dir: str | Path,
    structure: str | None = None,
    labels_dir: str | None = None,
) -> Tuple[List[str], str | None]:

    base = Path(base_dir)
    candidates = YAML_FILES + CLASS_FILES

    # 1) 根目录优先
    for n in candidates:
        p = base / n
        if p.is_file():
            names = read_class_names(p)
            if names:
                return names, str(p)

    # 2) labels 目录集合
    label_dirs: List[str] = []
    if labels_dir:
        label_dirs.append(labels_dir)
    else:
        if structure is None:
            structure, _img, _lbl = detect_yolo_structure(base)
        label_dirs = yolo_label_dirs(base, structure) if structure != 'unknown' else []

    for d in label_dirs:
        dp = Path(d)
        for n in candidates:
            p = dp / n
            if p.is_file():
                names = read_class_names(p)
                if names:
                    return names, str(p)

    return [], None
