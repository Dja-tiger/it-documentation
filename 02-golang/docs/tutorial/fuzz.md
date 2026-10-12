---
title: "Начало работы с fuzzing"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/fuzz.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Начало работы с fuzzing

Go fuzzing автоматически генерирует inputs и запускает их против test target, пытаясь найти crashes, invariant violations и security-relevant edge cases. Fuzzing может обнаруживать, например, input validation bugs, panic paths, denial-of-service conditions и некоторые injection/encoding проблемы.

Tutorial строит fuzz test для function, разворачивающей string.

> [!note]
> Coverage-guided Go fuzzing доступен на поддерживаемых architectures; official tutorial отдельно указывает AMD64 и ARM64 для instrumented fuzzing.

## Подготовка

```bash
mkdir fuzz
cd fuzz
go mod init example/fuzz
```

Начальная implementation:

```go
package main

import "fmt"

func Reverse(s string) string {
    b := []byte(s)
    for i, j := 0, len(b)-1; i < len(b)/2; i, j = i+1, j-1 {
        b[i], b[j] = b[j], b[i]
    }
    return string(b)
}

func main() {
    input := "The quick brown fox jumped over the lazy dog"
    rev := Reverse(input)
    doubleRev := Reverse(rev)

    fmt.Printf("original: %q\n", input)
    fmt.Printf("reversed: %q\n", rev)
    fmt.Printf("reversed again: %q\n", doubleRev)
}
```

## Сначала обычный unit test

```go
package main

import "testing"

func TestReverse(t *testing.T) {
    testcases := []struct {
        in   string
        want string
    }{
        {"Hello, world", "dlrow ,olleH"},
        {" ", " "},
        {"!12345", "54321!"},
    }

    for _, tc := range testcases {
        rev := Reverse(tc.in)
        if rev != tc.want {
            t.Errorf("Reverse: %q, want %q", rev, tc.want)
        }
    }
}
```

```bash
go test
```

Ограничение table-driven unit test — developer сам выбирает каждый input.

## Fuzz target

Заменим unit test на fuzz test:

```go
func FuzzReverse(f *testing.F) {
    testcases := []string{"Hello, world", " ", "!12345"}
    for _, tc := range testcases {
        f.Add(tc)
    }

    f.Fuzz(func(t *testing.T, orig string) {
        rev := Reverse(orig)
        doubleRev := Reverse(rev)

        if orig != doubleRev {
            t.Errorf("Before: %q, after: %q", orig, doubleRev)
        }

        if utf8.ValidString(orig) && !utf8.ValidString(rev) {
            t.Errorf("Reverse produced invalid UTF-8 string %q", rev)
        }
    })
}
```

Отличия от unit test:

- function называется `FuzzXxx`;
- принимает `*testing.F`;
- `f.Add` формирует seed corpus;
- `f.Fuzz` принимает fuzz target;
- generated inputs проверяются не по заранее известному exact result, а по **properties/invariants**.

Здесь проверяются два invariants:

1. double reverse должен восстановить original;
2. valid UTF-8 input после reverse должен остаться valid UTF-8.

Добавьте import:

```go
import (
    "testing"
    "unicode/utf8"
)
```

## Запуск seed corpus без fuzzing

```bash
go test
```

Либо конкретный fuzz test:

```bash
go test -run=FuzzReverse
```

## Запуск fuzzing

```bash
go test -fuzz=Fuzz
```

Ограничить время:

```bash
go test -fuzz=Fuzz -fuzztime=30s
```

Когда найден failing input, Go минимизирует его и сохраняет reproducible corpus entry в:

```text
testdata/fuzz/FuzzReverse/<hash>
```

Этот input затем запускается обычным `go test` даже без `-fuzz`.

Конкретный regression можно воспроизвести:

```bash
go test -run=FuzzReverse/<hash>
```

## Первый bug: byte reverse ломает UTF-8

Начальная implementation разворачивает `string` byte-by-byte. UTF-8 rune может занимать несколько bytes, поэтому их перестановка создаёт invalid encoding.

Исправление — разворачивать `[]rune`:

```go
func Reverse(s string) string {
    r := []rune(s)
    for i, j := 0, len(r)-1; i < len(r)/2; i, j = i+1, j-1 {
        r[i], r[j] = r[j], r[i]
    }
    return string(r)
}
```

Это сохраняет UTF-8 runes, хотя пример всё ещё не решает более сложную Unicode-проблему combining characters/grapheme clusters.

## Второй bug: Go string может содержать invalid UTF-8

Новый fuzzing обнаруживает другой input: string в Go является read-only sequence of bytes и **не обязан** содержать valid UTF-8.

При преобразовании invalid bytes в `[]rune` invalid encoding заменяется Unicode replacement rune `�`. Поэтому double reverse уже не восстанавливает original raw bytes.

Один из возможных contracts — отвергать invalid UTF-8:

```go
func Reverse(s string) (string, error) {
    if !utf8.ValidString(s) {
        return s, errors.New("input is not valid UTF-8")
    }

    r := []rune(s)
    for i, j := 0, len(r)-1; i < len(r)/2; i, j = i+1, j-1 {
        r[i], r[j] = r[j], r[i]
    }

    return string(r), nil
}
```

Fuzz target должен учитывать error contract:

```go
func FuzzReverse(f *testing.F) {
    testcases := []string{"Hello, world", " ", "!12345"}
    for _, tc := range testcases {
        f.Add(tc)
    }

    f.Fuzz(func(t *testing.T, orig string) {
        rev, err1 := Reverse(orig)
        if err1 != nil {
            return
        }

        doubleRev, err2 := Reverse(rev)
        if err2 != nil {
            return
        }

        if orig != doubleRev {
            t.Errorf("Before: %q, after: %q", orig, doubleRev)
        }

        if utf8.ValidString(orig) && !utf8.ValidString(rev) {
            t.Errorf("Reverse produced invalid UTF-8 string %q", rev)
        }
    })
}
```

Вместо `return` fuzz input можно explicitly skip через `t.Skip()`.

## Финальный код `main.go`

```go
package main

import (
    "errors"
    "fmt"
    "unicode/utf8"
)

func main() {
    input := "The quick brown fox jumped over the lazy dog"
    rev, revErr := Reverse(input)
    doubleRev, doubleRevErr := Reverse(rev)

    fmt.Printf("original: %q\n", input)
    fmt.Printf("reversed: %q, err: %v\n", rev, revErr)
    fmt.Printf("reversed again: %q, err: %v\n", doubleRev, doubleRevErr)
}

func Reverse(s string) (string, error) {
    if !utf8.ValidString(s) {
        return s, errors.New("input is not valid UTF-8")
    }

    r := []rune(s)
    for i, j := 0, len(r)-1; i < len(r)/2; i, j = i+1, j-1 {
        r[i], r[j] = r[j], r[i]
    }

    return string(r), nil
}
```

Fuzzing превращает найденный edge case в постоянный regression corpus и особенно хорошо подходит для parsers, codecs, protocol implementations, serialization, validation и security-sensitive input handling.
