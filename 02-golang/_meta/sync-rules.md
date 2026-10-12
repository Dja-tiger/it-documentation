# Правила синхронизации Go documentation

## Baseline

Для version-specific материалов источник фиксируется на `golang/go@go1.27.1`.
Для контента сайта `go.dev/doc` зафиксирован `golang/website@575a6925e2d55ad160ed77f402bfaa4ec7458749`.

## Правила

1. Не обновлять перевод по плавающей ветке без фиксации нового upstream SHA.
2. При выходе нового patch-релиза `1.27.x` сначала сравнивать `golang/go` tags; spec/runtime docs менять только при реальном diff.
3. При выходе Go 1.28 создать отдельный migration/sync commit и обновить release notes, spec, toolchain и связанные руководства.
4. Кодовые блоки, команды, identifiers, package paths, environment variables и API names не переводить.
5. Термины `goroutine`, `channel`, `interface`, `slice`, `map`, `module`, `package`, `workspace`, `toolchain`, `build constraint` при первом употреблении допускают русское пояснение, но техническое имя сохраняется.
6. Frontmatter каждой страницы должен хранить upstream repository/path/ref и `translation_status`.
7. `pkg.go.dev` standard-library API учитывать отдельно как generated reference: это не тот же тип контента, что User Manual и guides.

## Статусы

- `todo`
- `in_progress`
- `translated`
- `reviewed`
- `outdated`
