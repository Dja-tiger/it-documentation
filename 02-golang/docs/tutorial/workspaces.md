---
title: "Multi-module workspaces"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/workspaces.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Multi-module workspaces

Workspace mode позволяет Go command одновременно работать с несколькими local modules. Это удобно, когда изменение одного module нужно сразу тестировать в другом без временных `replace` directives в каждом `go.mod`.

## Первый module

```bash
mkdir workspace
cd workspace
mkdir hello
cd hello
go mod init example.com/hello
go get golang.org/x/example/hello/reverse
```

`hello.go`:

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

Проверка:

```text
$ go run .
olleH
```

## Создание workspace

Из родительского каталога:

```bash
go work init ./hello
```

Создаётся `go.work` примерно такого вида:

```text
go 1.18

use ./hello
```

- `go` задаёт Go version semantics workspace;
- `use` объявляет local modules, считающиеся main modules в workspace.

Теперь из workspace root:

```text
$ go run ./hello
olleH
```

## Добавление второго local module

Tutorial использует local clone `golang.org/x/example/hello`:

```bash
git clone https://go.googlesource.com/example
go work use ./example/hello
```

`go.work` становится:

```text
go 1.18

use (
    ./hello
    ./example/hello
)
```

Теперь imports `golang.org/x/example/hello/...` разрешаются в local workspace module, а не в previously downloaded module cache version.

## Изменение dependency module

В local `reverse` package добавим function:

```go
package reverse

import "strconv"

func Int(i int) int {
    i, _ = strconv.Atoi(String(strconv.Itoa(i)))
    return i
}
```

Caller:

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

Запуск:

```text
$ go run ./hello
olleH 10642
```

Workspace позволяет сразу видеть local change второго module.

## Workspace против `replace`

`go.work` может заменить временные `replace` directives, когда вы одновременно разрабатываете несколько modules.

При реальном release dependency module всё равно нужно опубликовать version и обновить normal `go.mod` requirement:

```bash
cd hello
go get golang.org/x/example/hello@v0.1.0
```

Вне workspace module должен быть разрешим обычным reproducible dependency mechanism.

## Основные `go work` commands

### Добавление/удаление modules

```bash
go work use ./module
```

`-r` рекурсивно ищет modules в subdirectories.

### Редактирование

```bash
go work edit
```

Аналогично `go mod edit`, но для `go.work`.

### Синхронизация

```bash
go work sync
```

Синхронизирует workspace build list с workspace modules.

Workspace — development configuration. Для опубликованных builds каждый module по-прежнему должен иметь корректный собственный `go.mod`.
