---
title: "Начало работы с Go"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/getting-started.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Начало работы с Go

Этот tutorial даёт краткое введение в программирование на Go. По ходу работы вы:

- установите Go, если он ещё не установлен;
- напишете простой `Hello, World`;
- воспользуетесь командой `go`, чтобы запустить код;
- используете инструмент поиска Go packages, чтобы найти packages для собственного кода;
- вызовете functions из external module.

> [!note]
> Другие tutorials см. на [go.dev/doc/tutorial](https://go.dev/doc/tutorial/).

## Предварительные требования {#prerequisites}

- **Некоторый programming experience.** Код простой, но полезно понимать, что такое functions.
- **Редактор кода.** Подойдёт любой text editor. Популярные варианты с хорошей поддержкой Go — VS Code, GoLand и Vim.
- **Command terminal.** Go работает в обычных terminals Linux/macOS и в PowerShell/`cmd` Windows.

## Установите Go {#install}

Используйте шаги из [[install|Скачивание и установка Go]].

## Напишите код {#code}

Начните с Hello, World.

1. Откройте command prompt и перейдите в home directory.

   Linux/macOS:

   ```bash
   cd
   ```

   Windows:

   ```text
   cd %HOMEPATH%
   ```

2. Создайте directory `hello` для первого Go source code:

   ```bash
   mkdir hello
   cd hello
   ```

3. Включите dependency tracking.

   Когда code импортирует packages из других modules, dependencies управляются через собственный module проекта. Module определяется file `go.mod`, который отслеживает modules, предоставляющие импортируемые packages. `go.mod` хранится вместе с source code, в том числе в source repository.

   Чтобы создать `go.mod` и включить tracking, выполните [`go mod init`](https://go.dev/ref/mod#go-mod-init), передав module path.

   В реальном development module path обычно соответствует repository location source code, например:

   ```text
   github.com/mymodule
   ```

   Если module будет опубликован для других пользователей, module path **должен** указывать location, откуда Go tools смогут его скачать. Подробнее см. [[modules/managing-dependencies|Управление dependencies]].

   Для tutorial используйте `example/hello`:

   ```text
   $ go mod init example/hello
   go: creating new go.mod: module example/hello
   ```

4. Создайте file `hello.go`.

5. Добавьте код:

   ```go
   package main

   import "fmt"

   func main() {
       fmt.Println("Hello, World!")
   }
   ```

   В этом коде:

   - объявляется package `main`. Package группирует functions и другие declarations и состоит из files одного directory;
   - импортируется standard library package [`fmt`](https://pkg.go.dev/fmt/), содержащий functions форматирования текста и вывода, включая console output;
   - определяется function `main`, печатающая message. Function `main` выполняется по умолчанию при запуске package `main`.

6. Запустите code:

   ```text
   $ go run .
   Hello, World!
   ```

   [`go run`](https://pkg.go.dev/cmd/go#hdr-Compile_and_run_Go_program) — одна из команд Go toolchain. Список остальных:

   ```text
   $ go help
   ```

## Вызовите code из external package {#call}

Если нужная functionality уже реализована кем-то другим, можно найти package с подходящими functions и использовать его в своём code.

1. Сделайте output интереснее с помощью function из external module.

   1. Откройте [pkg.go.dev](https://pkg.go.dev/) и [найдите package по запросу `quote`](https://pkg.go.dev/search?q=quote).
   2. В search results найдите version v1 package `rsc.io/quote` — она может быть показана как другая major version относительно `rsc.io/quote/v4`.
   3. В section **Documentation**, под **Index**, посмотрите список доступных functions. В tutorial используется `Go`.
   4. В верхней части package page видно, что package `quote` входит в module `rsc.io/quote`.

   `pkg.go.dev` позволяет находить опубликованные modules и packages, functions которых можно использовать в собственном code. Packages публикуются внутри modules, например `rsc.io/quote`. Modules получают новые versions, и consumer code может обновляться на улучшенные versions.

2. Импортируйте `rsc.io/quote` и вызовите `Go`:

   ```go
   package main

   import "fmt"

   import "rsc.io/quote"

   func main() {
       fmt.Println(quote.Go())
   }
   ```

3. Добавьте новые module requirements и checksums:

   ```text
   $ go mod tidy
   go: finding module for package rsc.io/quote
   go: found rsc.io/quote in rsc.io/quote v1.5.2
   ```

   Go добавит module `quote` как requirement и создаст/обновит `go.sum`, используемый для authentication содержимого modules. Подробнее см. [Authenticating modules](https://go.dev/ref/mod#authenticating) в Go Modules Reference.

4. Запустите:

   ```text
   $ go run .
   Don't communicate by sharing memory, share memory by communicating.
   ```

   Code вызывает `quote.Go` и печатает message.

   Во время `go mod tidy` Go нашёл и скачал module `rsc.io/quote`, содержащий imported package. В tutorial используется version `v1.5.2`.

## Напишите больше code {#write-more}

После этого короткого introduction Go установлен, создан первый module, использована команда `go` и external dependency.

Следующий tutorial — [[tutorial/create-module|Создание Go module]].
