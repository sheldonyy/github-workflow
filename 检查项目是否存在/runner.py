#!/usr/bin/env python3
"""
命令行爬虫脚本 - 用于 GitHub Actions
直接读取 keywords.json 并运行搜索任务
"""
import json
import os
import sys
from datetime import datetime

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from utils import sarch_task, write_to_res, write_to_fail, ENCRYPTED_URL, XOR_KEY
from my_chrome import decrypt_url

# 验证解密
decrypted_url = decrypt_url(ENCRYPTED_URL, XOR_KEY)
print(f"[DEBUG] 解密后的 URL: {decrypted_url}")
if not decrypted_url.startswith("http"):
    print(f"[ERROR] 解密失败，URL 格式不正确！")
    sys.exit(1)


def load_keywords(json_file):
    """从 JSON 文件加载关键词列表"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_results(new_results, output_file):
    """保存结果到 JSON 文件（追加模式）"""
    existing_results = []
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_results = json.load(f)
        except json.JSONDecodeError:
            existing_results = []

    # 追加新结果
    existing_results.extend(new_results)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(existing_results, f, ensure_ascii=False, indent=2)


def main():
    # 确定 keywords 文件路径
    keywords_file = os.path.join(current_dir, 'keywords.json')

    if not os.path.exists(keywords_file):
        print(f"错误: 找不到 keywords.json 文件: {keywords_file}")
        sys.exit(1)

    # 加载关键词
    keywords = load_keywords(keywords_file)
    print(f"加载了 {len(keywords)} 个关键词")

    # 确保结果文件在正确目录
    os.chdir(current_dir)

    # 清空之前的结果文件（可选）
    res_file = os.path.join(current_dir, 'res.txt')
    fail_file = os.path.join(current_dir, 'fail.txt')

    # 清理旧结果（可选）
    # with open(res_file, 'w', encoding='utf-8') as f:
    #     f.write(f"# 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    # with open(fail_file, 'w', encoding='utf-8') as f:
    #     f.write("")

    results = []
    success_count = 0
    fail_count = 0
    zero_count = 0
    has_result_count = 0

    for i, keyword in enumerate(keywords, 1):
        print(f"[{i}/{len(keywords)}] 搜索: {keyword}")
        count = sarch_task(keyword)

        result_entry = {
            "keyword": keyword,
            "count": count,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        results.append(result_entry)

        if count == -1:
            fail_count += 1
            print(f"  -> 失败")
        elif count == 0:
            zero_count += 1
            print(f"  -> 存在但无结果 (0条)")
        else:
            has_result_count += 1
            print(f"  -> 有结果 ({count}条)")

        success_count += 1

    # 保存 JSON 格式的结果
    output_file = os.path.join(current_dir, 'results.json')
    save_results(results, output_file)

    # 打印统计
    print("\n" + "=" * 50)
    print(f"搜索完成!")
    print(f"总计: {len(keywords)} 个关键词")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"无结果(0条): {zero_count}")
    print(f"有结果: {has_result_count}")
    print(f"=" * 50)
    print(f"结果已保存到: {output_file}")


if __name__ == "__main__":
    main()
