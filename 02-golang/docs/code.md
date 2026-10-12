---
title: "Как писать Go-код"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/code.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Как писать Go-код

## Введение {#Introduction}

Этот документ демонстрирует разработку простого Go package внутри module и знакомит с [`go` tool](https://go.dev/cmd/go/) — стандартным способом скачивать, собирать и устанавливать Go modules, packages и commands.

## Организация кода {#Organization}

Go-программы организованы в packages. **Package** — это набор source files в одном directory, которые компилируются вместе. Functions, types, variables и constants, объявленные в одном source file, видимы всем другим source files того же package.

Repository содержит один или несколько modules. **Module** — набор связанных Go packages, выпускаемых совместно. Обычно Go repository содержит один module в корне repository. File `go.mod` объявляет **module path** — prefix import path для всех packages module. Module включает packages из directory, содержащего `go.mod`, и его subdirectories до следующего вложенного directory с собственным `go.mod`, если такой есть.

Обратите внимание: публиковать code в remote repository до сборки не требуется. Module может быть определён локально и вообще не принадлежать repository. Тем не менее полезно организовывать code так, как будто однажды он будет опубликован.

Module path не только служит prefix для import paths packages, но и указывает команде `go`, где искать module для скачивания. Например, чтобы скачать module `golang.org/x/tools`, команда `go` обращается к repository, указанному через `https://golang.org/x/tools`.

**Import path** — строка, используемая для импорта package. Import path package состоит из module path и subdirectory package внутри module. Например, module `github.com/google/go-cmp` содержит package в directory `cmp/`; его import path — `github.com/google/go-cmp/cmp`. Packages стандартной библиотеки не имеют prefix module path.

## Первая программа {#Command}

Чтобы скомпилировать и запустить простую программу, сначала выберите module path. В примере используется `example/user/hello`. Затем создайте `go.mod`, объявляющий этот path:

```text
$ mkdir hello # Alternatively, clone it if it already exists in version control.
$ cd hello
$ go mod init example/user/hello
go: creating new go.mod: module example/user/hello
$ cat go.mod
module example/user/hello

go 1.16
$
```

Первым statement в Go source file должен быть `package name`. Executable commands всегда должны использовать `package main`.

Создайте внутри directory file `hello.go`:

```go
package main

import "fmt"

func main() {
    fmt.Println("Hello, world.")
}
```

Теперь программу можно собрать и установить с помощью `go` tool:

```text
$ go install example/user/hello
$
```

Команда собирает command `hello`, создавая executable binary, а затем устанавливает его как `$HOME/go/bin/hello` или, в Windows, `%USERPROFILE%\go\bin\hello.exe`.

Installation directory управляется environment variables `GOPATH` и `GOBIN`.

- Если задан `GOBIN`, binaries устанавливаются в этот directory.
- Если задан `GOPATH`, binaries устанавливаются в `bin` первого directory из списка `GOPATH`.
- Иначе binaries устанавливаются в `bin` default `GOPATH`: `$HOME/go` или `%USERPROFILE%\go`.

С помощью `go env` можно переносимо задать default value environment variable для будущих Go commands:

```text
$ go env -w GOBIN=/somewhere/else/bin
$
```

Чтобы удалить variable, ранее установленную через `go env -w`, используйте `go env -u`:

```text
$ go env -u GOBIN
$
```

Commands вроде `go install` выполняются в контексте module, содержащего current working directory. Если working directory не находится внутри module `example/user/hello`, `go install` может завершиться ошибкой.

Для удобства `go` commands принимают paths, относительные к working directory, а если path вообще не указан, по умолчанию используют package текущего working directory.

Поэтому в данном working directory следующие команды эквивалентны:

```text
$ go install example/user/hello
```

```text
$ go install .
```

```text
$ go install
```

Теперь запустим программу и убедимся, что она работает. Для удобства добавим installation directory в `PATH`:

```text
# Windows users should consult /wiki/SettingGOPATH
# for setting %PATH%.
$ export PATH=$PATH:$(dirname $(go list -f '{{.Target}}' .))
$ hello
Hello, world.
$
```

Если вы используете source control system, сейчас удобно инициализировать repository, добавить files и сделать первый commit. Этот шаг необязателен: source control не требуется для написания Go code.

```text
$ git init
Initialized empty Git repository in /home/user/hello/.git/
$ git add go.mod hello.go
$ git commit -m "initial commit"
[master (root-commit) 0b4507d] initial commit
 1 file changed, 7 insertion(+)
 create mode 100644 go.mod hello.go
$
```

Команда `go` определяет repository, содержащий заданный module path, отправляя request на соответствующий HTTPS URL и читая metadata из HTML response. Многие hosting services уже публикуют такую metadata для repositories с Go code, поэтому обычно проще всего сделать module path совпадающим с URL repository.

### Импорт packages из своего module {#ImportingLocal}

Создадим package `morestrings` и используем его из программы `hello`.

Сначала создайте directory `$HOME/hello/morestrings`, затем file `reverse.go`:

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

Поскольку function `ReverseRunes` начинается с uppercase letter, она **exported** и может использоваться другими packages, которые импортируют `morestrings`.

Проверим, что package компилируется:

```text
$ cd $HOME/hello/morestrings
$ go build
$
```

Output file не создаётся. Вместо этого compiled package сохраняется в local build cache.

После проверки измените исходный `$HOME/hello/hello.go`, чтобы использовать package `morestrings`:

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

Установите программу `hello`:

```text
$ go install example/user/hello
```

Запустив новую version, вы увидите перевёрнутое сообщение:

```text
$ hello
Hello, Go!
```

### Импорт packages из remote modules {#ImportingRemote}

Import path может описывать способ получения source code package через revision control system, например Git или Mercurial. `go` tool использует это свойство для автоматического скачивания packages из remote repositories.

Например, добавим `github.com/google/go-cmp/cmp`:

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

Теперь программа зависит от external module. Его нужно скачать и записать version в `go.mod`.

Команда `go mod tidy` добавляет отсутствующие module requirements для imported packages и удаляет requirements modules, которые больше не используются:

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
$ cat go.mod
module example/user/hello

go 1.16

require github.com/google/go-cmp v0.5.4
$
```

Module dependencies автоматически скачиваются в subdirectory `pkg/mod` directory, заданного environment variable `GOPATH`.

Скачанное содержимое конкретной version module совместно используется всеми локальными modules, которые требуют эту version, поэтому команда `go` делает эти files и directories read-only.

Чтобы удалить все скачанные modules, передайте `-modcache` команде `go clean`:

```text
$ go clean -modcache
$
```

## Тестирование {#Testing}

Go содержит лёгкий test framework, состоящий из команды `go test` и package `testing`.

Test создаётся в file с именем, заканчивающимся на `_test.go`, и содержит functions `TestXXX` с signature:

```go
func TestXXX(t *testing.T)
```

Test framework запускает каждую такую function. Если function вызывает failure function вроде `t.Error` или `t.Fail`, test считается failed.

Добавьте test в package `morestrings`, создав `$HOME/hello/morestrings/reverse_test.go`:

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

Запустите test:

```text
$ cd $HOME/hello/morestrings
$ go test
PASS
ok  	example/user/hello/morestrings 0.165s
$
```

Для дополнительных подробностей выполните:

```text
go help test
```

и обратитесь к [документации package `testing`](https://pkg.go.dev/testing/).

## Что дальше {#next}

Подпишитесь на mailing list [golang-announce](https://groups.google.com/group/golang-announce), чтобы получать уведомления о новых stable versions Go.

См. [[effective-go|Effective Go]] — советы по написанию ясного и идиоматичного Go code.

Пройдите [A Tour of Go](https://go.dev/tour/), чтобы познакомиться с самим языком.

Посетите [страницу документации Go](https://go.dev/doc/#articles), где собраны подробные статьи о языке Go, libraries и tools.

## Получение помощи {#help}

Для помощи в real time можно обратиться к участникам community-run [Gophers Slack](https://gophers.slack.com/messages/general/). Получить приглашение можно через [invite.slack.golangbridge.org](https://invite.slack.golangbridge.org/).

Официальный mailing list для обсуждения языка Go — [Go Nuts](https://groups.google.com/group/golang-nuts).

Сообщать об ошибках следует через [Go issue tracker](https://go.dev/issue).
