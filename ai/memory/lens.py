from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from memory.types import Diagnostic, Lens, MemoryNote, RelationHint
from workspace_paths import data_root

try:
    import yaml
except Exception:  # noqa: BLE001
    yaml = None


class LensStore:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.lens_root = data_root(self.project_root) / "lenses"
        self._cache: dict[str, Lens] | None = None

    def refresh(self) -> dict[str, Lens]:
        self.lens_root.mkdir(parents=True, exist_ok=True)
        lenses: dict[str, Lens] = {}
        for path in sorted([*self.lens_root.rglob("*.yaml"), *self.lens_root.rglob("*.yml")]):
            payload = _load_yaml(path)
            if not payload:
                continue
            lens_id = str(payload.get("id") or f"lens.{path.stem}")
            lenses[lens_id] = Lens(
                lens_id=lens_id,
                applies_to=[str(item) for item in payload.get("applies_to") or []],
                suggested_fields=dict(payload.get("suggested_fields") or {}),
                relation_hints=dict(payload.get("relation_hints") or {}),
                projection_hints=dict(payload.get("projection_hints") or {}),
                maturity_checks=dict(payload.get("maturity_checks") or {}),
            )
        self._cache = lenses
        return lenses

    def lenses(self) -> dict[str, Lens]:
        return self.refresh() if self._cache is None else self._cache

    def get(self, lens_id: str) -> Lens | None:
        normalized = str(lens_id or "").strip()
        if not normalized:
            return None
        return self.lenses().get(normalized)

    def pick(self, note: MemoryNote) -> Lens:
        lenses = self.lenses()
        if note.lens_id and note.lens_id in lenses:
            return lenses[note.lens_id]
        kind_lens = f"lens.{note.kind.lower()}"
        if kind_lens in lenses:
            return lenses[kind_lens]
        return lenses.get("lens.default") or Lens("lens.default")

    def list_rows(self) -> list[dict[str, Any]]:
        return [asdict(item) for item in sorted(self.lenses().values(), key=lambda lens: lens.lens_id)]


class LensInterpreter:
    def __init__(self, store: LensStore):
        self.store = store

    def analyze(self, note: MemoryNote) -> dict[str, Any]:
        lens = self.store.pick(note)
        normalized_fields = self.normalize_fields(note, lens)
        derived_relations = self.derive_relations(note, lens, normalized_fields)
        diagnostics = self.diagnose(note, lens, normalized_fields)
        return {
            "lens": asdict(lens),
            "normalized_fields": normalized_fields,
            "derived_relations": [asdict(item) for item in derived_relations],
            "diagnostics": [asdict(item) for item in diagnostics],
            "runtime_ready": not any(item.severity == "error" for item in diagnostics if item.code.startswith("runtime_ready")),
        }

    def normalize_fields(self, note: MemoryNote, lens: Lens) -> dict[str, Any]:
        normalized = dict(note.fields)
        for field_name, config in (lens.suggested_fields or {}).items():
            aliases = [field_name, *[str(item) for item in (config or {}).get("aliases") or []]]
            value = _first_field_value(note.fields, aliases)
            if value is None:
                continue
            kind = str((config or {}).get("kind") or "scalar")
            normalized[field_name] = _normalize_field_value(value, kind=kind)
        return normalized

    def derive_relations(self, note: MemoryNote, lens: Lens, normalized_fields: dict[str, Any]) -> list[RelationHint]:
        rows = list(note.relations)
        existing = {(item.predicate, item.target, item.kind) for item in rows}
        for field_name, config in (lens.relation_hints or {}).items():
            if field_name not in normalized_fields:
                continue
            predicate = str((config or {}).get("predicate") or field_name)
            kind = str((config or {}).get("kind") or "declared")
            values = normalized_fields.get(field_name)
            targets = values if isinstance(values, list) else [values]
            for target in targets:
                normalized_target = str(target or "").strip()
                key = (predicate, normalized_target, kind)
                if not normalized_target or key in existing:
                    continue
                existing.add(key)
                rows.append(
                    RelationHint(
                        predicate=predicate,
                        target=normalized_target,
                        label=predicate,
                        kind=kind,
                        status=_status_to_edge_status(note.status),
                        confidence=1.0,
                        evidence=f"{field_name}: {normalized_target}",
                        source_field=f"Fields.{field_name}",
                    )
                )
        return rows

    def diagnose(self, note: MemoryNote, lens: Lens, normalized_fields: dict[str, Any]) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        checks = lens.maturity_checks or {}
        diagnostics.extend(self._diagnose_stage(note, checks.get("published") or {}, normalized_fields, "published", "warning"))
        diagnostics.extend(self._diagnose_stage(note, checks.get("projectable") or {}, normalized_fields, "projectable", "warning"))
        diagnostics.extend(self._diagnose_stage(note, checks.get("runtime_ready") or {}, normalized_fields, "runtime_ready", "error"))
        return diagnostics

    def _diagnose_stage(
        self,
        note: MemoryNote,
        config: dict[str, Any],
        normalized_fields: dict[str, Any],
        stage: str,
        default_severity: str,
    ) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        required = [str(item) for item in config.get("required") or []]
        missing_required = [field for field in required if not _present(normalized_fields.get(field))]
        for field in missing_required:
            diagnostics.append(
                Diagnostic(
                    code=f"{stage}.missing_required",
                    severity=default_severity,
                    message=f"{stage} 缺少关键字段：{field}",
                    note_id=note.note_id,
                    field=field,
                )
            )
        required_any = [str(item) for item in config.get("required_any") or []]
        if required_any and not any(_present(normalized_fields.get(field)) for field in required_any):
            diagnostics.append(
                Diagnostic(
                    code=f"{stage}.missing_required_any",
                    severity=default_severity,
                    message=f"{stage} 至少需要其一字段：{', '.join(required_any)}",
                    note_id=note.note_id,
                )
            )
        recommended = [str(item) for item in config.get("recommended") or []]
        for field in recommended:
            if not _present(normalized_fields.get(field)):
                diagnostics.append(
                    Diagnostic(
                        code=f"{stage}.missing_recommended",
                        severity="info",
                        message=f"建议补充字段：{field}",
                        note_id=note.note_id,
                        field=field,
                    )
                )
        return diagnostics


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        return {}
    if yaml is not None:
        try:
            payload = yaml.safe_load(text) or {}
            return payload if isinstance(payload, dict) else {}
        except Exception:  # noqa: BLE001
            pass
    return _load_yaml_subset(text)


