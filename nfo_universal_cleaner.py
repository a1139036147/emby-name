import os
import xml.etree.ElementTree as ET
import configparser
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from opencc import OpenCC

# --- 日志记录设置 ---
def setup_logger(log_file):
    """配置日志记录器，用于记录错误。"""
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=log_file,
        filemode='w',
        encoding='utf-8'
    )

# --- 核心清理与映射逻辑 ---
class Cleaner:
    def __init__(self, config):
        self.config = config
        self.delimiters = config.get('RuleSettings', 'delimiters').split(',')
        self.patterns = [re.compile(p) for p in config.get('RuleSettings', 'patterns_to_remove').split(',') if p]
        self.case_format = config.get('RuleSettings', 'case_format')

    def apply_rules(self, text: str, mapping_dict: dict) -> str:
        """按顺序应用所有已启用的清理规则，最后进行映射。"""
        if not text:
            return ""

        original_text_for_mapping = text.strip()

        # 规则1：规范化空格
        if self.config.getboolean('Rules', 'normalize_whitespace'):
            text = text.replace('\u3000', ' ') # 全角空格转半角
            text = ' '.join(text.split())

        # 规则2：按分隔符截断
        if self.config.getboolean('Rules', 'truncate_on_delimiter'):
            first_pos = -1
            for char in self.delimiters:
                pos = text.find(char)
                if pos != -1 and (first_pos == -1 or pos < first_pos):
                    first_pos = pos
            if first_pos != -1:
                text = text[:first_pos]

        # 规则3：移除指定模式
        if self.config.getboolean('Rules', 'remove_patterns'):
            for pattern in self.patterns:
                text = pattern.sub('', text)

        # 清理首尾空格
        text = text.strip()

        # 规则4：大小写转换
        if self.config.getboolean('Rules', 'standardize_case'):
            if self.case_format == 'lower':
                text = text.lower()
            elif self.case_format == 'title':
                text = text.title()

        # 最后一步：标准化映射
        # 注意：使用清理前的原始文本进行映射查找，以匹配如 "演员A/别名" 这样的规则
        if mapping_dict and original_text_for_mapping in mapping_dict:
            return mapping_dict[original_text_for_mapping]
        # 如果原始文本没有匹配，再尝试用清理后的文本进行匹配
        if mapping_dict and text in mapping_dict:
            return mapping_dict[text]
            
        return text.strip()

# --- 文件处理 ---
def process_nfo_file(filepath: str, config, cleaner: Cleaner, mapping_dict: dict):
    """处理单个 NFO 文件，应用所有规则。"""
    basename = os.path.basename(filepath)
    is_modified = False
    change_logs = []
    # 从配置中读取要清理的标签列表，并去除空行
    tags_to_clean = [line.strip() for line in config.get('Tags', 'tags_to_clean').strip().split('\n') if line.strip()]

    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        parent_map = {c: p for p in root.iter() for c in p}

        for tag_path in tags_to_clean:
            elements = root.findall(tag_path)
            for elem in elements:
                if elem.text:
                    original_text = elem.text.strip()
                    cleaned_text = cleaner.apply_rules(original_text, mapping_dict)
                    
                    if original_text != cleaned_text:
                        is_modified = True
                        log_entry = f"  - <{elem.tag}> 清理: '{original_text}' -> '{cleaned_text}'"
                        
                        if not cleaned_text and config.getboolean('Rules', 'remove_empty_tags'):
                            if elem in parent_map:
                                parent_map[elem].remove(elem)
                                log_entry += " (标签已移除)"
                        else:
                            elem.text = cleaned_text
                        change_logs.append(log_entry)

        if is_modified and not config.getboolean('GeneralSettings', 'dry_run'):
            ET.indent(root, space="  ")
            tree.write(filepath, encoding='utf-8', xml_declaration=True)

        return (basename, is_modified, change_logs)

    except ET.ParseError as e:
        logging.error(f"XML解析错误: {filepath} - {e}")
        return (basename, False, [f"  ✗ 错误: XML格式错误。"])
    except Exception as e:
        logging.error(f"未知处理错误: {filepath} - {e}")
        return (basename, False, [f"  ✗ 错误: 处理失败。"])

