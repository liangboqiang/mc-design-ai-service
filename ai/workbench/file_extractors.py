from __future__ import annotations

import csv
import json
import zipfile
from html import unescape
from pathlib import Path
from xml.etree import ElementTree as ET


TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".py", ".js", ".ts", ".tsx", ".jsx", ".css", ".html", ".json", ".yaml", ".yml", ".toml", ".csv", ".log"}


def extract_text(path: Path, *, max_chars: int = 120_000) -> dict:
    """Best-effort local text extraction.

    Optional heavy parsers can be added later. This fallback keeps the package
    self-contained and supports common text, markdown, json/csv, docx and xlsx
    without external services.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(str(path))
    try:
        if suffix in TEXT_SUFFIXES:
            text = _read_text(path)
            if suffix == ".json":
                text = _pretty_json(text)
            if suffix == ".csv":
                text = _preview_csv(path)
            return _payload(path, text, "plain")
        if suffix == ".docx":
            return _payload(path, _read_docx(path), "docx")
        if suffix == ".xlsx":
            return _payload(path, _read_xlsx(path), "xlsx")
        if suffix == ".pdf":
            return _payload(path, _read_pdf_optional(path), "pdf")
        return _payload(path, _read_text(path), "binary-text-fallback")
    except UnicodeDecodeError:
        return _payload(path, "", "unsupported-binary", warning="暂不支持该二进制文件的本地文本抽取。")
    except Exception as exc:  # noqa: BLE001
        return _payload(path, "", "extract-error", warning=str(exc))


def _payload(path: Path, text: str, parser: str, warning: str = "") -> dict:
    text = (text or "")[:120_000]
    return {
        "path": path.as_posix(),
        "filename": path.name,
        "suffix": path.suffix.lower(),
        "parser": parser,
        "text": text,
        "markdown": _to_markdown(path, text, parser, warning),
        "warning": warning,
        "char_count": len(text),
    }


def _read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def _pretty_json(text: str) -> str:
    try:
        return json.dumps(json.loads(text), ensure_ascii=False, indent=2)
    except Exception:  # noqa: BLE001
        return text


def _preview_csv(path: Path) -> str:
    rows: list[list[str]] = []
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as fh:
        reader = csv.reader(fh)
        for idx, row in enumerate(reader):
            if idx >= 80:
                break
            rows.append([str(cell) for cell in row[:24]])
    if not rows:
        return ""
    widths = [0] * max(len(row) for row in rows)
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = min(40, max(widths[idx], len(cell)))
    lines = []
    for row in rows:
        padded = [cell[:40].ljust(widths[idx]) for idx, cell in enumerate(row)]
        lines.append(" | ".join(padded).rstrip())
    return "\n".join(lines)


def _read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", ns):
        texts = [node.text or "" for node in paragraph.findall(".//w:t", ns)]
        line = "".join(texts).strip()
        if line:
            paragraphs.append(line)
    return "\n\n".join(paragraphs)


def _read_xlsx(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in root.iter():
                if si.tag.endswith("}t") and si.text:
                    shared.append(si.text)
        sheets = [name for name in zf.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")]
        output: list[str] = []
        for sheet in sheets[:5]:
            root = ET.fromstring(zf.read(sheet))
            output.append(f"## {sheet}")
            for row in root.iter():
                if not row.tag.endswith("}row"):
                    continue
                values: list[str] = []
                for cell in row:
                    if not cell.tag.endswith("}c"):
                        continue
                    value_node = next((child for child in cell if child.tag.endswith("}v")), None)
                    value = value_node.text if value_node is not None else ""
                    if cell.attrib.get("t") == "s" and value.isdigit() and int(value) < len(shared):
                        value = shared[int(value)]
                    values.append(value or "")
                if any(values):
                    output.append(" | ".join(values))
        return "\n".join(output)


def _read_pdf_optional(path: Path) -> str:
    try:
        from PyPDF2 import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages[:30])
    except Exception as exc:  # noqa: BLE001
        return f"[PDF 本地抽取未启用或失败：{exc}]"


def _to_markdown(path: Path, text: str, parser: str, warning: str = "") -> str:
    title = path.stem.replace("_", " ").strip() or path.name
    warning_line = f"\n> 抽取提示：{unescape(warning)}\n" if warning else ""
    body = text.strip() or "暂无可抽取文本。"
    return f"# {title}\n\n- 文件：`{path.name}`\n- 解析器：`{parser}`\n{warning_line}\n## Extracted Text\n\n{body}\n"
