# Go / Golang — русская документация

Этот каталог содержит неофициальную русскоязычную локализацию официальной документации языка Go.

## Baseline

- стабильная линия: **Go 1.27**;
- patch baseline: **Go 1.27.1**;
- исходники toolchain/spec/runtime: `golang/go`, tag `go1.27.1`;
- исходники go.dev User Manual и tutorials: `golang/website`, commit `575a6925e2d55ad160ed77f402bfaa4ec7458749` от 2026-10-11;
- дата фиксации baseline: 2026-10-12.

## Текущее состояние

После технического ревью 2026-10-12 общий статус раздела — **`in_progress`**.

Фактическое дерево `docs/` содержит 65 Markdown-документов. Навигация и manifest синхронизированы с этим деревом, однако выборочная сверка с upstream показала, что часть страниц пока представляет собой сокращённую локализацию, а не полный перевод исходного документа.

Поэтому наличие файла с историческим `translation_status: translated` ещё не означает, что он прошёл полный source-parity review.

Подробности: [[_meta/review-2026-10-12|техническое ревью раздела Go]].

## Что уже представлено локально

В разделе есть материалы по:

- установке и началу работы;
- организации Go-кода;
- language specification и memory model;
- Effective Go, FAQ и doc comments;
- modules и toolchain;
- diagnostics, race detector, GC, PGO, GODEBUG и assembler;
- официальным tutorials;
- `database/sql`;
- security и vulnerability management;
- Go 1.27 release notes.

Документация standard library на `pkg.go.dev/std` генерируется из комментариев исходного кода тысяч API-symbols. Она учитывается отдельно как generated canonical reference и не смешивается с ручным переводом guides.

## Известные отсутствующие локальные зеркала

Пока не созданы полные локальные переводы:

- [Installing Go from source](https://go.dev/doc/install/source) → планируется `docs/install-source.md`;
- [Go Modules Reference](https://go.dev/ref/mod) → планируется `docs/modules/reference.md`;
- [Contribution Guide](https://go.dev/doc/contribute) → планируется `docs/contribute.md`.

До появления этих файлов навигация должна вести на официальный upstream, а не на несуществующие WikiLinks.

## Навигация

Начните с [[MOC|карты раздела Go]].

Для состояния покрытия и контроля качества:

- `_meta/manifest.json` — machine-readable inventory/status;
- [[_meta/sync-rules|правила синхронизации и Definition of Done]];
- [[_meta/review-2026-10-12|результаты технического ревью]];
- `_meta/validate.py` — автоматическая проверка структуры и metadata.

Запуск validator из корня repository:

```bash
python 02-golang/_meta/validate.py
```

## Лицензия

Исходная документация Go распространяется по BSD-style license. Полный текст сохранён в `LICENSE`. Перевод является производной работой; исходная атрибуция сохранена.
