---
title: "Go Toolchains"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/toolchain.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Go Toolchains

## Введение {#intro}

Начиная с Go 1.21 distribution Go состоит из команды `go` и bundled Go toolchain: standard library, compiler, assembler и других tools.

Команда `go` может использовать как bundled toolchain, так и другие versions, найденные в local `PATH` или скачанные при необходимости.

Выбор toolchain зависит от setting `GOTOOLCHAIN` и lines `go`/`toolchain` в `go.mod` main module либо в `go.work` current workspace.

При переходе между разными main modules и workspaces используемая toolchain version может меняться так же, как меняются versions module dependencies.

В standard configuration команда `go` использует собственный bundled toolchain, если он не старше versions из `go` или `toolchain` lines main module/workspace.

Например, команда `go` из Go 1.21.3 в module с `go 1.21.0` использует Go 1.21.3.

Если `go` или `toolchain` line новее bundled toolchain, команда запускает более новый toolchain.

Например, Go 1.21.3 в module с:

```text
go 1.21.9
```

ищет `go1.21.9` в `PATH`, а если его нет — скачивает и cache'ит Go 1.21.9 toolchain.

Automatic toolchain switching можно отключить. В таком режиме для precise forwards compatibility команда `go` откажется работать в module/workspace, где `go` line требует более новую Go version.

Иными словами, `go` line задаёт minimum Go version, необходимую для использования module/workspace.

Dependency modules иногда должны указывать minimum Go version ниже preferred toolchain, который удобнее использовать при разработке самого module. В таком случае `toolchain` line в `go.mod`/`go.work` задаёт preferred toolchain, имеющий priority над `go` line при выборе toolchain.

Lines `go` и `toolchain` можно рассматривать как version requirements зависимости module от самого Go toolchain — аналогично `require` lines для обычных modules.

Команда `go get` управляет этой dependency так же, как другими module dependencies. Например:

```text
go get go@latest
```

обновляет module до latest released Go toolchain.

`GOTOOLCHAIN` может принудительно выбрать конкретную Go version, overriding `go` и `toolchain` lines.

Например, test package через Go 1.21rc3:

```text
GOTOOLCHAIN=go1.21rc3 go test
```

Default:

```text
GOTOOLCHAIN=auto
```

Он включает automatic switching.

Форма `<name>+auto` задаёт default toolchain, от которого начинается selection, сохраняя возможность перейти на newer version.

Например:

```text
GOTOOLCHAIN=go1.21.3+auto
```

указывает начать с Go 1.21.3, но использовать newer toolchain, если этого требуют `go`/`toolchain` lines.

Поскольку default `GOTOOLCHAIN` можно изменить через `go env -w`, при установленном Go 1.21.0 или newer команда:

```text
go env -w GOTOOLCHAIN=go1.21.3+auto
```

эквивалентна замене installation Go 1.21.0 на Go 1.21.3 для default selection.

Оставшаяся часть документа подробно описывает versioning, selection и management Go toolchains.

## Go versions {#version}

Released versions Go имеют syntax `1.N.P`, где `P` обозначает release внутри line Go 1.N.

Initial release — `1.N.0`, например `1.21.0`. Более поздние releases вроде `1.N.9` обычно называют patch releases.

Release candidates Go 1.N, выпускаемые до `1.N.0`, имеют syntax `1.NrcR`. Первый RC, например, `1.23rc1`.

Форма `1.N` называется **language version**. Она обозначает family releases, реализующих одну version языка Go и standard library.

Language version конкретной Go version получается удалением всего после `N`: `1.21`, `1.21rc2` и `1.21.3` реализуют language version `1.21`.

Released toolchains, например Go 1.21.0 и Go 1.21rc1, возвращают конкретную version (`go1.21.0`, `go1.21rc1`) из `go version` и `runtime.Version`.

Unreleased toolchains, собранные из development repository, возвращают только language version, например `go1.21`.

Любые две Go versions можно сравнить.

Если language versions отличаются, это определяет ordering: например:

```text
1.21.9 < 1.22
```

Внутри одной language version порядок от меньшей к большей:

1. сама language version;
2. release candidates по `R`;
3. releases по `P`.

Например:

