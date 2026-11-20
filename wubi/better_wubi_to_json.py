#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Better Wubi 字典转 JSON 工具
将 better-wubi.dict 文件转换为 JSON 格式
格式：{"汉字": "编码"}
"""

import json
import sys
from pathlib import Path

def parse_better_wubi_dict(file_path):
    """
    解析 better-wubi.dict 文件

    Args:
        file_path (str): 字典文件路径

    Returns:
        dict: 汉字到编码的映射字典
    """
    wubi_dict = {}
    line_count = 0
    processed_count = 0

    try:
        print(f"开始解析文件: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line_count += 1
                line = line.strip()

                # 跳过空行
                if not line:
                    continue

                # 分割行，格式为：编码 汉字
                parts = line.split(' ', 1)  # 只分割第一个空格
                if len(parts) >= 2:
                    code = parts[0].strip()
                    text = parts[1].strip()

                    # 确保编码和文本都不为空
                    if code and text:
                        # 如果同一个汉字有多个编码，我们可以选择保留第一个或处理重复
                        if text in wubi_dict:
                            # 如果已存在，可以选择保留更短的编码
                            if len(code) < len(wubi_dict[text]):
                                wubi_dict[text] = code
                        else:
                            wubi_dict[text] = code

                        processed_count += 1

                # 每处理10000行打印一次进度
                if line_count % 10000 == 0:
                    print(f"已处理 {line_count} 行，有效条目 {processed_count} 个")

        print(f"\n解析完成！")
        print(f"总行数: {line_count}")
        print(f"有效条目: {processed_count}")
        print(f"唯一汉字/词组: {len(wubi_dict)}")

    except FileNotFoundError:
        print(f"错误：找不到文件 {file_path}")
        return {}
    except Exception as e:
        print(f"解析文件时出错：{e}")
        return {}

    return wubi_dict

def save_to_json(data, output_path, compact=False):
    """
    将数据保存为JSON格式

    Args:
        data (dict): 要保存的数据
        output_path (str): 输出文件路径
        compact (bool): 是否使用紧凑格式
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            if compact:
                json.dump(data, file, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
            else:
                json.dump(data, file, ensure_ascii=False, indent=2, sort_keys=True)

        # 计算文件大小
        file_size = Path(output_path).stat().st_size
        size_mb = file_size / (1024 * 1024)

        print(f"结果已保存到: {output_path}")
        print(f"文件大小: {size_mb:.2f} MB")

    except Exception as e:
        print(f"保存文件时出错：{e}")

def analyze_data(wubi_dict):
    """
    分析字典数据

    Args:
        wubi_dict (dict): 五笔字典数据
    """
    print("\n=== 数据分析 ===")
    print(f"总条目数：{len(wubi_dict)}")

    # 统计单字和词组
    single_chars = {k: v for k, v in wubi_dict.items() if len(k) == 1}
    multi_chars = {k: v for k, v in wubi_dict.items() if len(k) > 1}

    print(f"单字数量：{len(single_chars)}")
    print(f"词组数量：{len(multi_chars)}")

    # 统计编码长度分布
    code_lengths = {}
    for text, code in wubi_dict.items():
        length = len(code)
        code_lengths[length] = code_lengths.get(length, 0) + 1

    print("\n编码长度分布：")
    for length in sorted(code_lengths.keys()):
        print(f"  {length}位编码：{code_lengths[length]} 个")

    # 统计文本长度分布
    text_lengths = {}
    for text in wubi_dict.keys():
        length = len(text)
        text_lengths[length] = text_lengths.get(length, 0) + 1

    print("\n文本长度分布：")
    for length in sorted(text_lengths.keys())[:10]:  # 只显示前10种长度
        print(f"  {length}字：{text_lengths[length]} 个")

    # 显示一些示例
    print("\n单字示例（前10个）：")
    count = 0
    for char, code in single_chars.items():
        if count >= 10:
            break
        print(f"  \"{char}\": \"{code}\"")
        count += 1

    if multi_chars:
        print("\n词组示例（前5个）：")
        count = 0
        for word, code in multi_chars.items():
            if count >= 5:
                break
            print(f"  \"{word}\": \"{code}\"")
            count += 1

def main():
    """主函数"""
    print("Better Wubi 字典转 JSON 工具")
    print("=" * 50)

    # 输入文件路径
    input_file = "better-wubi.dict"

    # 检查文件是否存在
    if not Path(input_file).exists():
        print(f"错误：找不到文件 {input_file}")
        return

    # 解析字典
    wubi_dict = parse_better_wubi_dict(input_file)

    if not wubi_dict:
        print("解析失败或文件为空")
        return

    # 分析数据
    analyze_data(wubi_dict)

    # 保存完整数据（格式化）
    output_file = "better_wubi_complete.json"
    save_to_json(wubi_dict, output_file, compact=False)

    # 保存完整数据（紧凑格式）
    output_file_compact = "better_wubi_complete_compact.json"
    save_to_json(wubi_dict, output_file_compact, compact=True)

    # 保存仅单字数据
    single_chars = {k: v for k, v in wubi_dict.items() if len(k) == 1}
    single_output_file = "better_wubi_single_chars.json"
    save_to_json(single_chars, single_output_file, compact=False)

    print(f"\n完成！生成了三个文件：")
    print(f"  {output_file} - 包含所有数据（格式化）")
    print(f"  {output_file_compact} - 包含所有数据（紧凑格式）")
    print(f"  {single_output_file} - 仅包含单字数据")

    # 显示JSON字符串示例（前10个单字）
    print(f"\nJSON字符串示例（前10个单字）：")
    sample_dict = dict(list(single_chars.items())[:10])
    sample_json = json.dumps(sample_dict, ensure_ascii=False, sort_keys=True)
    print(sample_json)

if __name__ == "__main__":
    main()
