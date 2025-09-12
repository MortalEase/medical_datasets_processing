# 贡献指南

---

## 脚本编写规范

在仓库新增或修改脚本时，请遵循以下约定：

1) 顶部文档块（必选）

- 用中文简述脚本目标与关键行为，倾向于“要点式”而非正式 API 文档
- 可分条展示核心要点，如：
	- 核心：一句话概括主功能或策略
	- 扩展：列出可选行为或额外能力
	- 默认：说明默认输出路径/默认策略
- 需要时提供 1–2 个“使用示例”命令，便于复制

2) CLI 设计

- 使用 `argparse`；布尔开关用 `store_true`；必要时使用 `RawTextHelpFormatter` 展示多行帮助
- 参数名称稳定、简短，常见参数：`--input/-i`、`--output/-o`、`--config/-c`、`--seed`、`--train_ratio` 等
- 帮助信息说明默认值与取值范围（如“阈值 ∈ [0,1]”）

3) 编码风格

- 遵循 PEP 8（代码风格）。Docstring 采用本仓库“简洁中文 + 少量分节”的风格（见下）
- 使用类型注解表达参数与返回的核心类型信息；避免在 docstring 重复类型定义
- 路径优先使用 `pathlib.Path`；避免写死绝对路径；必要时自动 `mkdir(parents=True, exist_ok=True)`。
- 函数内职责单一；共性逻辑提炼到 `utils/`。
- 日志输出统一使用 `utils.logging_utils`：`log_info` / `log_warn` / `log_error`，必要时 `tee_stdout_stderr('logs')` 记录到 `logs/`。
- 入口保护：`if __name__ == '__main__': main()`。

4) Docstring 规范

- 风格：采用与 `yolo2coco.py` 一致的“简洁中文 + 少量分节”说明风格，偏用途说明，不强制遵循 Google/NumPy/reST 任一严格模板
- 标点：单行摘要的句尾使用英文句号“.”
- 模块级 docstring：建议概述脚本要点，可采用简短分节（如“核心/扩展/默认”），必要时增加“使用示例”
- 函数/方法级 docstring：
	- 单行摘要优先；必要时可追加 1–3 行补充说明
	- 允许使用中文分节标签“参数:”“返回:”“异常:”进行极简列点；不强制 `:param:`/`:return:` 或完整 Google/NumPy 标题
	- 类型信息以函数签名的类型注解为主，docstring 不重复书写

- 示例（模块）

	```python
	"""YOLO -> COCO 转换脚本

	核心: 自动检测多种数据结构并输出 COCO JSON
	扩展: 可选 --split 进行再划分
	默认: 未提供输出路径时写入合理默认位置
	"""
	```

- 示例（函数）

	```python
	def read_label_file(label_path: str) -> list[str]:
			"""读取单个 YOLO 标签文件, 返回每一行的去空白字符串列表."""

	def detect_structure(root_dir: str):
			"""检测数据集结构类型并返回结构标识与 (split, images_dir, labels_dir) 列表.

			返回:
					structure(str): format1 | format2 | standard | mixed | unknown
					paths(list[tuple]): [(split_name, images_dir, labels_dir), ...]
			"""
	```

5) 健壮性与边界

- 对空输入、缺失文件、图像读取失败、标签异常等情况要有清晰的降级与日志。
- 保持转换过程的“尽可能保留”：例如无标签图片仍保留到 images 列表。
- 对类别越界可按需扩展类别，或记录告警并跳过（与现有脚本行为一致）。

---

## 提交与分支流程

1) 分支命名

- `feat/<scope>-<short-desc>` 新功能
- `fix/<scope>-<issue-id-or-desc>` 缺陷修复
- `refactor/<scope>-<desc>` 重构（无行为变化）
- `docs/<scope>-<desc>` 文档
- `chore/<scope>-<desc>` 构建/杂项

2) 提交信息（严格参考 `.gitmessage`）

请在本地启用仓库的提交模板，保证一致性：

```bash
git config commit.template .gitmessage
```

模板结构：

```
<type>(<scope>): <subject>

<body>
<body 继续，可多段落>

<footer>
```

- type 取值（与模板一致）：`feat` | `fix` | `docs` | `style` | `refactor` | `perf` | `test` | `build` | `ci` | `chore` | `revert`
- scope 必选；必须在以下范围：`tools`, `utils`, `log`, `git`, `readme`
- subject：50 字符内，祈使句，英文，不以句号结尾
- body（可选）：说明动机/差异/影响，使用中文；每行 ≤ 72 字符，且每行以 `- ` 开头；各行之间不空行（与 `.gitmessage` 要求一致）
- footer（可选）：BREAKING CHANGE / 关联 Issue（如 `Closes #123`）

示例：

```
feat(script): add voc2yolo converter (standard & mixed)

- 支持 Pascal VOC XML -> YOLO txt 转换, 新增结构选择、自动/自定义类别、
- allow-new-classes, ignore-difficult, data.yaml 输出与统一日志.

Closes #15

BREAKING CHANGE: 移除旧的 voc_convert.py 脚本
```

---