# Правила синхронизации Go documentation

## Baseline

Для version-specific материалов источник фиксируется на `golang/go@go1.27.1`.
Для контента сайта `go.dev/doc` зафиксирован `golang/website@575a6925e2d55ad160ed77f402bfaa4ec7458749`.

## Источник истины

Для наличия локальных материалов источником истины является **фактическое дерево файлов** `02-golang/docs/`.

`manifest.json` и `MOC.md` обязаны соответствовать этому дереву и не могут объявлять локальный файл существующим, если файла физически нет.

Для технического содержания источником истины является зафиксированный upstream:

- `golang/go@go1.27.1` для specification, runtime/toolchain и version-specific core docs;
- `golang/website@575a6925e2d55ad160ed77f402bfaa4ec7458749` для go.dev documentation.

## Go-specific frontmatter

Для страниц `02-golang/docs/**/*.md` используется следующая обязательная схема:

```yaml
---
title: "..."
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/go | golang/website"
upstream_path: "..."
upstream_ref: "go1.27.1 | <website commit sha>"
translation_status: "todo | in_progress | translated | reviewed | outdated"
---
```

Имена code identifiers, commands, package paths и API names в frontmatter и body сохраняются в canonical form.

## Семантика статусов

- `todo` — локального перевода по существу ещё нет;
- `in_progress` — перевод начат, неполон, сокращён либо ещё требует восстановления source parity;
- `translated` — полный перевод upstream выполнен, но отдельный post-translation review ещё не завершён;
- `reviewed` — перевод полностью сверен с зафиксированным upstream;
- `outdated` — upstream изменился после перевода или review.

Критически важно: `translated` **не допускает summary вместо исходного текста**.

Если из upstream удалены paragraphs, notes, warnings, examples, code blocks или существенные пояснения, документ должен иметь `in_progress`, а не `translated`.

## Definition of Done для `reviewed`

Страница получает `reviewed` только после проверки всех условий:

1. upstream file существует по `upstream_repository + upstream_path + upstream_ref`;
2. сохранены все semantic sections upstream;
3. не потеряны paragraphs, lists, notes, warnings, tables и examples;
4. code blocks и commands не изменены по смыслу;
5. normative grammar/API identifiers не переименованы;
6. internal links разрешаются в существующие локальные страницы либо остаются canonical upstream links;
7. перевод не заменяет исходник кратким пересказом;
8. технический смысл не расширен собственными утверждениями, отсутствующими upstream, без отдельной явной редакторской пометки.

Для `spec.md`, memory model и других нормативных документов применяется особенно строгий режим: структурная адаптация не должна менять grammar, formal definitions и normative constraints.

## Правила синхронизации

1. Не обновлять перевод по плавающей ветке без фиксации нового upstream SHA.
2. При выходе нового patch-релиза `1.27.x` сначала сравнивать `golang/go` tags; spec/runtime docs менять только при реальном diff.
3. При выходе Go 1.28 создать отдельный migration/sync commit и обновить release notes, spec, toolchain и связанные руководства.
4. Кодовые блоки, команды, identifiers, package paths, environment variables и API names не переводить.
5. Термины `goroutine`, `channel`, `interface`, `slice`, `map`, `module`, `package`, `workspace`, `toolchain`, `build constraint` при первом употреблении допускают русское пояснение, но техническое имя сохраняется.
6. Frontmatter каждой страницы должен хранить upstream repository/path/ref и `translation_status`.
7. `pkg.go.dev` standard-library API учитывать отдельно как generated reference: это не тот же тип контента, что User Manual и guides.
8. Перед изменением `manifest.json` сначала проверять фактическое дерево `docs/`.
9. Не добавлять в MOC WikiLink на несуществующий локальный файл. Пока зеркало отсутствует, использовать canonical upstream URL и явно указывать, что local mirror pending.
10. После любого structural change запускать validator.

## Проверка целостности

Из корня repository:

```bash
python 02-golang/_meta/validate.py
```

Validator проверяет:

- соответствие manifest фактическому `docs/**/*.md`;
- существование WikiLinks из `MOC.md`;
- обязательный frontmatter;
- допустимые translation statuses.

Техническое ревью от 2026-10-12: [[review-2026-10-12]].
