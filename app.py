"""arXiv 每日新论文浏览器 — Streamlit UI。"""

from __future__ import annotations

import csv
import io
from datetime import date, timedelta
from html import escape

import pandas as pd
import streamlit as st

from fetcher import (
    CATEGORIES,
    Paper,
    arxiv_today,
    fetch_papers,
    papers_to_markdown,
)

st.set_page_config(
    page_title="arXiv Daily",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .block-container { padding-top: 1.5rem; max-width: 1100px; }
    .paper-card {
        border: 1px solid #e6e8eb;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.9rem;
        background: #fafbfc;
    }
    .paper-title { font-size: 1.05rem; font-weight: 650; margin-bottom: 0.35rem; }
    .meta { color: #5b6570; font-size: 0.9rem; margin-bottom: 0.45rem; }
    .abs { color: #2b3036; font-size: 0.95rem; line-height: 1.55; }
    .tag {
        display: inline-block;
        background: #eef2ff;
        color: #3730a3;
        border-radius: 6px;
        padding: 0.1rem 0.45rem;
        margin-right: 0.3rem;
        font-size: 0.78rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


def _render_paper(p: Paper, idx: int) -> None:
    authors = ", ".join(p.authors[:6])
    if len(p.authors) > 6:
        authors += " et al."
    tags = "".join(
        f'<span class="tag">{escape(c)}</span>' for c in p.categories[:6]
    )
    st.markdown(
        f"""
<div class="paper-card">
  <div class="paper-title">{idx}. {escape(p.title)}</div>
  <div class="meta">{escape(authors)}</div>
  <div class="meta">{p.published.strftime("%Y-%m-%d %H:%M UTC")} · ID: {escape(p.arxiv_id)}</div>
  <div style="margin-bottom:0.5rem;">{tags}</div>
  <div class="abs">{escape(p.summary)}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    c1, c2, _ = st.columns([1, 1, 6])
    c1.link_button("摘要页", p.abs_url, use_container_width=True)
    c2.link_button("PDF", p.pdf_url, use_container_width=True)


def main() -> None:
    st.title("arXiv Daily")
    st.caption("自动获取 arXiv 当日（或近几日）新论文，并按主题与关键词筛选。")

    with st.sidebar:
        st.header("筛选条件")
        cat_label = st.selectbox("主题分类", list(CATEGORIES.keys()), index=1)
        category = CATEGORIES[cat_label]

        custom_cat = st.text_input(
            "自定义分类代码（可选）",
            placeholder="例如 cs.LG 或 hep-th",
            help="填写后优先使用自定义分类，覆盖上方选择。",
        )
        if custom_cat.strip():
            category = custom_cat.strip()

        today = arxiv_today()
        target = st.date_input("目标日期（arXiv 东部时区）", value=today)
        days = st.slider(
            "回溯天数",
            min_value=1,
            max_value=7,
            value=1,
            help="1 = 仅当天；周末/节假日可适当加大。",
        )

        kw_raw = st.text_input(
            "关键词（逗号分隔）",
            placeholder="transformer, diffusion, LLM",
        )
        keywords = [k.strip() for k in kw_raw.split(",") if k.strip()]
        keyword_mode = st.radio(
            "关键词匹配",
            options=["any", "all"],
            format_func=lambda x: "命中任一" if x == "any" else "全部命中",
            horizontal=True,
        )

        source = st.selectbox(
            "数据源",
            options=["auto", "rss", "api"],
            format_func=lambda x: {
                "auto": "自动（RSS 优先）",
                "rss": "仅 RSS（更快）",
                "api": "仅官方 API（更全）",
            }[x],
        )
        max_results = st.slider("API 最大条数", 20, 300, 100, 20)

        fetch_btn = st.button("获取论文", type="primary", use_container_width=True)

    if "papers" not in st.session_state:
        st.session_state.papers = []
        st.session_state.last_query = None

    if fetch_btn:
        with st.spinner(f"正在拉取 {category} …"):
            try:
                papers = fetch_papers(
                    category=category,
                    keywords=keywords,
                    keyword_mode=keyword_mode,
                    target_date=target,
                    days=days,
                    source=source,
                    max_results=max_results,
                )
                st.session_state.papers = papers
                st.session_state.last_query = {
                    "category": category,
                    "date": str(target),
                    "days": days,
                    "keywords": keywords,
                }
            except Exception as e:
                st.error(f"拉取失败：{e}")
                return

    papers: list[Paper] = st.session_state.papers
    q = st.session_state.last_query

    if q is None:
        st.info("在左侧设置主题与关键词后，点击「获取论文」。")
        st.markdown(
            """
**说明**
- arXiv 按美国东部时间发布，工作日傍晚左右更新新帖公告。
- 「当天」若结果很少，可把回溯天数调到 2–3。
- 关键词会在标题、摘要、作者、分类中匹配（不区分大小写）。
"""
        )
        return

    end = date.fromisoformat(q["date"])
    start = end - timedelta(days=max(q["days"] - 1, 0))
    kw_text = ", ".join(q["keywords"]) if q["keywords"] else "（无）"
    st.success(
        f"分类 `{q['category']}` · {start} → {end} · 关键词: {kw_text} · 命中 **{len(papers)}** 篇"
    )

    if not papers:
        st.warning("没有符合条件的论文。可放宽关键词，或增大回溯天数。")
        return

    # 导出
    md = papers_to_markdown(
        papers,
        heading=f"arXiv {q['category']} {q['date']} (days={q['days']})",
    )
    rows = [p.to_dict() for p in papers]
    df = pd.DataFrame(rows)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

    e1, e2, e3 = st.columns(3)
    e1.download_button("导出 Markdown", md, file_name=f"arxiv_{q['category']}_{q['date']}.md")
    e2.download_button("导出 CSV", buf.getvalue(), file_name=f"arxiv_{q['category']}_{q['date']}.csv")
    e3.download_button(
        "导出 JSON",
        df.to_json(orient="records", force_ascii=False, indent=2),
        file_name=f"arxiv_{q['category']}_{q['date']}.json",
    )

    with st.expander("表格预览", expanded=False):
        st.dataframe(
            df[["arxiv_id", "title", "authors", "categories", "published", "abs_url"]],
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("论文列表")
    for i, p in enumerate(papers, 1):
        _render_paper(p, i)


if __name__ == "__main__":
    main()
