---
title: "Случайное приветствие и slices"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/random-greeting.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Случайное приветствие

Теперь `Hello` будет выбирать один из нескольких templates. Для хранения templates используется **slice** — динамическое представление последовательности поверх array storage.

```go
package greetings

import (
    "errors"
    "fmt"
    "math/rand"
)

func Hello(name string) (string, error) {
    if name == "" {
        return name, errors.New("empty name")
    }

    message := fmt.Sprintf(randomFormat(), name)
    return message, nil
}

func randomFormat() string {
    formats := []string{
        "Hi, %v. Welcome!",
        "Great to see you, %v!",
        "Hail, %v! Well met!",
    }

    return formats[rand.Intn(len(formats))]
}
```

Ключевые детали:

- `[]string{...}` — slice literal;
- `len(formats)` возвращает текущую length;
- `rand.Intn(n)` выбирает index `[0,n)`;
- `randomFormat` начинается с lowercase, поэтому не exported за пределы package;
- `Hello` переиспользует returned format.

Caller снова передаёт normal name:

```go
message, err := greetings.Hello("Gladys")
```

Повторные запуски возвращают разные templates.

Следующий шаг — [[greetings-multiple-people|map и несколько пользователей]].
