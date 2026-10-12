# Practice 13 — Performance lab

## Задание 1. Benchmark batching

### Условие

Сравнить минимум две реализации batching/aggregation на representative batch sizes.

### Ограничения

Результаты должны использоваться, чтобы compiler не устранил useful work. Подготовку fixtures отделить от measured region где возможно.

### Acceptance criteria

Зафиксировать `ns/op`, `B/op`, `allocs/op` и объяснить, что именно изменилось.

### Команды проверки

```bash
go test -bench=. -benchmem ./...
```

## Задание 2. CPU profile

Создать CPU-heavy transformation над price batches и собрать profile через benchmark/test/application mechanism.

### Acceptance criteria

Назвать top hot functions и cumulative path; предложить hypothesis до изменения кода.

### Команды проверки

```bash
go test -bench=BenchmarkProcess -cpuprofile=cpu.out ./...
go tool pprof cpu.out
```

## Задание 3. Heap/allocation profile

### Условие

Сравнить `alloc_space` и live/in-use view для parser/aggregation workload.

### Acceptance criteria

Не путать «много выделили за всё время» и «много удерживаем сейчас».

## Задание 4. Contention

Создать controlled version с global mutex вокруг aggregation и concurrent workers. Затем найти contention через mutex/block profile или runtime trace.

## Задание 5. Escape analysis after profiling

Только для выбранного hot allocation site:

```bash
go build -gcflags=-m=3 ./...
```

Сопоставить compiler message с source/design. Не переписывать весь code ради исчезновения каждого escape.

## Задание 6. PGO experiment

После появления representative final-service workload:

1. собрать CPU profile;
2. build baseline;
3. build с explicit `-pgo`;
4. выполнить одинаковый benchmark/load test;
5. зафиксировать benefit/regression/build trade-off.

PGO experiment считается необязательным до появления representative service workload.
