---
title: "Начало работы с Go"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/getting-started.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Начало работы с Go

Это краткое введение в программирование на Go. По ходу руководства вы:

- установите Go, если ещё этого не сделали;
- напишете простой `Hello, World`;
- запустите код через команду `go`;
- воспользуетесь поиском пакетов Go;
- вызовете функцию из внешнего модуля.

## Предварительные требования

- **Базовый опыт программирования.** Код простой, но полезно понимать, что такое функции.
- **Редактор кода.** Подойдёт любой текстовый редактор. Популярные варианты с хорошей поддержкой Go: VS Code, GoLand и Vim.
- **Терминал.** В Linux и macOS можно использовать любой terminal; в Windows — PowerShell или `cmd`.

## Установите Go

Следуйте инструкции [[install|Скачивание и установка Go]].

## Напишите код

Начнём с Hello, World.

1. Откройте terminal и перейдите в домашний каталог.

Linux/macOS:

```bash
cd
```

Windows:

```text
cd %HOMEPATH%
```

2. Создайте каталог `hello` для первого Go-кода:

```bash
mkdir hello
cd hello
```

3. Включите отслеживание зависимостей.

Если код импортирует packages из других modules, зависимости управляются через модуль вашего проекта. Модуль определяется файлом `go.mod`, который хранит список modules, предоставляющих импортируемые packages. `go.mod` является частью исходного кода и обычно коммитится в репозиторий.

Создайте `go.mod` командой `go mod init`, передав module path. В реальном проекте module path обычно совпадает с адресом репозитория, например `github.com/mymodule`. Если модуль будет опубликован, его path должен указывать на место, откуда Go tools способны скачать модуль.

Для этого tutorial используйте `example/hello`:

```text
$ go mod init example/hello
go: creating new go.mod: module example/hello
```

4. Создайте файл `hello.go`.

5. Вставьте и сохраните следующий код:

```go
package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}
```

Что здесь происходит:

- объявляется package `main`; package объединяет функции и другие declarations из файлов одного каталога;
- импортируется стандартный package `fmt`, содержащий функции форматирования и вывода текста;
- определяется функция `main`, которая выполняется при запуске package `main`.

6. Запустите программу:

```text
$ go run .
Hello, World!
```

`go run` — одна из команд Go toolchain. Полный список команд:

```bash
go help
```

## Вызов кода из внешнего package

Если нужная функциональность уже реализована кем-то другим, можно найти package с подходящим API и импортировать его.

1. Откройте [pkg.go.dev](https://pkg.go.dev/) и найдите package по запросу `quote`.
2. В результатах найдите v1 package `rsc.io/quote`.
3. В разделе Documentation найдите список доступных функций; в tutorial используется `Go`.
4. Обратите внимание: package `quote` входит в module `rsc.io/quote`.

`pkg.go.dev` позволяет искать опубликованные modules и packages. Modules получают новые версии, а проект может обновлять используемую версию зависимости.

Добавьте import и вызов функции:

```go
package main

import "fmt"
import "rsc.io/quote"

func main() {
    fmt.Println(quote.Go())
}
```

Затем добавьте необходимые module requirements и checksums:

```text
$ go mod tidy
go: finding module for package rsc.io/quote
go: found rsc.io/quote in rsc.io/quote v1.5.2
```

Go добавит module `rsc.io/quote` в зависимости и создаст/обновит `go.sum`, используемый для аутентификации содержимого модулей.

Запустите код:

```text
$ go run .
Don't communicate by sharing memory, share memory by communicating.
```

При выполнении `go mod tidy` Go нашёл и скачал module `rsc.io/quote`, содержащий импортированный package. В примере используется версия `v1.5.2`.

## Что дальше

Теперь Go установлен, создан первый module и использована внешняя зависимость. Следующий шаг — [[tutorial/create-module|Create a Go module]], где разбирается создание собственного reusable module.
