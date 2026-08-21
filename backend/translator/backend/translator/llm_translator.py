# -*- coding: utf-8 -*-
"""
LLM 翻译代理模块
默认通过 Electron 主进程的 LLM 桥接调用 CodeBuddy/WorkBuddy 内置 LLM
后端作为 fallback 提供 MyMemory API 翻译
"""
import re
import urllib.request
import urllib.parse
import json


_cache: dict[str, str] = {}


def _is_mostly_english(text: str) -> bool:
    """检测文本是否主要是英文"""
    alpha_chars = len(re.findall(r"[a-zA-Z]", text))
    cjk_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    total = alpha_chars + cjk_chars
    if total == 0:
        return False
    return alpha_chars / total > 0.5


def check_translation_quality(original: str, translated: str) -> dict:
    """
    轻量译文质量检查：
    - 译文中文占比（英文原文应产出以中文为主的译文）
    - 输出是否明显过短（疑似被截断）
    - Markdown 结构是否保留（标题数量接近）
    """
    if not original or not translated:
        return {"ok": False, "reason": "空内容"}
    cjk = len(re.findall(r"[\u4e00-\u9fff]", translated))
    alpha = len(re.findall(r"[a-zA-Z]", translated))
    total = cjk + alpha
    cn_ratio = cjk / total if total else 0.0
    length_ratio = len(translated) / max(1, len(original))
    orig_heads = len(re.findall(r"^#{1,6}\s", original, flags=re.MULTILINE))
    trans_heads = len(re.findall(r"^#{1,6}\s", translated, flags=re.MULTILINE))
    issues = []
    if cn_ratio < 0.2:
        issues.append("译文中文占比过低")
    if length_ratio < 0.15:
        issues.append("译文疑似截断")
    if orig_heads and abs(orig_heads - trans_heads) > max(1, orig_heads // 2):
        issues.append("标题结构丢失")
    return {"ok": not issues, "reason": "；".join(issues) if issues else "", "cn_ratio": round(cn_ratio, 3)}


# AI 领域术语表：MyMemory 机翻质量差，这里对高频术语做标准化后处理
# 仅当译文中出现"错误/生硬"译法时替换为标准中文表达（不强行插入英文）
_GLOSSARY = [
    (r"\bLLM\b", "大语言模型(LLM)"),
    (r"\bRAG\b", "检索增强生成(RAG)"),
    (r"\bAgent\b", "智能体(Agent)"),
    (r"\bPrompt\b", "提示词(Prompt)"),
    (r"\bFine[- ]?tuning\b", "微调"),
    (r"\bEmbedding\b", "向量嵌入(Embedding)"),
    (r"\bTransformer\b", "Transformer"),
    (r"\bToken\b", "Token"),
    (r"\bGPU\b", "GPU"),
    (r"\bInference\b", "推理"),
    (r"\bMultimodal\b", "多模态"),
    (r"\bBenchmark\b", "基准测试"),
    (r"\bOpen[- ]?source\b", "开源"),
    (r"\bQuantization\b", "量化"),
    (r"\bHallucination\b", "幻觉"),
    (r"\bFine[- ]?tune\b", "微调"),
    (r"\bPre[- ]?train\b", "预训练"),
    (r"\bZero[- ]?shot\b", "零样本"),
    (r"\bFew[- ]?shot\b", "少样本"),
    (r"\bChain[- ]?of[- ]?thought\b", "思维链"),
    (r"\bReinforcement Learning\b", "强化学习"),
]


def _apply_glossary(text: str) -> str:
    """对译文做术语标准化（避免机翻生硬译法）"""
    for pat, repl in _GLOSSARY:
        try:
            text = re.sub(pat, repl, text, flags=re.IGNORECASE)
        except Exception:
            pass
    return text


def _split_sentences(text: str) -> list[str]:
    """将文本按句子切分（保留 Markdown 结构，句子 < 500 字符以适配 MyMemory 限制）"""
    # 先按换行保护代码块/列表
    parts = re.split(r'(?<=[.!?。！？]\s)', text)
    out = []
    buf = ""
    for p in parts:
        if len(buf) + len(p) <= 450:
            buf += p
        else:
            if buf:
                out.append(buf)
            # 单句过长则按逗号再切
            if len(p) > 450:
                sub = re.split(r'(?<=[,，；;]\s)', p)
                for s in sub:
                    out.append(s)
            else:
                buf = p
    if buf:
        out.append(buf)
    return [x.strip() for x in out if x.strip()]


def _translate_mymemory(text: str) -> str:
    """MyMemory API 免费翻译（fallback，按句翻译 + 术语表修正）"""
    if not text or len(text.strip()) == 0:
        return text
    if text in _cache:
        return _cache[text]

    # 短文本直接翻译
    if len(text) <= 450:
        translated = _call_mymemory_single(text)
        translated = _apply_glossary(translated)
        _cache[text] = translated
        return translated

    # 长文本按句翻译拼接
    sentences = _split_sentences(text)
    chunks = []
    for s in sentences:
        chunks.append(_call_mymemory_single(s))
    translated = _apply_glossary("".join(chunks))
    _cache[text] = translated
    return translated


def _call_mymemory_single(text: str) -> str:
    """调用 MyMemory 单句翻译（带 email 参数提升限额）"""
    try:
        params = urllib.parse.urlencode({
            "q": text[:500],
            "langpair": "en|zh-CN",
            "de": "xmarkdown@local.app",  # 提升每日限额
        })
        url = f"https://api.mymemory.translated.net/get?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "XMarkdown/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            translated = data.get("responseData", {}).get("translatedText", "")
            if translated and translated != text:
                return translated
    except Exception as e:
        print(f"  [翻译] MyMemory 失败: {e}")
    return text


def translate_text(text: str, force: bool = False) -> str:
    """
    翻译文本（英 → 中）
    优先使用 LLM 桥接（由 Electron 主进程转发）
    Fallback: MyMemory API（按句翻译 + 术语表修正）
    """
    if not text or not text.strip():
        return text

    if not force and not _is_mostly_english(text):
        return text

    # 后端 fallback：MyMemory
    return _translate_mymemory(text)


def _split_markdown_chunks(text: str, max_chunk: int = 1500) -> list[str]:
    """
    按 Markdown 结构友好地分块，避免在代码块 / 链接 / 句子中间截断。
    优先按空行分段，段过大时按句子切分，但始终不在围栏代码块内断开。
    """
    chunks: list[str] = []
    # 先按段落切
    paragraphs = text.split("\n\n")
    buf = ""
    in_fence = False

    def flush():
        nonlocal buf
        if buf.strip():
            chunks.append(buf.strip())
        buf = ""

    for para in paragraphs:
        # 检查该段是否包含代码围栏
        will_enter_fence = "```" in para or "~~~" in para
        if not in_fence and will_enter_fence and len(para) > max_chunk:
            # 代码段过大：按行切（保留围栏完整），按 max_chunk 累积但不跨围栏断
            flush()
            lines = para.split("\n")
            sub = ""
            fence_open = False
            for ln in lines:
                if ln.strip().startswith("```") or ln.strip().startswith("~~~"):
                    fence_open = not fence_open
                if sub and len(sub) + len(ln) + 1 > max_chunk and not fence_open:
                    chunks.append(sub.strip())
                    sub = ln
                else:
                    sub = sub + "\n" + ln if sub else ln
            if sub:
                chunks.append(sub.strip())
            continue

        if len(buf) + len(para) + 2 > max_chunk and buf:
            flush()
            buf = para
        else:
            buf = buf + "\n\n" + para if buf else para
    flush()
    return chunks


def translate_long_text(text: str, chunk_size: int = 1500) -> str:
    """
    分段翻译长文本（Markdown 结构友好分块，避免破坏代码块/URL）
    """
    if not text or not text.strip():
        return text

    chunks = _split_markdown_chunks(text, chunk_size)
    if len(chunks) == 1:
        return translate_text(chunks[0])

    translated = []
    for ch in chunks:
        translated.append(translate_text(ch))
    return "\n\n".join(translated)
