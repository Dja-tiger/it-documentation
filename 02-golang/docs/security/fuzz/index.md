---
title: "Go Fuzzing"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/fuzz/index.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Go Fuzzing

Native coverage-guided fuzzing встроен в standard toolchain с Go 1.18. Он постоянно мутирует inputs, используя coverage feedback, чтобы находить новые code paths, panics, hangs и assertions failures.

Практический пошаговый пример: [[../../tutorial/fuzz|Tutorial]].

## Требования к fuzz test

Fuzz test:

```go
func FuzzXxx(f *testing.F)
```

- находится в `*_test.go`;
- принимает только `*testing.F`;
- не возвращает values;
- содержит ровно один `f.Fuzz(...)` target.

Target:

```go
f.Fuzz(func(t *testing.T, arg1 string, arg2 []byte) {
    // invariant checks
})
```

Поддерживаемые fuzzing argument types:

- `string`, `[]byte`;
- signed integers (`int`, `int8`...`int64`, включая `rune`);
- unsigned integers (`uint`, `uint8`...`uint64`, включая `byte`);
- `float32`, `float64`;
- `bool`.

Seed corpus entries через `f.Add` или files должны иметь **точно те же types и order**, что target arguments.

## Рекомендации target

- быстрый;
- deterministic;
- без state, переживающего один invocation;
- не зависит от global mutable state;
- допускает parallel workers и nondeterministic invocation order.

## Запуск

Обычный mode запускает seed corpus как tests:

```bash
go test
```

Fuzzing:

```bash
go test -fuzz=FuzzFoo
```

Перед active fuzzing обычные tests package выполняются, затем собирается baseline coverage из seed + generated corpus.

Для coverage-guided growth используйте architecture с coverage instrumentation support (upstream отдельно указывает AMD64/ARM64).

## Progress output

Typical counters:

- `elapsed` — время fuzzing session;
- `execs` — выполненные target inputs и throughput;
- `new interesting` — inputs, расширившие coverage;
- total corpus — текущий размер corpus.

Рост interesting inputs обычно быстрый в начале и замедляется по мере покрытия reachable paths.

## Failing input

Failure:

- panic;
- `t.Fail`/`Error`/`Fatal`;
- non-recoverable process failure (`os.Exit`, stack overflow, OOM...);
- target превышает execution timeout (default documented как около 1 second per target execution).

Recoverable failure обычно минимизируется до smaller human-readable input и сохраняется:

```text
testdata/fuzz/FuzzFoo/<hash>
```

Воспроизведение:

```bash
go test -run=FuzzFoo/<hash>
```

После фикса сохранённый input автоматически становится regression test при обычном `go test`.

Non-recoverable crash может быть сохранён без minimization, потому что повторные expensive crashes делают minimization непрактичной.

## Настройки

```bash
go test -fuzz=FuzzFoo -fuzztime=30s
```

Основные flags:

- `-fuzztime` — total duration/iterations active fuzzing;
- `-fuzzminimizetime` — budget minimization; `0` отключает minimization;
- `-parallel` — число worker processes, default связано с `$GOMAXPROCS`.

`-cpu` во время fuzzing не управляет worker count так же, как обычные tests.

## Corpus format

Пример file:

```text
go test fuzz v1
[]byte("hello\\xbd\\xb2=\\xbc ⌘")
int64(572293)
```

Первая строка — encoding version. Следующие lines — values в Go-like syntax, types/order совпадают target.

Large binary seed удобно конвертировать:

```bash
go install golang.org/x/tools/cmd/file2fuzz@latest
file2fuzz -h
```

Generated corpus хранится в `$GOCACHE/fuzz` и используется только active fuzzing. User seed corpus хранится в source tree и выполняется также обычным `go test`.

## Термины

- **corpus entry** — один input;
- **seed corpus** — user-provided entries (`f.Add` + `testdata/fuzz/...`);
- **generated corpus** — coverage-interesting entries engine в cache;
- **coverage guidance** — сохранение inputs, расширяющих execution coverage;
- **mutator** — изменяет corpus input;
- **fuzz target** — функция, запускаемая для generated inputs;
- **failing input** — input, воспроизводящий target failure;
- **fuzzing engine** — coordinator mutation/corpus/coverage/failure pipeline.

Technical internals: [[technical|Go Fuzzing technical details]].
