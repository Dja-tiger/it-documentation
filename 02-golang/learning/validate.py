#!/usr/bin/env python3
"""Validate the Go learning layer without external dependencies.

Checks the files that are intentionally outside docs/manifest:
- required roadmap/study/progress/project files exist;
- the expected stage/practice/project inventory is present;
- every stage follows the common section contract;
- every Obsidian WikiLink in learning/**/*.md resolves to a real Markdown file
  relative to the source file.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


LEARNING_ROOT = Path(__file__).resolve().parent
GO_ROOT = LEARNING_ROOT.parent.resolve()

REQUIRED_CORE_FILES = {
    "README.md",
    "roadmap.md",
    "progress.md",
    "study-rules.md",
    "standard-library.md",
    "projects/README.md",
}

EXPECTED_STAGE_FILES = {
    "01-foundations.md",
    "02-core-language.md",
    "03-methods-interfaces-generics.md",
    "04-errors-and-testing.md",
    "05-modules-packages-toolchain.md",
    "06-concurrency.md",
    "07-context-and-cancellation.md",
    "08-database.md",
    "09-http-and-json.md",
    "10-production-go.md",
    "11-security-and-hardening.md",
    "12-performance.md",
    "13-language-specification.md",
    "14-runtime-internals.md",
}

EXPECTED_PRACTICE_FILES = {
    "01-foundations.md",
    "02-core-language.md",
    "03-interfaces-generics.md",
    "04-errors-testing.md",
    "05-modules-toolchain.md",
    "06-concurrency.md",
    "07-context.md",
    "08-database-postgresql.md",
    "09-database-greenplum.md",
    "10-http-json.md",
    "11-production.md",
    "12-security.md",
    "13-performance.md",
    "14-spec-runtime-labs.md",
}

EXPECTED_PROJECT_FILES = {
    "README.md",
    "01-price-cli.md",
    "02-price-processor.md",
    "03-price-storage.md",
    "04-pricing-api.md",
    "05-pricing-pipeline.md",
}

REQUIRED_STAGE_HEADINGS = (
    "## Цель",
    "## Перед началом",
    "## Прочитать",
    "## Что необходимо понять",
    "## Что НЕ нужно пока изучать",
    "## Практика",
    "## Эксперименты",
    "## Проверка себя",
    "## Практическая проверка",
    "## Критерий завершения",
    "## Следующий этап",
)

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def markdown_inventory(root: Path) -> set[str]:
    if not root.exists():
        return set()
    return {path.name for path in root.glob("*.md") if path.is_file()}


def resolve_wikilink(raw_target: str, source: Path) -> Path | None:
    target = raw_target.split("|", 1)[0].strip()
    target = target.split("#", 1)[0].strip()

    if not target or target.startswith(("http://", "https://")):
        return None

    resolved = source.parent / target
    if resolved.suffix.lower() != ".md":
        resolved = Path(f"{resolved}.md")
    return resolved.resolve()


def validate_inventory() -> list[str]:
    errors: list[str] = []

    all_learning_files = {
        path.relative_to(LEARNING_ROOT).as_posix()
        for path in LEARNING_ROOT.rglob("*.md")
        if path.is_file()
    }
    for rel_path in sorted(REQUIRED_CORE_FILES - all_learning_files):
        errors.append(f"required learning file missing: learning/{rel_path}")

    inventories = (
        ("stage", LEARNING_ROOT / "stages", EXPECTED_STAGE_FILES),
        ("practice", LEARNING_ROOT / "practice", EXPECTED_PRACTICE_FILES),
        ("project", LEARNING_ROOT / "projects", EXPECTED_PROJECT_FILES),
    )

    for label, root, expected in inventories:
        actual = markdown_inventory(root)
        for filename in sorted(expected - actual):
            errors.append(f"required learning {label} missing: {root.name}/{filename}")
        for filename in sorted(actual - expected):
            errors.append(f"unexpected learning {label} file: {root.name}/{filename}")

    return errors


def validate_stage_contract() -> list[str]:
    errors: list[str] = []
    stages_root = LEARNING_ROOT / "stages"

    for filename in sorted(EXPECTED_STAGE_FILES):
        path = stages_root / filename
        if not path.exists():
            continue

        headings = {line.strip() for line in path.read_text(encoding="utf-8").splitlines()}
        for heading in REQUIRED_STAGE_HEADINGS:
            if heading not in headings:
                errors.append(
                    f"stage missing heading {heading!r}: stages/{filename}"
                )

    return errors


def validate_wikilinks() -> list[str]:
    errors: list[str] = []

    for source in sorted(LEARNING_ROOT.rglob("*.md")):
        text = source.read_text(encoding="utf-8")
        for match in WIKILINK_RE.finditer(text):
            raw_target = match.group(1)
            target = resolve_wikilink(raw_target, source)
            if target is None:
                continue

            try:
                target.relative_to(GO_ROOT)
            except ValueError:
                errors.append(
                    f"WikiLink escapes 02-golang root in "
                    f"{source.relative_to(GO_ROOT).as_posix()}: [[{raw_target}]]"
                )
                continue

            if not target.is_file():
                errors.append(
                    "dangling WikiLink in "
                    f"{source.relative_to(GO_ROOT).as_posix()}: "
                    f"[[{raw_target}]] -> "
                    f"{target.relative_to(GO_ROOT).as_posix()}"
                )

    return errors


def main() -> int:
    errors = []
    errors.extend(validate_inventory())
    errors.extend(validate_stage_contract())
    errors.extend(validate_wikilinks())

    if errors:
        print("Go learning validation FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    page_count = sum(1 for path in LEARNING_ROOT.rglob("*.md") if path.is_file())
    print(f"Go learning validation OK: {page_count} Markdown pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
