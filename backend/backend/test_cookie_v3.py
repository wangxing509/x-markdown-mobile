# -*- coding: utf-8 -*-
"""调试知乎 API 认证 - 添加完整请求头"""
import sys, io, json, urllib.parse
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import httpx

Z_C0 = "2|1:0|10:1785306062|4:z_c0|92:Mi4xTVpJZEF3QUFBQUNqc3huc0ZqV3JIQ1lBQUFCZ0FsVk5KZWxXYXdDLVFnUmE1bXp1YUJBcld2a3NfZENmeHVELW1R|01e44e0841fba10056310ea246462bca137bbc77651aa581385390b9de0b35ff"

# 完整的浏览器请求头（模拟真实浏览器）
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.zhihu.com/topic/19551275",
    "Origin": "https://www.zhihu.com",
    "Cookie": f"z_c0={Z_C0}; _zap=1; d_c0=ALC6mP7PRhGPtamIk3AQ5h0Z8e1Md3-_KGc=; __zhipin_id=1",
    "x-requested-with": "fetch",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "sec-ch-ua": '"Chromium";v="127", "Not?A_Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

# 测试1: 话题精华
print("=== 话题精华 ===")
url = "https://www.zhihu.com/api/v4/topics/19551275/feeds/top_activity"
params = {"include": "data[].target.content,voteup_count,comment_count,author.name", "limit": 3, "offset": 0}
r = httpx.get(url, headers=headers, params=params, timeout=15, follow_redirects=True)
print(f"Status: {r.status_code}")
print(f"Response headers: {dict(list(r.headers.items())[:5])}")
if r.status_code == 200:
    data = r.json()
    items = data.get("data", [])
    print(f"Items: {len(items)}")
else:
    print(f"Body: {r.text[:300]}")

# 测试2: 获取问题回答
print("\n=== 问题回答 ===")
url2 = "https://www.zhihu.com/api/v4/questions/19550992/answers"
params2 = {"include": "data.content,voteup_count,comment_count,author.name", "limit": 3, "offset": 0, "sort_by": "default"}
r2 = httpx.get(url2, headers=headers, params=params2, timeout=15, follow_redirects=True)
print(f"Status: {r2.status_code}")
if r2.status_code == 200:
    data = r2.json()
    items = data.get("data", [])
    print(f"Items: {len(items)}")
else:
    print(f"Body: {r2.text[:300]}")

# 测试3: 热门文章
print("\n=== 热门文章 ===")
url3 = "https://www.zhihu.com/api/v4/topstory/recommend"
params3 = {"limit": 3, "offset": 0}
r3 = httpx.get(url3, headers=headers, params=params3, timeout=15, follow_redirects=True)
print(f"Status: {r3.status_code}")
if r3.status_code == 200:
    data = r3.json()
    items = data.get("data", [])
    print(f"Items: {len(items)}")
    if items:
        first = items[0].get("target", {})
        print(f"  type: {first.get('type', '')}")
        print(f"  title: {first.get('title', '')[:50]}")
else:
    print(f"Body: {r3.text[:300]}")

# 测试4: 搜索
print("\n=== 搜索 ===")
url4 = f"https://www.zhihu.com/api/v4/search_v3?q={urllib.parse.quote('AI Agent')}&t=general&correction=1&offset=0&limit=3"
r4 = httpx.get(url4, headers={**headers, "Referer": "https://www.zhihu.com/search"}, timeout=15, follow_redirects=True)
print(f"Status: {r4.status_code}")
if r4.status_code == 200:
    data = r4.json()
    items = data.get("data", [])
    print(f"Items: {len(items)}")
else:
    print(f"Body: {r4.text[:300]}")
