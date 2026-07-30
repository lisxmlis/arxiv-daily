"""固定分类（筛选预设）的读写。"""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

from fetcher import CATEGORIES, resolve_categories, resolve_category

PRESETS_PATH = Path(__file__).resolve().parent / "presets.json"

DEFAULT_STORE: dict[str, Any] = {
    "version": 1,
    "last_preset_id": None,
    "presets": [],
}


def _empty_preset(name: str = "我的固定分类") -> dict[str, Any]:
    return {
        "id": uuid.uuid4().hex[:12],
        "name": name,
        "category": "cs.LG",
        "category_label": "机器学习 (cs.LG)",
        "categories": ["cs.LG"],
        "category_labels": ["机器学习 (cs.LG)"],
        "keywords": [],
        "keyword_mode": "any",
        "days": 2,
        "source": "auto",
        "max_results": 100,
    }


def _labels_for_codes(codes: list[str]) -> list[str]:
    code_to_label = {code: label for label, code in CATEGORIES.items()}
    return [code_to_label.get(c, c) for c in codes]


def _normalize_preset(p: dict[str, Any]) -> dict[str, Any]:
    base = _empty_preset()
    # 先合并旧字段
    for k, v in p.items():
        if k in base or k in ("categories", "category_labels"):
            base[k] = v

    if not base.get("id"):
        base["id"] = uuid.uuid4().hex[:12]
    if not isinstance(base.get("keywords"), list):
        base["keywords"] = []
    base["keywords"] = [str(k).strip() for k in base["keywords"] if str(k).strip()]

    # 兼容旧版单主题 -> 多主题
    raw_cats = base.get("categories")
    if not isinstance(raw_cats, list) or not raw_cats:
        raw_cats = [base.get("category") or "cs.LG"]
    raw_labels = base.get("category_labels")
    if not isinstance(raw_labels, list) or not raw_labels:
        raw_labels = [base.get("category_label") or base.get("name") or ""]

    codes = resolve_categories(raw_cats, raw_labels)
    if not codes:
        codes = ["cs.LG"]
    labels = _labels_for_codes(codes)
    # 若原 labels 更完整则尽量保留展示名
    if isinstance(base.get("category_labels"), list) and len(base["category_labels"]) == len(codes):
        labels = [
            old if old else new
            for old, new in zip(base["category_labels"], labels)
        ]

    base["categories"] = codes
    base["category_labels"] = labels
    base["category"] = codes[0]
    base["category_label"] = labels[0]
    return base


def load_store() -> dict[str, Any]:
    if not PRESETS_PATH.exists():
        store = deepcopy(DEFAULT_STORE)
        save_store(store)
        return store
    try:
        data = json.loads(PRESETS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        store = deepcopy(DEFAULT_STORE)
        save_store(store)
        return store

    if not isinstance(data, dict):
        store = deepcopy(DEFAULT_STORE)
        save_store(store)
        return store

    data.setdefault("version", 1)
    data.setdefault("last_preset_id", None)
    data.setdefault("presets", [])
    cleaned = [_normalize_preset(p) for p in data["presets"] if isinstance(p, dict)]
    data["presets"] = cleaned
    save_store(data)
    return data


def save_store(store: dict[str, Any]) -> None:
    PRESETS_PATH.write_text(
        json.dumps(store, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def list_presets(store: dict[str, Any]) -> list[dict[str, Any]]:
    return list(store.get("presets") or [])


def get_preset(store: dict[str, Any], preset_id: str | None) -> dict[str, Any] | None:
    if not preset_id:
        return None
    for p in list_presets(store):
        if p["id"] == preset_id:
            return p
    return None


def upsert_preset(store: dict[str, Any], preset: dict[str, Any]) -> dict[str, Any]:
    preset = _normalize_preset(preset)
    presets = list_presets(store)
    for i, p in enumerate(presets):
        if p["id"] == preset["id"]:
            presets[i] = preset
            store["presets"] = presets
            save_store(store)
            return preset
    presets.append(preset)
    store["presets"] = presets
    save_store(store)
    return preset


def delete_preset(store: dict[str, Any], preset_id: str) -> None:
    store["presets"] = [p for p in list_presets(store) if p["id"] != preset_id]
    if store.get("last_preset_id") == preset_id:
        store["last_preset_id"] = store["presets"][0]["id"] if store["presets"] else None
    save_store(store)


def set_last_preset(store: dict[str, Any], preset_id: str | None) -> None:
    store["last_preset_id"] = preset_id
    save_store(store)


def create_preset(
    store: dict[str, Any],
    name: str,
    *,
    category: str | None = None,
    category_label: str = "",
    categories: list[str] | None = None,
    category_labels: list[str] | None = None,
    keywords: list[str] | None = None,
    keyword_mode: str = "any",
    days: int = 2,
    source: str = "auto",
    max_results: int = 100,
) -> dict[str, Any]:
    preset = _empty_preset(name.strip() or "我的固定分类")
    cats = resolve_categories(
        categories if categories is not None else (category or "cs.LG"),
        category_labels if category_labels is not None else category_label,
    )
    if not cats:
        cats = [resolve_category(category or "cs.LG", category_label or name)]
    labels = category_labels or _labels_for_codes(cats)
    if len(labels) != len(cats):
        labels = _labels_for_codes(cats)

    preset["categories"] = cats
    preset["category_labels"] = labels
    preset["category"] = cats[0]
    preset["category_label"] = labels[0]
    preset["keywords"] = [k.strip() for k in (keywords or []) if k.strip()]
    preset["keyword_mode"] = keyword_mode
    preset["days"] = days
    preset["source"] = source
    preset["max_results"] = max_results
    upsert_preset(store, preset)
    set_last_preset(store, preset["id"])
    return preset
