# -*- coding: utf-8 -*-
"""
每日文章生成脚本（阶段 2）
由 GitHub Actions 每天定时调用：生成一篇「寓言式」文章，存入 content/ 目录。

- 零依赖：只使用 Python 标准库，不装任何第三方包
- 安全：API 密钥从环境变量 DEEPSEEK_API_KEY 读取，永不写入代码或仓库
- 幂等：当天文章已存在则跳过，可安全重复运行
- 容错：生成失败自动重试，最多 3 次
"""

import json
import os
import random
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

# ---------- 配置 ----------
# 北京时间（UTC+8，中国无夏令时）
TZ = timezone(timedelta(hours=8))

# 领域池（见 docs/requirements.md 4.2）
FIELDS = ["数学", "物理", "哲学", "经济学", "心理学", "计算机科学", "生物学", "语言学"]

# 文章目录（脚本在仓库根目录下运行）
CONTENT_DIR = "content"
INDEX_FILE = os.path.join(CONTENT_DIR, "index.json")

API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"

# 选题时避开最近几天的领域
RECENT_DAYS = 7

# 原始提示词（来自 docs/requirements.md 4.1，逐字保留）
BASE_PROMPT = (
    "请你从某个领域里，选择一个研究生水平的概念。然后写一个寓言故事，"
    "用间接的方式把这个概念讲清楚。不要一开始就说答案，尽量到故事快结束的时候，"
    "才让人意识到原来讲的是这个概念。故事结束后，再解释这个概念，"
    "以及故事里的隐喻分别对应什么。"
)

# 要求 AI 输出的固定格式，便于校验和入库
OUTPUT_FORMAT = """请严格按以下 Markdown 格式输出，不要有任何多余内容：

---
field: 领域名称
concept: 概念名称
title: 故事标题
---
## 故事
（寓言故事正文，3-5 段）

## 概念解释
（用通俗语言解释这个概念，1-2 段）

## 隐喻对应
- 故事元素A：对应的概念含义
- 故事元素B：对应的概念含义
（列出 4-6 条隐喻对应）
"""


# ---------- 工具函数 ----------

def today_str():
    """返回北京时间今天的日期字符串，如 2026-08-28"""
    return datetime.now(TZ).strftime("%Y-%m-%d")


def load_index():
    """读取文章索引；索引不存在或损坏时返回空列表"""
    try:
        with open(INDEX_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def pick_field(index):
    """从领域池随机选题，避开最近 RECENT_DAYS 天用过的领域"""
    recent = {item.get("field") for item in index[:RECENT_DAYS]}
    candidates = [f for f in FIELDS if f not in recent]
    # 领域池太小、避不开时，退回全量池
    return random.choice(candidates or FIELDS)


def normalize_concept(c):
    """规范化概念名（去括号内容、去空白与分隔符），用于重复判断"""
    c = re.sub(r"[（(].*?[)）]", "", c)
    c = re.sub(r"[\s·\-—/、]", "", c)
    return c.lower()


def used_concepts(index):
    """收集历史已用概念：原文列表（给 AI 看）+ 规范化集合（程序判断用）"""
    raw = [i.get("concept", "") for i in index if i.get("concept")]
    return raw, {normalize_concept(c) for c in raw}


def is_duplicate_concept(candidate, used_norm):
    """判断候选概念是否与历史重复（完全相同，或相互包含如 熵 与 熵增原理）"""
    cand = normalize_concept(candidate)
    if not cand:
        return False
    for u in used_norm:
        if cand == u:
            return True
        if len(cand) >= 2 and len(u) >= 2 and (cand in u or u in cand):
            return True
    return False


def call_api(api_key, field, used):
    """调用 DeepSeek API，返回文章文本；used 为已用概念，要求 AI 避开；失败时抛出异常"""
    user_prompt = BASE_PROMPT + "\n\n今天请从「" + field + "」领域选题。"
    if used:
        user_prompt += ("\n\n以下概念已经在过去的文章里讲过了，请务必选择一个新的、"
                        "不同的概念，不要与它们重复或雷同：\n" + "、".join(used))
    user_prompt += "\n\n" + OUTPUT_FORMAT
    messages = [
        {"role": "system",
         "content": "你是一位文笔优美的知识作家，擅长用寓言故事讲解深刻的概念。"},
        {"role": "user",
         "content": user_prompt},
    ]
    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "temperature": 0.9,   # 寓言写作需要一点创造力
        "max_tokens": 4000,   # 一篇完整文章足够
    }).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key,
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def validate_article(text):
    """校验文章是否包含完整的三段结构"""
    for marker in ("## 故事", "## 概念解释", "## 隐喻对应"):
        if marker not in text:
            return False
    return True


def parse_frontmatter(text):
    """从文章头部解析 field/concept/title 三个字段"""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    meta = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    return meta


# ---------- 主流程 ----------

def main():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        sys.exit("错误：未找到环境变量 DEEPSEEK_API_KEY")

    # 日期：默认今天；也可用命令行参数指定（补跑某天，格式 YYYY-MM-DD）
    date = today_str()
    if len(sys.argv) > 1:
        date = sys.argv[1]
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            sys.exit("错误：日期格式应为 YYYY-MM-DD，例如 2026-08-27")
    article_path = os.path.join(CONTENT_DIR, date + ".md")
    if os.path.exists(article_path):
        print("今日文章已存在，跳过：", date)
        return

    index = load_index()
    field = pick_field(index)
    used_raw, used_norm = used_concepts(index)
    print("今日领域：", field, "| 已用概念数：", len(used_raw))

    # 生成文章：失败、结构不完整或概念与历史重复则重试，最多 3 次
    text = None
    for attempt in range(3):
        try:
            candidate = call_api(api_key, field, used_raw)
            if not validate_article(candidate):
                print("第 %d 次生成的结构不完整，重试" % (attempt + 1))
                continue
            concept = parse_frontmatter(candidate).get("concept", "")
            if is_duplicate_concept(concept, used_norm):
                print("第 %d 次生成的概念与历史重复（%s），重试" % (attempt + 1, concept))
                continue
            text = candidate
            break
        except Exception as e:
            print("第 %d 次生成失败：%s" % (attempt + 1, e))
    if not text:
        sys.exit("错误：3 次尝试后仍未生成有效文章")

    # 保存文章
    os.makedirs(CONTENT_DIR, exist_ok=True)
    with open(article_path, "w", encoding="utf-8") as f:
        f.write(text)

    # 更新索引（最新文章在最前）
    meta = parse_frontmatter(text)
    entry = {
        "date": date,
        "field": meta.get("field", field),
        "concept": meta.get("concept", ""),
        "title": meta.get("title", ""),
    }
    index = [i for i in index if i.get("date") != date]  # 去重后插入
    index.insert(0, entry)
    index.sort(key=lambda x: x["date"], reverse=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print("已生成文章：", date, entry)


if __name__ == "__main__":
    main()
