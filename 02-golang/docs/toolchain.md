---
title: "Go Toolchains"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/toolchain.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Go Toolchains

## Введение

Начиная с Go 1.21 Go distribution состоит из команды `go` и bundled Go toolchain — standard library, compiler, assembler и других tools.

Команда `go` может использовать:

- bundled toolchain;
- другие Go toolchains, найденные в local `PATH`;
- toolchain, автоматически скачанный при необходимости.

Выбор зависит от:

- `GOTOOLCHAIN`;
- `go` directive в main module `go.mod` или workspace `go.work`;
- `toolchain` directive.

Поэтому разные modules/workspaces на одной машине могут запускаться разными Go toolchains, аналогично тому как modules используют разные dependency versions.

В стандартной конфигурации bundled toolchain используется, если он не старше требований `go`/`toolchain`. Если requirement новее, `go` command может найти или скачать нужный toolchain.

Пример: установлен `go1.21.3`, module требует:

```text
go 1.21.9
```

`go` сначала ищет executable `go1.21.9` в `PATH`, а при standard auto mode — может скачать и cache соответствующий toolchain.

Если automatic switching отключён, слишком старый toolchain откажется работать с module/workspace, требующим более новую Go version.

`go` и `toolchain` можно воспринимать как requirements на dependency «Go toolchain», подобно обычным `require` dependencies.

Управлять ими можно через `go get`, например:

```bash
go get go@latest
```

Принудительный запуск определённой версии:

```bash
GOTOOLCHAIN=go1.21rc3 go test
```

Default:

```text
GOTOOLCHAIN=auto
```

Форма `name+auto` задаёт начальный default, но разрешает перейти на newer version:

```bash
go env -w GOTOOLCHAIN=go1.21.3+auto
```

## Go versions

Начиная с современных release lines released versions имеют форму:

```text
1.N.P
```

где `P=0` — initial release, а `P>0` — patch release.

Release candidates:

```text
1.NrcR
```

`1.N` без patch/RC называется **language version** и обозначает семейство releases, реализующих эту language/standard-library version.

Например, `1.21`, `1.21rc2` и `1.21.3` относятся к language version `1.21`.

Ordering внутри одной language version:

```text
1.21 < 1.21rc1 < 1.21rc2 < 1.21.0 < 1.21.1 < 1.21.2
```

До Go 1.21 initial release назывался `1.N`, поэтому для старых lines ordering выглядит, например:

```text
1.20rc1 < 1.20rc2 < 1.20rc3 < 1.20 < 1.20.1
```

Исторические beta releases располагаются перед RC:

```text
1.18beta1 < 1.18beta2 < 1.18rc1 < 1.18 < 1.18.1
```

## Имена toolchains

Standard toolchain называется `goV`, где `V` — конкретная released/beta/RC Go version:

```text
go1.21rc1
go1.21.0
```

Для lines 1.21+ bare `go1.21` не является именем initial released toolchain — initial release это `go1.21.0`.

Non-standard toolchains могут иметь suffix:

```text
go1.21.0-custom
```

Для version ordering suffix после `-` не учитывается.

## Конфигурация module/workspace

`go.mod` и `go.work` хранят version requirements.

`go` line — minimum required Go version.

Если `go` line отсутствует:

- старый `go.mod` трактуется как имеющий implicit `go 1.16`;
- `go.work` — implicit `go 1.18`.

`toolchain` line — suggested toolchain. Если её нет, предполагается `toolchain goV`, где `V` соответствует `go` line.

Например:

```text
go 1.21.0
```

без explicit toolchain эквивалентно suggestion:

```text
toolchain go1.21.0
```

Toolchain отказывается загружать module/workspace, чей minimum `go` новее самого toolchain.

Module's `go` line должна быть не ниже `go` lines всех modules из `require`. Workspace's `go` line — не ниже `go` lines modules из `use`.

`go` line также задаёт language version compiler для packages конкретного module. Per-file language version можно повысить build constraint'ом `//go:build go1.22` (для соответствующих modern versions): файл одновременно будет доступен только подходящим toolchains и компилироваться с указанной language version.

## `GOTOOLCHAIN`

Приоритет получения `GOTOOLCHAIN`:

1. Process environment.
2. User Go environment defaults, управляемые `go env -w/-u`.
3. `$GOROOT/go.env` bundled distribution.

Official Go distributions обычно задают:

```text
GOTOOLCHAIN=auto
```

Если `$GOROOT/go.env` отсутствует/default не задан, используется `local`.

Показать effective setting:

```bash
go env GOTOOLCHAIN
```

## Выбор toolchain при запуске

Поддерживаются формы:

```text
<name>
<name>+auto
<name>+path
```

