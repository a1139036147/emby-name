**Read this in other languages: [English](README.md), [中文](README_zh.md).**

# NFO Metadata Universal Cleaner

A powerful **Python script** designed to automate the scanning, cleaning, and standardization of `.nfo` metadata files in your media library. With an external configuration file, you can precisely control various cleaning and mapping rules to build a clean and unified media information hub.

---

## Core Goals
This tool addresses common problems encountered when manually organizing `.nfo` files, such as:
- Redundant information  
- Inconsistent formatting  
- Irregular naming  

By automating the process, metadata management becomes **simple, efficient, and repeatable**.

---

## Key Features
- **Highly Configurable**: All operations are controlled via the external `config.ini` file — no code modification required.  
- **Generic Tag Handling**: Apply rules to any XML tags (e.g., actor, director, studio, genre, etc.).  
- **Comprehensive Cleaning Rule Set**: Built-in rules with on/off switches.  
- **Dual XML Mapping & Standardization**: Supports actor and general mapping files with intelligent merging.  
- **Safe Dry Run Mode**: Preview all changes before applying them.  
- **Efficient Concurrent Processing**: Multi-threaded design for handling large file sets.  

---

## File Structure
To run this tool properly, you need the following files in the same directory:

- `nfo_universal_cleaner.py`: Main script executing all logic.  
- `config.ini`: The “control center” where operations are defined.  
- `mapping_actor.xml`: Actor mapping file for standardized actor names.  
- `mapping_info.xml`: General mapping file for standardizing other tags (studio, series, etc.).  

---

## Feature Details

### 1. High Configurability (config.ini)
Control behavior precisely by editing `config.ini`, including paths, rule toggles, and custom parameters.

### 2. Generic Tag Handling
In the `[Tags]` section, specify any XML tags to process:

```ini
[Tags]
tags_to_clean =
    .//actor/name
    .//director
    .//studio
```

### 3. Comprehensive Cleaning Rule Set
Configured under `[Rules]` and `[RuleSettings]`:  

- **Truncate on Delimiter**  
  Example: `薫さん 21歳 大学生 -> 薫さん`  

- **Remove Patterns**  
  Example: `Studio Ghibli-tmdb-12345 -> Studio Ghibli`  

- **Normalize Whitespace**  
  Example: `John  Doe -> John Doe`  

- **Case Standardization**  
  Options: `lower` (lowercase), `title` (capitalize first letter).  

- **Remove Empty Tags**  
  Automatically deletes tags left empty after cleaning.  

### 4. XML Mapping & Standardization
- Cleaning is applied before mapping.  
- Both raw and cleaned text are used for lookup.  
- `mapping_actor.xml` rules take precedence over `mapping_info.xml`.  

### 5. Safe Dry Run Mode
In `config.ini`:

```ini
dry_run = True
```

- `True`: Preview only, no file modifications.  
- `False`: Apply and save modifications.  

### 6. Efficient Concurrent Processing
Utilizes `ThreadPoolExecutor` to speed up handling of large `.nfo` collections.

---

## Usage

### Step 1: Prepare Environment
Install Python (3.7+ recommended).  
Install required dependency:

```bash
pip install opencc-python-reimplemented
```

### Step 2: Prepare Files
Place these files in the same folder:
- `nfo_universal_cleaner.py`
- `config.ini`
- `mapping_actor.xml`
- `mapping_info.xml`

### Step 3: Modify Config
Edit `[Paths]` in `config.ini`:

```ini
scan_directory = your_nfo_directory
actor_mapping_xml = mapping_actor.xml
tag_mapping_xml = mapping_info.xml
```

### Step 4: Preview Run (Recommended)
Ensure `dry_run = True`.  
Run:

```bash
python nfo_universal_cleaner.py
```

Check console output for `(Planned Modification)` items.

### Step 5: Actual Run
If results are correct, change:

```ini
dry_run = False
```

Then run again:

```bash
python nfo_universal_cleaner.py
```

### Step 6: Check Logs
Errors (e.g., corrupted XML) will be logged in `cleaner_errors.log`.  

---

## Summary
This tool provides an **automated, customizable, and safe-to-preview** solution for maintaining a clean, standardized media library metadata system.  
**Tip: Always run Dry Run first to ensure results meet expectations!**
