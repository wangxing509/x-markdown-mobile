# -*- coding: utf-8 -*-
"""测试知乎热榜 API 和其他不需要签名的 API"""
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import httpx

Z_C0 = "2|1:0|10:1785306062|4:z_c0|92:Mi4xTVpZEF3QUFBQUNqc3huc0ZqV3JIQ1lBQUFCZ0FsVk5KZWxXYXdDLVFnUmE1bXp1YUJBcld2a3NfZENmeHVELW1R|01e44e0841fba10056310ea246462bca137bbc77651aa581385390b9de0b35ff"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/127.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cookie": f"z_c0={Z_C0}",
}

# 热榜详情
print("=== 热榜详情 ===")
url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50"
r = httpx.get(url, headers={**headers, "Referer": "https://www.zhihu.com/hot"}, timeout=15)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    items = data.get("data", [])
    print(f"获取到 {len(items)} 条热榜")
    for i, item in enumerate(items[:5]):
        target = item.get("target", {})
        title = target.get("title", "") or target.get("display_content", "")
        answer_count = target.get("answer_count", 0) or item.get("detail_text", "")
        url2 = target.get("url", "") or ""
        print(f"  [{i+1}] {title[:50]}")
        print(f"      detail: {item.get('detail_text', '')[:60]}")
        print(f"      url: {url2[:60]}")

# 热榜分类（AI/科技相关）
print("\n=== 热榜分类 ===")
hot_categories = [
    "tech",     # 科技
    "science",  # 科学
]
for cat in hot_categories:
    url = f"https://www.zhihu.com/api/v3/feed/topstory/hot-lists/{cat}?limit=20"
    r = httpx.get(url, headers={**headers, "Referer": f"https://www.zhihu.com/hot/{cat}"}, timeout=15)
    print(f"{cat}: status={r.status_code}")
    if r.status_code == 200:
        data = r.json()
        items = data.get("data", [])
        print(f"  items: {len(items)}")
        if items:
            target = items[0].get("target", {})
            print(f"  first: {target.get('title', '')[:50]}")

# 推荐流
print("\n=== 推荐流 ===")
url = "https://www.zhihu.com/api/v3/feed/topstory/recommend?limit=10"
r = httpx.get(url, headers={**headers, "Referer": "https://www.zhihu.com/"}, timeout=15)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    items = data.get("data", [])
    print(f"Items: {len(items)}")
    if items:
        for i, item in enumerate(items[:3]):
            target = item.get("target", {})
            print(f"  [{i+1}] type={target.get('type', '')} title={target.get('title', '')[:50]}")

# 问题相关回答（不需要签名）
print("\n=== 问题回答 ===")
question_ids = [
    ("19550992", "ChatGPT"),
    ("19551275", "人工智能"),
    ("26647135", "大语言模型"),
]
for qid, name in question_ids:
    url = f"https://www.zhihu.com/api/v4/questions/{qid}/answers?include=data.content,voteup_count,comment_count,author.name&limit=3&offset=0&sort_by=default"
    r = httpx.get(url, headers={**headers, "Referer": f"https://www.zhihu.com/question/{qid}"}, timeout=15)
    print(f"{name}: status={r.status_code}")
    if r.status_code == 200:
        data = r.json()
        items = data.get("data", [])
        print(f"  items: {len(items)}")
        if items:
            first = items[0]
            print(f"  first voteup: {first.get('voteup_count', 0)}")
            author = first.get("author", {}) or {}
            print(f"  author: {author.get('name', '') if isinstance(author, dict) else ''}")
