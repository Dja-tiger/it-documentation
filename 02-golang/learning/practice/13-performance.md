# Practice 13 — Performance lab

Главное правило: baseline → hypothesis → measurement → change → repeated measurement. Не оптимизировать по ощущению.

## Задание 1. Benchmark batching

### Условие

Сравнить минимум две реализации batching/aggregation на representative batch sizes.

### Входные данные

Sizes `100`, `3000`, `100000`; realistic `Price` shape.

### Ожидаемое поведение

Benchmark показывает reproducible difference или отсутствие meaningful difference.

### Ограничения

Compiler не должен устранить useful work; fixture preparation отделена от measured region где возможно.

### Acceptance criteria

Зафиксированы `ns/op`, `B/op`, `allocs/op`; выбор implementation объяснён не только цифрой, но и readability/complexity trade-off.

### Команды проверки

```bash
go test -bench=BenchmarkBatch -benchmem -count=5 ./...
```

## Задание 2. CPU profile

### Условие

Создать CPU-heavy transformation над price batches и снять profile.

### Входные данные

Representative dataset и benchmark/load duration, достаточная для useful samples.

### Ожидаемое поведение

Profile выявляет top/self/cumulative hot paths.

### Ограничения

До изменения code записать hypothesis; synthetic hotspot не переносить автоматически в production conclusions.

### Acceptance criteria

Названы минимум один top function и call path; выбран candidate optimization с reasoning.

### Команды проверки

```bash
go test -bench=BenchmarkProcess -cpuprofile=cpu.out ./...
go tool pprof -top cpu.out
```

## Задание 3. Heap/allocation profile

### Условие

Исследовать parser/aggregation workload по allocation и live memory views.

### Входные данные

Representative batch workload с repeat processing.

### Ожидаемое поведение

Можно различить высокий cumulative allocation и retained/in-use memory.

### Ограничения

Не считать любой allocation leak’ом; использовать одинаковый workload для сравнений.

### Acceptance criteria

Report отдельно описывает allocation pressure и retention; минимум один source location подтверждён profile.

### Команды проверки

```bash
go test -bench=BenchmarkProcess -memprofile=mem.out ./...
go tool pprof -top -alloc_space mem.out
go tool pprof -top -inuse_space mem.out
```

## Задание 4. Contention profile

### Условие

Создать controlled version с global mutex вокруг aggregation при concurrent workers и найти contention.

### Входные данные

Several workers, shared aggregation state и high enough operation count.

### Ожидаемое поведение

Mutex/block profile или trace показывает waiting/contention path.

### Ограничения

Intentional contention живёт в lab variant; final design определяется measurement, а не запретом mutex как такового.

### Acceptance criteria

Найдена точка contention; предложены минимум два design options и измерен выбранный variant.

### Команды проверки

```bash
go test -run TestContention -mutexprofile=mutex.out -blockprofile=block.out ./...
go tool pprof -top mutex.out
go tool pprof -top block.out
```

## Задание 5. Escape analysis after profiling

### Условие

Только для выбранного hot allocation site запустить compiler escape diagnostics.

### Входные данные

Function/source location, уже найденные heap/allocation profile.

### Ожидаемое поведение

Compiler объясняет escape/inlining decisions; их можно сопоставить с profile.

### Ограничения

Не переписывать весь project ради исчезновения каждого escape; optimization должна иметь measured benefit.

### Acceptance criteria

Для одного hotspot записано: что escapes, почему, можно ли изменить и какой benchmark effect.

### Команды проверки

```bash
go build -gcflags=-m=3 ./...
go test -bench=BenchmarkProcess -benchmem -count=5 ./...
```

## Задание 6. PGO experiment

### Условие

После появления representative final-service workload сравнить baseline build и build с PGO.

### Входные данные

Representative CPU profile `default.pgo`/explicit profile и одинаковый benchmark/load test.

### Ожидаемое поведение

Получить measurable benefit, neutral result или regression — любой вариант допустим при корректном measurement.

### Ограничения

Не использовать нерепрезентативный microprofile как production PGO profile; correctness tests обязательны для обоих builds.

### Acceptance criteria

Report содержит baseline/PGO numbers, variance, build/runtime trade-off и решение use/not use.

### Команды проверки

```bash
go build -pgo=off ./...
go build -pgo=default.pgo ./...
go test ./...
go test -bench=. -benchmem -count=5 ./...
```
