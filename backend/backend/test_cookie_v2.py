# -*- coding: utf-8 -*-
"""测试知乎 cookie 认证 API"""
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import httpx

# 检查 cookie 文件
COOKIE_FILE = Path.home() / ".zhihu_cookie.json"
print(f"Cookie 文件: {COOKIE_FILE}")
print(f"存在: {COOKIE_FILE.exists()}")

if COOKIE_FILE.exists():
    data = json.loads(COOKIE_FILE.read_text(encoding='utf-8'))
    z_c0 = data.get("z_c0", "")
    print(f"z_c0 长度: {len(z_c0)}")
    print(f"z_c0 前30字符: {z_c0[:30]}...")
else:
    print("Cookie 文件不存在，请先运行 zhihu_login.py")
    sys.exit(0)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/127.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.zhihu.com/',
    'Cookie': f'z_c0={z_c0}',
}

# 测试1: 话题精华回答
print("\n=== 话题精华回答 ===")
topic_id = 19551275  # 人工智能
url = f"https://www.zhihu.com/api/v4/topics/{topic_id}/feeds/top_activity"
params = {"include": "data[].target.content,voteup_count,comment_count,author.name,author.follower_count", "limit": 5, "offset": 0}
r = httpx.get(url, headers=headers, params=params, timeout=15)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    items = data.get("data", [])
    print(f"获取: {len(items)} 条")
    for i, entry in enumerate(items[:3]):
        target = entry.get("target", {})
        title = target.get("title", "") or (target.get("question", {}).get("title", "") if isinstance(target.get("question"), dict) else "")
        voteup = target.get("voteup_count", 0)
        author = target.get("author", {})
        author_name = author.get("name", "") if isinstance(author, dict) else ""
        content_len = len(target.get("content", "") or "")
        print(f"  [{i+1}] voteup={voteup} author={author_name}")
        print(f"      title: {title[:60]}")
        print(f"      content_len: {content_len}")
else:
    print(f"Body: {r.text[:200]}")

# 测试2: 搜索
print("\n=== 搜索 ===")
import urllib.parse
search_url = f"https://www.zhihu.com/api/v4/search_v3?q={urllib.parse.quote('AI Agent')}&t=general&correction=1&offset=0&limit=5"
r2 = httpx.get(search_url, headers={**headers, 'Referer': 'https://www.zhihu.com/search?q=AI'}, timeout=15)
print(f"Status: {r2.status_code}")
if r2.status_code == 200:
    data = r2.json()
    items = data.get("data", [])
    print(f"获取: {len(items)} 条")
    for i, entry in enumerate(items[:3]):
        obj = entry.get("object", {})
        title = obj.get("title", "")
        voteup = obj.get("voteup_count", 0)
        print(f"  [{i+1}] voteup={voteup} title={title[:60]}")
else:
    print(f"Body: {r2.text[:200]}")
