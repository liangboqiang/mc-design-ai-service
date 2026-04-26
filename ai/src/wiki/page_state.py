from __future__ import annotations

from .page_parser import parse_chinese_page

LOCKED_WORDS = {"锁定", "已锁定", "禁止修改", "禁止更新"}
DISABLED_WORDS = {"禁用", "已禁用", "禁止检索", "禁止图谱"}

def is_locked_markdown(markdown: str) -> bool:
    model = parse_chinese_page(markdown)
    value = str(model.fields.get("锁定状态") or "").strip()
    return any(word in value for word in LOCKED_WORDS) and "未锁定" not in value

def is_disabled_markdown(markdown: str) -> bool:
    model = parse_chinese_page(markdown)
    value = str(model.fields.get("禁用状态") or "").strip()
    return any(word in value for word in DISABLED_WORDS) and "未禁用" not in value

def page_scope(markdown: str) -> str:
    model = parse_chinese_page(markdown)
    return str(model.fields.get("作用范围") or "当前页面及直接关联对象").strip()

def local_relations(markdown: str) -> list[str]:
    model = parse_chinese_page(markdown)
    value = model.fields.get("局部关系") or []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [item.strip() for item in str(value).replace(",", "、").split("、") if item.strip()]