def create_mapping_from_xml(xml_path: str) -> dict:
    """从 XML 文件加载映射规则，支持简繁体转换。"""
    mapping = {}
    if not xml_path or not os.path.exists(xml_path):
        return mapping
        
    cc_t2s = OpenCC('t2s')
    cc_s2t = OpenCC('s2t')
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for item in root.findall('.//a'):
            # 默认使用 zh_cn 字段
            target_value = item.get('zh_cn', '')
            if not target_value: continue
            
            keywords = item.get('keyword', '').split(',')
            for keyword in keywords:
                keyword = keyword.strip()
                if keyword:
                    mapping[keyword] = target_value
                    mapping[cc_t2s.convert(keyword)] = target_value
                    mapping[cc_s2t.convert(keyword)] = target_value
        print(f"成功从 '{os.path.basename(xml_path)}' 加载 {len(mapping)} 条映射规则。")
    except Exception as e:
        print(f"警告: 加载XML映射文件 '{xml_path}' 失败: {e}")
    return mapping

# --- 主程序 ---
def main():
    config_file = 'config.ini'
    if not os.path.exists(config_file):
        print(f"错误: 配置文件 '{config_file}' 未找到！请先创建它。")
        return
        
    config = configparser.ConfigParser()
    config.read(config_file, encoding='utf-8')
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(script_dir, "cleaner_errors.log")
    setup_logger(log_file)

    scan_dir = config.get('Paths', 'scan_directory')
    actor_xml_file = config.get('Paths', 'actor_mapping_xml')
    tag_xml_file = config.get('Paths', 'tag_mapping_xml')
    is_dry_run = config.getboolean('GeneralSettings', 'dry_run')

    print("=" * 50)
    print("      NFO 元数据通用整理工具 (XML增强版)")
    print("=" * 50)
    print(f"扫描目录: {scan_dir}")
    print(f"运行模式: {'预览模式 (Dry Run)' if is_dry_run else '正式运行 (Applying Changes)'}")
    
    # 加载并合并两个XML映射文件
    actor_mapping = create_mapping_from_xml(actor_xml_file)
    tag_mapping = create_mapping_from_xml(tag_xml_file)
    # 合并字典，演员映射规则优先级更高，会覆盖通用标签规则
    merged_mapping = {**tag_mapping, **actor_mapping}
    print(f"总计加载了 {len(merged_mapping)} 条唯一映射规则。")
    
    cleaner = Cleaner(config)
    
    print("\n--- 正在扫描文件... ---")
    nfo_paths = [os.path.join(r, f) for r, _, files in os.walk(scan_dir) for f in files if f.lower().endswith('.nfo')]
    print(f"--- 扫描完成，找到 {len(nfo_paths)} 个 .nfo 文件 ---\n")
    if not nfo_paths: return

    changed_count = 0
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_nfo_file, path, config, cleaner, merged_mapping): path for path in nfo_paths}
        
        for i, future in enumerate(as_completed(futures), 1):
            basename, is_modified, logs = future.result()
            progress = f"[进度 {i}/{len(nfo_paths)}]"
            if is_modified:
                changed_count += 1
                status = "计划修改" if is_dry_run else "已修改"
                print(f"{progress} 文件: {basename} ({status})")
                for log in logs:
                    print(log)
            elif logs: # 打印错误
                 print(f"{progress} 文件: {basename} (错误)")
                 for log in logs:
                    print(log)

    print("\n--- 整理完成 ---")
    action_word = "计划修改" if is_dry_run else "成功修改"
    print(f"总共扫描文件: {len(nfo_paths)}")
    print(f"{action_word}文件: {changed_count}")
    if is_dry_run:
        print("\n** 当前为预览模式，未对任何文件进行实际修改。 **")
        print("** 请检查以上日志，确认无误后将 config.ini 中的 dry_run 设置为 False 再运行。 **")

if __name__ == "__main__":
    main()
