import os
import shutil
import argparse
from collections import defaultdict
from datetime import datetime
from utils.logging_utils import tee_stdout_stderr
_LOG_FILE = tee_stdout_stderr('logs')
from utils.yolo_utils import (
    detect_yolo_structure,
    yolo_label_dirs,
    iter_label_files,
    list_possible_class_files,
    read_class_names,
    write_class_names,
    get_folder_size,
)




def analyze_dataset_classes(base_dir):
    """分析数据集中的类别使用情况"""
    structure, _, _ = detect_yolo_structure(base_dir)
    
    if structure == 'unknown':
        print("❌ 错误: 未找到有效的数据集结构")
        return None, None
    
    print(f"📁 检测到数据集结构: {structure}")
    
    # 获取所有标签目录
    label_dirs = yolo_label_dirs(base_dir, structure)
    
    # 统计类别使用情况
    class_usage = defaultdict(int)  # {class_id: count}
    total_annotations = 0
    
    for labels_dir in label_dirs:
        for label_file in iter_label_files(labels_dir, structure):
            label_path = os.path.join(labels_dir, label_file)
            try:
                with open(label_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            class_id = int(line.split()[0])
                            class_usage[class_id] += 1
                            total_annotations += 1
            except Exception as e:
                print(f"警告: 无法读取标签文件 {label_path}: {e}")
    
    # 查找类别文件
    class_files = list_possible_class_files(base_dir)
    class_names = []
    
    if class_files:
        class_file_path = os.path.join(base_dir, class_files[0])
        class_names = read_class_names(class_file_path)
        print(f"📋 找到类别文件: {class_files[0]}")
    
    return class_usage, class_names


def delete_classes(base_dir, class_ids_to_delete, backup=True):
    """删除指定的类别"""
    print(f"\n开始删除类别: {class_ids_to_delete}")
    
    # 分析当前数据集
    class_usage, class_names = analyze_dataset_classes(base_dir)
    if class_usage is None:
        return False
    
    # 验证要删除的类别是否在类别文件中定义
    all_defined_classes = set(range(len(class_names))) if class_names else set()
    used_classes = set(class_usage.keys())
    
    # 检查要删除的类别是否在定义范围内
    invalid_classes = set(class_ids_to_delete) - all_defined_classes
    if invalid_classes:
        print(f"错误: 以下类别超出定义范围 (0-{len(class_names)-1}): {invalid_classes}")
        return False
    
    # 分类：已使用的类别和未使用的类别
    used_classes_to_delete = set(class_ids_to_delete) & used_classes
    unused_classes_to_delete = set(class_ids_to_delete) - used_classes
    
    print(f"要删除的已使用类别: {used_classes_to_delete}")
    print(f"要删除的未使用类别: {unused_classes_to_delete}")
    
    if not class_ids_to_delete:
        print("没有有效的类别需要删除")
        return False
    
    # 创建备份
    if backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"{base_dir}_backup_before_delete_{timestamp}"
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        shutil.copytree(base_dir, backup_dir)
        print(f"✓ 已创建备份: {backup_dir}")
    
    structure, _, _ = detect_yolo_structure(base_dir)
    label_dirs = yolo_label_dirs(base_dir, structure)
    
    # 所有要删除的类别
    all_classes_to_delete = set(class_ids_to_delete)
    
    # 创建类别映射 (删除后重新编号)
    remaining_classes = sorted([c for c in used_classes if c not in all_classes_to_delete])
    class_mapping = {old_id: new_id for new_id, old_id in enumerate(remaining_classes)}
    
    deleted_annotations = 0
    updated_files = 0
    
    # 处理每个标签目录 (只处理已使用的类别)
    for labels_dir in label_dirs:
        for label_file in iter_label_files(labels_dir, structure):
            label_path = os.path.join(labels_dir, label_file)
            updated_lines = []
            file_changed = False
            
            try:
                with open(label_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            parts = line.split()
                            class_id = int(parts[0])
                            
                            if class_id in all_classes_to_delete:
                                # 删除这个标注
                                deleted_annotations += 1
                                file_changed = True
                            else:
                                # 重新映射类别ID
                                new_class_id = class_mapping[class_id]
                                parts[0] = str(new_class_id)
                                updated_lines.append(' '.join(parts))
                                if new_class_id != class_id:
                                    file_changed = True
                
                if file_changed:
                    with open(label_path, 'w') as f:
                        for line in updated_lines:
                            f.write(line + '\n')
                    updated_files += 1
                    
            except Exception as e:
                print(f"错误: 无法处理标签文件 {label_path}: {e}")
    
    # 更新类别文件 (删除所有指定的类别，包括未使用的)
    class_files = list_possible_class_files(base_dir)
    if class_files and class_names:
        # 创建新的类别名称列表，排除所有要删除的类别
        remaining_class_indices = [i for i in range(len(class_names)) if i not in all_classes_to_delete]
        updated_class_names = [class_names[i] for i in remaining_class_indices]
        
        for class_file in class_files:
            class_file_path = os.path.join(base_dir, class_file)
            write_class_names(class_file_path, updated_class_names)
            print(f"✓ 已更新类别文件: {class_file}")
    
    print(f"\n删除操作完成:")
    print(f"删除的类别: {all_classes_to_delete}")
    print(f"删除的标注数量: {deleted_annotations}")
    print(f"更新的文件数量: {updated_files}")
    print(f"剩余类别数量: {len(class_names) - len(all_classes_to_delete) if class_names else 0}")
    
    return True


def rename_classes(base_dir, class_renames, backup=True):
    """重命名类别 (只更新类别文件中的名称，不改变标签文件中的ID)"""
    print(f"\n开始重命名类别: {class_renames}")
    
    # 查找类别文件
    class_files = list_possible_class_files(base_dir)
    if not class_files:
        print("错误: 未找到类别文件")
        return False
    
    # 创建备份
    if backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"{base_dir}_backup_before_rename_{timestamp}"
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        shutil.copytree(base_dir, backup_dir)
        print(f"✓ 已创建备份: {backup_dir}")
    
    # 读取现有类别名称
    class_file_path = os.path.join(base_dir, class_files[0])
    class_names = read_class_names(class_file_path)
    
    if not class_names:
        print("错误: 无法读取类别名称")
        return False
    
    print(f"原始类别: {class_names}")
    
    # 应用重命名
    updated_class_names = class_names.copy()
    for old_name, new_name in class_renames.items():
        if old_name in updated_class_names:
            index = updated_class_names.index(old_name)
            updated_class_names[index] = new_name
            print(f"✓ 重命名: {old_name} -> {new_name}")
        else:
            print(f"警告: 类别 '{old_name}' 不存在")
    
    # 更新所有类别文件
    for class_file in class_files:
        class_file_path = os.path.join(base_dir, class_file)
        write_class_names(class_file_path, updated_class_names)
        print(f"✓ 已更新类别文件: {class_file}")
    
    print(f"更新后类别: {updated_class_names}")
    print("重命名操作完成!")
    
    return True


def cleanup_backups(base_dir, keep_count=5, dry_run=False):
    """清理旧的备份文件夹"""
    import glob
    import re
    
    print(f"\n🧹 清理备份文件夹...")
    
    # 查找所有备份文件夹
    backup_pattern = f"{base_dir}_backup_*"
    backup_dirs = glob.glob(backup_pattern)
    
    if not backup_dirs:
        print("未找到任何备份文件夹")
        return
    
    # 按时间戳排序（提取时间戳部分）
    def extract_timestamp(path):
        # 匹配时间戳格式 YYYYMMDD_HHMMSS
        match = re.search(r'_(\d{8}_\d{6})$', path)
        return match.group(1) if match else '00000000_000000'
    
    backup_dirs.sort(key=extract_timestamp, reverse=True)
    
    print(f"找到 {len(backup_dirs)} 个备份文件夹:")
    for i, backup_dir in enumerate(backup_dirs):
        timestamp = extract_timestamp(backup_dir)
    size = get_folder_size(backup_dir)
    status = "保留" if i < keep_count else "删除"
    print(f"  {i+1}. {os.path.basename(backup_dir)} (时间: {timestamp}, 大小: {size:.1f}MB) - {status}")
    
    # 删除超出保留数量的备份
    to_delete = backup_dirs[keep_count:]
    
    if not to_delete:
        print(f"✓ 所有备份都在保留范围内 (保留最新 {keep_count} 个)")
        return
    
    if dry_run:
        print(f"\n[演习模式] 将要删除 {len(to_delete)} 个旧备份:")
        for backup_dir in to_delete:
            print(f"  - {backup_dir}")
        print("使用 --execute 参数执行实际删除")
        return
    
    print(f"\n开始删除 {len(to_delete)} 个旧备份...")
    deleted_count = 0
    total_size_freed = 0
    
    for backup_dir in to_delete:
        try:
            size = get_folder_size(backup_dir)
            shutil.rmtree(backup_dir)
            print(f"✓ 已删除: {backup_dir}")
            deleted_count += 1
            total_size_freed += size
        except Exception as e:
            print(f"✗ 删除失败: {backup_dir} - {e}")
    
    print(f"\n清理完成:")
    print(f"删除了 {deleted_count} 个备份文件夹")
    print(f"释放空间: {total_size_freed:.1f}MB")
    print(f"保留最新 {len(backup_dirs) - deleted_count} 个备份")


def show_dataset_info(base_dir):
    """显示数据集信息"""
    print(f"\n📊 数据集信息分析: {base_dir}")
    print("=" * 50)
    
    # 分析数据集
    class_usage, class_names = analyze_dataset_classes(base_dir)
    if class_usage is None:
        return
    
    # 显示类别信息
    print(f"📋 类别定义 (共 {len(class_names)} 个):")
    for i, name in enumerate(class_names):
        usage_count = class_usage.get(i, 0)
        print(f"  {i}: {name} (使用 {usage_count} 次)")
    
    # 显示使用统计
    print(f"\n📈 类别使用统计:")
    total_annotations = sum(class_usage.values())
    print(f"总标注数量: {total_annotations}")
    
    if class_usage:
        used_classes = len(class_usage)
        unused_classes = [i for i in range(len(class_names)) if i not in class_usage]
        
        print(f"已使用类别: {used_classes}")
        if unused_classes:
            print(f"未使用类别: {unused_classes}")
            print(f"未使用类别名称: {[class_names[i] for i in unused_classes if i < len(class_names)]}")
        
        # 显示使用频率排序
        sorted_usage = sorted(class_usage.items(), key=lambda x: x[1], reverse=True)
        print(f"\n使用频率排序:")
        for class_id, count in sorted_usage:
            class_name = class_names[class_id] if class_id < len(class_names) else f"未知类别{class_id}"
            percentage = count / total_annotations * 100
            print(f"  类别 {class_id} ({class_name}): {count} 次 ({percentage:.1f}%)")


def _images_dir_for_labels(base_dir: str, labels_dir: str, structure: str) -> str:
    """根据结构推导与 labels_dir 对应的 images 目录。"""
    if structure == 'standard':
        return os.path.join(base_dir, 'images')
    if structure == 'format1':
        # base/train/labels -> base/train/images
        parent = os.path.dirname(labels_dir)  # .../train
        return os.path.join(parent, 'images')
    if structure == 'format2':
        # base/labels/split -> base/images/split
        split = os.path.basename(labels_dir)
        return os.path.join(base_dir, 'images', split)
    # mixed: 与标签同目录
    return labels_dir


def _find_image_path(images_dir: str, stem: str) -> str | None:
    from utils.yolo_utils import IMG_EXTS
    for ext in IMG_EXTS:
        p = os.path.join(images_dir, stem + ext)
        if os.path.exists(p):
            return p
    return None


def _load_class_names_from_dataset(base_dir: str) -> list[str]:
    files = list_possible_class_files(base_dir)
    if not files:
        return []
    return read_class_names(os.path.join(base_dir, files[0]))


def _display_class_distribution(class_usage: dict[int, int], class_names: list[str]) -> None:
    total = sum(class_usage.values()) or 1
    print("\n📈 类别分布:")
    for cid, cnt in sorted(class_usage.items(), key=lambda x: x[1], reverse=True):
        name = class_names[cid] if cid < len(class_names) else f"Class_{cid}"
        pct = cnt * 100.0 / total
        print(f"  {cid}: {name} -> {cnt} ({pct:.1f}%)")


def _determine_classes_to_remove_by_strategy(strategy: dict, class_usage: dict[int, int]) -> list[int]:
    if not strategy:
        return []
    total = sum(class_usage.values())
    keys = set(class_usage.keys())
    t = strategy.get('type')
    if t == 'min_samples':
        thr = int(strategy['min_samples'])
        return [cid for cid, cnt in class_usage.items() if cnt < thr]
    if t == 'min_percentage':
        thr = float(strategy['min_percentage'])
        min_cnt = total * thr / 100.0
        return [cid for cid, cnt in class_usage.items() if cnt < min_cnt]
    if t == 'keep':
        keep = set(strategy['keep'])
        return [cid for cid in keys if cid not in keep]
    if t == 'remove':
        return list(set(strategy['remove']))
    if t == 'top_n':
        n = int(strategy['top_n'])
        sorted_c = sorted(class_usage.items(), key=lambda x: x[1], reverse=True)
        keep = {cid for cid, _ in sorted_c[:n]}
        return [cid for cid in keys if cid not in keep]
    if t == 'id_range':
        lo, hi = strategy['id_range']
        return [cid for cid in keys if lo <= cid <= hi]
    if t == 'combo':
        ms = int(strategy['min_samples'])
        mp = float(strategy['min_percentage'])
        min_cnt = total * mp / 100.0
        return [cid for cid, cnt in class_usage.items() if cnt < ms or cnt < min_cnt]
    return []


def _interactive_clean_strategy(class_usage: dict[int, int], class_names: list[str]) -> dict | None:
    print("\n====== 选择清理策略 ======")
    print("1. 按最小样本数清理 (删除样本数少于阈值的类别)")
    print("2. 按百分比清理 (删除占比少于阈值的类别)")
    print("3. 手动选择要保留的类别")
    print("4. 手动选择要删除的类别")
    print("5. 自定义清理规则")
    print("0. 取消")
    while True:
        try:
            ch = input("请输入选择 (0-5): ").strip()
        except KeyboardInterrupt:
            return None
        if ch in {'0', '1', '2', '3', '4', '5'}:
            break
        print("无效选择，请重试")
    if ch == '0':
        return None
    if ch == '1':
        v = int(input("最小样本数阈值: ").strip())
        return {'type': 'min_samples', 'min_samples': v}
    if ch == '2':
        v = float(input("最小百分比阈值(如 1.0): ").strip())
        return {'type': 'min_percentage', 'min_percentage': v}
    if ch == '3':
        print("当前类别:")
        for cid in sorted(class_usage.keys()):
            name = class_names[cid] if cid < len(class_names) else f"Class_{cid}"
            print(f"  {cid}: {name} ({class_usage[cid]})")
        s = input("输入要保留的类别ID(逗号分隔): ").strip()
        keep = [int(x) for x in s.split(',') if x.strip()]
        return {'type': 'keep', 'keep': keep}
    if ch == '4':
        print("当前类别:")
        for cid in sorted(class_usage.keys()):
            name = class_names[cid] if cid < len(class_names) else f"Class_{cid}"
            print(f"  {cid}: {name} ({class_usage[cid]})")
        s = input("输入要删除的类别ID(逗号分隔): ").strip()
        rem = [int(x) for x in s.split(',') if x.strip()]
        return {'type': 'remove', 'remove': rem}
    if ch == '5':
        print("1. 组合条件 (最小样本数 AND 最小百分比)")
        print("2. 保留前N个最多样本的类别")
        print("3. 删除特定ID范围")
        sc = input("选择(1-3): ").strip()
        if sc == '1':
            ms = int(input("最小样本数: ").strip())
            mp = float(input("最小百分比: ").strip())
            return {'type': 'combo', 'min_samples': ms, 'min_percentage': mp}
        if sc == '2':
            n = int(input("保留前N个: ").strip())
            return {'type': 'top_n', 'top_n': n}
        if sc == '3':
            lo = int(input("最小ID: ").strip())
            hi = int(input("最大ID: ").strip())
            return {'type': 'id_range', 'id_range': (lo, hi)}
    return None


def _generate_clean_report(base_dir: str, class_usage: dict[int, int], class_names: list[str], strategy: dict,
                           classes_removed: list[int], removed_files: list[str], updated_files: list[str]) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = os.path.join(base_dir, f"cleaning_report_{ts}.md")
    total_ann = sum(class_usage.values()) or 1
    with open(report, 'w', encoding='utf-8') as f:
        f.write("# YOLO数据集清理报告\n\n")
        f.write(f"**清理日期**: {ts}\n")
        f.write(f"**数据集路径**: `{base_dir}`\n\n")
        f.write("## 清理前统计\n\n")
        f.write(f"- **总标注数**: {total_ann}\n")
        f.write(f"- **类别数**: {len(class_usage)}\n\n")
        f.write("### 原始类别分布\n\n")
        f.write("| 类别ID | 类别名称 | 标注数 | 占比 |\n")
        f.write("|--------|----------|--------|------|\n")
        for cid, cnt in sorted(class_usage.items()):
            name = class_names[cid] if cid < len(class_names) else f"Class_{cid}"
            pct = cnt * 100.0 / total_ann
            f.write(f"| {cid} | {name} | {cnt} | {pct:.1f}% |\n")
        f.write("\n## 清理策略\n\n")
        f.write(f"{strategy}\n")
        if classes_removed:
            f.write("\n## 清理结果\n\n")
            f.write(f"- **删除类别数**: {len(classes_removed)}\n")
            f.write(f"- **删除文件数**: {len(removed_files)}\n")
            f.write(f"- **更新文件数**: {len(updated_files)}\n")
    print(f"📋 生成清理报告: {report}")
    return report


def clean_dataset(base_dir: str, *,
                  min_samples: int | None = None,
                  min_percentage: float | None = None,
                  keep_classes: list[int] | None = None,
                  remove_classes: list[int] | None = None,
                  top_n: int | None = None,
                  id_range: tuple[int, int] | None = None,
                  interactive: bool = False,
                  class_file: str | None = None,
                  backup: bool = True,
                  dry_run: bool = True,
                  assume_yes: bool = False) -> bool:
    """融合清理功能：支持多策略删除类别并重映射ID，同时删除无标注图片，更新类名与YAML，并生成报告。"""
    # 统计
    class_usage, ds_class_names = analyze_dataset_classes(base_dir)
    if class_usage is None:
        return False
    if class_file and os.path.exists(class_file):
        override = read_class_names(class_file)
        if override:
            ds_class_names = override
    print("\n🔍 数据集分析完成")
    _display_class_distribution(class_usage, ds_class_names)

    # 解析策略
    strategy: dict | None = None
    if interactive or all(v is None for v in [min_samples, min_percentage, keep_classes, remove_classes, top_n, id_range]):
        strategy = _interactive_clean_strategy(class_usage, ds_class_names)
        if strategy is None:
            print("已取消")
            return False
    else:
        if min_samples is not None:
            strategy = {'type': 'min_samples', 'min_samples': min_samples}
        elif min_percentage is not None:
            strategy = {'type': 'min_percentage', 'min_percentage': min_percentage}
        elif keep_classes is not None:
            strategy = {'type': 'keep', 'keep': keep_classes}
        elif remove_classes is not None:
            strategy = {'type': 'remove', 'remove': remove_classes}
        elif top_n is not None:
            strategy = {'type': 'top_n', 'top_n': top_n}
        elif id_range is not None:
            strategy = {'type': 'id_range', 'id_range': id_range}

    classes_to_remove = _determine_classes_to_remove_by_strategy(strategy, class_usage)
    if not classes_to_remove:
        print("✅ 没有需要删除的类别")
        return True

    total = sum(class_usage.values()) or 1
    removed_samples = sum(class_usage.get(cid, 0) for cid in classes_to_remove)
    kept_classes = sorted([cid for cid in class_usage.keys() if cid not in set(classes_to_remove)])
    kept_samples = total - removed_samples

    print("\n====== 清理预览 ======")
    print(f"❌ 将删除的类别({len(classes_to_remove)}): {sorted(classes_to_remove)}  共 {removed_samples} 个标注({removed_samples*100.0/total:.1f}%)")
    print(f"✅ 将保留的类别({len(kept_classes)}): {kept_classes}  共 {kept_samples} 个标注({kept_samples*100.0/total:.1f}%)")

    if dry_run:
        print("\n[预览模式] 未进行实际写入。使用 --execute 执行。")
        return True

    if not assume_yes:
        ans = input("是否确认执行清理? (y/n): ").strip().lower()
        if ans not in {'y', 'yes'}:
            print("已取消")
            return False

    # 备份
    if backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"{base_dir}_backup_before_clean_{timestamp}"
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        shutil.copytree(base_dir, backup_dir)
        print(f"✓ 已创建备份: {backup_dir}")

    structure, _, _ = detect_yolo_structure(base_dir)
    label_dirs = yolo_label_dirs(base_dir, structure)

    # 构建映射
    id_mapping = {old_id: new_id for new_id, old_id in enumerate(kept_classes)}

    removed_files: list[str] = []
    updated_files: list[str] = []

    for labels_dir in label_dirs:
        images_dir = _images_dir_for_labels(base_dir, labels_dir, structure)
        for label_file in iter_label_files(labels_dir, structure):
            label_path = os.path.join(labels_dir, label_file)
            try:
                new_lines = []
                with open(label_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        s = line.strip()
                        if not s:
                            continue
                        parts = s.split()
                        if len(parts) < 5:
                            continue
                        try:
                            cid = int(float(parts[0]))
                        except Exception:
                            continue
                        if cid in classes_to_remove:
                            continue
                        parts[0] = str(id_mapping[cid])
                        new_lines.append(' '.join(parts))

                if not new_lines:
                    # 删除标签文件和对应图片
                    try:
                        os.remove(label_path)
                        removed_files.append(label_path)
                    except Exception:
                        pass
                    stem = os.path.splitext(os.path.basename(label_path))[0]
                    img_path = _find_image_path(images_dir, stem)
                    if img_path and os.path.exists(img_path):
                        try:
                            os.remove(img_path)
                            removed_files.append(img_path)
                        except Exception:
                            pass
                else:
                    with open(label_path, 'w', encoding='utf-8') as f:
                        for ln in new_lines:
                            f.write(ln + '\n')
                    updated_files.append(label_path)
            except Exception as e:
                print(f"错误: 无法处理标签文件 {label_path}: {e}")

    # 更新类别/配置文件
    new_names: list[str] = []
    if ds_class_names:
        for new_id in range(len(kept_classes)):
            old_id = kept_classes[new_id]
            name = ds_class_names[old_id] if old_id < len(ds_class_names) else f"Class_{old_id}"
            new_names.append(name)
    else:
        new_names = [f"Class_{i}" for i in range(len(kept_classes))]

    class_files = list_possible_class_files(base_dir)
    for cf in class_files:
        try:
            write_class_names(os.path.join(base_dir, cf), new_names)
            print(f"✓ 已更新类别/配置文件: {cf}")
        except Exception as e:
            print(f"警告: 更新 {cf} 失败: {e}")

    # 报告
    _generate_clean_report(base_dir, class_usage, ds_class_names, strategy, classes_to_remove, removed_files, updated_files)

    print("\n📊 清理完成")
    print(f"  🗑️ 删除文件数: {len(removed_files)}")
    print(f"  ✏️ 更新文件数: {len(updated_files)}")
    return True


def reindex_classes(base_dir, target_class_names, strict=False, backup=True, dry_run=True, require_same_set=False):
    """根据目标类别顺序重排数据集中所有标签文件的类别ID，并更新类别文件。

    参数:
    - base_dir: 数据集根目录
    - target_class_names: 目标类别顺序(list[str])，写入类别文件并作为新ID映射依据
    - strict: 若为True，遇到旧类别在目标表中不存在则报错终止；否则跳过该标注
    - backup: 是否创建备份
    - dry_run: 演习模式，仅统计与预览，不实际改写
    """
    # 读取当前类别
    class_files = list_possible_class_files(base_dir)
    if not class_files:
        print("错误: 未找到类别文件，无法进行重排")
        return False
    current_class_file = os.path.join(base_dir, class_files[0])
    current_names = read_class_names(current_class_file)
    if not current_names:
        print("错误: 无法读取当前类别名称")
        return False

    print("当前类别顺序:", current_names)
    print("目标类别顺序:", target_class_names)

    if require_same_set:
        cur_set = set(current_names)
        tgt_set = set(target_class_names)
        if cur_set != tgt_set:
            only_in_cur = sorted(list(cur_set - tgt_set))
            only_in_tgt = sorted(list(tgt_set - cur_set))
            print("错误: 类别集合不一致，已启用 --require-same-set：")
            if only_in_cur:
                print(f"  仅在当前集合中存在: {only_in_cur}")
            if only_in_tgt:
                print(f"  仅在目标集合中存在: {only_in_tgt}")
            return False

    # 构建映射: 旧class_id -> 新class_id
    name_to_new = {n: i for i, n in enumerate(target_class_names)}
    missing_old = [n for n in current_names if n not in name_to_new]
    if missing_old:
        msg = f"警告: 以下旧类别在目标列表中不存在: {missing_old}"
        if strict:
            print("错误(严格模式):", msg)
            return False
        else:
            print(msg + "，这些类别的标注将被丢弃")

    old_to_new = {}
    for old_id, name in enumerate(current_names):
        if name in name_to_new:
            old_to_new[old_id] = name_to_new[name]
        else:
            old_to_new[old_id] = None  # 丢弃

    # 创建备份
    if backup and not dry_run:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"{base_dir}_backup_before_reindex_{timestamp}"
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        shutil.copytree(base_dir, backup_dir)
        print(f"✓ 已创建备份: {backup_dir}")

    structure, _, _ = detect_yolo_structure(base_dir)
    label_dirs = yolo_label_dirs(base_dir, structure)

    updated_files = 0
    dropped_annotations = 0
    total_annotations = 0

    for labels_dir in label_dirs:
        for label_file in iter_label_files(labels_dir, structure):
            label_path = os.path.join(labels_dir, label_file)
            try:
                new_lines = []
                with open(label_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        s = line.strip()
                        if not s:
                            continue
                        parts = s.split()
                        try:
                            old_id = int(parts[0])
                        except Exception:
                            continue
                        total_annotations += 1
                        new_id = old_to_new.get(old_id, None)
                        if new_id is None:
                            dropped_annotations += 1
                            continue
                        parts[0] = str(new_id)
                        new_lines.append(' '.join(parts))

                if not dry_run:
                    with open(label_path, 'w', encoding='utf-8') as f:
                        for ln in new_lines:
                            f.write(ln + '\n')
                updated_files += 1
            except Exception as e:
                print(f"错误: 无法处理标签文件 {label_path}: {e}")

    # 更新类别文件
    if not dry_run:
        for class_file in class_files:
            class_file_path = os.path.join(base_dir, class_file)
            write_class_names(class_file_path, target_class_names)
            print(f"✓ 已更新类别文件: {class_file}")

    print("\n重排完成(预览)" if dry_run else "\n重排完成")
    print(f"处理的标签文件: {updated_files}")
    print(f"总标注: {total_annotations}")
    if missing_old:
        print(f"丢弃的标注(因类别缺失): {dropped_annotations}")
    return True


def main():
    parser = argparse.ArgumentParser(description="YOLO数据集类别管理工具")
    parser.add_argument("--dataset_dir", "-d", required=True,
                       help="数据集目录路径")
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 信息命令
    info_parser = subparsers.add_parser('info', help='显示数据集类别信息')
    
    # 删除命令
    delete_parser = subparsers.add_parser('delete', help='删除指定类别')
    delete_parser.add_argument("--class_ids", "-c", nargs='+', type=int, required=True,
                              help="要删除的类别ID列表")
    delete_parser.add_argument("--no-backup", action="store_true",
                              help="不创建备份")
    
    # 重命名命令
    rename_parser = subparsers.add_parser('rename', help='重命名类别')
    rename_parser.add_argument("--renames", "-r", nargs='+', required=True,
                              help="重命名映射，格式: old_name1:new_name1 old_name2:new_name2")
    rename_parser.add_argument("--no-backup", action="store_true",
                              help="不创建备份")
    
    # 备份清理命令
    cleanup_parser = subparsers.add_parser('cleanup', help='清理旧的备份文件夹')
    cleanup_parser.add_argument("--keep", type=int, default=5,
                               help="保留最新的备份数量 (默认: 5)")
    cleanup_parser.add_argument("--dry-run", action="store_true",
                               help="演习模式，只显示将要删除的备份，不执行实际删除")
    cleanup_parser.add_argument("--execute", action="store_true",
                               help="执行实际删除操作")

    # 重排命令
    reindex_parser = subparsers.add_parser('reindex', help='根据目标类别顺序重排所有标签中的类别ID，并更新类别文件')
    reindex_group = reindex_parser.add_mutually_exclusive_group(required=True)
    reindex_group.add_argument("--to-file", dest="to_file", help="目标类别文件路径 (classes.txt 或 *.yaml)，其顺序将作为新类别顺序")
    reindex_group.add_argument("--to-classes", dest="to_classes", nargs='+', help="直接提供目标类别顺序列表，例如: --to-classes arco_0 arco_1 arco_2 ...")
    reindex_parser.add_argument("--strict", action="store_true", help="严格模式: 旧类别若不在目标列表中则报错终止")
    reindex_parser.add_argument("--require-same-set", action="store_true", help="强制要求当前与目标类别集合完全一致，否则中止")
    reindex_parser.add_argument("--no-backup", action="store_true", help="不创建备份")
    reindex_parser.add_argument("--dry-run", action="store_true", help="演习模式，仅预览更改，不写回磁盘 (默认: 预览)")
    reindex_parser.add_argument("--execute", action="store_true", help="执行实际重排(与 --dry-run 互斥)")

    # 清理命令（融合 yolo_label_cleaner 功能）
    clean_parser = subparsers.add_parser('clean', help='按策略清理类别与样本，重映射ID，删除无标注图片，并更新类名/YAML/报告')
    strategy_group = clean_parser.add_mutually_exclusive_group(required=False)
    strategy_group.add_argument("--min-samples", type=int, help="删除样本数少于阈值的类别")
    strategy_group.add_argument("--min-percentage", type=float, help="删除占比少于阈值(%)的类别")
    clean_parser.add_argument("--keep-classes", nargs='+', type=int, help="手动指定保留的类别ID列表")
    clean_parser.add_argument("--remove-classes", nargs='+', type=int, help="手动指定删除的类别ID列表")
    clean_parser.add_argument("--top-n", type=int, help="仅保留前N个最多样本的类别")
    clean_parser.add_argument("--remove-id-range", nargs=2, type=int, metavar=('MIN', 'MAX'), help="删除特定ID范围的类别")
    clean_parser.add_argument("--interactive", action="store_true", help="交互式选择策略")
    clean_parser.add_argument("--class-file", help="指定外部类别文件用于名称映射(可选)")
    clean_parser.add_argument("--no-backup", action="store_true", help="不创建备份")
    clean_parser.add_argument("--dry-run", action="store_true", help="预览模式(默认预览，使用 --execute 执行)")
    clean_parser.add_argument("--execute", action="store_true", help="执行实际清理")
    clean_parser.add_argument("--yes", action="store_true", help="无需确认直接执行")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 验证数据集目录
    if not os.path.exists(args.dataset_dir):
        print(f"错误: 数据集目录 {args.dataset_dir} 不存在")
        return
    
    if args.command == 'info':
        show_dataset_info(args.dataset_dir)
    
    elif args.command == 'delete':
        backup = not args.no_backup
        delete_classes(args.dataset_dir, args.class_ids, backup)
    
    elif args.command == 'rename':
        backup = not args.no_backup
        
        # 解析重命名映射
        class_renames = {}
        for rename_pair in args.renames:
            try:
                old_name, new_name = rename_pair.split(':', 1)
                class_renames[old_name] = new_name
            except ValueError:
                print(f"错误: 无效的重命名格式 '{rename_pair}'，应为 'old_name:new_name'")
                return
        
        rename_classes(args.dataset_dir, class_renames, backup)
    
    elif args.command == 'cleanup':
        if args.dry_run and args.execute:
            print("错误: --dry-run 和 --execute 不能同时使用")
            return
        
        dry_run = args.dry_run or not args.execute
        cleanup_backups(args.dataset_dir, args.keep, dry_run)

    elif args.command == 'reindex':
        if args.dry_run and args.execute:
            print("错误: --dry-run 和 --execute 不能同时使用")
            return
        dry_run = args.dry_run or not args.execute
        backup = not args.no_backup

        # 读取目标类别
        if args.to_file:
            if not os.path.exists(args.to_file):
                print(f"错误: 目标类别文件不存在: {args.to_file}")
                return
            target_names = read_class_names(args.to_file)
        else:
            target_names = args.to_classes or []

        if not target_names:
            print("错误: 目标类别列表为空")
            return

        reindex_classes(
            args.dataset_dir,
            target_names,
            strict=args.strict,
            backup=backup,
            dry_run=dry_run,
            require_same_set=args.require_same_set,
        )

    elif args.command == 'clean':
        if args.dry_run and args.execute:
            print("错误: --dry-run 和 --execute 不能同时使用")
            return
        dry_run = args.dry_run or not args.execute
        backup = not args.no_backup
        id_range = tuple(args.remove_id_range) if args.remove_id_range else None
        clean_dataset(
            args.dataset_dir,
            min_samples=args.min_samples,
            min_percentage=args.min_percentage,
            keep_classes=args.keep_classes,
            remove_classes=args.remove_classes,
            top_n=args.top_n,
            id_range=id_range,
            interactive=args.interactive,
            class_file=args.class_file,
            backup=backup,
            dry_run=dry_run,
            assume_yes=args.yes,
        )


if __name__ == "__main__":
    main()
