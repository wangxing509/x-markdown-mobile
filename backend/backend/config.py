# -*- coding: utf-8 -*-
"""
X markdown 后端全局配置
"""
from pathlib import Path

# 项目路径
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# 数据库
DATABASE_URL = f"sqlite:///{DATA_DIR / 'xmarkdown.db'}"

# 用户可配置目录（设置 / 来源 / 子 Agent / LLM 通道 / 代理）
USER_DIR = Path.home() / ".xmarkdown"
USER_DIR.mkdir(parents=True, exist_ok=True)

SETTINGS_PATH = USER_DIR / "settings.json"
SOURCES_PATH = USER_DIR / "sources.json"
AGENTS_PATH = USER_DIR / "agents.json"
LLM_CONFIG_PATH = USER_DIR / "llm.json"

# Bright Data 兜底抓取配置（界面可配置：API Key / 区域）
BRIGHTDATA_CONFIG_PATH = USER_DIR / "brightdata.json"
# 抓取失败页面记录（支持 Bright Data 批量重试）
FAILED_PAGES_PATH = USER_DIR / "failed_pages.json"

# 知识库目录
KB_DIR = USER_DIR / "knowledge-base"
KB_DIR.mkdir(parents=True, exist_ok=True)

# Skill 导出目录
SKILLS_DIR = Path.home() / ".codebuddy" / "skills"

# ==================== 每日精选目标（v2 配额）====================
# 默认每日目标 40 条，强制范围 [30, 50]
TOP_N = 40
TOP_N_MIN = 30
TOP_N_MAX = 50

# 中外文比例：英文 40% / 中文 60%（按篇判定语言，不再按平台硬编码）
EN_RATIO = 0.4
CN_RATIO = 0.6

# 审计（AI×审计）占比：目标 25%，强制范围 [20%, 30%]
AUDIT_TARGET_RATIO = 0.25
AUDIT_MIN_RATIO = 0.20
AUDIT_MAX_RATIO = 0.30

# 单源入选上限（手动粘贴渠道不限）
PER_SOURCE_CAP = 6

# 分类配额（聚焦文章/教程/应用案例三类，宁缺毋滥）
CATEGORY_QUOTA = {
    "article": 0.40,      # 文章 / 技术深度文 / 经验分享（软配额）
    "tutorial": 0.35,     # 教程 / 实战指南（软配额）
    "application": 0.25,  # 应用案例 / 落地实践（软配额）
}

# 调度时间（默认每天 09:00，可在设置页修改）
SCHEDULE_HOUR = 9
SCHEDULE_MINUTE = 0

# 去重阈值
SIMHASH_THRESHOLD = 6
TEXT_SIMILARITY_THRESHOLD = 0.75

# ==================== 原文保障（v2 核心）====================
# 正文富集与验证参数
ENRICH_CANDIDATE_MULTIPLIER = 3      # 候选池 = max(T*3, 60)
ENRICH_MIN_POOL = 60
ENRICH_MAX_RETRY_MULTIPLIER = 2      # 验证失败时可扩选 2 倍候选
ENRICH_CONCURRENCY = 4
ENRICH_TIMEOUT = 20                  # 单篇抓取超时（秒）
VERIFY_MIN_MD_LENGTH = 500           # 验证通过的正文最小字符数

# 评分权重（时效30% + 权威20% + 热度20% + TF-IDF相关度15% + 互动反馈15%）
SCORE_WEIGHTS = {
    "freshness": 0.30,
    "authority": 0.20,
    "hotness": 0.20,
    "tfidf_relevance": 0.15,
    "engagement": 0.15,
}

