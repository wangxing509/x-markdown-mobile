# -*- coding: utf-8 -*-
"""
B站爬虫：搜索 API 获取 AI 技术区高赞视频
使用旧版 search/type 接口（无需 wbi 签名）
"""
from datetime import datetime
import re
import urllib.parse
from config import SOURCE_AUTHORITY
from crawler.base import BaseCrawler


class BilibiliCrawler(BaseCrawler):
    source_name = "B站"
    source_authority = SOURCE_AUTHORITY["B站"]
    base_url = "https://www.bilibili.com"

    # AI 相关搜索关键词
    SEARCH_KEYWORDS = [
        "AI教程", "大模型", "LLM", "AI Agent", "人工智能",
        "ChatGPT", "机器学习", "深度学习", "AI工具", "AIGC",
    ]

    def fetch(self) -> list[dict]:
        articles = []
        seen = set()
        # 先获取首页 cookie
        try:
            self.get("https://www.bilibili.com")
        except Exception:
            pass

        # 保底关键词：点击量排序优先，不足则按发布时间补充
        for kw in self.SEARCH_KEYWORDS:
            if len(articles) >= 10:
                break
            try:
                items = self._fetch_search(kw, order="click")
                for it in items:
                    if it["bvid"] not in seen:
                        seen.add(it["bvid"])
                        articles.append(it)
            except Exception as e:
                print(f"  [B站] {kw} 失败: {e}")

        # 保底：不足 10 条时按发布时间补充，确保 ≥10 条高质量视频
        if len(articles) < 10:
            for kw in ["人工智能", "AI技术", "大模型", "机器学习教程", "深度学习"]:
                if len(articles) >= 10:
                    break
                try:
                    items = self._fetch_search(kw, order="pubdate")
                    for it in items:
                        if it["bvid"] not in seen:
                            seen.add(it["bvid"])
                            articles.append(it)
                except Exception as e:
                    print(f"  [B站] 保底 {kw} 失败: {e}")

        print(f"  [B站] 共获取 {len(articles)} 条视频")
        return articles

    # 低质/广告标题过滤
    SPAM_TITLE = [
        r"(招生|培训|课程|加盟|代刷|代做|免费领|扫码|广告|推广|商务合作)",
    ]

    # AI 强相关必含词：标题必须含至少一个，避免关键词误命中（如"切玻璃""小蜜蜂"）
    AI_REQUIRED = [
        "AI", "人工智能", "大模型", "LLM", "GPT", "ChatGPT", "DeepSeek", "Qwen",
        "机器学习", "深度学习", "神经网络", "Transformer", "Stable Diffusion",
        "Diffusion", "Agent", "智能体", "文心", "通义", "Claude", "Gemini",
        "ComfyUI", "Midjourney", "Sora", "RAG", "微调", "多模态", "AIGC",
        "PyTorch", "TensorFlow", "算力", "提示词", "Prompt",
    ]

    # 明显的非技术/生活娱乐词：命中则视为无关，直接剔除
    AI_NEGATIVE = [
        "料理", "拉面", "做菜", "美食", "菜谱", "烹饪", "鸡汤", "ASMR",
        "踩点", "小蜜蜂", "儿歌", "舞蹈", "鬼畜", "萌宠", "猫", "狗",
        "健身", "瑜伽", "穿搭", "美妆", "护肤", "旅游", "vlog", "日常",
    ]

    def _fetch_search(self, keyword: str, order: str = "click") -> list[dict]:
        """通过搜索 API 获取视频（旧版接口，无需 wbi 签名）

        order=click 按点击量，order=pubdate 按发布时间。
        返回规范化的视频条目（URL 带 https，可直接跳转打开）。
        """
        url = "https://api.bilibili.com/x/web-interface/search/type"
        params = {
            "search_type": "video",
            "keyword": keyword,
            "order": order,
            "page": 1,
        }
        headers = {
            **self.client.headers,
            "Referer": f"https://search.bilibili.com/all?keyword={urllib.parse.quote(keyword)}",
            "Origin": "https://www.bilibili.com",
        }
        resp = self.client.get(url, params=params, headers=headers)
        if resp.status_code != 200:
            return []

        try:
            data = resp.json()
        except Exception:
            return []

        if data.get("code") != 0:
            print(f"  [B站] {keyword}: code={data.get('code')}, msg={data.get('message', '')[:60]}")
            return []

        items = []
        results = data.get("data", {}).get("result", []) if isinstance(data.get("data"), dict) else []
        for v in results[:15]:
            if not isinstance(v, dict):
                continue
            title = v.get("title", "")
            # 清理 HTML 高亮标签
            title = title.replace("<em class=\"keyword\">", "").replace("</em>", "")
            bvid = v.get("bvid", "")
            if not bvid or not title:
                continue
            # 过滤广告/营销标题
            if any(re.search(p, title) for p in self.SPAM_TITLE):
                continue
            # AI 强相关校验：标题必须含 AI 技术词，避免关键词误命中
            if not any(w.lower() in title.lower() for w in self.AI_REQUIRED):
                continue
            # 剔除明显无关的生活/娱乐类视频
            if any(w.lower() in title.lower() for w in self.AI_NEGATIVE):
                continue
            # 规范化 URL：强制 https 前缀，确保点击标题可正常跳转打开视频
            video_url = f"https://www.bilibili.com/video/{bvid}"
            play = v.get("play", 0) or 0
            video_review = v.get("video_review", 0) or v.get("review", 0) or 0
            author = v.get("author", "")
            pubdate = v.get("pubdate", 0)

            # 综合评分：播放量为主，弹幕/评论加权
            score = int(play / 10 + (v.get("danmaku", 0) or 0) / 100 + video_review)

            items.append(self.build_article(
                title=title,
                url=video_url,
                summary=(v.get("description", "") or "")[:200],
                published_at=datetime.fromtimestamp(pubdate) if pubdate else None,
                likes=play,
                comments=video_review,
                author=author,
                category="video",
                score=score,
                bvid=bvid,
            ))
        print(f"  [B站] {keyword}({order}): {len(items)} 条")
        return items
