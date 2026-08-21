# -*- coding: utf-8 -*-
"""
HTML → Markdown 转换模块
优化：GitHub URL 使用 README API；其他 URL 用 HTML 爬取
"""
import httpx
from bs4 import BeautifulSoup
from config import HEADERS, REQUEST_TIMEOUT, HTTP_PROXY
from crawler.base import extract_summary, clean_html


def _fetch_github_readme(url: str) -> dict | None:
    """GitHub repo URL → 通过 API 获取 README"""
    # 从 URL 提取 owner/repo[/subdir]
    parts = url.rstrip("/").split("/")
    gh_idx = -1
    for i, p in enumerate(parts):
        if p == "github.com":
            gh_idx = i
            break
    if gh_idx < 0 or gh_idx + 2 >= len(parts):
        return None
    owner = parts[gh_idx + 1]
    repo = parts[gh_idx + 2]
    rest = parts[gh_idx + 3:]

    # tree 链接：定位到子目录 README（如 /tree/master/实践案例/OCR）
    subdir = ""
    if "/tree/" in url:
        try:
            tree_idx = rest.index("tree")
            subdir = "/".join(rest[tree_idx + 2:])
        except ValueError:
            pass

    api_path = f"repos/{owner}/{repo}"
    if subdir:
        api_path += f"/contents/{subdir}/README.md"

    try:
        api_url = f"https://api.github.com/{api_path}"
        client = httpx.Client(
            headers={**HEADERS, "Accept": "application/vnd.github.v3.raw+json"},
            timeout=httpx.Timeout(12, connect=6),
            follow_redirects=True,
            proxy=HTTP_PROXY if HTTP_PROXY else None,
        )
        resp = client.get(api_url)
        client.close()
        if resp.status_code == 200:
            content = resp.text
            # 如果是 HTML，转为纯文本
            if content.strip().startswith("<"):
                content = clean_html(content)
            # 限制长度
            if len(content) > 20000:
                content = content[:20000] + "\n\n...(内容过长已截断)"
            return {
                "markdown": f"# {owner}/{repo}" + (f"/{subdir}" if subdir else "") + f"\n\n{content}\n\n---\n> 来源: {url}",
                "title": f"{repo}" + (f"/{subdir}" if subdir else ""),
                "sourceUrl": url,
                "category": "tutorial" if subdir else "model",
            }
    except Exception as e:
        print(f"  [GitHub README] {owner}/{repo} 失败: {e}")

    if subdir:
        # 大小写兜底：readme.md
        try:
            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{subdir}/readme.md"
            client = httpx.Client(
                headers={**HEADERS, "Accept": "application/vnd.github.v3.raw+json"},
                timeout=httpx.Timeout(12, connect=6),
                follow_redirects=True,
                proxy=HTTP_PROXY if HTTP_PROXY else None,
            )
            resp = client.get(api_url)
            client.close()
            if resp.status_code == 200 and not resp.text.strip().startswith("["):
                content = resp.text
                if len(content) > 20000:
                    content = content[:20000] + "\n\n...(内容过长已截断)"
                return {
                    "markdown": f"# {owner}/{repo}/{subdir}\n\n{content}\n\n---\n> 来源: {url}",
                    "title": f"{repo}/{subdir}",
                    "sourceUrl": url,
                    "category": "tutorial",
                }
        except Exception as e:
            print(f"  [GitHub README] readme.md 兜底失败: {e}")
    return None