```text
1.21 < 1.21rc1 < 1.21rc2 < 1.21.0 < 1.21.1 < 1.21.2
```

До Go 1.21 initial toolchain release назывался `1.N`, а не `1.N.0`, поэтому для `N < 21` ordering скорректирован так, чтобы `1.N` шёл после RC:

```text
1.20rc1 < 1.20rc2 < 1.20rc3 < 1.20 < 1.20.1
```

Ранние Go versions также имели beta releases. Они идут непосредственно перед RC:

```text
1.18beta1 < 1.18beta2 < 1.18rc1 < 1.18 < 1.18.1
```

## Имена Go toolchains {#name}

Standard toolchains называются `goV`, где `V` — конкретная beta, RC или released Go version.

Например:

```text
go1.21rc1
go1.21.0
```

`go1.21` и `go1.22` не являются names released toolchains, потому что initial releases этих lines — `go1.21.0` и `go1.22.0`.

В то же время `go1.20` и `go1.19` — valid names historical initial releases.

Non-standard toolchains используют форму:

```text
goV-suffix
```

Для ordering сравнивается embedded version `V`: prefix `go` и suffix начиная с `-` игнорируются.

Поэтому `go1.21.0` и `go1.21.0-custom` равны с точки зрения ordering.

## Конфигурация module и workspace {#config}

Go modules/workspaces хранят version-related configuration в `go.mod` и `go.work`.

`go` line объявляет minimum Go version для использования module/workspace.

Для compatibility:

- если `go` line отсутствует в `go.mod`, считается implicit `go 1.16`;
- если отсутствует в `go.work`, считается implicit `go 1.18`.

`toolchain` line объявляет suggested toolchain.

Если default toolchain старее suggested toolchain, команда `go` может запустить suggested toolchain.

Если `toolchain` line отсутствует, предполагается:

```text
toolchain goV
```

где `V` — version из `go` line.

Поэтому:

```text
go 1.21.0
```

без explicit `toolchain` эквивалентно:

```text
toolchain go1.21.0
```

Toolchain отказывается загружать module/workspace с minimum Go version выше собственной.

Например, Go 1.21.2 откажется загружать module/workspace с `go 1.21.3` или `go 1.22`.

`go` line module должна быть greater than or equal to `go` version каждого module из `require`.

`go` line workspace должна быть greater than or equal to `go` version каждого module из `use`.

Например, если module M требует dependency D, чей `go.mod` содержит `go 1.22.0`, то M не может содержать `go 1.21.3`.

`go` line каждого module задаёт language version, которую compiler применяет при compilation packages этого module.

Language version можно изменить per-file с помощью build constraint. Если build constraint требует minimum version не ниже `go1.21`, compiler использует эту minimum language version для file.

Например, module с code Go 1.21 должен иметь `go 1.21` или `go 1.21.3`. Если конкретный source file должен compile'иться только newer toolchain, line:

```go
//go:build go1.22
```

одновременно исключает file из старых toolchains и меняет его language version на Go 1.22.