def _load_yaml_subset(text: str) -> dict[str, Any]:
    """Parse the small YAML subset used by data/lenses/*.yaml.

    This keeps LensStore usable in minimal Python environments where PyYAML is not
    installed. It intentionally supports only dict/list/scalar structures used by
    the built-in lens files; arbitrary YAML should still use PyYAML.
    """
    raw_lines = [line.rstrip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]

    for idx, raw_line in enumerate(raw_lines):
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1] if stack else root

        if line.startswith("- "):
            if isinstance(parent, list):
                parent.append(_yaml_scalar(line[2:].strip()))
            continue

        if ":" not in line or not isinstance(parent, dict):
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            parent[key] = _yaml_scalar(value)
            continue

        child: Any = [] if _next_content_is_list(raw_lines, idx, indent) else {}
        parent[key] = child
        stack.append((indent, child))
    return root


def _next_content_is_list(lines: list[str], idx: int, indent: int) -> bool:
    for following in lines[idx + 1 :]:
        next_indent = len(following) - len(following.lstrip(" "))
        if next_indent <= indent:
            return False
        stripped = following.strip()
        if stripped:
            return stripped.startswith("- ")
    return False


def _yaml_scalar(value: str) -> Any:
    raw = value.strip()
    if not raw:
        return ""
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [_yaml_scalar(part.strip()) for part in inner.split(",") if part.strip()]
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    if raw.lower() in {"true", "false"}:
        return raw.lower() == "true"
    try:
        return int(raw)
    except ValueError:
        return raw


def _first_field_value(fields: dict[str, Any], aliases: list[str]) -> Any:
    alias_lookup = {str(alias).strip().lower(): alias for alias in aliases if str(alias).strip()}
    for key, value in fields.items():
        if str(key).strip().lower() in alias_lookup:
            return value
    return None


def _normalize_field_value(value: Any, *, kind: str) -> Any:
    if kind == "link_list":
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return [str(item).strip() for item in str(value or "").split(",") if str(item).strip()]
    return value


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip() not in {"待补充", "TODO", "TBD"}
    if isinstance(value, list):
        return any(_present(item) for item in value)
    return True


def _status_to_edge_status(status: str) -> str:
    if status in {"published", "projectable", "runtime_ready", "locked"}:
        return "published"
    if status == "reviewed":
        return "reviewed"
    if status == "rejected":
        return "rejected"
    return "candidate"
