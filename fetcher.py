"""arXiv 当日新论文拉取与关键词筛选。"""

from __future__ import annotations

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

RSS_NEW = "https://rss.arxiv.org/rss/{category}"
RSS_RECENT = "https://rss.arxiv.org/rss/{category}?show=100"


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
        keys = [k.strip().lower() for k in keywords if k and k.strip()]
        if not keys:
            return True
        haystack = " ".join(
            [
                self.title,
                self.summary,
                " ".join(self.authors),
                " ".join(self.categories),
            ]
        ).lower()
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
        # feedparser 已解析时常用 struct_time；这里兼容 ISO / RFC
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
    # https://arxiv.org/abs/2401.12345v1 -> 2401.12345
    part = link.rstrip("/").split("/")[-1]
    return part.split("v")[0]


def fetch_from_rss(category: str, days: int = 1) -> list[Paper]:
    """
    通过 arXiv RSS 获取某分类的新论文（优先 new 公告源）。
    days>1 时回退到 recent 源并按日期过滤。
    """
    urls = [RSS_NEW.format(category=category)]
    if days > 1:
        urls.append(RSS_RECENT.format(category=category))

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    seen: set[str] = set()
    papers: list[Paper] = []

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
                # new 源通常已是当日；recent 源需要裁剪
                if "show=" in url:
                    continue

            title = (getattr(entry, "title", "") or "").replace("\n", " ").strip()
            summary = (getattr(entry, "summary", "") or "").replace("\n", " ").strip()
            # RSS 摘要常带 "arXiv:xxx Abstract: "
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


def fetch_from_api(
    category: str,
    target_date: date | None = None,
    days: int = 1,
    max_results: int = 200,
) -> list[Paper]:
    """
    通过官方 API 按提交日期拉取论文。
    submittedDate 区间使用东部时区的日历日。
    """
    end = target_date or arxiv_today()
    start = end - timedelta(days=max(days - 1, 0))
    # arXiv API 日期格式 YYYYMMDDHHMM（按 UTC 存储，这里用整天窗口）
    start_s = start.strftime("%Y%m%d0000")
    end_s = end.strftime("%Y%m%d2359")

    query = f"cat:{category} AND submittedDate:[{start_s} TO {end_s}]"
    client = arxiv.Client(page_size=min(100, max_results), delay_seconds=3.0, num_retries=3)
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    papers: list[Paper] = []
    for result in client.results(search):
        papers.append(
            Paper(
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
        )
    return papers


def fetch_papers(
    category: str,
    keywords: list[str] | None = None,
    keyword_mode: str = "any",
    target_date: date | None = None,
    days: int = 1,
    source: str = "auto",
    max_results: int = 200,
) -> list[Paper]:
    """
    拉取并筛选论文。
    source: auto | rss | api
      auto = 先 RSS（快），结果少时再补 API
    """
    keywords = keywords or []
    papers: list[Paper] = []

    if source in ("auto", "rss"):
        papers = fetch_from_rss(category, days=days)

    if source == "api" or (source == "auto" and len(papers) < 5):
        try:
            api_papers = fetch_from_api(
                category,
                target_date=target_date,
                days=days,
                max_results=max_results,
            )
            if source == "api":
                papers = api_papers
            else:
                seen = {p.arxiv_id for p in papers}
                for p in api_papers:
                    if p.arxiv_id not in seen:
                        papers.append(p)
                        seen.add(p.arxiv_id)
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
