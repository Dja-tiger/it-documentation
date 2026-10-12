# Practice 14 — Specification и runtime labs

Для каждого fragment сначала записать prediction и ссылку на [[../../docs/spec|локальный spec]], а нормативный edge case сверить с pinned Go 1.27.1 upstream. Только затем запускать compiler/runtime.

## Задание 1. Comparability matrix

### Условие

Составить matrix comparability для `[3]int`, `[]int`, comparable/non-comparable structs, map, func и interface values с разными dynamic types.

### Входные данные

Минимальные values каждого указанного type.

### Ожидаемое поведение

До запуска предсказать equality/map-key compile behavior и interface equality panic scenario.

### Ограничения

Каждый prediction привязать к spec rule; panic isolated.

### Acceptance criteria

Матрица compile/pass/panic совпадает с проверкой и объяснена нормативным правилом.

### Команды проверки

```bash
go test -run TestComparability -v ./...
```

## Задание 2. Method-set matrix

### Условие

Проверить assignments/calls для methods с receivers `T` и `*T`.

### Входные данные

`T`, `*T`, interface с required method, addressable и non-addressable values.

### Ожидаемое поведение

Prediction отделяет method set/interface satisfaction от automatic address-taking при method call.

### Ограничения

Не менять несколько факторов одновременно без отдельной matrix row.

### Acceptance criteria

Все combinations объяснены ссылкой на method-set rule.

### Команды проверки

```bash
go test -run TestMethodSet -v ./...
```

## Задание 3. Nil matrix

### Условие

Исследовать nil map read/write, nil channel send/receive/close, nil pointer dereference и typed nil interface.

### Входные данные

Zero/nil values соответствующих types.

### Ожидаемое поведение

До запуска классифицировать каждый case как valid immediate result, panic или permanent block.

### Ограничения

Blocking cases только с test/subprocess timeout; panics expected/recovered только для lab.

### Acceptance criteria

Matrix полностью заполнена и объяснена через spec, а не через запоминание output.

### Команды проверки

```bash
go test -run TestNilMatrix -v -timeout=5s ./...
```

## Задание 4. Slice capacity / full slice expression

### Условие

Использовать `a[low:high:max]`, aliases и `append` для исследования capacity/aliasing.

### Входные данные

Array/slice с известной length/capacity и несколько full-slice bounds.

### Ожидаемое поведение

До запуска предсказать `len`, `cap` и mutation visibility после append.

### Ограничения

Boundary panic cases isolated; values небольшие и легко проверяются вручную.

### Acceptance criteria

Predictions совпадают; можно объяснить, зачем ограничивать capacity full-slice expression’ом.

### Команды проверки

```bash
go test -run TestFullSlice -v ./...
```

## Задание 5. `defer` semantics

### Условие

Проверить evaluation arguments, reverse order, named result modification и nil deferred function behavior.

### Входные данные

Небольшие functions с observable variables/order.

### Ожидаемое поведение

Prediction точно разделяет момент evaluation deferred call arguments и момент invocation.

### Ограничения

Не смешивать panic/recover с основным defer experiment до понимания базовой семантики.

### Acceptance criteria

Каждый case объяснён spec rule; ordering test deterministic.

### Команды проверки

```bash
go test -run TestDefer -v ./...
```

## Задание 6. Map iteration и `select`

### Условие

Создать bug, зависящий от map iteration order, и code, ошибочно ожидающий fixed `select` priority; затем исправить design.

### Входные данные

Map с несколькими keys и `select` с несколькими одновременно ready cases.

### Ожидаемое поведение

Repeated runs могут показывать different valid orders/selections; correctness final code не зависит от них.

### Ограничения

Не пытаться «доказать random distribution» статистически; нужна только независимость correctness от unspecified/randomized choice.

### Acceptance criteria

Broken assumptions задокументированы; final tests проверяют invariant, а не конкретный incidental order.

### Команды проверки

```bash
go test -run TestMapSelect -count=100 ./...
```

## Задание 7. Happens-before: race → mutex → channel

### Условие

Создать intentional race shared variable, затем исправить отдельно mutex и channel ownership/communication variants.

### Входные данные

Concurrent writer/reader или counter workload.

### Ожидаемое поведение

Race variant обнаруживается `-race`; synchronized variants clean и дают deterministic invariant.

### Ограничения

Для каждого fixed variant нарисовать конкретный happens-before edge; timing/sleep не считается synchronization.

### Acceptance criteria

Можно объяснить correctness через memory model; `-race` green на fixed versions.

### Команды проверки

```bash
go test -race -run TestHappensBefore ./...
```

## Задание 8. Allocation profile → escape analysis

### Условие

Снять allocation profile representative processor и затем применить escape analysis только к найденному hotspot.

### Входные данные

Representative `price-processor` benchmark/workload.

### Ожидаемое поведение

Profile указывает hotspot; compiler diagnostic объясняет конкретные escapes/inlining choices.

### Ограничения

Не считать escape автоматически defect; изменение принимается только после benchmark/profile evidence.

### Acceptance criteria

Documented chain: profile evidence → compiler explanation → change/no-change decision.

### Команды проверки

```bash
go test -bench=BenchmarkProcess -memprofile=mem.out ./...
go tool pprof -top -alloc_space mem.out
go build -gcflags=-m=3 ./...
```

## Задание 9. Scheduler / runtime trace

### Условие

Сравнить runtime behavior для CPU-bound workers, blocked workers и mutex contention.

### Входные данные

Three controlled workloads с одинаково понятным goroutine topology.

### Ожидаемое поведение

Trace/schedtrace различимо показывает runnable/running/blocking/contention symptoms.

### Ограничения

G/M/P интерпретируются как runtime implementation model Go 1.27.1, а не language guarantee.

### Acceptance criteria

Для каждого workload описан observed scheduler symptom и выбран подходящий diagnostic tool.

### Команды проверки

```bash
go test -trace=trace.out -run TestSchedulerLab ./...
go tool trace trace.out
GODEBUG=schedtrace=1000 go test -run TestSchedulerLab -v ./...
```

## Задание 10. GC trade-off lab

### Условие

На synthetic allocation workload сравнить controlled runs с разным `GOGC` и отдельно realistic `GOMEMLIMIT`.

### Входные данные

Одинаковый workload; несколько documented GC configurations.

### Ожидаемое поведение

Наблюдаются trade-offs CPU, GC frequency, allocation/live heap и peak memory; не существует обязательного «лучшего» universal setting.

### Ограничения

Microbenchmark results не переносить напрямую в production; слишком низкий memory limit, вызывающий thrashing, использовать только controlled/local.

### Acceptance criteria

Report показывает CPU/memory trade-off и объясняет difference `GOGC` vs `GOMEMLIMIT`.

### Команды проверки

```bash
GOGC=50 go test -bench=BenchmarkAlloc -benchmem ./...
GOGC=200 go test -bench=BenchmarkAlloc -benchmem ./...
GOMEMLIMIT=256MiB go test -bench=BenchmarkAlloc -benchmem ./...
```

## Общая проверка

```bash
gofmt -w .
go test ./...
go test -race ./...
go vet ./...
go test -bench=. -benchmem ./...
```

Все intentional panics/deadlocks/races должны жить в isolated tests/examples и не ломать обычный suite.
