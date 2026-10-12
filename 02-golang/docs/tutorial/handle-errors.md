---
title: "Возврат и обработка ошибок"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/handle-errors.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Возврат и обработка error

В Go `error` обычно возвращается как обычное значение alongside результатом function.

Измените `greetings.Hello`:

```go
package greetings

import (
    "errors"
    "fmt"
)

func Hello(name string) (string, error) {
    if name == "" {
        return "", errors.New("empty name")
    }

    message := fmt.Sprintf("Hi, %v. Welcome!", name)
    return message, nil
}
```

Теперь function возвращает два значения: `string` и `error`.

- invalid input → empty result + non-nil error;
- success → result + `nil` error.

Caller:

```go
package main

import (
    "fmt"
    "log"

    "example.com/greetings"
)

func main() {
    log.SetPrefix("greetings: ")
    log.SetFlags(0)

    message, err := greetings.Hello("")
    if err != nil {
        log.Fatal(err)
    }

    fmt.Println(message)
}
```

Результат:

```text
$ go run .
greetings: empty name
exit status 1
```

Это базовый Go error-handling pattern: function возвращает error value, а caller явно проверяет `err != nil`.

Следующий шаг — [[random-greeting|slice и случайное приветствие]].