Shortcuts:

```text
auto = local+auto
path = local+path
```

- `local` — всегда bundled toolchain;
- `go1.X.Y` — всегда конкретный named toolchain;
- `+auto` — разрешить поиск и download newer toolchain;
- `+path` — разрешить switch только на toolchain, найденный в executable `PATH`, без download fallback.

При `auto/path` Go сравнивает default toolchain с `toolchain` и `go` lines текущего `go.work`/`go.mod`.

Особый directive:

```text
toolchain default
```

запрещает upgrade выше configured default.

Если нужен другой toolchain, `go` сначала ищет executable вроде `go1.27.1` в `PATH`; при `auto` и отсутствии executable может скачать toolchain.

Проверить selected toolchain:

```bash
go version
```

Проверить именно bundled version:

```bash
GOTOOLCHAIN=local go version
```

Начиная с Go 1.24 выбор toolchain можно трассировать:

```bash
GODEBUG=toolchaintrace=1 go version
```

## Switch во время выполнения command

Некоторые commands сами добавляют новые modules/workspace members и могут обнаружить requirement более новой Go version:

- `go get`;
- `go work use`;
- `go work sync`;
- `go install package@version`;
- `go run package@version`.

Если `GOTOOLCHAIN` разрешает switch, command выбирает подходящий newer supported toolchain и продолжает выполнение.

Go сообщает причину switch, например:

```text
go: module example.com/widget@v1.2.3 requires go >= 1.24rc1; switching to go 1.27.9
```

Go не обязан выбирать ровно minimum requested version. Он стремится выбрать минимальную из поддерживаемых candidate toolchains, удовлетворяющую requirement, следуя идее Minimal Version Selection.

При выборе рассматриваются до трёх supported candidates:

- latest RC следующей unreleased language version;
- latest patch самой свежей released language version;
- latest patch предыдущей supported language version.

Из них выбирается oldest candidate, который удовлетворяет новому requirement.

Если command обновляет `go` line, он также записывает `toolchain` line со своим toolchain для repeatability. Поэтому повторный запуск обычно уже стартует сразу на правильном toolchain и не печатает switch notice.

Исключение — `go install package@version` / `go run package@version`: они выполняются без writable main module/workspace, поэтому сохранять `toolchain` line негде.

## Скачивание toolchains

При `auto` Go скачивает newer toolchains как специальные modules:

```text
golang.org/toolchain
```

version имеет вид:

```text
v0.0.1-goVERSION.GOOS-GOARCH
```

Загрузка использует module infrastructure:

- учитывает `GOPROXY`;
- проверяется checksum database.

Toolchain checksum не записывается в project `go.sum`, потому что конкретный artifact зависит от default toolchain, `GOOS` и `GOARCH`.

Если `GOSUMDB=off`, automatic toolchain download не может быть проверен и завершается ошибкой verification. `GOPRIVATE`/`GONOSUMDB` patterns к toolchain downloads не применяются.

## Управление Go/toolchain requirements через `go get`

`go get` умеет управлять `go` и `toolchain` как versioned dependencies:

```bash
go get go@1.22.1 toolchain@1.24rc1
```

Получится логически:

```text
go 1.22.1
toolchain go1.24rc1
```

`toolchain` должен быть не ниже `go` requirement. Поэтому:

```bash
go get go@1.25.0
```

при необходимости также обновит toolchain. Если обе versions совпадают, explicit `toolchain` line может быть удалена как redundant.

При downgrade действует обратная constraint: попытка опустить toolchain ниже `go` line может потребовать downgrade самой `go` line и совместимых dependencies.

Удалить explicit toolchain:

```bash
go get toolchain@none
```

Version queries поддерживаются аналогично modules:

```bash
go get go@1.22
go get toolchain@go1.22
```

Go выберет latest available version соответствующей language line.

`go get` и `go mod tidy` поддерживают `go` line не ниже требований required dependency modules.

Если добавляемая dependency требует более новый Go, `go get` обновляет `go` line main module. Если затем принудительно downgrade `go`, Go может downgrade/remove dependencies, несовместимые с выбранной version.

Modern preferred способ сменить Go requirement:

```bash
go get go@1.27
```

Старый `go mod tidy -go=...` всё ещё поддерживается.

## Workspace requirements

`go get`, запущенный внутри workspace root, при необходимости обновляет `go.work` `go` line.

`go work use` проверяет, что workspace Go version не ниже requirements всех `use` modules. Чтобы пересинхронизировать устаревший `go.work`:

```bash
go work use
```

`go work init` и `go work sync` также корректируют Go version по необходимости.

Удалить `toolchain` из `go.work`:

```bash
go work edit -toolchain=none
```
