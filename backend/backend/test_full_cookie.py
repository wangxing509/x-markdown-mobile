# -*- coding: utf-8 -*-
"""
获取完整知乎 cookie（包括 d_c0）然后调用 API
d_c0 可以通过访问知乎首页自动设置
"""
import sys, io, json, urllib.parse
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import httpx

Z_C0 = "2|1:0|10:1785306062|4:z_c0|92:Mi4xTVpJZEF3QUFBQUNqc3huc0ZqV3JIQ1lBQUFCZ0FsVk5KZWxXYXdDLVFnUmE1bXp1YUJBcld2a3NfZENmeHVELW1R|01e44e0841fba10056310ea246462bca137bbc77651aa581385390b9de0b35ff"

# 创建一个 session 先获取 d_c0
print("=== 第1步: 获取 d_c0 cookie ===")
client = httpx.Client(
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    },
    follow_redirects=True,
    timeout=15,
)

# 访问知乎首页获取 d_c0
r = client.get("https://www.zhihu.com/")
print(f"首页 Status: {r.status_code}")

# 提取 d_c0
d_c0 = None
# httpx 的 cookies 是 Cookies 对象，支持 .get()
d_c0 = client.cookies.get("d_c0")
if d_c0:
    print(f"获取到 d_c0: {d_c0[:30]}...")
else:
    print("未获取到 d_c0 cookie")

if not d_c0:
    print("未获取到 d_c0，尝试从 Set-Cookie 头提取...")
    set_cookie = r.headers.get("set-cookie", "")
    if "d_c0=" in set_cookie:
        import re
        match = re.search(r'd_c0=([^;]+)', set_cookie)
        if match:
            d_c0 = match.group(1)
            print(f"从 Set-Cookie 提取 d_c0: {d_c0[:30]}...")

# 构建 cookie 字符串
cookie_str = f"z_c0={Z_C0}"
if d_c0:
    cookie_str += f"; d_c0={d_c0}"
print(f"\n完整 Cookie: {cookie_str[:80]}...")

# 第2步: 用完整 cookie 调用 API
print("\n=== 第2步: 调用知乎 API ===")
api_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.zhihu.com/topic/19551275",
    "x-requested-with": "fetch",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "Cookie": cookie_str,
}

# 测试话题精华
print("\n--- 话题精华 ---")
url = "https://www.zhihu.com/api/v4/topics/19551275/feeds/top_activity"
params = {"include": "data[].target.content,voteup_count,comment_count,author.name", "limit": 3, "offset": 0}
r2 = client.get(url, headers=api_headers, params=params)
print(f"Status: {r2.status_code}")
if r2.status_code == 200:
    data = r2.json()
    items = data.get("data", [])
    print(f"获取到 {len(items)} 条精华回答")
    for i, entry in enumerate(items[:3]):
        target = entry.get("target", {})
        title = target.get("title", "") or (target.get("question", {}).get("title", "") if isinstance(target.get("question"), dict) else "")
        voteup = target.get("voteup_count", 0)
        print(f"  [{i+1}] voteup={voteup} title={title[:50]}")
else:
    print(f"Body: {r2.text[:200]}")

# 测试搜索
print("\n--- 搜索 ---")
url2 = f"https://www.zhihu.com/api/v4/search_v3?q={urllib.parse.quote('AI Agent')}&t=general&correction=1&offset=0&limit=3"
r3 = client.get(url2, headers={**api_headers, "Referer": "https://www.zhihu.com/search"}, )
print(f"Status: {r3.status_code}")
if r3.status_code == 200:
    data = r3.json()
    items = data.get("data", [])
    print(f"获取到 {len(items)} 条搜索结果")
else:
    print(f"Body: {r3.text[:200]}")

# 测试知乎热榜
print("\n--- 热榜 ---")
url3 = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=5"
r4 = client.get(url3, headers={**api_headers, "Referer": "https://www.zhihu.com/hot"})
print(f"Status: {r4.status_code}")
if r4.status_code == 200:
    data = r4.json()
    items = data.get("data", [])
    print(f"获取到 {len(items)} 条热榜")
else:
    print(f"Body: {r4.text[:200]}")

client.close()
