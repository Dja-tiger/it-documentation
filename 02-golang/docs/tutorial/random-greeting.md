---
title: "Tutorial: случайное приветствие"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/random-greeting.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Возврат случайного приветствия

На этом этапе измените code так, чтобы вместо одного и того же greeting function возвращала одно из нескольких заранее определённых messages.

> [!note]
> Эта страница является частью многошагового tutorial, начинающегося с [[create-module|Создание Go module]].

Для этого используется Go **slice**. Slice похож на array, но его размер может динамически изменяться по мере добавления и удаления elements. Slice — один из наиболее полезных types Go.

Добавьте небольшой slice из трёх greeting formats и возвращайте один из них случайным образом. Подробнее о slices см. [Go slices](https://go.dev/blog/slices-intro) в Go blog.

1. Измените `greetings/greetings.go`:

   ```go
   package greetings

   import (
       "errors"
       "fmt"
       "math/rand"
   )

   // Hello returns a greeting for the named person.
   func Hello(name string) (string, error) {
       // If no name was given, return an error with a message.
       if name == "" {
           return name, errors.New("empty name")
       }
       // Create a message using a random format.
       message := fmt.Sprintf(randomFormat(), name)
       return message, nil
   }

   // randomFormat returns one of a set of greeting messages. The returned
   // message is selected at random.
   func randomFormat() string {
       // A slice of message formats.
       formats := []string{
           "Hi, %v. Welcome!",
           "Great to see you, %v!",
           "Hail, %v! Well met!",
       }

       // Return a randomly selected message format by specifying
       // a random index for the slice of formats.
       return formats[rand.Intn(len(formats))]
   }
   ```

В этом коде:

- добавляется function `randomFormat`, возвращающая случайно выбранный greeting format;
- имя `randomFormat` начинается со строчной буквы, поэтому function доступна только внутри своего package — она не exported;
- в `randomFormat` объявляется slice `formats` из трёх strings;
- при declaration slice размер внутри brackets не указывается: `[]string`. Это отличает slice от array и позволяет underlying storage работать с динамически изменяемой длиной;
- package [`math/rand`](https://pkg.go.dev/math/rand/) используется для получения случайного index;
- `Hello` вызывает `randomFormat`, а затем `fmt.Sprintf` подставляет `name` в выбранный format;
- function по-прежнему возвращает либо message + `nil`, либо error.

2. Измените `hello/hello.go`, снова передав непустое имя:

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
       message, err := greetings.Hello("Gladys")
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

3. Запустите application несколько раз и обратите внимание, что greeting меняется:

   ```text
   $ go run .
   Great to see you, Gladys!

   $ go run .
   Hi, Gladys. Welcome!

   $ go run .
   Hail, Gladys! Well met!
   ```

Следующий шаг — [[greetings-multiple-people|использование slice и map для greetings нескольких людей]].