def convert_url_to_markdown(url: str) -> dict:
    """
    将网页 URL 的内容转为 Markdown 格式
    返回: {markdown, title, sourceUrl, category}
    """
    url_lower = url.lower()

    # === GitHub 优先用 README API ===
    if "github.com" in url_lower and "/blob/" not in url_lower:
        result = _fetch_github_readme(url)
        if result:
            return result
        # README 失败则降级到 HTML 抓取

    # === 知乎日报特殊处理 ===
    if "daily.zhihu.com" in url_lower:
        return _fetch_zhihu_daily(url)

    # === Reddit 帖子特殊处理（用 .json 端点拿正文，保证英文原文可靠呈现）===
    if "reddit.com" in url_lower and "/comments/" in url_lower:
        return _fetch_reddit_post(url)

    try:
        client = httpx.Client(headers=HEADERS, timeout=httpx.Timeout(15, connect=8), follow_redirects=True, proxy=HTTP_PROXY if HTTP_PROXY else None)
        resp = client.get(url)
        client.close()

        if resp.status_code != 200:
            # 403/429 等反爬场景：改用浏览器请求头重试
            return _with_brightdata_fallback(_generic_fetch(url), url)

        html = resp.text
        soup = BeautifulSoup(html, "lxml")

        # 提取标题
        title = ""
        if soup.title:
            title = soup.title.get_text(strip=True)
        h1 = soup.find("h1")
        if h1 and not title:
            title = h1.get_text(strip=True)

        # 提取正文（优先 article 标签，其次 main，最后 body）
        content_el = soup.find("article") or soup.find("main") or soup.find("body")
        if not content_el:
            return _with_brightdata_fallback({
                "markdown": f"> 无法解析正文\n\nURL: {url}",
                "title": title or url,
                "sourceUrl": url,
                "category": "article",
            }, url)

        # 移除无关元素（更全面清理）
        for tag in content_el.find_all(["script", "style", "nav", "footer", "header", "aside",
                                         "iframe", "noscript", "svg", "form"]):
            tag.decompose()
        # 移除常见广告/侧栏 class
        for tag in content_el.find_all(class_=lambda c: c and any(x in str(c).lower()
            for x in ["sidebar", "ad-", "banner", "comment", "recommend", "related", "share", "copyright"])):
            tag.decompose()

        # 使用 markdownify 转换
        try:
            from markdownify import markdownify as md
            markdown = md(str(content_el), heading_style="ATX")
        except ImportError:
            markdown = f"# {title}\n\n{clean_html(str(content_el))}"

        # 限制内容长度
        if len(markdown) > 30000:
            markdown = markdown[:30000] + "\n\n...(内容过长已截断)"

        # 后处理：清理多余空行
        lines = markdown.split("\n")
        cleaned = []
        prev_blank = False
        for line in lines:
            is_blank = line.strip() == ""
            if is_blank and prev_blank:
                continue
            cleaned.append(line)
            prev_blank = is_blank
        markdown = "\n".join(cleaned).strip()

        # 内容过短（疑似 JS 壳/重定向页）：浏览器头重试
        if len(markdown) < 300:
            return _with_brightdata_fallback(_generic_fetch(url), url)

        # 类别判断
        if "bilibili.com" in url_lower or "youtube.com" in url_lower:
            category = "video"
        elif "github.com" in url_lower or "huggingface.co" in url_lower:
            category = "model"
        else:
            category = "article"

        # 添加标题和来源
        if not markdown.startswith("#"):
            markdown = f"# {title}\n\n{markdown}"
        markdown += f"\n\n---\n> 来源: {url}"

        return {
            "markdown": markdown,
            "title": title or url,
            "sourceUrl": url,
            "category": category,
        }
    except Exception as e:
        return _with_brightdata_fallback({
            "markdown": f"> 抓取失败: {e}\n\nURL: {url}",
            "title": url,
            "sourceUrl": url,
            "category": "article",
        }, url)


