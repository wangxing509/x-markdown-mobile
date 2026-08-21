# -*- coding: utf-8 -*-
"""获取 d_c0 并测试知乎 API"""
import sys, io, json, re, urllib.parse
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import httpx

Z_C0 = "2|1:0|10:1785306062|4:z_c0|92:Mi4xTVpJZEF3QUFBQUNqc3huc0ZqV3JIQ1lBQUFCZ0FsVk5KZWxXYXdDLVFnUmE1bXp1YUJBcld2a3NfZENmeHVELW1R|01e44e0841fba10056310ea246462bca137bbc77651aa581385390b9de0b35ff"

# 第1步：获取 d_c0
print("=== 获取 d_c0 ===")
client = httpx.Client(
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-CN,zh;q=0.9",
    },
    follow_redirects=True,
    timeout=15,
)

# 访问首页
r = client.get("https://www.zhihu.com/")
print(f"首页: {r.status_code}")

# 从 Set-Cookie 提取 d_c0
d_c0 = None
set_cookie = r.headers.get("set-cookie", "")
if set_cookie:
    match = re.search(r'd_c0=([^;]+)', set_cookie)
    if match:
        d_c0 = match.group(1)
        print(f"d_c0: {d_c0[:40]}...")

# 也从 client cookies 获取
if not d_c0:
    d_c0 = client.cookies.get("d_c0")
    if d_c0:
        print(f"d_c0 (from cookies): {d_c0[:40]}...")

if not d_c0:
    # 尝试访问 api.zhihu.com 获取
    r2 = client.get("https://api.zhihu.com/")
    print(f"api.zhihu.com: {r2.status_code}")
    set_cookie2 = r2.headers.get("set-cookie", "")
    if set_cookie2:
        match = re.search(r'd_c0=([^;]+)', set_cookie2)
        if match:
            d_c0 = match.group(1)
            print(f"d_c0 (from api): {d_c0[:40]}...")

if not d_c0:
    print("未获取到 d_c0，使用默认值")
    d_c0 = "ALC6mP7PRhGPtamIk3AQ5h0Z8e1Md3-_KGc="

print(f"\n最终 d_c0: {d_c0}")

# 第2步：带 d_c0 + z_c0 调用 API
print("\n=== 测试 API ===")
cookie_str = f"z_c0={Z_C0}; d_c0={d_c0}"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.zhihu.com/",
    "Cookie": cookie_str,
    "x-requested-with": "fetch",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}

# 测试热榜
print("\n--- 热榜 ---")
r = client.get("https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=10", headers={**headers, "Referer": "https://www.zhihu.com/hot"})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    items = data.get("data", [])
    print(f"Items: {len(items)}")
    for i, item in enumerate(items[:3]):
        target = item.get("target", {})
        print(f"  [{i+1}] {target.get('title', '')[:50]}")
else:
    print(f"Body: {r.text[:200]}")

# 测试推荐
print("\n--- 推荐 ---")
r = client.get("https://www.zhihu.com/api/v3/feed/topstory/recommend?limit=5", headers={**headers, "Referer": "https://www.zhihu.com/"})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    items = data.get("data", [])
    print(f"Items: {len(items)}")
    for i, item in enumerate(items[:3]):
        target = item.get("target", {})
        print(f"  [{i+1}] type={target.get('type', '')} title={target.get('title', '')[:50]}")
else:
    print(f"Body: {r.text[:200]}")

# 测试问题回答
print("\n--- 问题回答 ---")
qid = "19550992"  # ChatGPT
r = client.get(f"https://www.zhihu.com/api/v4/questions/{qid}/answers?include=data.content,voteup_count,comment_count,author.name&limit=3&offset=0&sort_by=default", headers={**headers, "Referer": f"https://www.zhihu.com/question/{qid}"})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    items = data.get("data", [])
    print(f"Items: {len(items)}")
    for i, item in enumerate(items[:3]):
        print(f"  [{i+1}] voteup={item.get('voteup_count', 0)}")
else:
    print(f"Body: {r.text[:200]}")

client.close()
