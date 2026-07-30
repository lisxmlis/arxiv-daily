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
    is_valid_category,
    papers_to_markdown,
    resolve_categories,
)
from categories_data import CATEGORY_GROUPS

from presets import (
    create_preset,
    delete_preset,
    get_preset,
    list_presets,
    load_store,
    set_last_preset,
    upsert_preset,
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
    .kw-chip {
        display: inline-block;
        background: #ecfdf5;
        color: #065f46;
        border-radius: 6px;
        padding: 0.15rem 0.5rem;
        margin: 0.15rem 0.25rem 0.15rem 0;
        font-size: 0.85rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


def _category_to_label(code: str) -> str:
    for label, cat in CATEGORIES.items():
        if cat == code:
            return label
    return code


def _parse_custom_codes(raw: str) -> list[str]:
    return [c.strip() for c in raw.replace(";", ",").split(",") if c.strip()]


def _codes_from_labels_and_custom(labels: list[str], custom_raw: str) -> list[str]:
    codes = [CATEGORIES[l] for l in labels if l in CATEGORIES]
    codes.extend(_parse_custom_codes(custom_raw))
    return resolve_categories(codes)


def _category_multiselect(
    *,
    key_prefix: str,
    default_codes: list[str] | None = None,
) -> list[str]:
    """分组 + 多选主题，返回分类代码列表。"""
    default_codes = list(default_codes or ["cs.LG"])
    group_names = ["全部类别", *CATEGORY_GROUPS.keys()]
    group = st.selectbox(
        "主题分组",
        options=group_names,
        index=0,
        key=f"{key_prefix}_group",
        help="先选分组缩小范围，再多选具体主题。已覆盖 arXiv 官方全部 155 个子类 + 一级大类。",
    )
    if group == "全部类别":
        options = list(CATEGORIES.keys())
    else:
        options = [x for x in CATEGORY_GROUPS.get(group, []) if x in CATEGORIES]
        for code in default_codes:
            label = _category_to_label(code)
            if label in CATEGORIES and label not in options:
                options.append(label)

    default_labels: list[str] = []
    for code in default_codes:
        label = _category_to_label(code)
        if label in options:
            default_labels.append(label)

    selected_labels = st.multiselect(
        "主题分类（可多选）",
        options=options,
        default=default_labels,
        key=f"{key_prefix}_cats",
        help="可同时选择多个主题；一级大类（如凝聚态全部 cond-mat）会覆盖其下全部子类。",
    )
    selected_codes = [CATEGORIES[l] for l in selected_labels if l in CATEGORIES]

    # 当前分组未显示、但仍属于默认/已选的自定义代码
    visible_codes = {CATEGORIES[l] for l in options if l in CATEGORIES}
    leftover = [c for c in default_codes if c not in selected_codes and c not in visible_codes]
    custom_default = ", ".join(leftover)
    custom_raw = st.text_input(
        "额外自定义分类代码（可选，逗号分隔）",
        value=custom_default,
        placeholder="例如 cond-mat.str-el, quant-ph",
        key=f"{key_prefix}_custom",
    )
    return _codes_from_labels_and_custom(selected_labels, custom_raw)


def _run_fetch(
    *,
    categories: list[str],
    keywords: list[str],
    keyword_mode: str,
    target: date,
    days: int,
    source: str,
    max_results: int,
    preset_name: str | None = None,
) -> None:
    cat_text = ", ".join(categories)
    with st.spinner(f"正在拉取 {cat_text} …"):
        try:
            papers = fetch_papers(
                categories=categories,
                keywords=keywords,
                keyword_mode=keyword_mode,
                target_date=target,
                days=days,
                source=source,
                max_results=max_results,
            )
            st.session_state.papers = papers
            st.session_state.last_query = {
                "category": cat_text,
                "categories": categories,
                "date": str(target),
                "days": days,
                "keywords": keywords,
                "preset_name": preset_name,
            }
        except Exception as e:
            st.error(f"拉取失败：{e}")


def _render_preset_keywords(keywords: list[str]) -> None:
    if not keywords:
        st.caption("尚未添加关键词。")
        return
    chips = "".join(f'<span class="kw-chip">{escape(k)}</span>' for k in keywords)
    st.markdown(chips, unsafe_allow_html=True)


def _render_category_chips(codes: list[str]) -> None:
    if not codes:
        st.caption("尚未选择主题。")
        return
    chips = "".join(f'<span class="kw-chip">{escape(c)}</span>' for c in codes)
    st.markdown(chips, unsafe_allow_html=True)


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


def _sidebar_presets(store: dict) -> None:
    presets = list_presets(store)
    st.subheader("固定分类")
    st.caption("保存常用主题 + 关键词，下次一键筛选。")

    if not presets:
        st.info("还没有固定分类，请先新建一个。")
    else:
        id_to_name = {p["id"]: p["name"] for p in presets}
        ids = list(id_to_name.keys())
        last_id = store.get("last_preset_id")
        default_idx = ids.index(last_id) if last_id in ids else 0

        selected_id = st.selectbox(
            "选择固定分类",
            options=ids,
            index=default_idx,
            format_func=lambda i: id_to_name[i],
            key="preset_select",
        )
        if selected_id != store.get("last_preset_id"):
            set_last_preset(store, selected_id)

        preset = get_preset(store, selected_id)
        assert preset is not None

        cat_codes = resolve_categories(
            preset.get("categories") or preset.get("category"),
            preset.get("category_labels") or preset.get("category_label") or preset.get("name"),
        )
        st.write("**主题代码：**")
        _render_category_chips(cat_codes)
        bad = [c for c in cat_codes if not is_valid_category(c)]
        if not cat_codes:
            st.error("尚未选择主题，请在编辑里至少选一个。")
        elif bad:
            st.error(
                f"分类代码无效：{bad!r}。请点下方「编辑此固定分类」重新选择并保存。"
            )
        elif cat_codes != list(preset.get("categories") or []):
            st.warning(f"已自动纠正主题列表。")
            preset["categories"] = cat_codes
            upsert_preset(store, preset)

        st.markdown("**关键词：**")
        _render_preset_keywords(preset.get("keywords") or [])
        st.caption(
            f"匹配方式：{'命中任一' if preset.get('keyword_mode') == 'any' else '全部命中'}"
            f" · 回溯 {preset.get('days', 1)} 天"
        )

        if st.button("一键筛选", type="primary", use_container_width=True, key="preset_fetch"):
            _run_fetch(
                categories=cat_codes,
                keywords=list(preset.get("keywords") or []),
                keyword_mode=preset.get("keyword_mode", "any"),
                target=arxiv_today(),
                days=int(preset.get("days", 2)),
                source=preset.get("source", "auto"),
                max_results=max(int(preset.get("max_results", 100)), 200),
                preset_name=preset["name"],
            )

        with st.expander("编辑此固定分类", expanded=False):
            _edit_preset_form(store, preset)

    with st.expander("新建固定分类", expanded=not presets):
        _create_preset_form(store)


def _edit_preset_form(store: dict, preset: dict) -> None:
    pid = preset["id"]
    name = st.text_input("名称", value=preset["name"], key=f"edit_name_{pid}")

    current_codes = resolve_categories(
        preset.get("categories") or preset.get("category"),
        preset.get("category_labels") or preset.get("category_label"),
    )
    categories = _category_multiselect(
        key_prefix=f"edit_{pid}",
        default_codes=current_codes,
    )

    st.markdown("**关键词列表**")
    keywords = list(preset.get("keywords") or [])
    if not keywords:
        st.caption("暂无关键词。")
    for i, kw in enumerate(keywords):
        c1, c2 = st.columns([5, 1])
        c1.write(f"· {kw}")
        if c2.button("删除", key=f"del_kw_{pid}_{i}"):
            keywords.pop(i)
            preset["keywords"] = keywords
            upsert_preset(store, preset)
            st.rerun()

    new_kw = st.text_input("新增关键词", placeholder="例如 spintronics", key=f"add_kw_{pid}")
    if st.button("添加关键词", key=f"add_kw_btn_{pid}"):
        k = new_kw.strip()
        if not k:
            st.warning("请输入关键词。")
        elif k.lower() in {x.lower() for x in keywords}:
            st.warning("该关键词已存在。")
        else:
            keywords.append(k)
            preset["keywords"] = keywords
            upsert_preset(store, preset)
            st.rerun()

    batch = st.text_input(
        "批量添加（逗号分隔）",
        placeholder="LLM, transformer, attention",
        key=f"batch_kw_{pid}",
    )
    if st.button("批量添加", key=f"batch_kw_btn_{pid}"):
        existing = {x.lower() for x in keywords}
        added = 0
        for part in batch.split(","):
            k = part.strip()
            if k and k.lower() not in existing:
                keywords.append(k)
                existing.add(k.lower())
                added += 1
        if added:
            preset["keywords"] = keywords
            upsert_preset(store, preset)
            st.rerun()
        else:
            st.warning("没有可添加的新关键词。")

    keyword_mode = st.radio(
        "关键词匹配",
        options=["any", "all"],
        index=0 if preset.get("keyword_mode", "any") == "any" else 1,
        format_func=lambda x: "命中任一" if x == "any" else "全部命中",
        horizontal=True,
        key=f"edit_mode_{pid}",
    )
    days = st.slider("回溯天数", 1, 7, int(preset.get("days", 2)), key=f"edit_days_{pid}")
    source = st.selectbox(
        "数据源",
        options=["auto", "rss", "api"],
        index=["auto", "rss", "api"].index(preset.get("source", "auto")),
        format_func=lambda x: {
            "auto": "自动（RSS 优先）",
            "rss": "仅 RSS（更快）",
            "api": "仅官方 API（更全）",
        }[x],
        key=f"edit_src_{pid}",
    )
    max_results = st.slider(
        "API 最大条数", 20, 300, int(preset.get("max_results", 100)), 20, key=f"edit_max_{pid}"
    )

    b1, b2 = st.columns(2)
    if b1.button("保存修改", type="primary", use_container_width=True, key=f"save_{pid}"):
        if not categories:
            st.error("请至少选择一个主题。")
        elif any(not is_valid_category(c) for c in categories):
            st.error(f"存在无效分类代码：{categories!r}")
        else:
            preset["name"] = name.strip() or preset["name"]
            preset["categories"] = categories
            preset["category_labels"] = [_category_to_label(c) for c in categories]
            preset["category"] = categories[0]
            preset["category_label"] = preset["category_labels"][0]
            preset["keywords"] = keywords
            preset["keyword_mode"] = keyword_mode
            preset["days"] = days
            preset["source"] = source
            preset["max_results"] = max_results
            upsert_preset(store, preset)
            set_last_preset(store, pid)
            st.success(f"已保存（主题 {', '.join(categories)}）。")
            st.rerun()

    if b2.button("删除此分类", use_container_width=True, key=f"delete_{pid}"):
        delete_preset(store, pid)
        st.rerun()


def _create_preset_form(store: dict) -> None:
    name = st.text_input("名称", value="我的研究兴趣", key="new_preset_name")
    categories = _category_multiselect(key_prefix="new", default_codes=["cs.LG"])
    kw_raw = st.text_input(
        "初始关键词（逗号分隔）",
        placeholder="spintronics, van der Waals, neuromorphic",
        key="new_kws",
    )
    keywords = [k.strip() for k in kw_raw.split(",") if k.strip()]
    keyword_mode = st.radio(
        "关键词匹配",
        options=["any", "all"],
        format_func=lambda x: "命中任一" if x == "any" else "全部命中",
        horizontal=True,
        key="new_mode",
    )
    days = st.slider("回溯天数", 1, 7, 2, key="new_days")

    if st.button("创建固定分类", type="primary", use_container_width=True, key="create_preset"):
        if not categories:
            st.error("请至少选择一个主题。")
        elif any(not is_valid_category(c) for c in categories):
            st.error(f"存在无效分类代码：{categories!r}")
        else:
            create_preset(
                store,
                name=name,
                categories=categories,
                category_labels=[_category_to_label(c) for c in categories],
                keywords=keywords,
                keyword_mode=keyword_mode,
                days=days,
            )
            st.success(f"已创建「{name}」（主题 {', '.join(categories)}）。")
            st.rerun()


def _sidebar_manual(store: dict) -> None:
    st.subheader("手动筛选")
    categories = _category_multiselect(key_prefix="manual", default_codes=["cs.LG"])

    today = arxiv_today()
    target = st.date_input("目标日期（arXiv 东部时区）", value=today, key="manual_date")
    days = st.slider(
        "回溯天数",
        min_value=1,
        max_value=7,
        value=1,
        help="1 = 仅当天；周末/节假日可适当加大。",
        key="manual_days",
    )

    kw_raw = st.text_input(
        "关键词（逗号分隔）",
        placeholder="transformer, diffusion, LLM",
        key="manual_kws",
    )
    keywords = [k.strip() for k in kw_raw.split(",") if k.strip()]
    keyword_mode = st.radio(
        "关键词匹配",
        options=["any", "all"],
        format_func=lambda x: "命中任一" if x == "any" else "全部命中",
        horizontal=True,
        key="manual_mode",
    )

    source = st.selectbox(
        "数据源",
        options=["auto", "rss", "api"],
        format_func=lambda x: {
            "auto": "自动（RSS 优先）",
            "rss": "仅 RSS（更快）",
            "api": "仅官方 API（更全）",
        }[x],
        key="manual_src",
    )
    max_results = st.slider("API 最大条数", 20, 300, 100, 20, key="manual_max")

    if st.button("获取论文", type="primary", use_container_width=True, key="manual_fetch"):
        if not categories:
            st.error("请至少选择一个主题。")
        else:
            _run_fetch(
                categories=categories,
                keywords=keywords,
                keyword_mode=keyword_mode,
                target=target,
                days=days,
                source=source,
                max_results=max_results,
            )

    save_name = st.text_input("保存为固定分类（名称）", key="save_as_name")
    if st.button("保存当前条件为固定分类", use_container_width=True, key="save_as_preset"):
        if not categories:
            st.error("请至少选择一个主题。")
        else:
            create_preset(
                store,
                name=save_name.strip() or "未命名固定分类",
                categories=categories,
                category_labels=[_category_to_label(c) for c in categories],
                keywords=keywords,
                keyword_mode=keyword_mode,
                days=days,
                source=source,
                max_results=max_results,
            )
            st.success("已保存为固定分类，可在上方切换到「固定分类」使用。")


def main() -> None:
    st.title("arXiv Daily")
    st.caption("自动获取 arXiv 当日（或近几日）新论文，并按主题与关键词筛选。")

    store = load_store()

    with st.sidebar:
        st.header("筛选条件")
        mode = st.radio(
            "模式",
            options=["preset", "manual"],
            format_func=lambda x: "固定分类" if x == "preset" else "手动筛选",
            horizontal=True,
            key="filter_mode",
        )
        st.divider()
        if mode == "preset":
            _sidebar_presets(store)
        else:
            _sidebar_manual(store)

    if "papers" not in st.session_state:
        st.session_state.papers = []
        st.session_state.last_query = None

    papers: list[Paper] = st.session_state.papers
    q = st.session_state.last_query

    if q is None:
        st.info("左侧选择「固定分类」后点「一键筛选」，或切换到「手动筛选」。")
        st.markdown(
            """
**固定分类怎么用**
1. 左侧选「固定分类」→「新建固定分类」，填入主题和关键词并创建  
2. 之后每次进入，选中该分类，点「一键筛选」即可  
3. 在「编辑此固定分类」里可多选主题，并增加 / 删除关键词  

**说明**
- arXiv 按美国东部时间发布，工作日傍晚左右更新新帖公告  
- 「当天」若结果很少，可把回溯天数调到 2–3  
- 关键词匹配标题、摘要、作者、分类（不区分大小写）  
"""
        )
        return

    end = date.fromisoformat(q["date"])
    start = end - timedelta(days=max(q["days"] - 1, 0))
    kw_text = ", ".join(q["keywords"]) if q["keywords"] else "（无）"
    preset_bit = f" · 固定分类「{q['preset_name']}」" if q.get("preset_name") else ""
    st.success(
        f"分类 `{q['category']}` · {start} → {end} · 关键词: {kw_text}"
        f"{preset_bit} · 命中 **{len(papers)}** 篇"
    )

    if not papers:
        st.warning("没有符合条件的论文。可放宽关键词，或增大回溯天数。")
        return

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
