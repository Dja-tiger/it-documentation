---
title: "Добавление unit test"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/add-a-test.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Добавление test

Go имеет встроенную testing infrastructure: naming conventions, standard package `testing` и command `go test`.

Создайте `greetings_test.go`. Суффикс `_test.go` сообщает `go test`, что файл содержит test code.

```go
package greetings

import (
    "regexp"
    "testing"
)

func TestHelloName(t *testing.T) {
    name := "Gladys"
    want := regexp.MustCompile(`\b` + name + `\b`)

    msg, err := Hello("Gladys")
    if !want.MatchString(msg) || err != nil {
        t.Errorf(
            `Hello("Gladys") = %q, %v, want match for %#q, nil`,
            msg,
            err,
            want,
        )
    }
}

func TestHelloEmpty(t *testing.T) {
    msg, err := Hello("")
    if msg != "" || err == nil {
        t.Errorf(`Hello("") = %q, %v, want "", error`, msg, err)
    }
}
```

Правила:

- test functions имеют форму `TestName`;
- принимают `*testing.T`;
- failure можно сообщить через `t.Errorf`, `t.Error`, `t.Fatal` и другие methods.

Запуск:

```text
$ go test
PASS
ok      example.com/greetings   0.364s
```

Verbose:

```text
$ go test -v
=== RUN   TestHelloName
--- PASS: TestHelloName (0.00s)
=== RUN   TestHelloEmpty
--- PASS: TestHelloEmpty (0.00s)
PASS
```

Tutorial предлагает намеренно сломать `Hello`, чтобы увидеть failing test. Это показывает важный feedback loop: regression обнаруживается сразу после изменения code.

Следующий шаг — [[compile-install|build/install]].