Безопаснее всего менять `go` и `toolchain` через `go get`; см. раздел [ниже](#get).

До Go 1.21 toolchains считали `go` line advisory requirement: если build проходил, считалось, что всё работает; иначе печатался note о possible version mismatch.

Go 1.21 сделал requirement mandatory.

Часть behavior backported:

- Go 1.19.13+;
- Go 1.20.8+

отказываются загружать module/workspace с Go 1.22 или newer.

До Go 1.21 также не требовалось, чтобы `go` line module/workspace была не ниже `go` versions dependency modules.

## Setting `GOTOOLCHAIN` {#GOTOOLCHAIN}

Команда `go` выбирает toolchain на основе `GOTOOLCHAIN`.

Setting определяется стандартными правилами Go environment:

1. если `GOTOOLCHAIN` имеет non-empty value в process environment — используется оно;
2. иначе используется value из user environment defaults, управляемых `go env -w` / `go env -u`;
3. иначе используется value из `$GOROOT/go.env` bundled distribution.

Standard distributions задают в `$GOROOT/go.env`:

```text
GOTOOLCHAIN=auto
```

Repackaged distributions могут использовать другой value.

Если `$GOROOT/go.env` отсутствует или не задаёт default, принимается:

```text
GOTOOLCHAIN=local
```

Показать effective value:

```text
go env GOTOOLCHAIN
```

## Выбор Go toolchain {#select}

При startup команда `go` выбирает toolchain.

`GOTOOLCHAIN` имеет формы:

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

`<name>` задаёт default toolchain:

- `local` — bundled toolchain;
- другое name должно быть concrete toolchain name, например `go1.21.0`.

Команда предпочитает default toolchain.

Начиная с Go 1.21 toolchains не запускаются в modules/workspaces, требующих newer Go version; вместо этого они сообщают error и exit, если switching не разрешён.

При:

```text
GOTOOLCHAIN=local
```

всегда используется bundled toolchain.

При:

```text
GOTOOLCHAIN=go1.21.0
```

всегда используется конкретный named toolchain. Если binary найден в system `PATH`, используется он; иначе toolchain скачивается и verified.

При `<name>+auto`, `<name>+path`, `auto` или `path` команда может выбрать newer Go version.

Она читает `toolchain` и `go` lines current `go.work`, либо main `go.mod`, если workspace нет.

Selection logic:

1. Если есть `toolchain <tname>` и `<tname>` новее default — используется `<tname>`.
2. Если есть `toolchain default` — используется default toolchain и automatic update выше него отключается.
3. Иначе, если `go <version>` новее default — используется `go<version>`.

Чтобы запустить non-bundled toolchain, команда ищет program с соответствующим name в executable path (`$PATH`, `%PATH%`).

Если program не найден, при `auto` toolchain скачивается. Форма `+path` отключает download fallback и после поиска `PATH` прекращает selection.

Показать selected toolchain:

```text
go version
```

Показать именно bundled version:

```text
GOTOOLCHAIN=local go version
```

Начиная с Go 1.24 process selection можно трассировать:

```text
GODEBUG=toolchaintrace=1 go version
```

## Переключение Go toolchain во время command {#switch}

Для большинства commands `go.work` или main `go.mod` уже имеет `go` line не ниже requirements dependency modules, поэтому startup selection сразу выбирает sufficiently new toolchain.

Но некоторые commands добавляют новые module versions во время execution:

- `go get` добавляет dependencies main module;
- `go work use` добавляет local modules в workspace;
- `go work sync` resynchronizes workspace с изменившимися local modules;
- `go install package@version` и `go run package@version` фактически работают в empty main module и добавляют `package@version` как dependency.

Такие commands могут встретить module, чей `go.mod` требует newer Go version, чем currently executing toolchain.

Если `GOTOOLCHAIN` допускает switching (`auto`/`path`), команда выбирает подходящий newer toolchain и продолжает current command.

При switch после startup команда печатает причину:

```text
go: module example.com/widget@v1.2.3 requires go >= 1.24rc1; switching to go 1.27.9
```

Toolchain может быть новее minimum requirement: команда стремится выбрать **supported** Go toolchain.

Сначала `go` получает список available toolchains:

- для `auto` — скачивает list available toolchains;
- для `path` — scans `PATH` для executables с valid toolchain names.

Из списка формируется до трёх candidates:

- latest RC следующей unreleased language version;
- latest patch наиболее свежей released language version;
- latest patch предыдущей language version.

Это supported releases согласно Go release policy.

В духе Minimal Version Selection выбирается minimum, то есть oldest candidate, удовлетворяющий requirement.

Например, если module требует Go 1.24rc1+, а available supported candidates — Go 1.27.9, Go 1.28.3 и Go 1.29rc2, будет выбран Go 1.27.9.

Если requirement — Go 1.28+, будет выбран 1.28.3; для Go 1.29+ — 1.29rc2.

Commands, добавляющие module versions с новым Go requirement, записывают новый minimum в `go` line current `go.work` или main `go.mod`.

Для repeatability любой command, обновивший `go` line, также обновляет `toolchain` line своим toolchain name.

Например, `go get example.com/widget@v1.2.3` может switch'нуться на Go 1.27.9, завершить operation и записать:

```text
toolchain go1.27.9
```

Следующий command выберет его уже на startup и не напечатает switching message.

В общем случае, если одинаковый `go` command выполнить дважды, switch message будет только в первом запуске, потому что первый обновит `go.mod`/`go.work`.

Исключение — `go install package@version` и `go run package@version`: у них нет writable main module/workspace, куда можно сохранить `toolchain` line, поэтому message повторяется каждый раз, когда нужен switch.

## Скачивание toolchains {#download}

При `GOTOOLCHAIN=auto` или `<name>+auto` Go скачивает newer toolchains по необходимости.

Они упакованы как special modules:

```text
module path: golang.org/toolchain
version: v0.0.1-goVERSION.GOOS-GOARCH
```

Toolchains скачиваются так же, как обычные modules:

- downloads можно proxy'ить через `GOPROXY`;
- checksums проверяются Go checksum database.

Конкретный artifact зависит от default toolchain system, `GOOS` и `GOARCH`, поэтому записывать toolchain module checksums в project `go.sum` непрактично.

Вместо этого automatic download fail'ится из-за отсутствия verification при:

```text
GOSUMDB=off
```

Patterns `GOPRIVATE` и `GONOSUMDB` к toolchain downloads не применяются.

## Управление Go version requirements через `go get` {#get}

Команда `go` рассматривает `go` и `toolchain` lines как versioned toolchain dependencies main module.

`go get` управляет ими так же, как `require` dependencies.

Например:

```text
go get go@1.22.1 toolchain@1.24rc1
```

получает:

```text
go 1.22.1
toolchain go1.24rc1
```

Dependency `go` требует `toolchain` dependency с version greater than or equal to Go requirement.

Продолжая example, последующий:

```text
go get go@1.25.0
```

обновит toolchain до `go1.25.0`.

Когда toolchain точно совпадает с `go` line, explicit `toolchain` избыточен, поэтому line удаляется.

Та же constraint действует при downgrade.

Если исходно:

```text
go 1.22.1
toolchain go1.24rc1
```

то:

```text
go get toolchain@go1.22.9
```

меняет только toolchain.

Но:

```text
go get toolchain@go1.21.3
```

также downgrade'ит `go` line до `go 1.21.3`. Итог может содержать только `go 1.21.3`, без `toolchain`.

Special form:

```text
toolchain@none
```

удаляет explicit line, например:

```text
go get toolchain@none
go get go@1.25.0 toolchain@none
```

Version syntax и queries для `go`/`toolchain` работают аналогично modules.

Как `go get example.com/widget@v1.2` выбирает latest `v1.2.x`, так:

```text
go get go@1.22
```

выбирает latest available release language version 1.22, например RC до release или latest patch после release.

То же относится к:

```text
go get toolchain@go1.22
```

`go get` и `go mod tidy` поддерживают `go` line не ниже `go` line любой required dependency.

Если main module содержит `go 1.22.1`, а `go get example.com/widget@v1.2.3` добавляет module с `go 1.24rc1`, main `go` line будет повышена до `go 1.24rc1`.

Последующий:

```text
go get go@1.22.1
```

downgrade'ит `example.com/widget` до compatible version либо удалит requirement, аналогично downgrade обычной dependency.

До Go 1.21 recommended command для обновления module до новой Go version была:

```text
go mod tidy -go=1.22
```

Она всё ещё valid, но теперь предпочтительнее:

```text
go get go@1.22
```

Когда `go get` запускается внутри module, находящегося под workspace root, он в основном игнорирует workspace, но при необходимости повышает `go` line в `go.work`, чтобы workspace не остался слишком старым.

## Управление Go version requirements workspace через `go work` {#work}

Как отмечено выше, `go get` внутри workspace root обновляет `go.work` `go` line так, чтобы она была не ниже modules внутри root.

Но workspace может ссылаться на modules за пределами root. `go get`, выполненный там, может оставить invalid workspace configuration, где `go` version в `go.work` меньше requirements одного из `use` modules.

`go work use`, добавляющий `use` directives, также проверяет, что `go` version workspace достаточна для всех existing `use` entries.

Чтобы синхронизировать workspace, чья Go version отстала от modules:

```text
go work use
```

Команды `go work init` и `go work sync` также обновляют Go version при необходимости.

Удалить `toolchain` line из `go.work`:

```text
go work edit -toolchain=none
```
