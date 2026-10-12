---
title: "Управление dependencies"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/modules/managing-dependencies.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Управление dependencies

Когда code использует external packages, эти packages — распространяемые как modules — становятся dependencies. Со временем их требуется обновлять или заменять. Go предоставляет dependency management tools, помогающие поддерживать applications в безопасном и согласованном состоянии.

Эта страница описывает основные dependency management tasks. Большинство выполняется Go tools; также приведены дополнительные useful practices.

**См. также:**

- Если Go modules незнакомы, начните с [[../getting-started|Getting Started]].
- Использование `go` commands помогает сохранять requirements согласованными, а `go.mod` — valid. Reference: [Command go](https://pkg.go.dev/cmd/go/). CLI help: `go help <command>`, например `go help mod tidy`.
- Go commands редактируют `go.mod`; его structure описана в [[gomod-ref|go.mod file reference]].
- IDE/editor с module awareness упрощает работу; см. [[../editors|Editor plugins и IDEs]].
- Разработка и публикация собственных modules рассматриваются отдельно: [[developing|Разработка и публикация modules]].

## Workflow использования и управления dependencies {#workflow}

С Go tools можно находить и подключать packages с [pkg.go.dev](https://pkg.go.dev).

Обычная последовательность:

1. [[#Поиск и import полезных packages|Найдите полезный package]] на pkg.go.dev.
2. Импортируйте package в code.
3. Если code ещё не находится в module, [[#Включение dependency tracking|включите dependency tracking]].
4. [[#Добавление dependency|Добавьте external packages как dependencies]].
5. Со временем [[#Upgrade или downgrade dependency|upgrade/downgrade versions]] по необходимости.

## Управление dependencies как modules {#modules}

Dependencies в Go управляются как modules, содержащие импортируемые packages.

Модель поддерживается следующими механизмами:

- **Децентрализованная публикация.** Maintainers публикуют modules из собственных repositories и присваивают version numbers.
- **pkg.go.dev.** Search engine и documentation browser для поиска modules/packages.
- **Version numbering convention.** Позволяет понимать stability и backward compatibility; см. [[version-numbers|Нумерация versions module]].
- **Go tools.** Скачивание source, upgrades и другие dependency operations.

## Поиск и import полезных packages {#locating_packages}

На [pkg.go.dev](https://pkg.go.dev) найдите package с нужной functionality.

На package page скопируйте package path и используйте его в import:

```go
import "rsc.io/quote"
```

После import включите dependency tracking и получите source package для compilation. См. [[#Включение dependency tracking]] и [[#Добавление dependency]].

## Включение dependency tracking {#enable_tracking}

Чтобы отслеживать dependencies, поместите code в собственный module. В root source tree создаётся `go.mod`, где перечисляются managed dependencies.

В root directory:

```text
$ go mod init example/mymodule
```

Argument `go mod init` — module path. Если возможно, это должен быть repository location source code.

Если repository location пока неизвестен, используйте безопасный temporary prefix — domain, которым вы владеете, company name или другой controlled namespace. См. [[#Именование module]].

По мере работы Go tools обновляют `go.mod`.

При добавлении dependencies также создаётся `go.sum` с checksums modules. Go использует его для проверки integrity скачанных module files, в том числе на machines других developers.

Commit'ьте `go.mod` и `go.sum` вместе с code.

Подробнее: [[gomod-ref|go.mod reference]].

## Именование module {#naming_module}

Module path — имя module и prefix import paths всех packages внутри него. Выбирайте path, который не конфликтует с другими modules.

Типичная форма:

```text
<prefix>/<descriptive-text>
```

### Prefix

Обычно описывает origin module.

Лучший вариант для published module — repository location, например:

```text
github.com/<project-name>/
```

Если repository path не используется, выберите namespace, который контролируете, например company name. Избегайте generic names вроде `widgets`, `utilities`, `app`.

### Descriptive text

Обычно project name. Основной смысл functionality всё равно несут package names; module path создаёт namespace для них.

### Зарезервированные module path prefixes

Go гарантирует, что следующие prefixes не будут использоваться обычными package names:

- `test` — для modules, создаваемых локально в tests. Например test может выполнить `go mod init test`, затем настроить temporary module для проверки source analyzer.
- `example` — используется в документации Go для локальных examples/tutorials.

`example.com` также используется в docs, когда example имитирует потенциально published module.

## Добавление dependency {#adding_dependency}

После import package из published module добавьте module как dependency через [`go get`](https://pkg.go.dev/cmd/go#hdr-Add_dependencies_to_current_module_and_install_them).

`go get`:

- при необходимости добавляет `require` directives в `go.mod` для modules, нужных packages command line;
- скачивает module source для compilation;
- может получать modules через proxy (например `proxy.golang.org`) либо напрямую из VCS repository;
- сохраняет source в local module cache;
- authenticates каждый downloaded module, проверяя неизменность опубликованного content. Если content version изменился после публикации, Go tools возвращают security error.

Добавить dependencies текущего package:

```text
$ go get .
```

Добавить конкретный module:

```text
$ go get example.com/theirmodule
```

Location download можно настраивать через module proxy; см. [[#Настройка module proxy server]].

## Получение конкретной dependency version {#getting_version}

`go get` принимает `@version` и обновляет соответствующий `require` в `go.mod`.

Это полезно, если:

- нужно проверить pre-release;
- current version не подходит и требуется известная stable version;
- нужно upgrade/downgrade dependency.

Конкретная version:

```text
$ go get example.com/theirmodule@v1.3.4
```

Latest:

```text
$ go get example.com/theirmodule@latest
```

Соответствующий `go.mod`:

```text
require example.com/theirmodule v1.3.4
```

## Поиск доступных updates {#discovering_updates}

[`go list -m`](https://go.dev/ref/mod#go-list-m) показывает текущие dependency modules и available versions.

Все dependencies вместе с latest available:

```text
$ go list -m -u all
```

Один module:

```text
$ go list -m -u example.com/theirmodule
```

После обнаружения update протестируйте новую version до принятия решения об upgrade.

## Upgrade или downgrade dependency {#upgrading}

1. Найдите available versions через `go list`, как описано выше.
2. Получите нужную version через `go get module@version`.

## Синхронизация dependencies с code {#synchronizing}

После изменений code и imports managed dependencies могут перестать точно соответствовать реально используемым packages.

Используйте:

```text
$ go mod tidy
```

`go mod tidy`:

- добавляет missing modules, необходимые imported packages;
- удаляет unused modules, которые больше не предоставляют relevant packages;
- синхронизирует `go.mod` и `go.sum`.

Flag `-v` выводит информацию об удалённых modules.

## Разработка и тестирование с unpublished module code {#unpublished}

Можно указать dependency module, который ещё не опубликован. Source может находиться:

- в его repository;
- в вашем fork repository;
- в local directory рядом с consumer module.

Use cases:

- вы fork'нули external module, чтобы исправить bug/add feature и протестировать change до pull request;
- вы разрабатываете новый module, который пока недоступен через `go get`.

### Использование code module из local directory {#local_directory}

Чтобы consumer использовал local copy dependency, добавьте `replace` в `go.mod`.

Это полезно при:

- параллельной разработке двух собственных modules;
- тестировании fixes/features external module из local checkout.

Пример:

```text
module example.com/mymodule

go 1.23.0

require example.com/theirmodule v0.0.0-unpublished

replace example.com/theirmodule v0.0.0-unpublished => ../theirmodule
```

Fictitious version `v0.0.0-unpublished` гарантирует, что dependency разрешается только через replacement.

Настройте pair через Go tools:

```text
$ go mod edit -replace=example.com/theirmodule@v0.0.0-unpublished=../theirmodule
$ go get example.com/theirmodule@v0.0.0-unpublished
```

> [!note]
> При `replace` Go tools не authenticate external module способом, описанным в [[#Добавление dependency]].

С Go 1.18 доступен workspace mode для одновременной работы с несколькими modules. См. [[../tutorial/workspaces|Multi-module workspaces]].

### Использование external module из собственного repository fork {#external_fork}

Если external module fork'нут для fix/feature, Go tools можно направить на fork через `replace`.

Пример:

```text
module example.com/mymodule

go 1.23.0

require example.com/theirmodule v1.2.3

replace example.com/theirmodule v1.2.3 => example.com/myfork/theirmodule v1.2.3-fixed
```

Сначала узнайте current version:

```text
$ go list -m example.com/theirmodule
example.com/theirmodule v1.2.3
```

Затем задайте replacement:

```text
$ go mod edit -replace=example.com/theirmodule@v1.2.3=example.com/myfork/theirmodule@v1.2.3-fixed
```

Как и для local replace, authentication original module не применяется.

## Получение конкретного commit по repository identifier {#repo_identifier}

`go get` может добавить unpublished code конкретного commit.

По commit hash:

```text
$ go get example.com/theirmodule@4cf76c2
```

По branch:

```text
$ go get example.com/theirmodule@bugfixes
```

`go get` добавит `require` с pseudo-version, generated из commit metadata.

## Удаление dependency {#removing_dependency}

Удалить все unused dependencies:

```text
$ go mod tidy
```

Удалить конкретный module:

```text
$ go get example.com/theirmodule@none
```

`go get ...@none` может также downgrade'ить или удалить другие dependencies, зависящие от удаляемого module.

## Tool dependencies {#tools}

Tool dependencies позволяют управлять developer tools, написанными на Go: generators, linters, formatters и т. п.

Пример — [`stringer`](https://pkg.go.dev/golang.org/x/tools/cmd/stringer) вместе с [`go generate`](https://go.dev/blog/generate).

### Go 1.24+

Добавить tool dependency:

```text
$ go get -tool golang.org/x/tools/cmd/stringer
```

Go добавит `tool` directive в `go.mod` и необходимые `require` directives.

После этого tool можно запускать по last package path component:

```text
$ go tool stringer
```

Если short name неоднозначен либо совпадает с tool из Go distribution, используйте full package path:

```text
$ go tool golang.org/x/tools/cmd/stringer
```

Список доступных tools:

```text
$ go tool
```

`tool` directive можно добавить вручную, но module, содержащий tool, должен присутствовать в `require`. Missing requirements проще всего восстановить:

```text
$ go mod tidy
```

Requirements tool dependencies участвуют в module graph как обычные requirements:

- minimal version selection;
- `require`;
- `replace`;
- `exclude`.

Благодаря module graph pruning dependency module, который сам использует tool dependency, обычно не заставляет ваш module наследовать requirements, нужные только для этого tool.

Meta-pattern `tool` позволяет выполнять operation над всеми tools одновременно.

Upgrade всех tools:

```text
$ go get tool
```

эквивалентно:

```text
$ go get tool@upgrade
```

Install всех tools в `$GOBIN`:

```text
$ go install tool
```

### До Go 1.24

Аналогичный effect можно получить через blank import tool package в `.go` file, исключённом из normal build с помощью build constraints. Tool затем запускается через `go run <full-package-path>`.

## Настройка module proxy server {#proxy_server}

По умолчанию Go tools скачивают modules через `proxy.golang.org` или непосредственно из repository module.

Другой proxy может использоваться для:

- internal/private infrastructure;
- дополнительного контроля dependencies;
- caching/auditing policies.

Настройка выполняется через `GOPROXY`.

Default behavior:

```text
GOPROXY="https://proxy.golang.org,direct"
```

Можно указать несколько URLs. Semantics separator важна.

### Comma `,`

Следующий proxy используется только если текущий вернул HTTP `404` или `410`:

```text
GOPROXY="https://proxy.example.com,https://proxy2.example.com"
```

### Pipe `|`

Следующий proxy используется независимо от HTTP error code:

```text
GOPROXY="https://proxy.example.com|https://proxy2.example.com"
```

Подробнее: [Module downloading and verification](https://pkg.go.dev/cmd/go#hdr-Module_downloading_and_verification).

### Private modules

Modules часто находятся в VCS servers/proxies, недоступных public internet.

`GOPRIVATE` настраивает `go` command для private module prefixes. `GOPRIVATE` или `GONOPROXY` могут содержать glob patterns prefixes, которые нельзя запрашивать через public proxy.

Пример:

```text
GOPRIVATE=*.corp.example.com,*.research.example.com
```

После такой настройки `go` command получает private modules из private sources, не отправляя matching module paths в public proxy infrastructure.