def _fetch_zhihu_daily(url: str) -> dict:
    """知乎日报内容获取"""
    try:
        # 从 URL 提取 story_id
        parts = url.rstrip("/").split("/")
        story_id = parts[-1]

        api_url = f"https://news-at.zhihu.com/api/4/news/{story_id}"
        resp = httpx.get(api_url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            title = data.get("title", "")
            body = data.get("body", "")
            # 清理 HTML
            text = clean_html(body)
            markdown = f"# {title}\n\n{text}\n\n---\n> 来源: {url}"
            return {
                "markdown": markdown,
                "title": title,
                "sourceUrl": url,
                "category": "article",
            }
    except Exception as e:
        print(f"  [知乎日报] {url} 失败: {e}")

    return _with_brightdata_fallback({
        "markdown": f"> 知乎日报内容获取失败\n\nURL: {url}",
        "title": url,
        "sourceUrl": url,
        "category": "article",
    }, url)


def _fetch_reddit_post(url: str) -> dict:
    """Reddit 帖子：通过 .json 端点获取正文（保证英文原文可靠呈现）"""
    json_url = url.rstrip("/") + ".json"
    try:
        client = httpx.Client(
            headers={**HEADERS, "User-Agent": "XMarkdown/1.0"},
            timeout=httpx.Timeout(15, connect=8),
            follow_redirects=True,
            proxy=HTTP_PROXY if HTTP_PROXY else None,
        )
        resp = client.get(json_url)
        client.close()
        if resp.status_code != 200:
            # 降级到 HTML 抓取
            return _with_brightdata_fallback(_generic_fetch(url), url)
        data = resp.json()
        post = data[0]["data"]["children"][0]["data"]
        title = post.get("title", "")
        selftext = post.get("selftext", "") or ""
        url_out = "https://www.reddit.com" + post.get("permalink", "")
        body_parts = []
        if selftext.strip():
            body_parts.append(selftext)
        # 评论区高质量讨论也纳入（英文原文完整呈现）
        comments = []
        try:
            for child in data[1]["data"]["children"][:8]:
                c = child.get("data", {})
                body = c.get("body", "")
                if body and len(body) > 30 and not c.get("stickied"):
                    comments.append(f"- {body}")
        except Exception:
            pass
        if comments:
            body_parts.append("\n\n## 热门评论\n" + "\n".join(comments))
        markdown = f"# {title}\n\n" + "\n\n".join(body_parts) + f"\n\n---\n> 来源: {url_out}"
        return {
            "markdown": markdown,
            "title": title,
            "sourceUrl": url_out,
            "category": "article",
        }
    except Exception as e:
        print(f"  [Reddit] {url} 失败: {e}")
        return _with_brightdata_fallback(_generic_fetch(url), url)


def _looks_failed(result: dict) -> bool:
    """判断转换结果是否为失败/无效内容（内容过短或含失败标记）"""
    md = (result.get("markdown") or "").strip()
    if not md or len(md) < 300:
        return True
    fail_markers = ["抓取失败", "无法解析正文", "内容过长已截断", "转换失败", "获取失败"]
    return any(m in md[:300] for m in fail_markers)


def convert_with_brightdata(url: str) -> dict | None:
    """通过 Bright Data Web Unlocker 抓取并转换为 Markdown；失败返回 None"""
    from brightdata import fetch_html
    html = fetch_html(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.get_text(strip=True) if soup.title else url
    content_el = soup.find("article") or soup.find("main") or soup.find("body")
    if not content_el:
        return None
    for tag in content_el.find_all(["script", "style", "nav", "footer", "header",
                                     "aside", "iframe", "noscript", "svg", "form"]):
        tag.decompose()
    for tag in content_el.find_all(class_=lambda c: c and any(
            x in str(c).lower() for x in
            ["sidebar", "ad-", "banner", "comment", "recommend", "related", "share", "copyright"])):
        tag.decompose()
    try:
        from markdownify import markdownify as md
        markdown = md(str(content_el), heading_style="ATX")
    except ImportError:
        markdown = clean_html(str(content_el))
    markdown = "\n".join(
        line for line in markdown.split("\n") if line.strip() or True
    ).strip()
    if len(markdown) < 300:
        return None
    if not markdown.startswith("#"):
        markdown = f"# {title}\n\n{markdown}"
    markdown += f"\n\n---\n> 来源: {url}"
    return {
        "markdown": markdown,
        "title": title or url,
        "sourceUrl": url,
        "category": "article",
    }


def _with_brightdata_fallback(result: dict, url: str) -> dict:
    """普通抓取失败时用 Bright Data 兜底；仍失败则记录失败页面"""
    if not _looks_failed(result):
        return result
    try:
        fallback = convert_with_brightdata(url)
        if fallback and not _looks_failed(fallback):
            return fallback
    except Exception as e:
        print(f"  [BrightData] 兜底失败 {url}: {e}")
    try:
        from brightdata import record_failed_page
        record_failed_page(
            url,
            title=(result.get("title") or url),
            source="",
            error=(result.get("markdown") or "")[:120],
        )
    except Exception:
        pass
    return result


def _generic_fetch(url: str) -> dict:
    """通用 HTML 抓取（兜底）。升级浏览器请求头 + 失败重试一次。"""
    try:
        from urllib.parse import urlparse
        _p = urlparse(url)
        _origin = f"{_p.scheme}://{_p.netloc}"
        _browser_headers = {
            **HEADERS,
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Cache-Control": "max-age=0",
            "Referer": _origin + "/",
        }

        last_status = None
        resp = None
        for _attempt in (1, 2):
            try:
                _client = httpx.Client(
                    headers=_browser_headers,
                    timeout=httpx.Timeout(15, connect=8),
                    follow_redirects=True,
                    proxy=HTTP_PROXY if HTTP_PROXY else None,
                )
                resp = _client.get(url)
                _client.close()
                last_status = resp.status_code
                if resp.status_code == 200:
                    break
            except Exception:
                if _attempt == 2:
                    raise
                continue
        if last_status != 200 or resp is None:
            return {"markdown": f"> 抓取失败 (HTTP {last_status})\n\nURL: {url}", "title": url, "sourceUrl": url, "category": "article"}

        soup = BeautifulSoup(resp.text, "lxml")
        title = soup.title.get_text(strip=True) if soup.title else url
        content_el = soup.find("article") or soup.find("main") or soup.find("body")
        if not content_el:
            return {"markdown": f"> 无法解析正文\n\nURL: {url}", "title": title, "sourceUrl": url, "category": "article"}
        for tag in content_el.find_all(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript", "svg", "form"]):
            tag.decompose()
        from markdownify import markdownify as md
        try:
            markdown = md(str(content_el), heading_style="ATX")
        except ImportError:
            markdown = clean_html(str(content_el))
        return {"markdown": f"# {title}\n\n{markdown}\n\n---\n> 来源: {url}", "title": title, "sourceUrl": url, "category": "article"}
    except Exception as e:
        return {"markdown": f"> 抓取失败: {e}\n\nURL: {url}", "title": url, "sourceUrl": url, "category": "article"}
