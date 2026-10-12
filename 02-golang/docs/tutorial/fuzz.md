---
title: "Tutorial: начало работы с fuzzing"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/fuzz.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Начало работы с fuzzing

Этот tutorial знакомит с основами fuzzing в Go. При fuzzing случайные data многократно передаются в test, чтобы найти vulnerabilities или inputs, приводящие к crash. Среди проблем, которые может обнаружить fuzzing: SQL injection, buffer overflow, denial of service и cross-site scripting attacks.

В tutorial вы:

- напишете fuzz test для простой function;
- запустите его через команду `go`;
- найдёте и отладите failures;
- исправите обнаруженные bugs.

Терминология: [[../security/fuzz/index|Go Fuzzing glossary]].

Последовательность:

1. создать folder для code;
2. добавить code, который будет test'иться;
3. добавить unit test;
4. преобразовать его в fuzz test;
5. исправить два bugs;
6. изучить дополнительные resources.

> [!note]
> Другие tutorials см. на [go.dev/doc/tutorial](https://go.dev/doc/tutorial/).

> [!note]
> Go fuzzing поддерживает subset built-in types, перечисленный в [[../security/fuzz/index|Go Fuzzing requirements]]. Поддержка дополнительных built-in types может расширяться.

## Предварительные требования

- **Go.** Рекомендуется актуальная version. Установка: [[../install|Установка Go]].
- **Редактор.** Подойдёт любой text editor.
- **Terminal.** Linux/macOS terminal или PowerShell/`cmd` в Windows.
- **Environment с поддержкой fuzzing.** Coverage-instrumented Go fuzzing в upstream этой документации доступен на AMD64 и ARM64.

## Создайте folder для code {#create_folder}

1. Перейдите в home directory.

Linux/macOS:

```text
$ cd
```

Windows:

```text
C:\> cd %HOMEPATH%
```

Далее prompt показан как `$`; commands также работают в Windows.

2. Создайте directory `fuzz`:

```text
$ mkdir fuzz
$ cd fuzz
```

3. Создайте module:

```text
$ go mod init example/fuzz
go: creating new go.mod: module example/fuzz
```

> [!note]
> В production code module path должен соответствовать реальному project/repository. Подробнее см. [[../modules/managing-dependencies|Управление dependencies]].

Теперь добавьте простую function reverse string, которую позже будете fuzz'ить.

## Добавьте code для test {#code_to_test}

### Напишите код

1. Создайте `main.go`.
2. Добавьте package declaration:

```go
package main
```

Standalone program находится в package `main`.

3. Добавьте function:

```go
func Reverse(s string) string {
    b := []byte(s)
    for i, j := 0, len(b)-1; i < len(b)/2; i, j = i+1, j-1 {
        b[i], b[j] = b[j], b[i]
    }
    return string(b)
}
```

Function принимает `string`, проходит по нему по одному `byte` и возвращает reversed string.

> [!note]
> Этот code основан на `stringutil.Reverse` из `golang.org/x/example`.

4. Добавьте `main`:

```go
func main() {
    input := "The quick brown fox jumped over the lazy dog"
    rev := Reverse(input)
    doubleRev := Reverse(rev)
    fmt.Printf("original: %q\n", input)
    fmt.Printf("reversed: %q\n", rev)
    fmt.Printf("reversed again: %q\n", doubleRev)
}
```

Function выполняет несколько calls `Reverse` и печатает results — это удобно для наблюдения поведения и debugging.

5. Импортируйте `fmt`:

```go
package main

import "fmt"
```

### Запустите код

```text
$ go run .
original: "The quick brown fox jumped over the lazy dog"
reversed: "god yzal eht revo depmuj xof nworb kciuq ehT"
reversed again: "The quick brown fox jumped over the lazy dog"
```

Original string, reversed string и double reverse совпадают ожидаемо. Теперь добавьте test.

## Добавьте unit test {#unit_test}

### Напишите код

1. Создайте `reverse_test.go`.
2. Добавьте:

```go
package main

import (
    "testing"
)

func TestReverse(t *testing.T) {
    testcases := []struct {
        in, want string
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

Test проверяет, что указанные inputs правильно reverse'ятся.

### Запустите test

```text
$ go test
PASS
ok      example/fuzz  0.013s
```

Далее преобразуйте unit test в fuzz test.

## Добавьте fuzz test {#fuzz_test}

Ограничение unit test: каждый input должен вручную добавить developer. Fuzzing генерирует дополнительные inputs автоматически и способен найти edge cases, о которых автор test не подумал.

Unit tests, benchmarks и fuzz tests могут находиться в одном `_test.go`, но в tutorial unit test заменяется fuzz test.

### Напишите код

Замените unit test в `reverse_test.go`:

```go
func FuzzReverse(f *testing.F) {
    testcases := []string{"Hello, world", " ", "!12345"}
    for _, tc := range testcases {
        f.Add(tc)  // Use f.Add to provide a seed corpus
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

В unit test можно заранее знать expected output. Например, для `Reverse("Hello, world")` ожидается `"dlrow ,olleH"`.

В fuzzing inputs заранее неизвестны, поэтому exact expected output предсказать нельзя. Вместо этого проверяются **properties** function:

1. double reverse должен сохранять original value;
2. если original string valid UTF-8, reversed string также должен оставаться valid UTF-8.

Отличия fuzz test:

- имя начинается с `FuzzXxx`, а argument — `*testing.F` вместо `*testing.T`;
- `f.Fuzz` принимает fuzz target function с `*testing.T` и values fuzzed types;
- known inputs добавляются в seed corpus через `f.Add`.

Добавьте import:

```go
package main

import (
    "testing"
    "unicode/utf8"
)
```

### Запустите код

1. Сначала выполните fuzz test без fuzzing, чтобы проверить seed inputs:

```text
$ go test
PASS
ok      example/fuzz  0.013s
```

Если в file есть другие tests, конкретно этот fuzz test можно запустить:

```bash
go test -run=FuzzReverse
```

2. Запустите fuzzing:

```bash
go test -fuzz=Fuzz
```

Полезный flag `-fuzztime` ограничивает duration, например:

```bash
go test -fuzz=Fuzz -fuzztime 10s
```

Другие flags см. в [testing flags](https://pkg.go.dev/cmd/go#hdr-Testing_flags).

При запуске tutorial обнаруживает failure:

```text
$ go test -fuzz=Fuzz
fuzz: elapsed: 0s, gathering baseline coverage: 0/3 completed
fuzz: elapsed: 0s, gathering baseline coverage: 3/3 completed, now fuzzing with 8 workers
fuzz: minimizing 38-byte failing input file...
--- FAIL: FuzzReverse (0.01s)
    --- FAIL: FuzzReverse (0.00s)
        reverse_test.go:20: Reverse produced invalid UTF-8 string "\x9c\xdd"

    Failing input written to testdata/fuzz/FuzzReverse/af69258a12129d6cbba438df5d5f25ba0ec050461c116f777e77ea7c9a0d217a
    To re-run:
    go test -run=FuzzReverse/af69258a12129d6cbba438df5d5f25ba0ec050461c116f777e77ea7c9a0d217a
FAIL
exit status 1
FAIL    example/fuzz  0.030s
```

Fuzzing записывает failing input в seed corpus file. При следующем `go test` этот input выполняется снова даже без `-fuzz`.

Пример corpus file:

```text
go test fuzz v1
string("泃")
```

Первая строка указывает encoding version. Каждая следующая строка представляет value одного input type. Здесь fuzz target имеет один input, поэтому после version находится одно value.

3. Выполните обычный test ещё раз:

```text
$ go test
--- FAIL: FuzzReverse (0.00s)
    --- FAIL: FuzzReverse/af69258a12129d6cbba438df5d5f25ba0ec050461c116f777e77ea7c9a0d217a (0.00s)
        reverse_test.go:20: Reverse produced invalid string
FAIL
exit status 1
FAIL    example/fuzz  0.016s
```

Теперь failure стабильно воспроизводится и можно переходить к debugging.

## Исправьте invalid string error {#fix_invalid_string_error}

### Диагностируйте error

Есть разные способы debugging. В VS Code можно использовать [Go debugger](https://github.com/golang/vscode-go/blob/master/docs/debugging.md). Tutorial использует logging.

Документация [`utf8.ValidString`](https://pkg.go.dev/unicode/utf8) определяет function так:

```text
ValidString reports whether s consists entirely of valid UTF-8-encoded runes.
```

Текущий `Reverse` reverse'ит string **byte-by-byte**. Это и есть проблема: чтобы сохранить UTF-8 runes, string нужно reverse'ить **rune-by-rune**.

Чтобы понять, почему input — например Chinese character `泃` — превращается в invalid string, добавьте число runes в log.

Замените fuzz target:

```go
f.Fuzz(func(t *testing.T, orig string) {
    rev := Reverse(orig)
    doubleRev := Reverse(rev)
    t.Logf("Number of runes: orig=%d, rev=%d, doubleRev=%d", utf8.RuneCountInString(orig), utf8.RuneCountInString(rev), utf8.RuneCountInString(doubleRev))
    if orig != doubleRev {
        t.Errorf("Before: %q, after: %q", orig, doubleRev)
    }
    if utf8.ValidString(orig) && !utf8.ValidString(rev) {
        t.Errorf("Reverse produced invalid UTF-8 string %q", rev)
    }
})
```

`t.Logf` печатает message при test error или при запуске с `-v`.

Запустите:

```text
$ go test
--- FAIL: FuzzReverse (0.00s)
    --- FAIL: FuzzReverse/28f36ef487f23e6c7a81ebdaa9feffe2f2b02b4cddaa6252e87f69863046a5e0 (0.00s)
        reverse_test.go:16: Number of runes: orig=1, rev=3, doubleRev=1
        reverse_test.go:21: Reverse produced invalid UTF-8 string "\x83\xb3\xe6"
FAIL
exit status 1
FAIL    example/fuzz    0.598s
```

Seed corpus до этого содержал только chars размером один byte. Но `泃` кодируется несколькими bytes. Byte-by-byte reverse разрушает multi-byte encoding.

Подробнее о strings/runes: [Strings, bytes, runes and characters in Go](https://go.dev/blog/strings).

### Исправьте error

Reverse'ите string по runes:

```go
func Reverse(s string) string {
    r := []rune(s)
    for i, j := 0, len(r)-1; i < len(r)/2; i, j = i+1, j-1 {
        r[i], r[j] = r[j], r[i]
    }
    return string(r)
}
```

Теперь iteration происходит по `rune`, а не по `byte`.

> [!note]
> Это учебный пример и он не решает корректно все случаи [combining characters](https://en.wikipedia.org/wiki/Combining_character).

Запустите:

```text
$ go test
PASS
ok      example/fuzz  0.016s
```

Fuzzing снова:

```text
$ go test -fuzz=Fuzz
fuzz: elapsed: 0s, gathering baseline coverage: 0/37 completed
fuzz: minimizing 506-byte failing input file...
fuzz: elapsed: 0s, gathering baseline coverage: 5/37 completed
--- FAIL: FuzzReverse (0.02s)
    --- FAIL: FuzzReverse (0.00s)
        reverse_test.go:33: Before: "\x91", after: "�"

    Failing input written to testdata/fuzz/FuzzReverse/1ffc28f7538e29d79fce69fef20ce5ea72648529a9ca10bea392bcff28cd015c
    To re-run:
    go test -run=FuzzReverse/1ffc28f7538e29d79fce69fef20ce5ea72648529a9ca10bea392bcff28cd015c
FAIL
exit status 1
FAIL    example/fuzz  0.032s
```

Теперь double reverse отличается от original. Новый input сам является invalid Unicode. Почему это возможно, если fuzzed type — `string`? Go string — read-only sequence bytes и может содержать bytes, не являющиеся valid UTF-8.

## Исправьте double reverse error {#fix_double_reverse_error}

### Диагностируйте error

Original string содержит один byte `\x91`. При conversion в `[]rune` invalid byte sequence декодируется в Unicode replacement character `�`. После этого original byte string и reconstructed UTF-8 string уже не равны.

Добавьте debug output в `Reverse`:

```go
func Reverse(s string) string {
    fmt.Printf("input: %q\n", s)
    r := []rune(s)
    fmt.Printf("runes: %q\n", r)
    for i, j := 0, len(r)-1; i < len(r)/2; i, j = i+1, j-1 {
        r[i], r[j] = r[j], r[i]
    }
    return string(r)
}
```

Для debugging конкретного corpus entry используйте `go test -run` и hash failing input:

```text
$ go test -run=FuzzReverse/28f36ef487f23e6c7a81ebdaa9feffe2f2b02b4cddaa6252e87f69863046a5e0
input: "\x91"
runes: ['�']
input: "�"
runes: ['�']
--- FAIL: FuzzReverse (0.00s)
    --- FAIL: FuzzReverse/28f36ef487f23e6c7a81ebdaa9feffe2f2b02b4cddaa6252e87f69863046a5e0 (0.00s)
        reverse_test.go:16: Number of runes: orig=1, rev=1, doubleRev=1
        reverse_test.go:18: Before: "\x91", after: "�"
FAIL
exit status 1
FAIL    example/fuzz    0.145s
```

### Исправьте error

Если input не является valid UTF-8, `Reverse` будет возвращать error:

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

Теперь invalid UTF-8 input возвращает error.

Поскольку signature изменилась, обновите `main`:

```go
func main() {
    input := "The quick brown fox jumped over the lazy dog"
    rev, revErr := Reverse(input)
    doubleRev, doubleRevErr := Reverse(rev)
    fmt.Printf("original: %q\n", input)
    fmt.Printf("reversed: %q, err: %v\n", rev, revErr)
    fmt.Printf("reversed again: %q, err: %v\n", doubleRev, doubleRevErr)
}
```

Для этого valid UTF-8 input оба errors должны быть `nil`.

Добавьте imports:

```go
import (
    "errors"
    "fmt"
    "unicode/utf8"
)
```

Обновите fuzz test:

```go
func FuzzReverse(f *testing.F) {
    testcases := []string {"Hello, world", " ", "!12345"}
    for _, tc := range testcases {
        f.Add(tc)  // Use f.Add to provide a seed corpus
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

Вместо `return` можно вызвать `t.Skip()` для прекращения обработки конкретного fuzz input.

### Запустите код

1. Обычный test:

```text
$ go test
PASS
ok      example/fuzz  0.019s
```

2. Запустите fuzzing и остановите через `Ctrl-C` через некоторое время. Без `-fuzztime` fuzzing продолжает работать до failure либо interruption:

```text
$ go test -fuzz=Fuzz
fuzz: elapsed: 0s, gathering baseline coverage: 0/38 completed
fuzz: elapsed: 0s, gathering baseline coverage: 38/38 completed, now fuzzing with 4 workers
fuzz: elapsed: 3s, execs: 86342 (28778/sec), new interesting: 2 (total: 35)
fuzz: elapsed: 6s, execs: 193490 (35714/sec), new interesting: 4 (total: 37)
fuzz: elapsed: 9s, execs: 304390 (36961/sec), new interesting: 4 (total: 37)
...
fuzz: elapsed: 3m45s, execs: 7246222 (32357/sec), new interesting: 8 (total: 41)
^Cfuzz: elapsed: 3m48s, execs: 7335316 (31648/sec), new interesting: 8 (total: 41)
PASS
ok      example/fuzz  228.000s
```

3. Или ограничьте fuzzing 30 seconds:

```text
$ go test -fuzz=Fuzz -fuzztime 30s
fuzz: elapsed: 0s, gathering baseline coverage: 0/5 completed
fuzz: elapsed: 0s, gathering baseline coverage: 5/5 completed, now fuzzing with 4 workers
fuzz: elapsed: 3s, execs: 80290 (26763/sec), new interesting: 12 (total: 12)
fuzz: elapsed: 6s, execs: 210803 (43501/sec), new interesting: 14 (total: 14)
fuzz: elapsed: 9s, execs: 292882 (27360/sec), new interesting: 14 (total: 14)
fuzz: elapsed: 12s, execs: 371872 (26329/sec), new interesting: 14 (total: 14)
fuzz: elapsed: 15s, execs: 517169 (48433/sec), new interesting: 15 (total: 15)
fuzz: elapsed: 18s, execs: 663276 (48699/sec), new interesting: 15 (total: 15)
fuzz: elapsed: 21s, execs: 771698 (36143/sec), new interesting: 15 (total: 15)
fuzz: elapsed: 24s, execs: 924768 (50990/sec), new interesting: 16 (total: 16)
fuzz: elapsed: 27s, execs: 1082025 (52427/sec), new interesting: 17 (total: 17)
fuzz: elapsed: 30s, execs: 1172817 (30281/sec), new interesting: 17 (total: 17)
fuzz: elapsed: 31s, execs: 1172817 (0/sec), new interesting: 17 (total: 17)
PASS
ok      example/fuzz  31.025s
```

Fuzzing проходит успешно.

Дополнительные fuzz flags описаны в [[../security/fuzz/index|Go Fuzzing]]. В output термин **new interesting** обозначает inputs, расширяющие code coverage текущего fuzz corpus. В начале fuzzing их число обычно быстро растёт, затем увеличивается всплесками при открытии новых code paths и постепенно стабилизируется.

## Заключение {#conclusion}

Вы познакомились с fuzzing в Go.

Следующий практический шаг — выбрать подходящую function собственного codebase и fuzz'ить её. Если fuzzing найдёт bug, его можно добавить в [Fuzzing trophy case](https://go.dev/wiki/Fuzzing-trophy-case).

Problems и feature ideas можно отправлять через [Go issue tracker](https://go.dev/issue/new/?&labels=fuzz).

Для discussion доступен [#fuzzing channel](https://gophers.slack.com/archives/CH5KV1AKE) в Gophers Slack.

Дополнительное чтение: [[../security/fuzz/index|Go Fuzzing]].

## Полный код

### `main.go`

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

### `reverse_test.go`

```go
package main

import (
    "testing"
    "unicode/utf8"
)

func FuzzReverse(f *testing.F) {
    testcases := []string{"Hello, world", " ", "!12345"}
    for _, tc := range testcases {
        f.Add(tc) // Use f.Add to provide a seed corpus
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
