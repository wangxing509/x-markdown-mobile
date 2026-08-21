# -*- coding: utf-8 -*-
"""
视频字幕 → 结构化文章转换模块
去除语气词、无效表达，分段整理
"""
import re
import httpx
from config import HEADERS, REQUEST_TIMEOUT


# 语气词和无效表达（英文）
FILLER_WORDS = {
    "um", "uh", "ah", "er", "like", "you know", "i mean", "sort of",
    "kind of", "basically", "actually", "literally", "honestly",
    "right", "so", "well", "okay", "ok", "let's see", "let me see",
    "going to", "gonna", "wanna", "gotta",
}


def clean_subtitle_text(text: str) -> str:
    """清理字幕文本，去除语气词和无效表达"""
    text = text.lower()
    # 去除语气词
    for word in FILLER_WORDS:
        text = re.sub(rf"\b{re.escape(word)}\b[,\.]?\s*", "", text, flags=re.IGNORECASE)
    # 去除多余空格
    text = re.sub(r"\s+", " ", text).strip()
    # 标点修正
    text = re.sub(r"\s+([,\.!?])", r"\1", text)
    return text


def split_into_sentences(text: str) -> list[str]:
    """将文本拆分为句子"""
    sentences = re.split(r"(?<=[\.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def group_sentences_to_paragraphs(sentences: list[str], group_size: int = 5) -> list[str]:
    """将句子组合成段落"""
    paragraphs = []
    for i in range(0, len(sentences), group_size):
        para = " ".join(sentences[i:i + group_size])
        paragraphs.append(para)
    return paragraphs


def convert_subtitles_to_article(
    subtitles: list[str],
    video_title: str = "",
    duration: str = "",
) -> str:
    """
    将字幕列表转为结构化 Markdown 文章
    """
    # 合并所有字幕
    full_text = " ".join(subtitles)
    # 清理
    cleaned = clean_subtitle_text(full_text)
    # 拆句
    sentences = split_into_sentences(cleaned)
    # 组段落
    paragraphs = group_sentences_to_paragraphs(sentences)

    # 构建 Markdown
    md_parts = []
    if video_title:
        md_parts.append(f"# {video_title}")
        md_parts.append("")

    if duration:
        md_parts.append(f"> 视频时长: {duration}")
        md_parts.append("")

    # 概述
    if paragraphs:
        md_parts.append("## 概述")
        md_parts.append("")
        md_parts.append(paragraphs[0])
        md_parts.append("")

    # 详细内容
    if len(paragraphs) > 1:
        md_parts.append("## 详细内容")
        md_parts.append("")
        for para in paragraphs[1:]:
            md_parts.append(para)
            md_parts.append("")

    return "\n".join(md_parts)


def fetch_bilibili_subtitle(video_url: str) -> dict:
    """获取 B站视频字幕"""
    try:
        # 提取 BV 号
        match = re.search(r"(BV[\w]+)", video_url)
        if not match:
            return {"markdown": "> 无法解析视频 ID", "videoTitle": video_url, "duration": ""}

        bvid = match.group(1)
        client = httpx.Client(headers=HEADERS, timeout=REQUEST_TIMEOUT, follow_redirects=True)

        # 获取视频信息
        info_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        info_resp = client.get(info_url)
        if info_resp.status_code != 200:
            client.close()
            return {"markdown": "> 获取视频信息失败", "videoTitle": video_url, "duration": ""}

        info_data = info_resp.json().get("data", {})
        title = info_data.get("title", "")
        duration_sec = info_data.get("duration", 0)
        duration = f"{duration_sec // 60}:{duration_sec % 60:02d}"

        # 获取字幕
        cid = info_data.get("cid", 0)
        if not cid:
            client.close()
            # 降级：返回视频信息
            return {
                "markdown": f"# {title}\n\n> 视频地址: {video_url}\n> 时长: {duration}\n\n（字幕暂不可用）",
                "videoTitle": title,
                "duration": duration,
            }

        # 字幕接口
        sub_url = f"https://api.bilibili.com/x/player/v2?cid={cid}&bvid={bvid}"
        sub_resp = client.get(sub_url)
        client.close()

        if sub_resp.status_code != 200:
            return {
                "markdown": f"# {title}\n\n> 视频地址: {video_url}\n> 时长: {duration}\n\n（字幕获取失败）",
                "videoTitle": title,
                "duration": duration,
            }

        sub_data = sub_resp.json().get("data", {})
        subtitle_info = sub_data.get("subtitle", {})
        subtitles_list = subtitle_info.get("subtitles", [])

        if not subtitles_list:
            return {
                "markdown": f"# {title}\n\n> 视频地址: {video_url}\n> 时长: {duration}\n\n（该视频无字幕）",
                "videoTitle": title,
                "duration": duration,
            }

        # 获取字幕内容
        sub_url = subtitles_list[0].get("subtitle_url", "")
        if sub_url and not sub_url.startswith("http"):
            sub_url = "https:" + sub_url

        sub_resp2 = httpx.get(sub_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if sub_resp2.status_code != 200:
            return {
                "markdown": f"# {title}\n\n> 时长: {duration}\n\n（字幕下载失败）",
                "videoTitle": title,
                "duration": duration,
            }

        sub_json = sub_resp2.json()
        body = sub_json.get("body", [])
        subtitle_texts = [item.get("content", "") for item in body if item.get("content")]

        markdown = convert_subtitles_to_article(subtitle_texts, title, duration)
        return {"markdown": markdown, "videoTitle": title, "duration": duration}
    except Exception as e:
        return {"markdown": f"> 字幕获取失败: {e}", "videoTitle": video_url, "duration": ""}
