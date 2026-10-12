---
title: "Coverage для Go applications"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/build-cover.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Coverage для Go applications

Go поддерживает coverage не только через `go test -cover`, но и для **собранных application binaries**, которые затем можно запускать в integration/system environments и объединять collected coverage data.

Это особенно полезно, когда unit tests не воспроизводят real process lifecycle, network calls, external services или production-like configuration.

## Общий workflow

1. Собрать instrumented binary через `go build -cover`.
2. Запустить его с `GOCOVERDIR`, указывающим directory для coverage files.
3. Повторить запуск в разных scenarios/platforms.
4. Объединить/преобразовать data через `go tool covdata`.

## Пример program

```go
package main

import (
    "fmt"
    "os"
)

func main() {
    fmt.Println("hello")
    if len(os.Args) > 1 {
        fmt.Println("extra arg:", os.Args[1])
    }
}
```

Build:

```bash
go build -cover -o myapp .
```

Создайте output directory:

```bash
mkdir -p /tmp/coverage
```

Run:

```bash
GOCOVERDIR=/tmp/coverage ./myapp
```

При завершении process runtime записывает coverage metadata/counter files в directory.

## Что instrumentируется

`go build -cover` instrumentирует packages main module. Coverage packages можно точнее управлять через `-coverpkg`.

Например:

```bash
go build -cover -coverpkg=./... -o myapp ./cmd/myapp
```

`-coverpkg` принимает package patterns и определяет set packages, для которых compiler вставляет coverage instrumentation.

## `GOCOVERDIR`

Instrumented binary пишет data только если установлен `GOCOVERDIR`.

```bash
GOCOVERDIR=/var/tmp/myapp-cover ./myapp
```

Directory должен существовать и быть writable.

Output состоит из metadata и counter files с именами, содержащими hashes/process-specific parts. Не полагайтесь на internal filename format; используйте `go tool covdata`.

## Просмотр percent coverage

```bash
go tool covdata percent -i=/tmp/coverage
```

Output показывает percentage statements per package.

## Text profile

Преобразовать application coverage в traditional text profile:

```bash
go tool covdata textfmt \
    -i=/tmp/coverage \
    -o=profile.txt
```

После этого можно использовать привычные tools:

```bash
go tool cover -func=profile.txt
go tool cover -html=profile.txt
```

## Объединение нескольких запусков

Допустим, coverage collected в:

```text
/tmp/cov1
/tmp/cov2
/tmp/cov3
```

Объединить:

```bash
go tool covdata merge \
    -i=/tmp/cov1,/tmp/cov2,/tmp/cov3 \
    -o=/tmp/cov-merged
```

Затем:

```bash
go tool covdata percent -i=/tmp/cov-merged
```

Это позволяет складывать coverage:

- разных integration scenarios;
- нескольких process invocations;
- runs на разных machines/platforms, если metadata совместима;
- long-running system tests.

## Вычитание coverage sets

`covdata subtract` позволяет получить execution paths, присутствующие в одном set, но отсутствующие в другом.

```bash
go tool covdata subtract \
    -i=/tmp/full,/tmp/baseline \
    -o=/tmp/delta
```

Полезно для сравнения test suites/scenarios.

## Пересечение

`covdata intersect` оставляет coverage, общую для нескольких inputs:

```bash
go tool covdata intersect \
    -i=/tmp/cov1,/tmp/cov2 \
    -o=/tmp/common
```

## Debug dump

Для low-level inspection:

```bash
go tool covdata debugdump -i=/tmp/coverage
```

Это diagnostic representation, а не stable storage format application tooling.

## `covdata` modes

Coverage counters могут собираться в modes, аналогичных test coverage semantics (`set`, `count`, `atomic`). Exact supported behavior зависит от build instrumentation/options.

Для concurrent code режим `atomic` даёт корректные counter updates ценой большего overhead.

## Integration с `go test`

Обычный package coverage остаётся:

```bash
go test -cover ./...
go test -coverprofile=coverage.out ./...
```

Application coverage дополняет его, а не заменяет. Unit test coverage отвечает: «какие statements исполнили tests package». Instrumented binary отвечает: «какие statements исполнил реальный application process в конкретном environment».

## Ограничения и production use

Coverage instrumentation имеет runtime/size overhead. Обычно instrumented binaries используют для CI, staging, system tests или специально выделенных production canaries, а не как постоянный production artifact без измерения overhead.

`GOCOVERDIR` должен быть уникально/безопасно организован при parallel runs. После collection не анализируйте raw files вручную — merge/convert через `go tool covdata`.

## Рекомендуемый pipeline

```text
unit tests
  -> go test -coverprofile
integration/system build
  -> go build -cover
scenario runs
  -> GOCOVERDIR=...
merge
  -> go tool covdata merge
report
  -> covdata percent / textfmt / go tool cover
```

Так coverage становится measure всей test strategy, а не только unit layer.
