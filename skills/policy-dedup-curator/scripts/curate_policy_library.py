#!/usr/bin/env python3
import argparse
import csv
import json
import re
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

REQ_FIELDS = ["title", "summary", "url"]

FIELD_ALIASES = {
    "title": ["标题", "title", "Title"],
    "summary": ["摘要", "summary", "Summary", "正文", "content", "正文摘要"],
    "url": ["原文地址", "原文链接", "url", "URL", "source_url", "link"],
    "source_name": ["来源地方", "来源网站", "source", "source_name"],
    "published_at": ["发布时间", "published_at", "date"],
}


def clean_text(s: str) -> str:
    s = "" if s is None else str(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_url(url: str) -> str:
    url = clean_text(url)
    if not url:
        return ""
    url = url.replace("\u002F", "/")
    return url.rstrip("/")


def pick(row: dict, logical_name: str) -> str:
    for key in FIELD_ALIASES.get(logical_name, []):
        if key in row and clean_text(row[key]):
            return clean_text(row[key])
    return ""


def iter_json(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield item
    elif isinstance(data, dict):
        for key in ["results", "rows", "data", "items", "records"]:
            val = data.get(key)
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        yield item
                return
        yield data


def iter_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield dict(row)


def iter_xlsx(path: Path):
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("a:si", ns):
                txt = "".join(t.text or "" for t in si.findall(".//a:t", ns))
                shared.append(txt)
        sheet_name = "xl/worksheets/sheet1.xml"
        if sheet_name not in z.namelist():
            return
        root = ET.fromstring(z.read(sheet_name))
        rows = root.findall(".//a:sheetData/a:row", ns)
        parsed_rows = []
        for row in rows:
            vals = []
            for c in row.findall("a:c", ns):
                t = c.get("t")
                v = c.find("a:v", ns)
                value = ""
                if v is not None and v.text is not None:
                    value = v.text
                    if t == "s":
                        try:
                            value = shared[int(value)]
                        except Exception:
                            pass
                else:
                    is_node = c.find("a:is", ns)
                    if is_node is not None:
                        value = "".join(tn.text or "" for tn in is_node.findall(".//a:t", ns))
                vals.append(clean_text(value))
            parsed_rows.append(vals)
        if not parsed_rows:
            return
        headers = parsed_rows[0]
        for vals in parsed_rows[1:]:
            row = {}
            for i, h in enumerate(headers):
                if h:
                    row[h] = vals[i] if i < len(vals) else ""
            if row:
                yield row


def iter_records(path: Path):
    suffix = path.suffix.lower()
    if suffix == ".json":
        yield from iter_json(path)
    elif suffix == ".csv":
        yield from iter_csv(path)
    elif suffix == ".xlsx":
        yield from iter_xlsx(path)


def write_xlsx(rows, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "政策库"
    headers = ["标题", "摘要", "原文链接", "来源地方", "发布时间"]
    ws.append(headers)
    for r in rows:
        ws.append([
            r.get("title", ""),
            r.get("summary", ""),
            r.get("url", ""),
            r.get("source_name", ""),
            r.get("published_at", ""),
        ])
    wb.save(output_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, nargs="+", help="Input files or directories")
    ap.add_argument("--output", required=True, help="Output xlsx path")
    ap.add_argument("--log", required=False, help="Optional log json path")
    args = ap.parse_args()

    paths = []
    for raw in args.input:
        p = Path(raw).expanduser()
        if p.is_dir():
            for sub in p.rglob("*"):
                if sub.is_file() and sub.suffix.lower() in {".xlsx", ".csv", ".json"}:
                    paths.append(sub)
        elif p.is_file():
            paths.append(p)

    total_in = 0
    dropped_missing = 0
    deduped = 0
    seen_urls = set()
    curated = []

    for path in paths:
        for row in iter_records(path):
            total_in += 1
            title = pick(row, "title")
            summary = pick(row, "summary")
            url = normalize_url(pick(row, "url"))
            source_name = pick(row, "source_name")
            published_at = pick(row, "published_at")

            if not title or not summary or not url:
                dropped_missing += 1
                continue
            if url in seen_urls:
                deduped += 1
                continue
            seen_urls.add(url)
            curated.append({
                "title": title,
                "summary": summary,
                "url": url,
                "source_name": source_name,
                "published_at": published_at,
            })

    write_xlsx(curated, Path(args.output).expanduser())

    if args.log:
        log = {
            "total_input_records": total_in,
            "dropped_missing_required_fields": dropped_missing,
            "dropped_duplicate_by_original_url": deduped,
            "output_records": len(curated),
            "required_fields": REQ_FIELDS,
            "dedup_key": "原文地址",
            "output": str(Path(args.output).expanduser()),
            "inputs": [str(p) for p in paths],
        }
        Path(args.log).expanduser().write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
