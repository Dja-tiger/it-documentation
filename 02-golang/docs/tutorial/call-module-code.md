---
title: "Tutorial: вызов кода из другого module"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/call-module-code.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Вызов кода из другого module

В [[create-module|предыдущем разделе]] вы создали module `greetings`. Теперь напишите executable application, которая вызывает function `Hello` из этого module.

> [!note]
> Эта страница является частью многошагового tutorial, начинающегося с [[create-module|Создание Go module]].

1. Создайте directory `hello` для source code caller module.

   После этого `hello` и `greetings` должны находиться на одном уровне:

   ```text
   <home>/
    |-- greetings/
    |-- hello/
   ```

   Если terminal сейчас находится в `greetings`:

   ```bash
   cd ..
   mkdir hello
   cd hello
   ```

2. Включите dependency tracking для нового кода.

   Выполните [`go mod init`](https://go.dev/ref/mod#go-mod-init), передав module path нового module. В tutorial используется `example.com/hello`:

   ```text
   $ go mod init example.com/hello
   go: creating new go.mod: module example.com/hello
   ```

3. В directory `hello` создайте file `hello.go`.

4. Напишите код, который вызывает `Hello` и печатает возвращённое значение:

   ```go
   package main

   import (
       "fmt"

       "example.com/greetings"
   )

   func main() {
       // Get a greeting message and print it.
       message := greetings.Hello("Gladys")
       fmt.Println(message)
   }
   ```

В этом коде:

- объявляется package `main`. В Go executable application должна находиться в `main` package;
- импортируются `example.com/greetings` и стандартный package [`fmt`](https://pkg.go.dev/fmt/). Импорт `greetings` даёт доступ к созданной ранее function `Hello`, а `fmt` предоставляет text input/output functions;
- вызывается `greetings.Hello`, а returned greeting сохраняется и печатается.

5. Настройте `example.com/hello` так, чтобы он использовал локальный `example.com/greetings`.

В production module `example.com/greetings` был бы опубликован из repository с реальным module path, по которому Go tools могли бы скачать его. Но сейчас module ещё не опубликован, поэтому `hello` должен быть перенаправлен с module path на local directory.

Для этого используйте [`go mod edit`](https://go.dev/ref/mod#go-mod-edit):

```bash
go mod edit -replace example.com/greetings=../greetings
```

Эта команда говорит Go tools заменять dependency `example.com/greetings` локальным directory `../greetings`.

После выполнения `go.mod` в `hello` должен содержать [`replace` directive](../modules/gomod-ref.md#replace):

```text
module example.com/hello

go 1.16

replace example.com/greetings => ../greetings
```

Теперь выполните [`go mod tidy`](https://go.dev/ref/mod#go-mod-tidy), чтобы синхронизировать dependencies module с imports исходного кода:

```text
$ go mod tidy
go: found example.com/greetings in example.com/greetings v0.0.0-00010101000000-000000000000
```

После этого `go.mod` должен выглядеть так:

```text
module example.com/hello

go 1.16

replace example.com/greetings => ../greetings

require example.com/greetings v0.0.0-00010101000000-000000000000
```

Команда нашла локальный code в `greetings` и добавила [`require` directive](../modules/gomod-ref.md#require), потому что `hello.go` импортирует package `greetings`.

Число после module path — **pseudo-version**: сгенерированная version, используемая вместо semantic version, которой у локального unpublished module пока нет.

Для опубликованного module `go.mod` обычно не содержит `replace`, а `require` указывает tagged version, например:

```text
require example.com/greetings v1.1.0
```

Подробнее о versions см. [[../modules/version-numbers|Нумерация versions module]].

6. Находясь в directory `hello`, запустите application:

```text
$ go run .
Hi, Gladys. Welcome!
```

Теперь у вас два работающих modules.

Следующий шаг — [[handle-errors|возврат и обработка error]].
