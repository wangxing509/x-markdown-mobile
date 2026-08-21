# -*- coding: utf-8 -*-
"""查找所有可能的浏览器 cookie 文件"""
import sys, io, os
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

home = Path.home()
appdata_local = home / "AppData" / "Local"
appdata_roaming = home / "AppData" / "Roaming"

# 搜索所有可能的浏览器目录
search_dirs = [
    appdata_local / "Google" / "Chrome",
    appdata_local / "Microsoft" / "Edge",
    appdata_local / "BraveSoftware",
    appdata_local / "Chromium",
    appdata_roaming / "Mozilla" / "Firefox",
    appdata_local / "Vivaldi",
    appdata_local / "Opera Software",
]

print("=== 搜索浏览器目录 ===")
for sd in search_dirs:
    if sd.exists():
        print(f"\n{sd}:")
        # 搜索所有 Cookies 文件
        for root, dirs, files in os.walk(sd):
            for f in files:
                if f.lower() == "cookies" or f.lower() == "cookies.sqlite":
                    fp = Path(root) / f
                    print(f"  {fp}")

# 也搜索 User Data 下的所有 Profile
print("\n=== Chrome/Edge User Data profiles ===")
for ud in [appdata_local / "Google" / "Chrome" / "User Data",
           appdata_local / "Microsoft" / "Edge" / "User Data"]:
    if ud.exists():
        print(f"\n{ud}:")
        for item in ud.iterdir():
            if item.is_dir():
                cookie_file = item / "Cookies"
                if cookie_file.exists():
                    print(f"  {cookie_file} (exists)")
                # Network\Cookies (新版 Chrome)
                net_cookie = item / "Network" / "Cookies"
                if net_cookie.exists():
                    print(f"  {net_cookie} (exists)")