# 平台源权威度（用户指定的高质量 AI 平台清单）
# 分类：中文平台（CN）/ 外文平台（EN）
SOURCE_AUTHORITY = {
    # ===== 中文平台 =====
    "WaytoAGI": 0.90,                 # WaytoAGI 精选 AI 教程/案例
    "魔搭ModelScope": 0.88,           # 阿里魔搭社区：博客/案例/教程
    "微软AI教育社区": 0.87,            # 微软 Learn 中文 AI 教程/案例
    "腾讯CodeBuddy": 0.86,            # 腾讯 CodeBuddy 官方社区
    "DeepSeek": 0.90,                 # DeepSeek 官方论坛/社区
    "字节Trae": 0.84,                 # 字节 Trae 官方社区
    "Kimi": 0.85,                     # 月之暗面 Kimi 官方社区
    "审计署": 0.92,                    # 国家审计署（审计×AI 中文权威源）
    "中国内部审计协会": 0.90,           # CIIA 行业动态
    "中国注册会计师协会": 0.90,          # CICPA 行业动态
    # ===== 外文平台 =====
    "GitHub": 0.95,                   # GitHub Trending（高质量开源应用案例）
    "Reddit": 0.89,                   # Reddit AI 板块（r/MachineLearning 等）
    "Hugging Face": 0.88,             # HF blog / discussions / models
    "OpenAI Blog": 0.97,              # OpenAI 官方博客（RSS）
    "Anthropic News": 0.97,           # Anthropic 官方博客（RSS）
    "Google AI Blog": 0.95,           # Google DeepMind AI 博客（RSS）
    "Microsoft Research": 0.95,       # Microsoft Research 博客（RSS）
    "Journal of Accountancy": 0.93,   # JofA：会计/审计×AI（RSS）
    "IIA Internal Auditor": 0.92,     # IIA 内部审计师杂志（RSS）
    "ISACA": 0.91,                    # ISACA 治理/审计/风险（RSS）
}

# 平台语言归属（仅作为“正文为空”时的兜底，正常逐篇判定）
SOURCE_LANG = {
    "WaytoAGI": "cn", "魔搭ModelScope": "cn", "微软AI教育社区": "cn",
    "腾讯CodeBuddy": "cn", "DeepSeek": "cn", "字节Trae": "cn", "Kimi": "cn",
    "审计署": "cn", "中国内部审计协会": "cn", "中国注册会计师协会": "cn",
    "GitHub": "en", "Reddit": "en", "Hugging Face": "en",
    "OpenAI Blog": "en", "Anthropic News": "en", "Google AI Blog": "en",
    "Microsoft Research": "en", "Journal of Accountancy": "en",
    "IIA Internal Auditor": "en", "ISACA": "en",
}

# 明确拒绝使用的平台（用户要求剔除）
EXCLUDED_SOURCES = ["掘金", "博客园", "知乎", "B站", "和鲸社区", "CSDN", "GAO.GS高手社区", "智源社区", "Hacker News"]

# ==================== AI×审计 领域关键词（v2）====================
AUDIT_KEYWORDS = [
    # 中文
    "审计", "内部审计", "外部审计", "审计署", "注册会计师", "内控", "内部控制",
    "合规", "舞弊", "欺诈", "风险控制", "风险管理", "财报", "财务报告", "会计",
    "税务", "大数据审计", "数字化审计", "智能审计", "审计自动化", "连续审计",
    "审计分析", "审计底稿", "审计抽样", "审计证据", "审计程序", "审计报告",
    "审计准则", "审计师", "监管", "内审", "外审", "治理", "三道防线", "审计整改",
    # 英文
    "audit", "auditing", "auditor", "assurance", "internal control", "internal audit",
    "external audit", "compliance", "fraud", "risk management", "financial statement",
    "accounting", "tax", "continuous auditing", "audit analytics", "audit automation",
    "audit sampling", "audit evidence", "audit procedure", "audit report", "audit committee",
    "audit quality", "audit data", "sox", "coso", "corporate governance", "regulatory",
    "cpa", "cae", "iia", "isaca", "audit board",
]

# 审计域必须同时命中的“AI 相关度”关键词（复用 AI_KEYWORDS，另补充审计场景词）
AUDIT_AI_KEYWORDS = [
    "RPA", "流程自动化", "机器人流程自动化", "数据挖掘", "数据分析", "机器学习",
    "深度学习", "大模型", "LLM", "生成式AI", "生成式人工智能", "智能体", "Agent",
    "异常检测", "预测模型", "文本分析", "OCR", "知识图谱", "图数据库", "自然语言处理",
    "NLP", "决策支持", "风险预警", "实时监控", "自动化工具", "低代码", "提示词",
    "audit analytics", "machine learning", "data analytics", "artificial intelligence",
    "generative ai", "large language model", "llm", "rpa", "robotic process automation",
    "continuous monitoring", "anomaly detection", "predictive analytics", "nlp",
    "natural language processing", "knowledge graph", "intelligent automation",
]

