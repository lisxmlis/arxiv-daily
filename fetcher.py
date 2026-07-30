"""arXiv 当日新论文拉取与关键词筛选。"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Iterable
from zoneinfo import ZoneInfo

import arxiv
import feedparser

# arXiv 公告时区（美国东部）
ARXIV_TZ = ZoneInfo("America/New_York")

# 常用学科分类（展示名 -> arXiv category code）
CATEGORIES: dict[str, str] = {
    "人工智能 (cs.AI)": "cs.AI",
    "机器学习 (cs.LG)": "cs.LG",
    "计算机视觉 (cs.CV)": "cs.CV",
    "计算与语言 (cs.CL)": "cs.CL",
    "信息检索 (cs.IR)": "cs.IR",
    "神经网络与进化计算 (cs.NE)": "cs.NE",
    "机器人 (cs.RO)": "cs.RO",
    "密码学与安全 (cs.CR)": "cs.CR",
    "分布式/并行/集群 (cs.DC)": "cs.DC",
    "人机交互 (cs.HC)": "cs.HC",
    "软件工程 (cs.SE)": "cs.SE",
    "系统与控制 (cs.SY)": "cs.SY",
    "统计机器学习 (stat.ML)": "stat.ML",
    "量子物理 (quant-ph)": "quant-ph",
    "凝聚态 (cond-mat)": "cond-mat",
    "高能理论 (hep-th)": "hep-th",
    "数学 (math)": "math",
    "电气工程 (eess)": "eess",
    "定量生物 (q-bio)": "q-bio",
    "定量金融 (q-fin)": "q-fin",
}

# 中文/别名 -> 标准代码
CATEGORY_ALIASES: dict[str, str] = {
    "凝聚态": "cond-mat",
    "人工智能": "cs.AI",
    "机器学习": "cs.LG",
    "计算机视觉": "cs.CV",
    "量子物理": "quant-ph",
    "高能理论": "hep-th",
    "数学": "math",
}

# 含有子类的一级 archive；API 需用 cat:xxx.*
PARENT_ARCHIVES = {
    "cond-mat",
    "cs",
    "math",
    "astro-ph",
    "physics",
    "nlin",
    "q-bio",
    "q-fin",
    "stat",
    "eess",
    "econ",
}

RSS_NEW = "https://rss.arxiv.org/rss/{category}"
RSS_RECENT = "https://rss.arxiv.org/rss/{category}?show=2000"

_ARXIV_CAT_RE = re.compile(r"^[A-Za-z][A-Za-z0-9\-]+(\.[A-Za-z0-9\-]+)?$")


def normalize_text(text: str) -> str:
    """小写 + 去掉重音（Moiré -> moire），便于关键词匹配。"""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower()


def resolve_category(category: str, category_label: str = "") -> str:
    """把界面上的分类名/别名解析成 arXiv 代码。"""
    raw = (category or "").strip()
    label = (category_label or "").strip()

    if raw in CATEGORIES.values():
        return raw
    if raw in CATEGORIES:
        return CATEGORIES[raw]
    if raw in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[raw]

    # 从「凝聚态 (cond-mat)」提取
    for text in (label, raw):
        m = re.search(r"\(([^)]+)\)\s*$", text)
        if m:
            code = m.group(1).strip()
            if _ARXIV_CAT_RE.match(code):
                return code
        if text in CATEGORY_ALIASES:
            return CATEGORY_ALIASES[text]
        for disp, code in CATEGORIES.items():
            if text == disp or text in disp:
                return code

    if _ARXIV_CAT_RE.match(raw):
        return raw
    return raw


def resolve_categories(
    categories: str | list[str] | None,
    category_labels: str | list[str] | None = None,
) -> list[str]:
    """解析并去重多个分类代码，保持顺序。"""
    if categories is None:
        cats = []
    elif isinstance(categories, str):
        cats = [c.strip() for c in categories.replace(";", ",").split(",") if c.strip()]
    else:
        cats = [str(c).strip() for c in categories if str(c).strip()]

    if category_labels is None:
        labels: list[str] = []
    elif isinstance(category_labels, str):
        labels = [category_labels]
    else:
        labels = [str(x) for x in category_labels]

    resolved: list[str] = []
    seen: set[str] = set()
    for i, cat in enumerate(cats):
        label = labels[i] if i < len(labels) else (labels[0] if labels else "")
        code = resolve_category(cat, label)
        if code and code not in seen:
            seen.add(code)
            resolved.append(code)
    return resolved


def is_valid_category(category: str) -> bool:
    return bool(_ARXIV_CAT_RE.match((category or "").strip()))


def api_category_clause(category: str | list[str]) -> str:
    """构造 API 分类子句；一级 archive 使用 cat:xxx.* 覆盖子类；多主题用 OR。"""
    cats = resolve_categories(category)
    if not cats:
        raise ValueError("至少需要一个有效主题分类。")

    parts = []
    for cat in cats:
        if cat in PARENT_ARCHIVES:
            parts.append(f"cat:{cat}.*")
        elif cat.endswith(".*"):
            parts.append(f"cat:{cat}")
        else:
            parts.append(f"cat:{cat}")
    if len(parts) == 1:
        return parts[0]
    return "(" + " OR ".join(parts) + ")"

@dataclass
class Paper:
    arxiv_id: str
    title: str
    authors: list[str]
    summary: str
    categories: list[str]
    published: datetime
    updated: datetime
    pdf_url: str
    abs_url: str

    def matches_keywords(self, keywords: Iterable[str], mode: str = "any") -> bool:
        """mode: any = 任一命中；all = 全部命中。"""
        keys = [normalize_text(k.strip()) for k in keywords if k and k.strip()]
        if not keys:
            return True
        haystack = normalize_text(
            " ".join(
                [
                    self.title,
                    self.summary,
                    " ".join(self.authors),
                    " ".join(self.categories),
                ]
            )
        )
        hits = [k in haystack for k in keys]
        return all(hits) if mode == "all" else any(hits)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["authors"] = ", ".join(self.authors)
        d["categories"] = ", ".join(self.categories)
        d["published"] = self.published.isoformat()
        d["updated"] = self.updated.isoformat()
        return d


def arxiv_today(ref: date | None = None) -> date:
    """返回 arXiv 东部时区下的“今天”。"""
    if ref is not None:
        return ref
    return datetime.now(ARXIV_TZ).date()


def _parse_feed_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = feedparser._parse_date(value)  # type: ignore[attr-defined]
        if parsed:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
    except Exception:
        pass
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
    ):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _id_from_link(link: str) -> str:
    part = link.rstrip("/").split("/")[-1]
    return part.split("v")[0]


def _result_to_paper(result: arxiv.Result) -> Paper:
    return Paper(
        arxiv_id=result.get_short_id().split("v")[0],
        title=result.title.replace("\n", " ").strip(),
        authors=[a.name for a in result.authors],
        summary=result.summary.replace("\n", " ").strip(),
        categories=list(result.categories),
        published=result.published,
        updated=result.updated,
        pdf_url=result.pdf_url,
        abs_url=result.entry_id,
    )


def fetch_from_rss(category: str | list[str], days: int = 1) -> list[Paper]:
    """
    通过 arXiv RSS 获取某分类（可多个）的新论文。
    days>1 时回退到 recent 源并按日期过滤。
    """
    categories = resolve_categories(category)
    if not categories:
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    seen: set[str] = set()
    papers: list[Paper] = []

    for category in categories:
        urls = [RSS_NEW.format(category=category)]
        if days > 1:
            urls.append(RSS_RECENT.format(category=category))

        for url in urls:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                link = getattr(entry, "link", "") or ""
                if not link:
                    continue
                arxiv_id = _id_from_link(link)
                if arxiv_id in seen:
                    continue

                published = None
                if getattr(entry, "published_parsed", None):
                    t = entry.published_parsed
                    published = datetime(*t[:6], tzinfo=timezone.utc)
                else:
                    published = _parse_feed_datetime(getattr(entry, "published", None))

                updated = published
                if getattr(entry, "updated_parsed", None):
                    t = entry.updated_parsed
                    updated = datetime(*t[:6], tzinfo=timezone.utc)

                if published and published < cutoff and days >= 1:
                    if "show=" in url:
                        continue

                title = (getattr(entry, "title", "") or "").replace("\n", " ").strip()
                summary = (getattr(entry, "summary", "") or "").replace("\n", " ").strip()
                if "Abstract:" in summary:
                    summary = summary.split("Abstract:", 1)[-1].strip()

                authors = []
                if getattr(entry, "authors", None):
                    authors = [a.get("name", "") for a in entry.authors if a.get("name")]
                elif getattr(entry, "author", None):
                    authors = [entry.author]

                tags = []
                if getattr(entry, "tags", None):
                    tags = [t.get("term", "") for t in entry.tags if t.get("term")]
                if not tags:
                    tags = [category]

                pdf_url = link.replace("/abs/", "/pdf/")
                papers.append(
                    Paper(
                        arxiv_id=arxiv_id,
                        title=title,
                        authors=authors,
                        summary=summary,
                        categories=tags,
                        published=published or datetime.now(timezone.utc),
                        updated=updated or published or datetime.now(timezone.utc),
                        pdf_url=pdf_url,
                        abs_url=link if "/abs/" in link else f"https://arxiv.org/abs/{arxiv_id}",
                    )
                )
                seen.add(arxiv_id)

    papers.sort(key=lambda p: p.published, reverse=True)
    return papers

def _keyword_api_clause(keywords: list[str], mode: str = "any") -> str:
    parts = []
    for k in keywords:
        k = k.strip()
        if not k:
            continue
        # 短语加引号；单词语可不加
        if " " in k or "-" in k:
            parts.append(f'all:"{k}"')
        else:
            parts.append(f"all:{k}")
    if not parts:
        return ""
    joiner = " AND " if mode == "all" else " OR "
    return f"({joiner.join(parts)})"


def fetch_from_api(
    category: str | list[str],
    target_date: date | None = None,
    days: int = 1,
    max_results: int = 200,
    keywords: list[str] | None = None,
    keyword_mode: str = "any",
) -> list[Paper]:
    """
    通过官方 API 按提交日期拉取论文。
    支持多主题（OR）；对 cond-mat / cs / math 等一级分类使用 cat:xxx.*。
    若提供关键词，则一并写入查询，避免只靠本地二次过滤漏检。
    """
    end = target_date or arxiv_today()
    start = end - timedelta(days=max(days - 1, 0))
    start_s = start.strftime("%Y%m%d0000")
    end_s = end.strftime("%Y%m%d2359")

    cat_clause = api_category_clause(category)
    query = f"{cat_clause} AND submittedDate:[{start_s} TO {end_s}]"
    kw_clause = _keyword_api_clause(keywords or [], mode=keyword_mode)
    if kw_clause:
        query = f"{query} AND {kw_clause}"

    client = arxiv.Client(page_size=min(100, max_results), delay_seconds=3.0, num_retries=3)
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    return [_result_to_paper(result) for result in client.results(search)]

def _merge_papers(*groups: list[Paper]) -> list[Paper]:
    seen: set[str] = set()
    out: list[Paper] = []
    for group in groups:
        for p in group:
            if p.arxiv_id in seen:
                continue
            seen.add(p.arxiv_id)
            out.append(p)
    out.sort(key=lambda p: p.published, reverse=True)
    return out


def fetch_papers(
    category: str | list[str] | None = None,
    keywords: list[str] | None = None,
    keyword_mode: str = "any",
    target_date: date | None = None,
    days: int = 1,
    source: str = "auto",
    max_results: int = 200,
    categories: list[str] | None = None,
) -> list[Paper]:
    """
    拉取并筛选论文。
    category / categories 均可传多个主题。
    source: auto | rss | api
      auto = RSS + API 合并（有关键词时 API 会带关键词检索，避免漏检）
    """
    keywords = keywords or []
    cats = resolve_categories(categories if categories is not None else category)
    papers: list[Paper] = []

    if not cats:
        raise ValueError("请至少选择一个主题分类。")
    bad = [c for c in cats if not is_valid_category(c)]
    if bad:
        raise ValueError(
            f"无效的 arXiv 分类代码：{bad!r}。"
            "请选择「凝聚态 (cond-mat)」等标准主题，或填写如 cond-mat / cs.LG 的代码。"
        )

    if source in ("auto", "rss"):
        papers = fetch_from_rss(cats, days=days)

    need_api = source == "api" or source == "auto"
    if need_api:
        try:
            api_papers = fetch_from_api(
                cats,
                target_date=target_date,
                days=days,
                max_results=max_results,
                keywords=keywords if keywords else None,
                keyword_mode=keyword_mode,
            )
            if source == "api":
                papers = api_papers
            else:
                papers = _merge_papers(papers, api_papers)
        except Exception:
            if source == "api":
                raise

    papers.sort(key=lambda p: p.published, reverse=True)

    if keywords:
        papers = [p for p in papers if p.matches_keywords(keywords, mode=keyword_mode)]
    return papers


def papers_to_markdown(papers: list[Paper], heading: str = "arXiv Daily") -> str:
    lines = [f"# {heading}", "", f"共 {len(papers)} 篇", ""]
    for i, p in enumerate(papers, 1):
        authors = ", ".join(p.authors[:8])
        if len(p.authors) > 8:
            authors += " et al."
        lines.extend(
            [
                f"## {i}. {p.title}",
                "",
                f"- **ID**: [{p.arxiv_id}]({p.abs_url})",
                f"- **作者**: {authors}",
                f"- **分类**: {', '.join(p.categories)}",
                f"- **发布**: {p.published.strftime('%Y-%m-%d %H:%M UTC')}",
                f"- **PDF**: [下载]({p.pdf_url})",
                "",
                f"{p.summary}",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines)
