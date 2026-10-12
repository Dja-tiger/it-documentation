---
title: "Как писать Go-код"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/code.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Как писать Go-код

## Введение

Этот документ показывает разработку простого Go package внутри module и знакомит с `go` tool — стандартным способом скачивать, собирать и устанавливать Go modules, packages и commands.

## Организация кода

Go-программы организованы в packages. **Package** — это набор source-файлов в одном каталоге, которые компилируются вместе. Functions, types, variables и constants, объявленные в одном source-файле, доступны всем другим source-файлам того же package.

Repository содержит один или несколько modules. **Module** — набор связанных Go packages, выпускаемых совместно. Обычно Go repository содержит один module в корне repository. Файл `go.mod` объявляет **module path** — префикс import path для всех packages этого module. Module включает packages из каталога с `go.mod` и его подкаталогов до следующего вложенного каталога с собственным `go.mod`.

Публиковать код в remote repository до сборки не требуется. Module может существовать только локально. Тем не менее полезно изначально организовывать код так, как будто он позже будет опубликован.

Module path одновременно служит префиксом import path и подсказывает команде `go`, откуда скачать module. Например, для `golang.org/x/tools` Go tools находят repository, связанный с этим path.

**Import path** — строка, используемая для импорта package. Import path package состоит из module path и относительного подкаталога package внутри module. Например, module `github.com/google/go-cmp` содержит package в каталоге `cmp/`; его import path — `github.com/google/go-cmp/cmp`. Packages стандартной библиотеки не имеют префикса module path.

## Первая программа

Выберите module path. В примере используется `example/user/hello`, затем создайте `go.mod`:

```text
$ mkdir hello
$ cd hello
$ go mod init example/user/hello
go: creating new go.mod: module example/user/hello
$ cat go.mod
module example/user/hello

go 1.16
```

Первое statement в Go source file — `package name`. Исполняемые commands всегда используют `package main`.

Создайте `hello.go`:

```go
package main

import "fmt"

func main() {
    fmt.Println("Hello, world.")
}
```

Соберите и установите программу:

```bash
go install example/user/hello
```

Команда собирает executable `hello` и устанавливает его в `$HOME/go/bin/hello`, а в Windows — `%USERPROFILE%\go\bin\hello.exe`.

Installation directory управляется переменными `GOPATH` и `GOBIN`. Если задан `GOBIN`, binaries устанавливаются туда. Если задан `GOPATH`, используется `bin` первого каталога из списка `GOPATH`. Иначе используется `bin` стандартного `GOPATH`: `$HOME/go` или `%USERPROFILE%\go`.

Значение environment variable для будущих Go commands можно задать переносимым способом:

```bash
go env -w GOBIN=/somewhere/else/bin
```

Удалить настройку, ранее заданную через `go env -w`:

```bash
go env -u GOBIN
```

Commands вроде `go install` выполняются в контексте module, содержащего текущий working directory. Если working directory находится вне `example/user/hello`, установка может завершиться ошибкой.

Внутри module относительные пути поддерживаются, а при отсутствии path команда по умолчанию работает с package текущего каталога. Поэтому здесь эквивалентны:

```bash
go install example/user/hello
go install .
go install
```

Чтобы запускать установленный binary без полного path, добавьте installation directory в `PATH`. Например:

```bash
export PATH=$PATH:$(dirname $(go list -f '{{.Target}}' .))
hello
```

Результат:

```text
Hello, world.
```

Если используется version control, сейчас удобно инициализировать repository и сохранить первый commit:

```text
$ git init
$ git add go.mod hello.go
$ git commit -m "initial commit"
```

Команда `go` определяет repository для module path через соответствующий HTTPS URL и metadata в HTML response. Многие hosting services уже публикуют такую metadata, поэтому обычно проще всего делать module path совпадающим с URL repository.

### Импорт packages из собственного module

Создадим package `morestrings`. Создайте каталог `$HOME/hello/morestrings` и файл `reverse.go`:

```go
// Package morestrings implements additional functions to manipulate UTF-8
// encoded strings, beyond what is provided in the standard "strings" package.
package morestrings

// ReverseRunes returns its argument string reversed rune-wise left to right.
func ReverseRunes(s string) string {
    r := []rune(s)
    for i, j := 0, len(r)-1; i < len(r)/2; i, j = i+1, j-1 {
        r[i], r[j] = r[j], r[i]
    }
    return string(r)
}
```

Имя `ReverseRunes` начинается с заглавной буквы, поэтому identifier **exported** и доступен другим packages, которые импортируют `morestrings`.

Проверьте компиляцию:

```bash
cd $HOME/hello/morestrings
go build
```

Отдельный output-файл не создаётся: compiled package сохраняется в local build cache.

Измените `$HOME/hello/hello.go`:

```go
package main

import (
    "fmt"

    "example/user/hello/morestrings"
)

func main() {
    fmt.Println(morestrings.ReverseRunes("!oG ,olleH"))
}
```

Установите command:

```bash
go install example/user/hello
```

Запустите:

```text
$ hello
Hello, Go!
```

### Импорт packages из remote modules

Import path может описывать location исходного кода в Git или другой VCS. `go` tool использует это для автоматического скачивания packages из remote repositories.

Добавим `github.com/google/go-cmp/cmp`:

```go
package main

import (
    "fmt"

    "example/user/hello/morestrings"
    "github.com/google/go-cmp/cmp"
)

func main() {
    fmt.Println(morestrings.ReverseRunes("!oG ,olleH"))
    fmt.Println(cmp.Diff("Hello World", "Hello Go"))
}
```

Теперь есть зависимость от внешнего module. `go mod tidy` добавляет отсутствующие requirements для импортируемых packages и удаляет requirements, которые больше не используются:

```text
$ go mod tidy
go: finding module for package github.com/google/go-cmp/cmp
go: found github.com/google/go-cmp/cmp in github.com/google/go-cmp v0.5.4
$ go install example/user/hello
$ hello
Hello, Go!
  string(
-     "Hello World",
+     "Hello Go",
  )
```

`go.mod` будет содержать requirement:

```text
require github.com/google/go-cmp v0.5.4
```

Module dependencies автоматически скачиваются в `pkg/mod` внутри каталога `GOPATH`. Одна скачанная версия module используется совместно всеми локальными modules, которым она нужна. Файлы module cache делаются read-only.

Очистить весь module cache:

```bash
go clean -modcache
```

## Тестирование

В Go есть лёгкий test framework, состоящий из команды `go test` и package `testing`.

Тесты размещаются в файлах `*_test.go`. Test functions имеют имена `TestXXX` и сигнатуру:

```go
func TestXXX(t *testing.T)
```

Framework запускает такие функции. Если test вызывает `t.Error`, `t.Fail` или другую failure-функцию, тест считается проваленным.

Создайте `$HOME/hello/morestrings/reverse_test.go`:

```go
package morestrings

import "testing"

func TestReverseRunes(t *testing.T) {
    cases := []struct {
        in, want string
    }{
        {"Hello, world", "dlrow ,olleH"},
        {"Hello, 世界", "界世 ,olleH"},
        {"", ""},
    }
    for _, c := range cases {
        got := ReverseRunes(c.in)
        if got != c.want {
            t.Errorf("ReverseRunes(%q) == %q, want %q", c.in, got, c.want)
        }
    }
}
```

Запустите тесты:

```text
$ cd $HOME/hello/morestrings
$ go test
PASS
ok      example/user/hello/morestrings 0.165s
```

Дополнительная справка:

```bash
go help test
```

## Что дальше

- [[effective-go|Effective Go]] — рекомендации по ясному и идиоматичному Go-коду;
- [A Tour of Go](https://go.dev/tour/) — интерактивное знакомство с языком;
- [Go documentation](https://go.dev/doc/) — официальные статьи о языке, библиотеках и инструментах.

## Получение помощи

Для обсуждения Go доступны community Slack и mailing list Go Nuts. Ошибки самого Go следует отправлять в официальный Go issue tracker.
