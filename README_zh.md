# NFO 元数据通用整理工具

这是一个 **Python 脚本**，旨在自动化地扫描、清理并标准化媒体库中的 `.nfo` 元数据文件。通过一个外部配置文件，您可以精确控制各种清理和映射规则，以建立一个干净、统一的媒体信息中心。

---

## 核心目标
本工具旨在解决手动整理 `.nfo` 文件时遇到的常见问题，如：
- 信息冗余
- 格式不一
- 命名不规范  

通过自动化流程，让元数据管理变得 **简单、高效且可重复**。

---

## 主要功能一览
- **高度可配置**：所有操作均通过外部 `config.ini` 文件控制，无需修改代码。  
- **通用标签处理**：可对任意指定的 XML 标签（如演员、导演、工作室、类型等）应用规则。  
- **强大的清理规则库**：内置多种清理规则，可按需启用或禁用。  
- **双 XML 映射与标准化**：支持演员映射与通用映射文件，并智能合并规则。  
- **安全的预览模式 (Dry Run)**：先预览改动，再决定是否应用。  
- **高效并发处理**：多线程加速，快速处理大量文件。  

---

## 文件组成
要完整运行此工具，需在同一目录下准备以下文件：

- `nfo_universal_cleaner.py`：主程序脚本，负责执行逻辑。  
- `config.ini`：配置文件，定义操作规则。  
- `mapping_actor.xml`：演员映射文件，标准化演员名称。  
- `mapping_info.xml`：通用映射文件，标准化其他标签（工作室、系列等）。  

---

## 功能详解

### 1. 高度可配置化 (config.ini)
通过 `config.ini` 文件精确控制工具行为，包括路径设置、规则开关、参数自定义等。

### 2. 通用标签处理
在 `[Tags]` 部分指定任意数量的 XML 标签路径：

```ini
[Tags]
tags_to_clean =
    .//actor/name
    .//director
    .//studio
```

### 3. 强大的清理规则库
在 `[Rules]` 与 `[RuleSettings]` 中配置：

- **按分隔符截断 (truncate_on_delimiter)**  
  示例：`薫さん 21歳 大学生 -> 薫さん`  

- **移除指定模式 (remove_patterns)**  
  示例：`Studio Ghibli-tmdb-12345 -> Studio Ghibli`  

- **规范化空格 (normalize_whitespace)**  
  示例：`John  Doe -> John Doe`  

- **大小写转换 (standardize_case)**  
  支持 `lower` (小写) 或 `title` (首字母大写)。  

- **移除空标签 (remove_empty_tags)**  
  清理后内容为空时，自动移除标签。  

### 4. XML 映射与标准化
- 清理后再进行映射匹配。  
- 原始文本与清理后文本双重匹配。  
- `mapping_actor.xml` 优先级高于 `mapping_info.xml`。  

### 5. 安全的预览模式 (Dry Run)
在 `config.ini` 中：

```ini
dry_run = True
```

- `True`：仅预览修改，不写入文件。  
- `False`：实际写入修改。  

### 6. 高效的并发处理
使用 `ThreadPoolExecutor` 并发处理，大量 `.nfo` 文件时显著提升速度。

---

## 使用方法

### 步骤一：准备环境
安装 Python (建议 3.7+)。  
安装依赖：

```bash
pip install opencc-python-reimplemented
```

### 步骤二：准备文件
将以下文件放在同一文件夹：
- `nfo_universal_cleaner.py`
- `config.ini`
- `mapping_actor.xml`
- `mapping_info.xml`

### 步骤三：修改配置文件
在 `[Paths]` 部分修改：

```ini
scan_directory = 您的NFO文件目录
actor_mapping_xml = mapping_actor.xml
tag_mapping_xml = mapping_info.xml
```

### 步骤四：预览运行 (推荐)
确保 `dry_run = True`。  
运行：

```bash
python nfo_universal_cleaner.py
```

检查命令行输出，确认 `(计划修改)` 是否符合预期。

### 步骤五：正式运行
确认无误后，修改：

```ini
dry_run = False
```

再次运行：

```bash
python nfo_universal_cleaner.py
```

### 步骤六：检查日志
出现错误时会生成 `cleaner_errors.log`，可查看详细信息。

---

## 总结
本工具提供了一个 **自动化、可定制、可安全预览** 的解决方案，帮助您维护一个整洁、标准化的媒体库元数据。  
**建议：始终先运行 Dry Run 确保结果符合预期！**
