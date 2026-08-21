# -*- coding: utf-8 -*-
"""
中文审计官方站点爬虫：审计署 / 中国内部审计协会 / 中国注册会计师协会。
列表页解析链接，并对每条链接抓取正文（保证 AI×审计 候选有实质内容）。
"""
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import HEADERS, REQUEST_TIMEOUT
from crawler.base import BaseCrawler, extract_summary


def _decode(resp) -> str:
    """优先 UTF-8，失败回退 GB18030（部分政府站点为 GBK）"""
    content = resp.content
    for enc in ("utf-8", "gb18030"):
        try:
            return content.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return content.decode("utf-8", errors="replace")


class AuditListCrawler(BaseCrawler):
    """通用中文审计站点列表爬虫（每站点一个实例）"""

    def __init__(self, source_config: dict):
        self.source_config = source_config
        self.source_name = source_config["name"]
        self.source_authority = float(source_config.get("authority", 0.88))
        self.base_url = (source_config.get("urls") or [""])[0]
        self.verify_ssl = False  # 政府/协会站点证书链常不完整
        super().__init__()

    def fetch(self) -> list[dict]:
        items = []
        for page_url in (self.source_config.get("urls") or []):
            try:
                items.extend(self._fetch_page(page_url))
            except Exception as e:
                print(f"  [审计:{self.source_name}] {page_url} 失败: {e}")
        print(f"  [审计:{self.source_name}] 共 {len(items)} 条")
        return items

    def _fetch_page(self, page_url: str) -> list[dict]:
        resp = self.get(page_url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return []
        html = _decode(resp)
        soup = BeautifulSoup(html, "lxml")
        candidates = []
        seen = set()
        for a in soup.select("a[href]"):
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if not title or len(title) < 8 or len(title) > 80:
                continue
            full = urljoin(page_url, href)
            if not full.startswith(("http://", "https://")):
                continue
            if full in seen:
                continue
            seen.add(full)
            # 列表页常见噪音
            low_title = title.lower()
            if any(k in low_title for k in [
                "更多", "版权所有", "隐私", "联系我们", "网站地图", "设为首页", "加入收藏",
                "skip to", "menu", "搜索", "登录", "注册", "订阅", "newsletter", "subscribe",
                "sign in", "login", "search", "about us", "联系我们", "privacy", "terms",
                "careers", "contact", "advertise", "editorial", "follow us", "cookie",
            ]):
                continue
            candidates.append((title, full))
            if len(candidates) >= 15:
                break

        items = []
        for title, full in candidates[:10]:
            body, summary = self._fetch_body(full)
            items.append(self.build_article(
                title=title,
                url=full,
                summary=summary,
                raw_text=body,
                published_at=datetime.now(),
                author=self.source_name,
                category="article",
                score=78.0,
                lang="cn",
            ))
        return items

    def _fetch_body(self, url: str) -> tuple[str, str]:
        """抓取正文（含正文则返回 body+summary；失败返回空）"""
        try:
            resp = self.get(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                return "", ""
            html = _decode(resp)
            soup = BeautifulSoup(html, "lxml")
            content = soup.find("article") or soup.find("main") or soup.find("body")
            if content is None:
                return "", ""
            for tag in content.find_all(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
                tag.decompose()
            text = content.get_text("\n", strip=True)
            text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
            if len(text) < 40:
                return "", ""
            return text[:4000], extract_summary(text)[:200]
        except Exception:
            return "", ""


def build_audit_crawlers(sources: list[dict]) -> list[BaseCrawler]:
    crawlers = []
    for cfg in sources:
        if cfg.get("kind") == "html" and cfg.get("audit") and cfg.get("enabled", True) and cfg.get("urls"):
            crawlers.append(AuditListCrawler(cfg))
    return crawlers
