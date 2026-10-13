# Go / Golang — русская документация

Этот каталог содержит неофициальную русскоязычную локализацию официальной документации языка Go.

## Baseline

- стабильная линия: **Go 1.27**;
- patch baseline: **Go 1.27.1**;
- исходники toolchain/spec/runtime: `golang/go`, tag `go1.27.1`;
- исходники go.dev User Manual и tutorials: `golang/website`, commit `575a6925e2d55ad160ed77f402bfaa4ec7458749` от 2026-10-11;
- дата фиксации baseline: 2026-10-12.

## Текущее состояние

Раздел проходит full-fidelity review относительно зафиксированного upstream. Общий статус остаётся **`in_progress`**, пока не завершена постраничная сверка всех документов.

Фактическое дерево `docs/` содержит **69 Markdown-документов**. Наличие файла с `translation_status: translated` означает, что перевод существует, но не означает автоматически, что он прошёл полный source-parity review. Документы, сверенные с pinned upstream, помечаются `translation_status: reviewed`.

Подробности исходного технического аудита: [[_meta/review-2026-10-12|техническое ревью раздела Go]].

## Что представлено локально

В разделе есть материалы по:

- установке, включая сборку Go из исходников, и началу работы;
- организации Go-кода;
- language specification и memory model;
- Effective Go, FAQ и doc comments;
- Go Modules Reference, разработке и публикации модулей, `go.mod` и toolchain;
- diagnostics, race detector, GC, PGO, GODEBUG и assembler;
- официальным tutorials;
- `database/sql`;
- security и vulnerability management;
- Contribution Guide;
- Go 1.27 release notes.

Документация standard library на `pkg.go.dev/std` генерируется из комментариев исходного кода тысяч API-symbols. Она учитывается отдельно как generated canonical reference и не смешивается с ручным переводом guides.

## Канонические внешние ресурсы

Некоторые официальные ресурсы остаются внешними, поскольку генерируются из исходного кода или являются интерактивными:

- [Standard library API](https://pkg.go.dev/std);
- [Command documentation](https://pkg.go.dev/cmd);
- [A Tour of Go](https://go.dev/tour/);
- [История релизов Go](https://go.dev/doc/devel/release).

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
