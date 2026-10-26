#!/usr/bin/env python3
"""Structural source audit, not a certification of translation accuracy.

No dependencies. Sources stay outside the repository. Counts are signals:
translated comments, reformatted examples and combined blocks may differ.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REF = "apache-iceberg-1.12.0"
BASE = f"https://raw.githubusercontent.com/apache/iceberg/{REF}/"


def structure(text):
    headings, blocks, table_keys = [], [], []
    fence, buf = None, []
    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence) and not match[2].strip():
                blocks.append("\n".join(buf))
                fence, buf = None, []
            else:
                buf.append(line)
        elif match:
            fence = match[1]
        else:
            if re.match(r"^#{1,6}\s", line):
                headings.append(line)
            if line.startswith("|"):
                key = line.split("|")[1].strip().strip("`")
                if re.fullmatch(r"[a-z][a-z0-9_.-]*", key) and ("." in key or "-" in key):
                    table_keys.append(key)
    if fence:
        blocks.append("\n".join(buf))
    return headings, blocks, table_keys


def fingerprint(code):
    # Only whitespace is ignored; SQL case and comments remain significant.
    return re.sub(r"\s+", "", code)


def obtain(cache, name, download):
    target = cache / name
    if download:
        data = urllib.request.urlopen(BASE + name, timeout=60).read()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    if not target.exists():
        raise SystemExit(f"Missing source: {target}; use --download or supply --source-root")
    return target.read_bytes()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--write", action="store_true", help="write source-parity.json and .md")
    args = parser.parse_args()
    nav_bytes = obtain(args.source_root, "docs/mkdocs.yml", args.download)
    nav = nav_bytes.decode()
    expected = set(re.findall(r"(?:^\s*-\s+|:\s+)([a-z][a-z0-9-]*\.md)\s*$", nav, re.M))
    # These pages are linked by section anchors rather than .md names in nav.
    expected.update(re.findall(r":\s+([a-z][a-z0-9-]*)/#", nav))
    expected = {name if name.endswith(".md") else name + ".md" for name in expected}
    local = {p.name for p in (ROOT / "docs").glob("*.md")}
    if expected != local:
        raise SystemExit(f"Navigation mismatch: missing={sorted(expected-local)}, extra={sorted(local-expected)}")
    pages = []
    for name in sorted(expected):
        raw = obtain(args.source_root, "docs/docs/" + name, args.download)
        source = raw.decode()
        target = (ROOT / "docs" / name).read_text()
        sh, sb, sk = structure(source)
        th, tb, tk = structure(target)
        available = Counter(fingerprint(b) for b in tb)
        unmatched = []
        for index, block in enumerate(sb, 1):
            key = fingerprint(block)
            if available[key]:
                available[key] -= 1
            else:
                unmatched.append(index)
        # A key outside a table may be explained in prose instead. This remains a signal.
        absent_keys = sorted({key for key in sk if key not in target})
        pages.append({
            "file": name, "source_sha256": hashlib.sha256(raw).hexdigest(),
            "translation_sha256": hashlib.sha256(target.encode()).hexdigest(),
            "source_headings": len(sh), "translation_headings": len(th),
            "source_code_blocks": len(sb), "translation_code_blocks": len(tb),
            "source_code_blocks_without_whitespace_match": unmatched,
            "source_table_keys_absent_from_translation": absent_keys,
        })
    report = {
        "source_ref": REF, "nav_sha256": hashlib.sha256(nav_bytes).hexdigest(),
        "pages": pages,
        "limitations": "Structural signals only; no paragraph-level or semantic certification. "
                        "Different block counts do not alone prove omissions. Code matching ignores only whitespace.",
    }
    lines = ["# Сверка структуры с Iceberg 1.12.0", "",
             f"Проверено страниц навигации: **{len(pages)}**.", "",
             "Это автоматическая сверка, а не подтверждение полноты перевода. Разное число блоков может означать объединение примеров. Несовпадение кода может быть следствием регистра SQL или перевода комментариев. Отсутствие ключа требует проверки исходного контекста.", "",
             "SHA-256 исходников и переводов, номера несовпавших блоков и отсутствующие ключи сохранены в [JSON](source-parity.json).", "",
             "| Страница | Заголовки: источник / перевод | Код: источник / перевод | Блоки без совпадения | Отсутствующие ключи таблиц |",
             "| --- | --- | --- | --- | --- |"]
    for page in pages:
        missing = ", ".join(f"`{k}`" for k in page["source_table_keys_absent_from_translation"]) or "—"
        lines.append(f"| [{page['file']}](../docs/{page['file']}) | "
                     f"{page['source_headings']} / {page['translation_headings']} | "
                     f"{page['source_code_blocks']} / {page['translation_code_blocks']} | "
                     f"{len(page['source_code_blocks_without_whitespace_match'])} | {missing} |")
    lines.extend(["", "Повторить из корня репозитория:", "", "```sh",
                  "python3 01-apache-iceberg/_meta/source-parity.py \\",
                  "  --source-root /tmp/iceberg-source-1.12.0 --download --write", "```", "",
                  "Для повторной сверки по загруженным исходникам уберите `--download`. Источники загружаются по фиксированному tag; их контрольные суммы позволяют обнаружить изменение содержимого.", ""])
    if args.write:
        (ROOT / "_meta/source-parity.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        (ROOT / "_meta/source-parity.md").write_text("\n".join(lines))
    print(f"Checked {len(pages)} pages against {REF}; structural audit only")


if __name__ == "__main__":
    main()
