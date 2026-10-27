#!/usr/bin/env python3
"""Check local links, image targets, frontmatter, fences and audit freshness."""
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def prose(text):
    output, fence = [], None
    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence) and not match[2].strip():
                fence = None
            output.append("")
        elif match:
            fence = match[1]
            output.append("")
        else:
            output.append(line)
    return "\n".join(output), fence


def clean_heading(value):
    return re.sub(r"\s+", " ", value.replace("`", "").replace("*", "").replace("_", "")).strip().casefold()


def anchors(path):
    body, _ = prose(path.read_text())
    headings = re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", body, re.M)
    result = {clean_heading(h) for h in headings}
    used = {}
    for heading in headings:
        slug = re.sub(r"[^\w\s-]", "", heading.replace("`", "").casefold()).replace(" ", "-")
        number = used.get(slug, 0)
        used[slug] = number + 1
        result.add(slug if number == 0 else f"{slug}-{number}")
    result.update(re.findall(r'<a\s+(?:id|name)="([^"]+)"', body))
    return result


def main():
    errors = []
    pages = list(ROOT.rglob("*.md"))
    for path in pages:
        text = path.read_text()
        body, fence = prose(text)
        relative = path.relative_to(ROOT)
        if fence:
            errors.append(f"{relative}: unclosed code fence")
        if path.parent == ROOT / "docs":
            for field in ("title", "source_project", "source_file", "source_ref", "source_url", "translation_status"):
                if not re.search(rf"^{field}:\s*\S", text, re.M):
                    errors.append(f"{relative}: missing {field}")
            if "source_ref: apache-iceberg-1.12.0" not in text:
                errors.append(f"{relative}: source ref mismatch")
        links = [(target, False) for target in re.findall(r"!?\[[^\]\n]*\]\(([^)\n]+)\)", body)]
        # Literal arrays in inline code are not Obsidian links.
        without_inline_code = re.sub(r"(`+).*?\1", "", body)
        links += [(target.split("|")[0], True) for target in re.findall(r"\[\[([^\]\n]+)\]\]", without_inline_code)]
        for target, wiki in links:
            target = target.strip().strip("<>")
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                continue
            name, _, fragment = unquote(target).partition("#")
            if wiki and name and not Path(name).suffix:
                name += ".md"
            dest = (path.parent / name).resolve() if name else path
            if not dest.exists():
                errors.append(f"{relative}: missing target {target}")
            elif fragment and dest.suffix == ".md":
                options = anchors(dest)
                if fragment.casefold() not in options and clean_heading(fragment) not in options:
                    errors.append(f"{relative}: missing anchor {target}")
    report_path = ROOT / "_meta/source-parity.json"
    if report_path.exists():
        for page in json.loads(report_path.read_text())["pages"]:
            path = ROOT / "docs" / page["file"]
            if hashlib.sha256(path.read_bytes()).hexdigest() != page["translation_sha256"]:
                errors.append(f"{path.relative_to(ROOT)}: source-parity report is stale; regenerate it")
    else:
        errors.append("missing source-parity.json")
    assets_path = ROOT / "_meta/assets.json"
    if assets_path.exists():
        for asset in json.loads(assets_path.read_text())["assets"]:
            path = ROOT / asset["path"]
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != asset["sha256"]:
                errors.append(f"{asset['path']}: missing or changed upstream image")
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    print(f"Validated {len(pages)} Markdown files: local links, images, anchors, frontmatter, fences and audit hashes")


if __name__ == "__main__":
    main()
