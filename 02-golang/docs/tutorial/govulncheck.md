---
title: "Tutorial: поиск и исправление уязвимых dependencies с govulncheck"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/govulncheck.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Поиск и исправление уязвимых dependencies с govulncheck

`govulncheck` — low-noise tool, помогающий находить и исправлять уязвимые dependencies в Go projects. Он сканирует dependencies проекта на известные vulnerabilities, а затем определяет, существуют ли в вашем коде прямые или косвенные calls уязвимых symbols.

В этом tutorial вы научитесь:

- сканировать простую program через `govulncheck`;
- оценивать и приоритизировать vulnerabilities;
- сосредотачиваться сначала на наиболее значимых findings;
- обновлять vulnerable dependencies и повторно проверять project.

Подробнее:

- [govulncheck documentation](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck);
- [Go vulnerability management](https://go.dev/blog/vuln);
- [govulncheck feedback](https://go.dev/s/govulncheck-feedback).

## Предварительные требования

- **Go.** Рекомендуется актуальная версия Go. Установка: [[../install|Установка Go]].
- **Code editor.** Подойдёт любой editor.
- **Terminal.** Подойдёт terminal Linux/macOS или PowerShell/`cmd` в Windows.

Tutorial состоит из четырёх этапов:

1. создать sample Go module с vulnerable dependency;
2. установить и запустить `govulncheck`;
3. оценить vulnerabilities;
4. обновить vulnerable dependencies.

## Создайте sample Go module с vulnerable dependency

### Шаг 1

Создайте directory `vuln-tutorial` и инициализируйте Go module. Если Go modules вам незнакомы, сначала см. [[create-module|Создание Go module]].

```text
$ mkdir vuln-tutorial
$ cd vuln-tutorial
$ go mod init vuln.tutorial
```

### Шаг 2

Создайте `main.go` внутри `vuln-tutorial`:

```go
package main

import (
        "fmt"
        "os"

        "golang.org/x/text/language"
)

func main() {
        for _, arg := range os.Args[1:] {
                tag, err := language.Parse(arg)
                if err != nil {
                        fmt.Printf("%s: error: %v\n", arg, err)
                } else if tag == language.Und {
                        fmt.Printf("%s: undefined\n", arg)
                } else {
                        fmt.Printf("%s: tag %s\n", arg, tag)
                }
        }
}
```

Program принимает list language tags через command-line arguments и для каждого tag сообщает:

- успешно ли он parsed;
- является ли tag undefined;
- возник ли error во время parsing.

### Шаг 3

Выполните `go mod tidy`, чтобы `go.mod` получил dependencies, необходимые коду `main.go`:

```text
$ go mod tidy
go: finding module for package golang.org/x/text/language
go: downloading golang.org/x/text v0.9.0
go: found golang.org/x/text/language in golang.org/x/text v0.9.0
```

### Шаг 4

Проверьте `go.mod`:

```text
module vuln.tutorial

go 1.20

require golang.org/x/text v0.9.0
```

### Шаг 5

Намеренно downgrade'ните `golang.org/x/text` до `v0.3.5`, содержащей известные vulnerabilities:

```text
$ go get golang.org/x/text@v0.3.5
go: downgraded golang.org/x/text v0.9.0 => v0.3.5
```

Теперь `go.mod` должен содержать:

```text
module vuln.tutorial

go 1.20

require golang.org/x/text v0.3.5
```

Теперь можно проверить module через `govulncheck`.

## Установите и запустите govulncheck

### Шаг 6

Установите tool:

```bash
go install golang.org/x/vuln/cmd/govulncheck@latest
```

### Шаг 7

Из directory анализируемого project выполните:

```bash
govulncheck ./...
```

В tutorial ожидается output следующего типа:

```text
govulncheck is an experimental tool. Share feedback at https://go.dev/s/govulncheck-feedback.

Using go1.20.3 and govulncheck@v0.0.0 with
vulnerability data from https://vuln.go.dev (last modified 2023-04-18 21:32:26 +0000 UTC).

Scanning your code and 46 packages across 1 dependent module for known vulnerabilities...
Your code is affected by 1 vulnerability from 1 module.

Vulnerability #1: GO-2021-0113
  Due to improper index calculation, an incorrectly formatted
  language tag can cause Parse to panic via an out of bounds read.
  If Parse is used to process untrusted user inputs, this may be
  used as a vector for a denial of service attack.

  More info: https://pkg.go.dev/vuln/GO-2021-0113

  Module: golang.org/x/text
    Found in: golang.org/x/text@v0.3.5
    Fixed in: golang.org/x/text@v0.3.7

    Call stacks in your code:
      main.go:12:29: vuln.tutorial.main calls golang.org/x/text/language.Parse

=== Informational ===

Found 1 vulnerability in packages that you import, but there are no call
stacks leading to the use of this vulnerability. You may not need to
take any action. See https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck
for details.

Vulnerability #1: GO-2022-1059
  An attacker may cause a denial of service by crafting an
  Accept-Language header which ParseAcceptLanguage will take
  significant time to parse.
  More info: https://pkg.go.dev/vuln/GO-2022-1059
  Found in: golang.org/x/text@v0.3.5
  Fixed in: golang.org/x/text@v0.3.8
```

## Интерпретация output

> [!note]
> Если используется не самая новая Go version, output может дополнительно содержать vulnerabilities standard library.

Code действительно затронут vulnerability [GO-2021-0113](https://pkg.go.dev/vuln/GO-2021-0113), потому что напрямую вызывает vulnerable function `golang.org/x/text/language.Parse` из version `v0.3.5`.

В module `golang.org/x/text@v0.3.5` существует также [GO-2022-1059](https://pkg.go.dev/vuln/GO-2022-1059), но `govulncheck` показывает её как **Informational**, потому что code не вызывает — ни напрямую, ни косвенно — vulnerable functions этого report.

Теперь нужно оценить findings и принять решение.

## Оцените vulnerabilities

### a. Оцените применимость

Прочитайте description vulnerability и определите, применима ли она к вашему code и use case. При необходимости откройте `More info`.

GO-2021-0113 может вызвать panic, если `Parse` обрабатывает untrusted input. Предположим, приложение должно безопасно выдерживать untrusted input и denial-of-service risk важен. Тогда vulnerability применима.

GO-2022-1059, напротив, вероятно не затрагивает этот program, поскольку code не вызывает vulnerable functions этого report.

### b. Выберите действие

Для mitigation GO-2021-0113 есть несколько вариантов.

- **Вариант 1: обновиться до fixed version.** Если исправление существует, vulnerable dependency можно удалить, обновив module до исправленной version.
- **Вариант 2: перестать использовать vulnerable symbol(s).** Можно удалить calls уязвимой function и найти альтернативу либо реализовать equivalent functionality самостоятельно.

В этом случае fixed version существует, а `Parse` является важной частью program, поэтому dependency разумно обновить минимум до `v0.3.7`.

Informational vulnerability GO-2022-1059 можно было бы deprioritize, но она находится в том же module, а её fixed version — `v0.3.8`. Поэтому обе vulnerabilities легко устранить одним обновлением до `v0.3.8`.

## Обновите vulnerable dependencies

### Шаг 8

Обновите `golang.org/x/text` до `v0.3.8`:

```text
$ go get golang.org/x/text@v0.3.8
go: upgraded golang.org/x/text v0.3.5 => v0.3.8
```

Можно было бы обновиться и до `latest`, либо до любой version после `v0.3.8`.

### Шаг 9

Повторно запустите:

```bash
govulncheck ./...
```

Теперь ожидаемый output:

```text
govulncheck is an experimental tool. Share feedback at https://go.dev/s/govulncheck-feedback.

Using go1.20.3 and govulncheck@v0.0.0 with
vulnerability data from https://vuln.go.dev (last modified 2023-04-06 19:19:26 +0000 UTC).

Scanning your code and 46 packages across 1 dependent module for known vulnerabilities...
No vulnerabilities found.
```

`govulncheck` подтверждает, что известных vulnerabilities больше не найдено.

Регулярное сканирование dependencies через `govulncheck` помогает защищать codebase, обнаруживая, приоритизируя и устраняя vulnerabilities.
