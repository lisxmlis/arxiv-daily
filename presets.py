"""固定分类（筛选预设）的读写。"""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

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
        "keywords": [],
        "keyword_mode": "any",
        "days": 2,
        "source": "auto",
        "max_results": 100,
    }


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
    # 规范化每条预设
    cleaned = []
    for p in data["presets"]:
        if not isinstance(p, dict):
            continue
        base = _empty_preset()
        base.update({k: v for k, v in p.items() if k in base})
        if not base.get("id"):
            base["id"] = uuid.uuid4().hex[:12]
        if not isinstance(base.get("keywords"), list):
            base["keywords"] = []
        base["keywords"] = [str(k).strip() for k in base["keywords"] if str(k).strip()]
        cleaned.append(base)
    data["presets"] = cleaned
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
    category: str = "cs.LG",
    category_label: str = "",
    keywords: list[str] | None = None,
    keyword_mode: str = "any",
    days: int = 2,
    source: str = "auto",
    max_results: int = 100,
) -> dict[str, Any]:
    preset = _empty_preset(name.strip() or "我的固定分类")
    preset["category"] = category
    preset["category_label"] = category_label or category
    preset["keywords"] = [k.strip() for k in (keywords or []) if k.strip()]
    preset["keyword_mode"] = keyword_mode
    preset["days"] = days
    preset["source"] = source
    preset["max_results"] = max_results
    upsert_preset(store, preset)
    set_last_preset(store, preset["id"])
    return preset
