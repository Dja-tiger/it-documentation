---
title: "Tutorial: начало работы с multi-module workspaces"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/workspaces.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Начало работы с multi-module workspaces

Этот tutorial знакомит с основами multi-module workspaces в Go.

Workspace позволяет сообщить команде `go`, что вы одновременно разрабатываете код в нескольких modules, и удобно собирать и запускать код этих modules вместе.

В tutorial вы:

- создадите два modules в общем multi-module workspace;
- внесёте изменения в оба modules;
- увидите результат этих изменений при build.

> [!note]
> Другие tutorials см. на [go.dev/doc/tutorial](https://go.dev/doc/tutorial/).

## Предварительные требования

- **Go.** Рекомендуется актуальная версия Go. Установка описана в [[../install|Установка Go]].
- **Редактор.** Подойдёт любой text editor.
- **Terminal.** Подойдёт terminal Linux/macOS либо PowerShell/`cmd` в Windows.

## Создайте module для своего кода {#create_folder}

1. Перейдите в home directory.

Linux/macOS:

```text
$ cd
```

Windows:

```text
C:\> cd %HOMEPATH%
```

Далее prompt в примерах показывается как `$`; команды также работают в Windows.

2. Создайте directory `workspace`:

```bash
mkdir workspace
cd workspace
```

3. Инициализируйте module.

В примере создаётся module `hello`, зависящий от module `golang.org/x/example`.

Создайте `hello`:

```text
$ mkdir hello
$ cd hello
$ go mod init example.com/hello
go: creating new go.mod: module example.com/hello
```

Добавьте dependency на package `golang.org/x/example/hello/reverse` через `go get`:

```bash
go get golang.org/x/example/hello/reverse
```

Создайте `hello.go`:

```go
package main

import (
    "fmt"

    "golang.org/x/example/hello/reverse"
)

func main() {
    fmt.Println(reverse.String("Hello"))
}
```

Запустите:

```text
$ go run .
olleH
```

## Создайте workspace

Теперь создайте `go.work`, описывающий workspace с module.

#### Инициализируйте workspace

В directory `workspace` выполните:

```bash
go work init ./hello
```

`go work init` создаёт `go.work` для workspace, включающего module из `./hello`.

Полученный file выглядит так:

```text
go 1.18

use ./hello
```

Syntax `go.work` похож на `go.mod`.

Directive `go` указывает Go version, в semantics которой должен интерпретироваться file. Он аналогичен `go` directive в `go.mod`.

Directive `use` говорит Go, что module в directory `hello` должен рассматриваться как main module при build.

Следовательно, в любом subdirectory `workspace` этот module будет active.

#### Запустите program из workspace directory

```text
$ go run ./hello
olleH
```

Команда `go` включает все modules workspace как main modules. Благодаря этому можно ссылаться на package module даже находясь вне его directory.

Запуск аналогичной команды вне module и вне workspace завершился бы error, потому что команда `go` не знала бы, какие modules использовать.

Далее добавьте локальную копию module `golang.org/x/example/hello` в workspace. Этот module находится в subdirectory Git repository `go.googlesource.com/example`. После этого добавьте новую function в package `reverse` и используйте её вместо `String`.

## Скачайте и измените module `golang.org/x/example/hello`

На этом шаге:

- clone'ируется Git repository, содержащий `golang.org/x/example/hello`;
- module добавляется в workspace;
- в него добавляется новая function;
- новая function используется из program `hello`.

1. Clone repository из workspace directory:

```text
$ git clone https://go.googlesource.com/example
Cloning into 'example'...
remote: Total 165 (delta 27), reused 165 (delta 27)
Receiving objects: 100% (165/165), 434.18 KiB | 1022.00 KiB/s, done.
Resolving deltas: 100% (27/27), done.
```

2. Добавьте module в workspace.

Repository находится в `./example`, а source module `golang.org/x/example/hello` — в `./example/hello`.

```bash
go work use ./example/hello
```

`go work use` добавляет новый module в `go.work`, который теперь выглядит так:

```text
go 1.18

use (
    ./hello
    ./example/hello
)
```

Workspace содержит два modules:

- `example.com/hello`;
- `golang.org/x/example/hello`, предоставляющий package `golang.org/x/example/hello/reverse`.

Теперь application использует код из вашей local copy `reverse`, а не version из module cache, ранее скачанную через `go get`.

3. Добавьте новую function, разворачивающую integer.

Создайте `workspace/example/hello/reverse/int.go`:

```go
package reverse

import "strconv"

// Int returns the decimal reversal of the integer i.
func Int(i int) int {
    i, _ = strconv.Atoi(String(strconv.Itoa(i)))
    return i
}
```

4. Измените `workspace/hello/hello.go`:

```go
package main

import (
    "fmt"

    "golang.org/x/example/hello/reverse"
)

func main() {
    fmt.Println(reverse.String("Hello"), reverse.Int(24601))
}
```

#### Запустите code в workspace

Из directory `workspace`:

```text
$ go run ./hello
olleH 10642
```

Команда `go` находит module `example.com/hello`, указанный command line argument, в directory `hello` из `go.work`, и аналогично разрешает import `golang.org/x/example/hello/reverse` через workspace.

`go.work` можно использовать вместо [`replace` directives](https://go.dev/ref/mod#go-mod-file-replace), когда разработка ведётся сразу в нескольких modules.

Поскольку оба modules находятся в одном workspace, изменения одного module сразу доступны другому.

#### Следующий шаг в реальной разработке

Для правильного release этих modules потребовалось бы опубликовать version `golang.org/x/example/hello`, например `v0.1.0`. Обычно это выполняется созданием tag на commit в version control repository.

Подробнее см. [[../modules/release-workflow|Module release workflow]].

После release requirement в `hello/go.mod` можно обновить:

```bash
cd hello
go get golang.org/x/example/hello@v0.1.0
```

После этого команда `go` сможет корректно разрешать module и вне workspace.

## Подробнее о workspaces

Кроме `go work init`, команда `go` предоставляет дополнительные workspace subcommands:

- `go work use [-r] [dir]` добавляет `use` directive для `dir`, если directory существует, и удаляет `use`, если указанный directory отсутствует. Flag `-r` recursively просматривает subdirectories `dir`;
- `go work edit` изменяет `go.work` аналогично `go mod edit`;
- `go work sync` синхронизирует dependencies из workspace build list в modules workspace.

Подробный reference см. в [Go Modules Reference — Workspaces](https://go.dev/ref/mod#workspaces).
