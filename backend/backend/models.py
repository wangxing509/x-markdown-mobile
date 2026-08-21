# -*- coding: utf-8 -*-
"""
Pydantic 请求/响应模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ArticleData(BaseModel):
    """爬虫输出的统一文章格式"""
    title: str
    url: str
    summary: str = ""
    source: str
    source_authority: float = 0.5
    published_at: Optional[datetime] = None
    raw_text: str = ""
    simhash_value: str = ""
    category: str = "article"
    score: float = 0.0
    likes: int = 0
    comments: int = 0
    author: str = ""
    author_followers: int = 0


class Top100ItemOut(BaseModel):
    """API 输出的 Top100 条目"""
    id: int
    rank: int
    title: str
    url: str
    summary: str
    source: str
    sourceAuthority: float
    publishedAt: Optional[datetime]
    category: str
    score: float
    tags: str = ""
    likes: int = 0
    comments: int = 0
    author: str = ""
    authorFollowers: int = 0
    lang: str = ""
    domain: str = "ai_general"
    verified: bool = False
    mdLength: int = 0


class Top100Stats(BaseModel):
    """每日精选统计"""
    total: int = 0
    target: int = 40
    cn: int = 0
    en: int = 0
    audit: int = 0
    general: int = 0
    shortfall: int = 0
    cells: dict = {}


class Top100Response(BaseModel):
    """Top100 接口响应"""
    updateTime: str
    nextRefresh: str
    items: List[Top100ItemOut]
    totalCount: int
    stats: Top100Stats = Top100Stats()


class RefreshResponse(BaseModel):
    """手动刷新响应"""
    success: bool
    message: str
    rawCount: Optional[int] = None
    dedupCount: Optional[int] = None
    verifiedCount: Optional[int] = None
    curatedCount: Optional[int] = None
    enCount: Optional[int] = None
    cnCount: Optional[int] = None
    auditCount: Optional[int] = None
    generalCount: Optional[int] = None
    shortfall: Optional[int] = None
    stats: Optional[dict] = None


class MarkdownConvertRequest(BaseModel):
    """Markdown 转换请求"""
    url: str


class MarkdownConvertResponse(BaseModel):
    """Markdown 转换响应"""
    markdown: str
    title: str
    sourceUrl: str
    category: str = "article"


class SubtitleConvertRequest(BaseModel):
    """字幕转换请求"""
    videoUrl: str


class SubtitleConvertResponse(BaseModel):
    """字幕转换响应"""
    markdown: str
    videoTitle: str
    duration: str = ""


class TranslateRequest(BaseModel):
    """翻译请求"""
    texts: List[str] = Field(..., max_length=10)
    source_lang: str = "auto"
    target_lang: str = "zh-CN"


class TranslationItem(BaseModel):
    original: str
    translated: str


class TranslateResponse(BaseModel):
    results: List[TranslationItem]


class DistillRequest(BaseModel):
    """Skill 蒸馏请求"""
    text: str
    skillName: str


class DistillResponse(BaseModel):
    """Skill 蒸馏响应"""
    skillName: str
    content: str
    skillPath: str


class ChatRequest(BaseModel):
    """Chat 请求"""
    message: str
    context: str = ""


class ChatResponse(BaseModel):
    """Chat 响应"""
    reply: str
    references: List[str] = []


class KbItemOut(BaseModel):
    """知识库条目输出"""
    name: str
    path: str
    size: int
    modified: str
    sourceUrl: str = ""
    domain: str = "ai_general"
    lang: str = ""
    category: str = "article"
    source: str = ""
    hasTranslation: bool = False


class KbListResponse(BaseModel):
    """知识库列表响应"""
    items: List[KbItemOut]


class KbSaveRequest(BaseModel):
    """知识库保存请求（原文+可选译文）"""
    url: str = ""
    title: str
    originalMd: str
    translatedMd: str = ""
    domain: str = "ai_general"
    category: str = "article"
    lang: str = ""
    source: str = ""
    tags: List[str] = []
    force: bool = False


class KbSaveResponse(BaseModel):
    """知识库保存响应"""
    success: bool
    duplicate: bool = False
    id: Optional[int] = None
    originalPath: str = ""
    translatedPath: str = ""
    message: str = ""


class KbSearchResult(BaseModel):
    id: int
    title: str
    path: str = ""
    domain: str = ""
    lang: str = ""
    category: str = ""
    source: str = ""
    snippet: str = ""
    score: float = 0.0
    matchType: str = ""


class KbSearchResponse(BaseModel):
    results: List[KbSearchResult]


class KbTreeItem(BaseModel):
    """目录树文章节点"""
    name: str
    path: str
    size: int = 0
    modified: str = ""
    sourceUrl: str = ""
    domain: str = "ai_general"
    lang: str = ""
    category: str = "article"
    source: str = ""
    hasTranslation: bool = False
    author: str = ""
    topic: str = ""


class KbTreeAuthor(BaseModel):
    """目录树作者节点"""
    author: str
    count: int = 0
    items: List[KbTreeItem] = []


class KbTreeTopic(BaseModel):
    """目录树主题节点"""
    topic: str
    count: int = 0
    authors: List[KbTreeAuthor] = []


class KbTreeCategory(BaseModel):
    """目录树聚合类别节点"""
    key: str
    label: str
    domain: str = ""
    category: str = ""
    count: int = 0
    topics: List[KbTreeTopic] = []


class KbTreeResponse(BaseModel):
    total: int = 0
    updatedAt: str = ""
    categories: List[KbTreeCategory] = []


class AgentOut(BaseModel):
    id: str
    name: str
    desc: str = ""
    systemPrompt: str = ""
    filters: dict = {}
    topK: int = 5
    temperature: float = 0.3


class SettingsOut(BaseModel):
    top_n: int = 40
    en_ratio: float = 0.4
    audit_ratio: float = 0.25
    schedule: dict = {}


class LlmConfigOut(BaseModel):
    provider: str = "local"
    apiBase: str = ""
    apiKey: str = ""
    model: str = ""
    temperature: float = 0.2


class SourceOut(BaseModel):
    name: str
    enabled: bool = True
    kind: str = "html"
    authority: float = 0.85
    lang: str = ""
    audit: bool = False
    feeds: List[str] = []
    urls: List[str] = []
