---
title: "Управление зависимостями"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/modules/managing-dependencies.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Управление зависимостями

Когда код использует внешние packages, modules, в которых эти packages публикуются, становятся dependencies. Со временем зависимости приходится добавлять, обновлять, понижать, заменять локальными forks, удалять и проверять на целостность. Go предоставляет для этого встроенные dependency-management tools.

## Типичный workflow

Обычная последовательность выглядит так:

1. Найти подходящий package на [pkg.go.dev](https://pkg.go.dev/).
2. Добавить его import path в исходный код.
3. Если проект ещё не module — включить dependency tracking через `go mod init`.
4. Добавить dependency через Go tools.
5. По мере необходимости upgrade/downgrade versions.
6. Периодически синхронизировать dependency graph через `go mod tidy`.

## Dependencies как modules

Go управляет внешними dependencies на уровне modules. Эту модель поддерживают:

- децентрализованная публикация module source;
- pkg.go.dev для поиска packages и API docs;
- semantic module versioning;
- Go commands для разрешения, загрузки, обновления и проверки modules.

## Поиск и импорт packages

На pkg.go.dev найдите package и скопируйте его package path. Затем импортируйте его:

```go
import "rsc.io/quote"
```

После изменения imports module dependency необходимо разрешить и записать в `go.mod`/`go.sum`.

## Включение dependency tracking

Перейдите в root проекта и создайте module:

```bash
go mod init example/mymodule
```

Аргумент — module path. Если module будет публиковаться, лучше сразу использовать будущий repository path.

Go tools изменяют `go.mod` при операциях с dependencies. При скачивании dependencies также формируется `go.sum` с checksums modules. `go.mod` и `go.sum` следует хранить в version control.

## Выбор module path

Module path становится именем module и префиксом import paths всех его packages.

Типичная форма:

```text
<prefix>/<descriptive-text>
```

`prefix` обычно является repository location, например:

```text
github.com/project-name/mymodule
```

Если repository ещё неизвестен, можно временно использовать уникальное имя, которым вы управляете, например domain/company name.

Не используйте слишком общие prefixes вроде `widgets`, `utilities` или `app`, если существует риск конфликта.

Go резервирует некоторые prefixes для documentation/testing scenarios:

- `test` — для локальных test modules;
- `example` — для examples в документации;
- `example.com` часто используется в примерах, имитирующих публикуемый module.

## Добавление dependency

После импорта package используйте `go get`:

```bash
go get .
```

или для конкретного module:

```bash
go get example.com/theirmodule
```

`go get` при необходимости:

- добавляет `require` directives в `go.mod`;
- выбирает необходимую module version;
- скачивает module source через proxy или VCS;
- сохраняет содержимое в local module cache;
- аутентифицирует скачанный module.

Если опубликованное содержимое той же module version внезапно отличается от ранее зафиксированного checksum, Go tools выдают security error. Это защищает от изменения уже опубликованных versions.

## Получение конкретной version

Конкретная version:

```bash
go get example.com/theirmodule@v1.3.4
```

Latest:

```bash
go get example.com/theirmodule@latest
```

В `go.mod` это отражается, например, так:

```text
require example.com/theirmodule v1.3.4
```

Конкретная версия полезна для pre-release testing, rollback на известную рабочую version, upgrade и downgrade.

## Поиск доступных updates

Показать dependencies текущего module и доступные newer versions:

```bash
go list -m -u all
```

Для одного module:

```bash
go list -m -u example.com/theirmodule
```

После анализа available versions нужная version устанавливается через `go get module@version`.

## Upgrade и downgrade dependency

1. Определите доступные versions через `go list -m -u`.
2. Установите нужную через `go get module@version`.

Go пересчитывает module graph с учётом Minimal Version Selection и может скорректировать связанные requirements.

## Синхронизация dependencies

После серии изменений source/imports dependency declarations могут перестать точно соответствовать используемым packages. Для синхронизации применяйте:

```bash
go mod tidy
```

Команда:

- добавляет недостающие modules, необходимые imports/tests;
- удаляет requirements, которые больше не нужны;
- приводит `go.mod` и `go.sum` к согласованному состоянию.

`-v` выводит информацию об удаляемых modules.

## Разработка и тестирование против неопубликованного module

Dependency может ещё не быть опубликована либо вы можете тестировать локальный fix/fork.

### Локальный directory через `replace`

Пример `go.mod`:

```text
module example.com/mymodule

go 1.23.0

require example.com/theirmodule v0.0.0-unpublished

replace example.com/theirmodule v0.0.0-unpublished => ../theirmodule
```

Удобнее редактировать через Go tools:

```bash
go mod edit -replace=example.com/theirmodule@v0.0.0-unpublished=../theirmodule
go get example.com/theirmodule@v0.0.0-unpublished
```

> [!warning]
> При `replace` на локальный/forked source обычная authentication внешнего module не применяется так же, как при стандартной загрузке опубликованной version.

Начиная с Go 1.18 для одновременной разработки нескольких modules также существует workspace mode и `go.work`.

### Fork внешнего repository

Можно сохранить исходные import paths, но перенаправить module на fork:

```text
module example.com/mymodule

go 1.23.0

require example.com/theirmodule v1.2.3

replace example.com/theirmodule v1.2.3 => example.com/myfork/theirmodule v1.2.3-fixed
```

Определить текущую version и добавить replacement:

```text
$ go list -m example.com/theirmodule
example.com/theirmodule v1.2.3
$ go mod edit -replace=example.com/theirmodule@v1.2.3=example.com/myfork/theirmodule@v1.2.3-fixed
```

Imports в source code менять не нужно: `replace` изменяет resolution module source, а не logical package path.

## Конкретный commit или branch

`go get` может принимать repository identifier.

Commit:

```bash
go get example.com/theirmodule@4cf76c2
```

Branch:

```bash
go get example.com/theirmodule@bugfixes
```

Go записывает выбранный revision в `go.mod` как корректную pseudo-version.

## Удаление dependency

Удалить все неиспользуемые dependencies:

```bash
go mod tidy
```

Удалить конкретный module:

```bash
go get example.com/theirmodule@none
```

При удалении Go может также downgrade/remove dependencies, которые зависят от удаляемого module.

## Tool dependencies

В Go 1.24+ developer tools можно хранить как module dependencies через `tool` directive.

Добавить tool:

```bash
go get -tool golang.org/x/tools/cmd/stringer
```

После этого tool можно запускать:

```bash
go tool stringer
```

Если короткое имя неоднозначно либо конфликтует с встроенным tool, используйте полный package path:

```bash
go tool golang.org/x/tools/cmd/stringer
```

Список доступных tools:

```bash
go tool
```

Если `tool` directive добавлен вручную, module, содержащий tool, также должен присутствовать в `require`. Самый простой способ восстановить requirements:

```bash
go mod tidy
```

Tool dependencies входят в обычный module graph, участвуют в Minimal Version Selection и учитывают `require`, `replace`, `exclude`.

Meta-pattern `tool` позволяет применять команды ко всем tools:

```bash
go get tool
go install tool
```

До Go 1.24 аналогичный эффект обычно реализовывали через blank import в excluded-by-build-constraint `.go` file и запускали tool через `go run full/package/path`.

## Module proxy

По умолчанию Go tools используют public proxy и затем direct VCS access:

```text
GOPROXY="https://proxy.golang.org,direct"
```

Другой proxy задаётся через `GOPROXY`.

### Разница `,` и `|`

Comma означает переход к следующему proxy только при HTTP `404` или `410`:

```text
GOPROXY="https://proxy.example.com,https://proxy2.example.com"
```

Pipe означает переход к следующему URL независимо от HTTP error code:

```text
GOPROXY="https://proxy.example.com|https://proxy2.example.com"
```

Это важная разница для security/policy: comma позволяет первому proxy блокировать module ошибкой, отличной от `404/410`; pipe разрешает fallback и при других ошибках.

## Private modules

Для modules, которые не должны запрашиваться через public proxy/checksum infrastructure, настраивается `GOPRIVATE` и при необходимости `GONOPROXY`/`GONOSUMDB`.

Пример:

```text
GOPRIVATE=*.corp.example.com,*.research.example.com
```

Значения представляют собой comma-separated glob patterns module path prefixes. Это позволяет `go` command обращаться к private sources согласно локальной конфигурации, не отправляя private module paths в public proxy.
