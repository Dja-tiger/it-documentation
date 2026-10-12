---
title: "Tutorial: добавление test"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/add-a-test.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Добавление test

Теперь код достиг достаточно стабильного состояния, поэтому добавьте test. Testing во время development помогает обнаруживать bugs, которые появляются при последующих изменениях. На этом этапе вы добавите tests для function `Hello`.

> [!note]
> Эта страница является частью многошагового tutorial, начинающегося с [[create-module|Создание Go module]].

Встроенная unit testing support Go позволяет быстро писать и запускать tests через naming conventions, package `testing` и command `go test`.

1. В directory `greetings` создайте file `greetings_test.go`.

   Суффикс `_test.go` сообщает команде `go test`, что file содержит test functions.

2. Вставьте следующий код:

```go
package greetings

import (
    "testing"
    "regexp"
)

// TestHelloName calls greetings.Hello with a name, checking
// for a valid return value.
func TestHelloName(t *testing.T) {
    name := "Gladys"
    want := regexp.MustCompile(`\b`+name+`\b`)
    msg, err := Hello("Gladys")
    if !want.MatchString(msg) || err != nil {
        t.Errorf(`Hello("Gladys") = %q, %v, want match for %#q, nil`, msg, err, want)
    }
}

// TestHelloEmpty calls greetings.Hello with an empty string,
// checking for an error.
func TestHelloEmpty(t *testing.T) {
    msg, err := Hello("")
    if msg != "" || err == nil {
        t.Errorf(`Hello("") = %q, %v, want "", error`, msg, err)
    }
}
```

В этом коде:

- test functions находятся в том же package, что и код, который они проверяют;
- определены две test functions для `greetings.Hello`;
- имена test functions имеют форму `TestName`, где `Name` описывает конкретный test;
- test function принимает pointer `*testing.T`. Methods [`testing.T`](https://pkg.go.dev/testing#T) используются для reporting и logging результатов test.

Два tests проверяют разные paths:

- `TestHelloName` вызывает `Hello` с valid name. Если function возвращает error или response без переданного имени, вызывается [`t.Errorf`](https://pkg.go.dev/testing#T.Errorf).
- `TestHelloEmpty` вызывает `Hello` с empty string и проверяет error handling. Если returned string не пустая или `error == nil`, test сообщает failure через `t.Errorf`.

3. В directory `greetings` выполните [`go test`](https://pkg.go.dev/cmd/go#hdr-Test_packages):

```text
$ go test
PASS
ok      example.com/greetings   0.364s
```

`go test` запускает test functions, чьи имена начинаются с `Test`, из files, заканчивающихся на `_test.go`.

Для verbose output используйте `-v`:

```text
$ go test -v
=== RUN   TestHelloName
--- PASS: TestHelloName (0.00s)
=== RUN   TestHelloEmpty
--- PASS: TestHelloEmpty (0.00s)
PASS
ok      example.com/greetings   0.372s
```

4. Теперь намеренно сломайте `greetings.Hello`, чтобы увидеть failing test.

`TestHelloName` проверяет, что returned greeting содержит name, переданный в `Hello`. Измените function так, чтобы имя больше не подставлялось:

```go
// Hello returns a greeting for the named person.
func Hello(name string) (string, error) {
    // If no name was given, return an error with a message.
    if name == "" {
        return name, errors.New("empty name")
    }
    // Create a message using a random format.
    // message := fmt.Sprintf(randomFormat(), name)
    message := fmt.Sprint(randomFormat())
    return message, nil
}
```

5. Снова выполните `go test`, теперь без `-v`.

Без verbose mode output обычно показывает только failing tests, что особенно удобно при большом test suite.

`TestHelloName` должен завершиться failure, а `TestHelloEmpty` продолжит проходить:

```text
$ go test
--- FAIL: TestHelloName (0.00s)
    greetings_test.go:15: Hello("Gladys") = "Hail, %v! Well met!", <nil>, want match for `\bGladys\b`, nil
FAIL
exit status 1
FAIL    example.com/greetings   0.182s
```

Следующий и последний практический этап tutorial — [[compile-install|компиляция и установка application]].
