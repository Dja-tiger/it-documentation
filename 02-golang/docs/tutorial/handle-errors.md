---
title: "Tutorial: возврат и обработка error"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/handle-errors.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Возврат и обработка error

Обработка errors — обязательная часть надёжного кода. На этом этапе module `greetings` начнёт возвращать error, а caller будет его обрабатывать.

> [!note]
> Эта страница является частью многошагового tutorial, начинающегося с [[create-module|Создание Go module]].

1. В `greetings/greetings.go` измените код следующим образом.

   Нет смысла возвращать greeting, если неизвестно, кого приветствовать. Если `name` пустой, function должна вернуть error.

   ```go
   package greetings

   import (
       "errors"
       "fmt"
   )

   // Hello returns a greeting for the named person.
   func Hello(name string) (string, error) {
       // If no name was given, return an error with a message.
       if name == "" {
           return "", errors.New("empty name")
       }

       // If a name was received, return a value that embeds the name
       // in a greeting message.
       message := fmt.Sprintf("Hi, %v. Welcome!", name)
       return message, nil
   }
   ```

Что изменилось:

- function теперь возвращает два values: `string` и `error`. Caller будет проверять второе value, чтобы определить, произошёл ли error. Go function может возвращать несколько values; подробнее см. [[../effective-go#Multiple return values|Effective Go]].
- импортирован standard package `errors`, чтобы использовать [`errors.New`](https://pkg.go.dev/errors/#example-New);
- `if` проверяет invalid request — пустую string вместо имени — и возвращает `error`, созданный `errors.New`;
- при successful execution вторым return value передаётся `nil`, означающий отсутствие error.

2. В `hello/hello.go` обработайте `error`, который теперь возвращает `Hello`.

   ```go
   package main

   import (
       "fmt"
       "log"

       "example.com/greetings"
   )

   func main() {
       // Set properties of the predefined Logger, including
       // the log entry prefix and a flag to disable printing
       // the time, source file, and line number.
       log.SetPrefix("greetings: ")
       log.SetFlags(0)

       // Request a greeting message.
       message, err := greetings.Hello("")
       // If an error was returned, print it to the console and
       // exit the program.
       if err != nil {
           log.Fatal(err)
       }

       // If no error was returned, print the returned message
       // to the console.
       fmt.Println(message)
   }
   ```

В этом коде:

- package [`log`](https://pkg.go.dev/log/) настраивается так, чтобы log messages начинались с `greetings: ` и не включали timestamp/source location;
- оба return values `Hello`, включая `error`, присваиваются variables;
- вместо имени Gladys передаётся empty string, чтобы проверить error path;
- code проверяет `err != nil`; продолжать normal execution при error нет смысла;
- при error вызывается [`log.Fatal`](https://pkg.go.dev/log#Fatal), которая печатает error и завершает program.

3. Находясь в directory `hello`, запустите application:

   ```text
   $ go run .
   greetings: empty name
   exit status 1
   ```

Поскольку сейчас передаётся empty name, ожидается error.

Это типичный подход Go к error handling: **error возвращается как обычное value, чтобы caller мог его проверить**.

Следующий шаг — [[random-greeting|использование slice для случайного greeting]].
