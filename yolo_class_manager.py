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
    """分析数据集中的类别使用情况
    Returns: (class_usage: dict[int,int], class_names: list[str])
    """
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


def delete_classes(base_dir, explicit_class_ids=None, backup=True, min_samples=None, min_percentage=None, assume_yes=False, dry_run=False):
    """删除类别：支持显式ID、最小样本数阈值、最小占比阈值。"""
    explicit_class_ids = set(explicit_class_ids or [])
    class_usage, class_names = analyze_dataset_classes(base_dir)
    if class_usage is None:
        return False

    total = sum(class_usage.values()) or 1
    # 自动阈值选择
    auto_ids = set()
    if min_samples is not None:
        auto_ids.update([cid for cid, cnt in class_usage.items() if cnt < min_samples])
    if min_percentage is not None:
        min_cnt = total * (float(min_percentage) / 100.0)
        auto_ids.update([cid for cid, cnt in class_usage.items() if cnt < min_cnt])

    target_ids = explicit_class_ids | auto_ids
    if not target_ids:
        print("未指定需要删除的类别 (既没有ID也没有阈值命中)")
        return False

    all_defined_classes = set(range(len(class_names))) if class_names else set()
    invalid = target_ids - all_defined_classes
    if invalid:
        print(f"错误: 以下类别超出定义范围 (0-{len(class_names)-1}): {sorted(invalid)}")
        return False

    used_classes = set(class_usage.keys())
    used_to_delete = sorted(target_ids & used_classes)
    unused_to_delete = sorted(target_ids - used_classes)

    removed_ann = sum(class_usage.get(cid, 0) for cid in used_to_delete)
    preview_lines = ["====== 删除预览 ======",
                     f"总标注: {total}",
                     f"拟删除类别总数: {len(target_ids)} (已使用 {len(used_to_delete)}, 未使用 {len(unused_to_delete)})",
                     f"已使用删除类别: {used_to_delete}",
                     f"未使用删除类别: {unused_to_delete}",
                     f"将删除标注数: {removed_ann} ({removed_ann*100.0/total:.1f}%)"]
    if min_samples is not None:
        preview_lines.append(f"按最小样本数阈值(<{min_samples})匹配: {sorted([c for c in class_usage if class_usage[c] < min_samples])}")
    if min_percentage is not None:
        preview_lines.append(f"按最小占比阈值(<{min_percentage}% )匹配: {sorted([c for c in class_usage if class_usage[c] < total * (float(min_percentage)/100.0)])}")
    print('\n'.join(preview_lines))

    if dry_run:
        print("[预览模式] 未写入。使用 --execute 进行实际删除。")
        return True

    if not assume_yes:
        ans = input("确认执行删除? (y/n): ").strip().lower()
        if ans not in {'y', 'yes'}:
            print("已取消")
            return False

    # 备份
    if backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"{base_dir}_backup_before_delete_{timestamp}"
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        shutil.copytree(base_dir, backup_dir)
        print(f"✓ 已创建备份: {backup_dir}")

    structure, _, _ = detect_yolo_structure(base_dir)
    label_dirs = yolo_label_dirs(base_dir, structure)

    remaining_used_classes = sorted([c for c in used_classes if c not in target_ids])
    class_mapping = {old: new for new, old in enumerate(remaining_used_classes)}

    deleted_annotations = 0
    updated_files = 0

    for labels_dir in label_dirs:
        for label_file in iter_label_files(labels_dir, structure):
            label_path = os.path.join(labels_dir, label_file)
            try:
                new_lines = []
                file_changed = False
                with open(label_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        s = line.strip()
                        if not s:
                            continue
                        parts = s.split()
                        try:
                            cid = int(parts[0])
                        except Exception:
                            continue
                        if cid in target_ids:
                            deleted_annotations += 1
                            file_changed = True
                            continue
                        # 重新映射
                        if cid in class_mapping and class_mapping[cid] != cid:
                            parts[0] = str(class_mapping[cid])
                            file_changed = True
                        new_lines.append(' '.join(parts))
                if file_changed:
                    with open(label_path, 'w', encoding='utf-8') as f:
                        for ln in new_lines:
                            f.write(ln + '\n')
                    updated_files += 1
            except Exception as e:
                print(f"错误: 无法处理标签文件 {label_path}: {e}")

    # 更新类别文件
    class_files = list_possible_class_files(base_dir)
    if class_files and class_names:
        remaining_indices = [i for i in range(len(class_names)) if i not in target_ids]
        new_names = [class_names[i] for i in remaining_indices]
        for cf in class_files:
            write_class_names(os.path.join(base_dir, cf), new_names)
            print(f"✓ 已更新类别文件: {cf}")

    print("\n删除完成")
    print(f"删除类别: {sorted(list(target_ids))}")
    print(f"删除标注: {deleted_annotations}")
    print(f"更新文件: {updated_files}")
    print(f"剩余类别: {len(class_names) - len(target_ids) if class_names else 0}")
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

    # delete 阈值扩展参数
    delete_parser.add_argument("--min-samples", type=int, help="删除样本数少于阈值的类别")
    delete_parser.add_argument("--min-percentage", type=float, help="删除占比少于阈值(%)的类别")
    delete_parser.add_argument("--dry-run", action="store_true", help="预览删除，不写入磁盘")
    delete_parser.add_argument("--execute", action="store_true", help="实际执行删除(与 --dry-run 互斥，默认预览)")
    delete_parser.add_argument("--yes", action="store_true", help="无需确认直接执行")
    
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
        if args.dry_run and args.execute:
            print("错误: --dry-run 与 --execute 不能同时使用")
            return
        dry_run = args.dry_run or not args.execute
        backup = not args.no_backup
        delete_classes(
            args.dataset_dir,
            explicit_class_ids=args.class_ids,
            backup=backup,
            min_samples=args.min_samples,
            min_percentage=args.min_percentage,
            assume_yes=args.yes,
            dry_run=dry_run,
        )
    
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

    # clean 子命令已移除


if __name__ == "__main__":
    main()
