# -*- coding: utf-8 -*-
"""
测试从浏览器 cookie 调用知乎 API
用户在浏览器登录知乎后，可以通过 cookie 调用需要认证的 API
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import httpx
import urllib.parse

# 知乎 API 需要的 cookie 字段
# 最关键的是 z_c0（登录后的认证 token）
# 用户需要从浏览器 F12 → Application → Cookies → zhihu.com → 找到 z_c0

# 先测试不带 cookie 的 API（确认 403）
headers_base = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/127.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': 'https://www.zhihu.com/',
    'Origin': 'https://www.zhihu.com',
}

# 测试1: 话题精华回答 API（需要认证）
print("=== 话题精华回答 API ===")
topic_id = 19551275  # 人工智能
url = f"https://www.zhihu.com/api/v4/topics/{topic_id}/feeds/top_activity"
params = {"include": "data[].target.content,voteup_count,comment_count", "limit": 5, "offset": 0}

# 不带 cookie
r = httpx.get(url, headers=headers_base, params=params, timeout=10)
print(f"无cookie: status={r.status_code}")

# 带假 cookie 测试（看返回什么错误）
fake_cookie = "z_c0=test"
r2 = httpx.get(url, headers={**headers_base, "Cookie": fake_cookie}, params=params, timeout=10)
print(f"假cookie: status={r2.status_code}")

# 测试2: 热门回答 API
print("\n=== 热门回答 API ===")
question_id = 19550992  # ChatGPT 话题
url2 = f"https://www.zhihu.com/api/v4/questions/{question_id}/answers"
params2 = {"include": "data.content,voteup_count,comment_count", "limit": 5, "offset": 0, "sort_by": "default"}
r3 = httpx.get(url2, headers=headers_base, params=params2, timeout=10)
print(f"无cookie: status={r3.status_code}")
if r3.status_code == 200:
    data = r3.json()
    items = data.get('data', [])
    print(f"items: {len(items) if isinstance(items, list) else 'N/A'}")

# 测试3: 搜索 API
print("\n=== 搜索 API ===")
search_url = f"https://www.zhihu.com/api/v4/search_v3"
params3 = {"q": "AI Agent", "t": "general", "correction": 1, "offset": 0, "limit": 5}
r4 = httpx.get(search_url, headers=headers_base, params=params3, timeout=10)
print(f"无cookie: status={r4.status_code}")

print("\n=== 结论 ===")
print("如果以上 API 都返回 401/403，需要用户从浏览器提取 z_c0 cookie")
print("请在浏览器中打开 zhihu.com，登录后:")
print("  F12 → Application → Cookies → zhihu.com")
print("  找到 z_c0 字段，复制其值")