# AI 相关关键词（用于 TF-IDF 相关度评分 + 内容过滤）
AI_KEYWORDS = [
    "AI", "人工智能", "LLM", "大模型", "GPT", "Claude", "Gemini",
    "Agent", "智能体", "RAG", "向量数据库", "embedding",
    "fine-tuning", "微调", "prompt engineering", "提示词",
    "Copilot", "Cursor", "CodeBuddy", "WorkBuddy", "Trae",
    "LangChain", "LlamaIndex", "AutoGPT", "CrewAI", "Dify", "Coze",
    "transformer", "diffusion", "stable diffusion", "midjourney",
    "Hugging Face", "open source", "开源",
    "机器学习", "深度学习", "神经网络", "NLP", "计算机视觉",
    "AGI", "通用人工智能", "多模态", "具身智能",
    "function calling", "tool use", "MCP", "MCP协议",
    "ChatGPT", "OpenAI", "Anthropic", "DeepSeek", "通义千问", "文心一言",
    "Llama", "Qwen", "Mistral", "Phi", "Gemma", "Kimi", "GLM",
    "sora", "whisper", "tts", "语音识别", "图像生成",
    "fine tune", "LoRA", "QLoRA", "量化", "quantization",
    "vllm", "ollama", "llama.cpp", "gguf", "推理部署", "模型部署",
    "工作流", "自动化", "AI应用", "AI编程", "AI助手",
]

# 分类关键词（用于自动分类为 article / tutorial / application）
ARTICLE_KEYWORDS = [
    "文章", "blog", "post", "分析", "解读", "review", "深度", "原理",
    "解析", "介绍", "了解", "什么是", "聊聊", "谈谈", "思考",
    "总结", "对比", "评测", "体验", "实践", "经验", "观点", "洞察",
    "为什么", "如何看", "我们是如何", "复盘", "踩坑", "心得",
]
TUTORIAL_KEYWORDS = [
    "教程", "tutorial", "guide", "实战", "how-to", "从零", "入门",
    "手把手", "搭建", "部署", "配置", "安装", "使用", "快速开始",
    "quick start", "step by step", "一步步", "实现", "开发", "保姆级",
    "手把手教你", "最佳实践", "完整教程", "上手", "跟我做",
]
APPLICATION_KEYWORDS = [
    "app", "应用", "案例", "demo", "tool", "工具", "SDK", "integration",
    "集成", "插件", "plugin", "extension", "平台", "framework",
    "落地", "实践案例", "业务", "解决方案", "场景", "构建", "打造",
    "上线", "产品", "项目", "实战项目",
]
# video / model 关键词不再参与主分类（聚焦三类），仅作负向/辅助判断

# 爬虫请求配置
REQUEST_TIMEOUT = 15        # 单平台超时15秒（避免外网站点卡住整体流程）
REQUEST_DELAY = 0.5
MAX_CONCURRENT = 8          # 8平台并发
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/127.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# Playwright 兜底开关
ENABLE_PLAYWRIGHT_FALLBACK = True

# 代理配置（访问 Reddit/Hugging Face 等外网站点时必需，留空则不使用）
# 优先级：1) 本地配置文件 ~/.xmarkdown/proxy.json（界面可填，运行时生效）
#         2) 系统/环境变量（HTTP_PROXY / HTTPS_PROXY / http_proxy / https_proxy）
#         3) 下列硬编码兜底（可在此临时写死，如 "http://127.0.0.1:7890"）
HARDCODED_PROXY = ""  # 仅当环境变量与配置文件都未设置时使用的兜底值

# 本地代理配置文件（与 Electron 界面共享，保证两端一致）
PROXY_CONFIG_PATH = Path.home() / ".xmarkdown" / "proxy.json"


def _load_proxy_from_config() -> str:
    """从本地配置文件读取代理地址（界面写入，运行时生效）"""
    try:
        if PROXY_CONFIG_PATH.exists():
            import json as _json
            with open(PROXY_CONFIG_PATH, "r", encoding="utf-8") as _f:
                _data = _json.load(_f)
            _enabled = _data.get("enabled", False)
            _url = (_data.get("url") or "").strip()
            if _enabled and _url:
                return _url
    except Exception:
        pass
    return ""


def _normalize_proxy(url: str) -> str:
    url = (url or "").strip()
    if url and not url.startswith("http"):
        url = "http://" + url
    return url


import os as _os

# 解析最终代理地址（配置 > 环境变量 > 硬编码）
_config_proxy = _load_proxy_from_config()
_env_proxy = (
    _os.environ.get("HTTPS_PROXY")
    or _os.environ.get("HTTP_PROXY")
    or _os.environ.get("https_proxy")
    or _os.environ.get("http_proxy")
    or ""
)
HTTP_PROXY = _normalize_proxy(_config_proxy or _env_proxy or HARDCODED_PROXY)
