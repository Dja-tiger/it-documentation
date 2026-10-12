---
title: "Tutorial: приветствия для нескольких людей"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/greetings-multiple-people.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Возврат приветствий для нескольких людей

В последних изменениях business code module добавьте возможность получать greetings сразу для нескольких людей одним request. Нужно принять multi-value input и сопоставить каждому входному value соответствующее output value.

> [!note]
> Эта страница является частью многошагового tutorial, начинающегося с [[create-module|Создание Go module]].

Есть важная проблема: если изменить parameter существующей function `Hello` с одного имени на набор имён, изменится function signature. Если `example.com/greetings` уже опубликован и users уже написали код, вызывающий `Hello`, такое изменение сломает их programs.

Поэтому лучше создать **новую** function с другим именем, которая принимает несколько values, сохранив старую `Hello` ради backward compatibility.

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

// Hellos returns a map that associates each of the named people
// with a greeting message.
func Hellos(names []string) (map[string]string, error) {
    // A map to associate names with messages.
    messages := make(map[string]string)
    // Loop through the received slice of names, calling
    // the Hello function to get a message for each name.
    for _, name := range names {
        message, err := Hello(name)
        if err != nil {
            return nil, err
        }
        // In the map, associate the retrieved message with
        // the name.
        messages[name] = message
    }
    return messages, nil
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

    // Return one of the message formats selected at random.
    return formats[rand.Intn(len(formats))]
}
```

В этом коде:

- добавляется function `Hellos`, принимающая slice имён вместо одного name;
- один из return types новой function — `map[string]string`, чтобы вернуть соответствие name → greeting;
- `Hellos` повторно использует существующую `Hello`, уменьшая duplication и сохраняя обе APIs;
- `messages` создаётся как map через:

  ```go
  make(map[string]string)
  ```

  Общий синтаксис: `make(map[key-type]value-type)`. Подробнее см. [Go maps in action](https://go.dev/blog/maps);
- цикл `for ... range` проходит по `names`; `range` возвращает index и copy текущего value. Index не нужен, поэтому он игнорируется blank identifier `_`. Подробнее см. [[../effective-go#The blank identifier|Effective Go — blank identifier]];
- при error из `Hello` новая function немедленно возвращает `nil, err`;
- при успехе каждое greeting сохраняется в `messages[name]`.

2. В caller `hello/hello.go` передайте slice имён и напечатайте returned map:

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

    // A slice of names.
    names := []string{"Gladys", "Samantha", "Darrin"}

    // Request greeting messages for the names.
    messages, err := greetings.Hellos(names)
    if err != nil {
        log.Fatal(err)
    }
    // If no error was returned, print the returned map of
    // messages to the console.
    fmt.Println(messages)
}
```

Изменения:

- `names` объявляется как slice из трёх names;
- этот slice передаётся в `Hellos`;
- returned map печатается после проверки error.

3. Перейдите в directory с `hello/hello.go` и запустите:

```text
$ go run .
map[Darrin:Hail, Darrin! Well met! Gladys:Hi, Gladys. Welcome! Samantha:Hail, Samantha! Well met!]
```

Output представляет map, связывающий names с messages. Конкретные greetings могут отличаться из-за random selection.

Этот этап вводит `map` для name/value pairs и показывает принцип сохранения backward compatibility: новая или изменённая functionality добавляется через новую function, вместо breaking change существующей API.

Подробнее о compatibility см. [Keeping your modules compatible](https://go.dev/blog/module-compatibility).

Следующий шаг — [[add-a-test|unit test для кода]].
