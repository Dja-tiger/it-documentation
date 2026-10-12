---
title: "Справочник go.mod"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/modules/gomod-ref.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Справочник `go.mod`

Каждый Go module определяется файлом `go.mod`. Он описывает свойства module, включая module path, минимальную версию Go и dependencies.

Основные возможности `go.mod`:

- уникальный **module path**, который также является prefix import paths packages этого module;
- минимальная **Go version**;
- минимальные versions требуемых **modules**;
- optional rules для `replace`, `exclude`, `retract`, `ignore`, tool dependencies и GODEBUG behavior.

Создание:

```bash
go mod init example/mymodule
```

Для изменений dependencies предпочтительно использовать `go get`, `go mod tidy`, `go mod edit`, а не ручное редактирование.

## Пример

```text
module example.com/mymodule

go 1.14

require (
    example.com/othermodule v1.2.3
    example.com/thismodule v1.2.3
    example.com/thatmodule v1.2.3
)

replace example.com/thatmodule => ../thatmodule
exclude example.com/thismodule v1.3.0
```

## `module`

Объявляет module path — уникальный identifier module вместе с version и prefix import paths его packages.

Синтаксис:

```text
module module-path
```

Для v0/v1:

```text
module example.com/mymodule
```

Для v2+ major suffix обязателен:

```text
module example.com/mymodule/v2
```

Обычно module path соответствует repository URL без scheme. Даже если module пока не публикуется, будущий repository path часто является лучшим выбором, чтобы позже не переименовывать imports.

## `go`

Объявляет минимальную Go version и language semantics, для которых написан module.

```text
go minimum-go-version
```

Пример:

```text
go 1.27.0
```

Начиная с Go 1.21 это не advisory hint, а обязательное minimum requirement: слишком старый Go toolchain откажется использовать module.

`go` directive также влияет на language features и поведение `go` command.

Важные historical behavior changes:

- `go 1.14+`: может автоматически использовать vendoring, если `vendor/modules.txt` согласован с `go.mod`;
- `go 1.16+`: pattern `all` ограничен transitively imported packages/tests main module;
- `go 1.17+`: `go.mod` хранит explicit `require` для modules, обеспечивающих transitively imported packages, что поддерживает module graph pruning и lazy loading; indirect requirements обычно помещаются в отдельный block;
- `go 1.21+`: `go` line — mandatory minimum, должна быть не ниже `go` lines dependencies; изменены compatibility/checksum правила.

Compiler также ограничивает language features version, указанной module's `go` directive. Например, module `go 1.12` не может использовать syntax, появившийся в Go 1.13.

## `toolchain`

Указывает предпочитаемый Go toolchain для работы с main module/workspace:

```text
toolchain toolchain-name
```

Пример:

```text
toolchain go1.27.1
```

`toolchain default` запрещает автоматический switch выше default toolchain.

Directive учитывается, когда текущий module является main module. Подробно: [[../toolchain|Go Toolchains]].

## `godebug`

Задаёт default GODEBUG settings для main packages текущего module.

```text
godebug debug-key=debug-value
```

Пример:

```text
godebug asynctimerchan=0
```

Block form:

```text
godebug (
    default=go1.21
    panicnil=1
)
```

Настройки действуют на builds main packages и test binaries текущего module. Когда module используется только как dependency, его `godebug` settings не навязываются main program.

Explicit `//go:debug` в main package может переопределить module defaults.

## `require`

Объявляет dependency и minimum selected version:

```text
require module-path module-version
```

Release example:

```text
require example.com/othermodule v1.2.3
```

Pseudo-version:

```text
require example.com/othermodule v0.0.0-20200921210052-fa0125251cc4
```

Для v2+ module path содержит major suffix `/v2`, `/v3` и т. д.

Go commands автоматически создают/обновляют `require` по импортируемым packages. Module source можно перенаправить через `replace`.

## `tool`

Добавляет Go package как developer tool dependency текущего module и делает его доступным через `go tool`.

```text
tool package-path
```

Tool из текущего module:

```text
module example.com/mymodule

tool example.com/mymodule/cmd/mytool
```

Tool из внешнего module:

```text
module example.com/mymodule

tool example.com/atool/cmd/atool

require example.com/atool v1.2.3
```

Запуск:

```bash
go tool mytool
```

либо полный path:

```bash
go tool example.com/mymodule/cmd/mytool
```

В workspace mode доступны tools всех workspace modules.

Tool использует тот же module graph и подчиняется `require`, `replace`, `exclude` и MVS.

## `replace`

Заменяет содержимое конкретной version module или всех versions другим module/version либо local directory.

```text
replace module-path [module-version] => replacement-path [replacement-version]
```

### Fork

```text
require example.com/othermodule v1.2.3
replace example.com/othermodule => example.com/myfork/othermodule v1.2.3-fixed
```

Imports остаются исходными: replacement меняет resolution, а не import path client code.

### Принудительно другая version

```text
require example.com/othermodule v1.2.2
replace example.com/othermodule => example.com/othermodule v1.2.3
```

Только для одной source version:

```text
replace example.com/othermodule v1.2.5 => example.com/othermodule v1.2.3
```

### Local directory

```text
require example.com/othermodule v1.2.3
replace example.com/othermodule => ../othermodule
```

или только конкретной version:

```text
replace example.com/othermodule v1.2.5 => ../othermodule
```

> [!important]
> `replace` сам по себе не добавляет module в module graph. Нужен соответствующий `require` — в main module либо в dependency graph.

Если real version отсутствует, для локальной разработки допустим fake version:

```text
require example.com/mod v0.0.0-replace
replace example.com/mod v0.0.0-replace => ./mod
```

`replace` main module не становится transitive policy для modules, которые зависят от вашего module.

## `exclude`

Запрещает конкретную version module в dependency graph текущего main module:

```text
exclude module-path module-version
```

Пример:

```text
exclude example.com/theirmodule v1.3.0
```

Можно применить командой:

```bash
go mod edit -exclude=example.com/theirmodule@v1.3.0
```

Это полезно, например, если конкретная version непригодна или имеет некорректный checksum.

`exclude`, как и `replace`, управляет dependency resolution main module и не навязывается downstream consumers.

## `retract`

Помечает опубликованную version или диапазон versions как нежелательные для нового использования.

Одна version:

```text
retract v1.1.0 // Published accidentally.
```

Диапазон:

```text
retract [v1.0.0,v1.0.5] // Build broken on some platforms.
```

Retracted versions не выбираются обычным upgrade flow и не показываются как updates через `go list -m -u`, но должны оставаться доступными, чтобы существующие builds оставались воспроизводимыми.

Go находит retractions в `go.mod` latest version module. Поэтому после добавления `retract` обычно требуется опубликовать новую, более высокую version.

Можно выпустить version только для объявления retraction и retract саму её:

```text
retract v1.0.0 // Published accidentally.
retract v1.0.1 // Contains retraction only.
```

Уже опубликованную version нельзя безопасно «перетегировать» на другой commit: checksums могут перестать совпадать.

Показать retracted versions можно через соответствующий `go list -m` option `-retracted`.

## `ignore`

Исключает directory paths внутри main module из package pattern matching, например `./...`.

Относительно root:

```text
ignore ./node_modules
```

Все directories с конкретным именем на любой глубине:

```text
ignore generated
```

Block:

```text
ignore (
    static
    content/html
    ./third_party/javascript
)
```

Ignored directories остаются физически в module tree, но не рассматриваются package patterns.

`ignore` применяется только к `go.mod` main module и игнорируется в dependency modules.
