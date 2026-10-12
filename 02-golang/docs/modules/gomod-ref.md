---
title: "Справочник go.mod"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/modules/gomod-ref.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Справочник `go.mod`

Каждый Go module определяется file `go.mod`, описывающим свойства module, включая dependencies на другие modules и требуемые versions Go.

К таким свойствам относятся:

- **Module path** текущего module. Обычно это location, откуда Go tools могут скачать module, например repository location. Вместе с version number path является unique identifier module и prefix всех package paths внутри него. Как Go находит module: [[reference|Go Modules Reference]].
- Минимальная **Go version**, необходимая module.
- Список minimum versions других **required modules**.
- Optional instructions:
  - **replace** required module другой version или local directory;
  - **exclude** конкретную version required module;
  - **ignore** определённые directories внутри module при package-pattern matching.

`go.mod` создаётся [`go mod init`](https://go.dev/ref/mod#go-mod-init):

```text
$ go mod init example/mymodule
```

Dependencies рекомендуется управлять через Go commands: они поддерживают requirements согласованными и сохраняют `go.mod` valid. Основные commands:

- [`go get`](https://go.dev/ref/mod#go-get);
- [`go mod tidy`](https://go.dev/ref/mod#go-mod-tidy);
- [`go mod edit`](https://go.dev/ref/mod#go-mod-edit).

Command reference: [Command go](https://pkg.go.dev/cmd/go/). CLI help: `go help <command>`, например `go help mod tidy`.

**См. также:**

- Go tools изменяют `go.mod` в процессе dependency management; см. [[managing-dependencies|Управление dependencies]].
- Более строгие rules и constraints `go.mod`: [[reference#go.mod files|Go Modules Reference]].

## Example {#example}

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

## `module` {#module}

Объявляет module path — unique identifier module вместе с version number. Module path становится import prefix всех packages module.

Normative details: [[reference#module directive|Go Modules Reference — module directive]].

### Syntax {#module-syntax}

```text
module module-path
```

`module-path` — module path, обычно repository location, откуда Go tools могут скачать code. Для v2+ path обязан оканчиваться major suffix, например `/v2`.

### Examples {#module-examples}

v0/v1:

```text
module example.com/mymodule
```

v2:

```text
module example.com/mymodule/v2
```

### Notes {#module-notes}

Module path должен uniquely identify module. Для большинства published modules это URL/location code либо redirect на него.

Для modules, которые никогда не будут скачиваться напрямую, path может быть controlled name, обеспечивающий uniqueness. Prefix `example/` зарезервирован для examples.

На практике path обычно строится из repository domain + path к module code.

Даже если module пока не планируется публиковать, repository-style path является best practice: это уменьшает вероятность будущего rename.

Если eventual repository location пока неизвестен, временно используйте safe controlled prefix — например собственный domain или company name:

```text
go mod init <company-name>/stringtools
```

Подробнее: [[managing-dependencies#Именование module|Именование module]].

## `go` {#go}

Показывает, что module написан с assumptions о semantics указанной Go version.

Normative details: [[reference#go directive|Go Modules Reference — go directive]].

### Syntax {#go-syntax}

```text
go minimum-go-version
```

`minimum-go-version` — minimum Go version, required для compilation packages module.

Пример:

```text
go 1.14
```

### Notes {#go-notes}

До Go 1.21 `go` directive была advisory. Начиная с Go 1.21 это mandatory requirement: Go toolchain отказывается использовать module, объявляющий более новую Go version, чем способен поддерживать.

`go` line также участвует в выборе toolchain; см. [[../toolchain|Go toolchains]].

Directive влияет на доступность language features. Например, module с `go 1.12` не может использовать numeric literal `1_000_000`, появившийся в Go 1.13. Если older compiler видит source, требующий более новой language version, diagnostic указывает заявленную Go version module.

`go` directive также меняет behavior команды `go` между language/toolchain eras:

- **Go 1.14+.** Automatic vendoring может включаться, если `vendor/modules.txt` присутствует и согласован с `go.mod`; explicit `-mod=vendor` не нужен.
- **Go 1.16+.** Pattern `all` соответствует packages, transitively imported packages/tests main module. В более старых versions он также включал tests dependencies recursively.
- **Go 1.17+.**
  - `go.mod` содержит explicit `require` для каждого module, предоставляющего package, transitively imported package/test main module; это поддерживает module graph pruning и lazy loading;
  - indirect dependencies могут находиться в отдельном block;
  - `go mod vendor` не кладёт `go.mod`/`go.sum` dependencies в vendor tree;
  - `vendor/modules.txt` фиксирует Go version каждой dependency.
- **Go 1.21+.**
  - `go` line задаёт обязательную minimum Go version;
  - она должна быть >= `go` lines всех dependencies;
  - команда `go` больше не пытается поддерживать compatibility с предыдущей older Go version;
  - checksums `go.mod` в `go.sum` поддерживаются более строго.

В `go.mod` может быть максимум одна `go` directive. Большинство commands при её отсутствии добавляют current Go version.

## `toolchain` {#toolchain}

Объявляет suggested Go toolchain для main module. Directive действует только когда module является main и default toolchain старее suggested toolchain.

Подробнее: [[../toolchain|Go toolchains]] и [[reference#toolchain directive|Modules Reference]].

### Syntax {#toolchain-syntax}

```text
toolchain toolchain-name
```

Standard names имеют форму `goV`, например:

```text
go1.21.0
go1.18rc1
```

Special value:

```text
default
```

отключает automatic toolchain switching.

Пример:

```text
toolchain go1.21.0
```

## `godebug` {#godebug}

Задаёт default [`GODEBUG`](../godebug.md) settings для main packages этого module.

Они:

- override toolchain defaults;
- override'ятся explicit `//go:debug` lines в main packages.

### Syntax {#godebug-syntax}

```text
godebug debug-key=debug-value
```

`debug-key` — setting name из [[../godebug#GODEBUG History|GODEBUG History]].

`debug-value` — value setting; если не определено иначе, обычно `0` выключает behavior, а `1` включает.

Examples:

```text
godebug asynctimerchan=0
```

Использовать defaults Go 1.21, но old `panicnil=1` behavior:

```text
godebug (
    default=go1.21
    panicnil=1
)
```

Settings применяются только при builds main packages и test binaries текущего module. Когда module используется как dependency, его `godebug` directives эффекта не имеют.

## `require` {#require}

Объявляет module dependency и minimum required version.

### Syntax {#require-syntax}

```text
require module-path module-version
```

- `module-path` — module path; для v2+ заканчивается major suffix, например `/v2`.
- `module-version` — release version (`v1.2.3`) либо generated pseudo-version (`v0.0.0-20200921210052-fa0125251cc4`).

Examples:

```text
require example.com/othermodule v1.2.3
```

```text
require example.com/othermodule v0.0.0-20200921210052-fa0125251cc4
```

Commands вроде `go get` автоматически добавляют `require` для modules imported packages. Если module revision не tagged, Go tools генерируют pseudo-version.

Dependency можно перенаправить через [[#replace|replace]].

Подробнее:

- [[version-numbers|Version numbers]];
- [[managing-dependencies#Добавление dependency|Adding dependency]];
- [[managing-dependencies#Получение конкретной dependency version|Getting specific version]];
- [[managing-dependencies#Поиск доступных updates|Discovering updates]];
- [[managing-dependencies#Upgrade или downgrade dependency|Upgrade/downgrade]];
- [[managing-dependencies#Синхронизация dependencies с code|Synchronizing]].

## `tool` {#tool}

Добавляет package как dependency текущего module и делает его доступным через `go tool`, когда working directory находится внутри module.

### Syntax {#tool-syntax}

```text
tool package-path
```

Package path включает module path и optional subpath package, реализующего tool.

Tool внутри текущего module:

```text
module example.com/mymodule

tool example.com/mymodule/cmd/mytool
```

Tool в external module:

```text
module example.com/mymodule

tool example.com/atool/cmd/atool

require example.com/atool v1.2.3
```

Tool запускается full package path либо unambiguous last path segment:

```text
go tool mytool
go tool example.com/mymodule/cmd/mytool
```

В workspace mode можно запускать tool, declared в любом workspace module.

Tools build'ятся через тот же module graph, что и module. Поэтому:

- нужен `require`, выбирающий module version tool;
- `replace` и `exclude` применяются к tool и dependencies tool.

Подробнее: [[managing-dependencies#Tool dependencies|Tool dependencies]].

## `replace` {#replace}

Заменяет content module конкретной version или всех versions другим module/version либо local directory. Go tools используют replacement при dependency resolution.

### Syntax {#replace-syntax}

```text
replace module-path [module-version] => replacement-path [replacement-version]
```

- `module-path` — заменяемый module.
- Optional `module-version` — если отсутствует, replacement применяется ко всем versions module.
- `replacement-path` — другой module path либо local directory.
- `replacement-version` разрешён только если replacement path — module path; для local directory version указывать нельзя.

### Замена fork'ом

```text
require example.com/othermodule v1.2.3

replace example.com/othermodule => example.com/myfork/othermodule v1.2.3-fixed
```

Imports менять не нужно.

### Замена version

Все versions на v1.2.3:

```text
require example.com/othermodule v1.2.2

replace example.com/othermodule => example.com/othermodule v1.2.3
```

Только v1.2.5:

```text
replace example.com/othermodule v1.2.5 => example.com/othermodule v1.2.3
```

### Замена local code

Все versions:

```text
require example.com/othermodule v1.2.3

replace example.com/othermodule => ../othermodule
```

Только v1.2.5:

```text
require example.com/othermodule v1.2.5

replace example.com/othermodule v1.2.5 => ../othermodule
```

### Notes {#replace-notes}

`replace` временно redirects module source resolution без изменения imports.

`replace` и `exclude` влияют на build-time dependency resolution **только когда module является main module**; consumers этого module игнорируют его replace/exclude directives.

Typical uses:

- unpublished local module;
- local checkout external dependency для testing fix.

`replace` сам по себе **не добавляет module в module graph**. Нужен `require` где-либо в main/dependency graph.

Если конкретная version отсутствует, можно использовать fake version:

```text
require example.com/mod v0.0.0-replace

replace example.com/mod v0.0.0-replace => ./mod
```

Помните: такой `replace` не переносится consumers module.

## `exclude` {#exclude}

Исключает конкретную module version из dependency graph текущего main module.

### Syntax {#exclude-syntax}

```text
exclude module-path module-version
```

Example:

```text
exclude example.com/theirmodule v1.3.0
```

Используется, например, чтобы исключить indirectly required version, которую невозможно load'ить, в том числе version с invalid checksum.

`exclude`, как и `replace`, действует только при build текущего main module и игнорируется consumers.

Через command:

```text
go mod edit -exclude=example.com/theirmodule@v1.3.0
```

## `retract` {#retract}

Указывает, что конкретная version или range versions текущего module не должны использоваться как dependency. Полезно, если version опубликована случайно либо после release найден серьёзный defect.

### Syntax {#retract-syntax}

Одна version:

```text
retract version // rationale
```

Range, включая обе boundaries:

```text
retract [version-low,version-high] // rationale
```

`rationale` optional, но может показываться users.

Examples:

```text
retract v1.1.0 // Published accidentally.
```

```text
retract [v1.0.0,v1.0.5] // Build broken on some platforms.
```

### Notes {#retract-notes}

Retracted version:

- не выбирается автоматически `go get`, `go mod tidy` и другими commands;
- не показывается обычным available update в `go list -m -u`;
- должна оставаться доступной для existing users, которые уже зависят от неё.

Даже если source tag удалён из repository, mirror вроде `proxy.golang.org` может продолжать хранить immutable published content.

Go command узнаёт retractions из `go.mod` **latest version module**, определяемой в порядке:

1. highest release version;
2. highest pre-release version;
3. pseudo-version tip default branch.

Поэтому после добавления `retract` почти всегда требуется опубликовать новую, более высокую version.

Можно выпустить version, единственная цель которой — объявить retractions, и retract'нуть даже её саму:

```text
retract v1.0.0 // Published accidentally.
retract v1.0.1 // Contains retraction only.
```

Published version immutable. Если позднее tag `v1.0.0` переставить на другой commit, Go может обнаружить checksum mismatch в `go.sum` или checksum database.

По умолчанию `go list -m -versions` retracted versions не показывает. Для этого используется `-retracted`.

## `ignore` {#ignore}

Указывает directories внутри module, которые команда `go` должна игнорировать при matching package patterns.

### Syntax {#ignore-syntax}

```text
ignore path
```

Если path начинается с `./`, он интерпретируется относительно module root. Иначе игнорируется directory с этим именем на любой depth.

Local directory относительно root:

```text
ignore ./node_modules
```

Все directories `generated`:

```text
ignore generated
```

Несколько paths:

```text
ignore (
    static
    content/html
    ./third_party/javascript
)
```

`ignore` полезен, чтобы wildcard patterns вроде `./...` не находили packages внутри generated или non-Go directories.

Ignored directories остаются в module file tree, но исключаются из package pattern matching.

`ignore` применяется **только** в `go.mod` main module; directives dependencies эффекта не имеют.
