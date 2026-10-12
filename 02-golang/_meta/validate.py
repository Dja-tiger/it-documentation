#!/usr/bin/env python3
"""Validate structural integrity of the 02-golang documentation tree.

The validator intentionally uses only the Python standard library so it can be
run locally and in CI without extra dependencies.

Checks:
- manifest inventory exactly matches docs/**/*.md;
- manifest document count matches the actual tree;
- MOC WikiLinks point to existing local Markdown files;
- every documentation page has the required Go-specific frontmatter;
- translation_status uses an allowed value.

This script validates repository integrity, not translation fidelity. Full
source-parity review remains a manual/content-review task.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


GO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = GO_ROOT / "docs"
MANIFEST_PATH = GO_ROOT / "_meta" / "manifest.json"
MOC_PATH = GO_ROOT / "MOC.md"

REQUIRED_FRONTMATTER_KEYS = {
    "title",
    "technology",
    "version",
    "upstream_repository",
    "upstream_path",
    "upstream_ref",
    "translation_status",
}

ALLOWED_TRANSLATION_STATUSES = {
    "todo",
    "in_progress",
    "translated",
    "reviewed",
    "outdated",
}

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
FRONTMATTER_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):(?:\s*(.*))?$")


def load_manifest() -> dict:
    try:
        with MANIFEST_PATH.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        raise RuntimeError(f"manifest not found: {MANIFEST_PATH}") from None
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"invalid JSON in {MANIFEST_PATH}: line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def actual_document_paths() -> set[str]:
    return {
        path.relative_to(GO_ROOT).as_posix()
        for path in DOCS_ROOT.rglob("*.md")
        if path.is_file()
    }


def manifest_document_paths(manifest: dict) -> set[str]:
    try:
        values = manifest["documents"]["present_localized"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError(
            "manifest must contain documents.present_localized"
        ) from exc

    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        raise RuntimeError("documents.present_localized must be a list of strings")

    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise RuntimeError(
            "duplicate paths in documents.present_localized: " + ", ".join(duplicates)
        )

    return set(values)


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    if not lines or lines[0].strip() != "---":
        return {}

    result: dict[str, str] = {}

    for line in lines[1:]:
        if line.strip() == "---":
            return result

        # Only parse top-level scalar keys. This is enough for the current
        # Go-specific schema and avoids introducing a YAML dependency.
        if line.startswith((" ", "\t")):
            continue

        match = FRONTMATTER_KEY_RE.match(line)
        if not match:
            continue

        key = match.group(1)
        value = (match.group(2) or "").strip().strip('"').strip("'")
        result[key] = value

    return {}


def resolve_wikilink_target(raw_target: str) -> Path | None:
    target = raw_target.split("|", 1)[0].strip()
    target = target.split("#", 1)[0].strip()

    if not target:
        return None

    # MOC should use Markdown URLs for remote resources, not WikiLinks.
    if target.startswith(("http://", "https://")):
        return None

    target_path = GO_ROOT / target
    if target_path.suffix.lower() != ".md":
        target_path = Path(f"{target_path}.md")

    return target_path


def validate() -> list[str]:
    errors: list[str] = []

    try:
        manifest = load_manifest()
        manifest_paths = manifest_document_paths(manifest)
    except RuntimeError as exc:
        return [str(exc)]

    actual_paths = actual_document_paths()

    missing_files = sorted(manifest_paths - actual_paths)
    untracked_files = sorted(actual_paths - manifest_paths)

    for path in missing_files:
        errors.append(f"manifest references missing file: {path}")

    for path in untracked_files:
        errors.append(f"docs file missing from manifest: {path}")

    expected_count = manifest.get("integrity", {}).get("actual_markdown_documents")
    if expected_count is not None:
        if not isinstance(expected_count, int):
            errors.append("integrity.actual_markdown_documents must be an integer")
        elif expected_count != len(actual_paths):
            errors.append(
                "manifest document count mismatch: "
                f"integrity.actual_markdown_documents={expected_count}, actual={len(actual_paths)}"
            )

    for rel_path in sorted(actual_paths):
        path = GO_ROOT / rel_path
        frontmatter = parse_frontmatter(path)

        if not frontmatter:
            errors.append(f"missing or malformed YAML frontmatter: {rel_path}")
            continue

        missing_keys = sorted(REQUIRED_FRONTMATTER_KEYS - frontmatter.keys())
        if missing_keys:
            errors.append(
                f"missing frontmatter keys in {rel_path}: {', '.join(missing_keys)}"
            )

        status = frontmatter.get("translation_status")
        if status and status not in ALLOWED_TRANSLATION_STATUSES:
            errors.append(
                f"invalid translation_status in {rel_path}: {status!r}; "
                f"allowed: {', '.join(sorted(ALLOWED_TRANSLATION_STATUSES))}"
            )

        technology = frontmatter.get("technology")
        if technology and technology != "Go":
            errors.append(
                f"unexpected technology in {rel_path}: {technology!r}; expected 'Go'"
            )

        version = frontmatter.get("version")
        if version and version != "1.27.1":
            errors.append(
                f"unexpected version in {rel_path}: {version!r}; expected '1.27.1'"
            )

        upstream_repository = frontmatter.get("upstream_repository")
        upstream_ref = frontmatter.get("upstream_ref")

        if upstream_repository == "golang/go" and upstream_ref != "go1.27.1":
            errors.append(
                f"unexpected golang/go ref in {rel_path}: {upstream_ref!r}; expected 'go1.27.1'"
            )

        if upstream_repository == "golang/website":
            expected_ref = manifest.get("baseline", {}).get("website_ref")
            if expected_ref and upstream_ref != expected_ref:
                errors.append(
                    f"unexpected golang/website ref in {rel_path}: {upstream_ref!r}; "
                    f"expected {expected_ref!r}"
                )

    if not MOC_PATH.exists():
        errors.append(f"MOC not found: {MOC_PATH.relative_to(GO_ROOT)}")
    else:
        moc_text = MOC_PATH.read_text(encoding="utf-8")
        for match in WIKILINK_RE.finditer(moc_text):
            raw_target = match.group(1)
            target = resolve_wikilink_target(raw_target)
            if target is None:
                continue

            if not target.exists():
                try:
                    rendered = target.relative_to(GO_ROOT).as_posix()
                except ValueError:
                    rendered = str(target)
                errors.append(
                    f"dangling MOC WikiLink [[{raw_target}]] -> {rendered}"
                )

    return errors


def main() -> int:
    errors = validate()

    if errors:
        print("Go documentation validation FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    document_count = len(actual_document_paths())
    print(f"Go documentation validation OK: {document_count} Markdown documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
