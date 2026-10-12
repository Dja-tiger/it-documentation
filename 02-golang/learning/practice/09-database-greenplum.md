# Practice 09 — Greenplum workload из Go

Это не tutorial по Greenplum. Цель — применить Go `database/sql`, batching, context и bounded concurrency к знакомой MPP-системе.

## Задание 1. Batch writer

### Условие

Взять 100000 `PriceUpdate`, разбить по 3000 и загрузить в staging table Greenplum выбранным driver-supported способом.

### Входные данные

100000+ generated records, configurable batch size и test/stage Greenplum endpoint.

### Ожидаемое поведение

Concurrency bounded; cancellation прекращает новые batches; ошибки содержат batch identity/context; restart semantics predictable.

### Ограничения

No goroutine per row; DB concurrency — configuration parameter и учитывает cluster/connection limits; не использовать production для destructive tests.

### Acceptance criteria

Есть counters: rows attempted/accepted, batches succeeded/failed, duration, pool wait stats. Все input records accounted for по выбранной failure policy.

### Команды проверки

```bash
go test ./...
go test -race ./...
go test -run TestGreenplumBatchIntegration -v ./...
```

## Задание 2. Read → process → write

### Условие

Реализовать streaming flow `Greenplum source query → rows.Scan → validation/batcher → bounded workers → sink`.

### Входные данные

Source result больше одного batch и records с invalid domain values.

### Ожидаемое поведение

Source не materialize’ится целиком в RAM без причины; downstream slowdown создаёт bounded backpressure.

### Ограничения

`Rows`/context lifecycle корректны; queues bounded; transaction scope не растягивается на весь job без обоснования.

### Acceptance criteria

Memory usage определяется in-flight batches, а не полным dataset; counts read/valid/invalid/written сходятся.

### Команды проверки

```bash
go test -run TestReadProcessWrite -v ./...
go test -race -run TestReadProcessWrite ./...
```

## Задание 3. Cancellation drill

### Условие

Отменить job во время long-running DB operation.

### Входные данные

Job context с manual cancel/timeout и workload, гарантированно активный в момент cancellation.

### Ожидаемое поведение

New batches не стартуют; goroutines завершаются; partial work соответствует documented transaction/idempotency policy; connection возвращается/закрывается согласно driver behavior.

### Ограничения

Safety timeout обязателен; тестировать на non-production environment.

### Acceptance criteria

После cancel нет hanging goroutines; повторный запуск ведёт себя согласно restart contract.

### Команды проверки

```bash
go test -run TestGreenplumCancellation -v -timeout=20s ./...
go test -race -run TestGreenplumCancellation ./...
```

## Задание 4. Connection budget

### Условие

Задать application concurrency budget исходя из DB connection limit и других workloads.

### Входные данные

Max DB connections, chosen worker count, queue size, expected parallel processes и query timeout.

### Ожидаемое поведение

Application не создаёт скрытую DB concurrency выше documented budget; saturation приводит к bounded wait/timeout.

### Ограничения

Budget должен оставлять headroom для других workloads/operations; worker count не равен автоматически max pool size.

### Acceptance criteria

README отвечает: max open connections; workers holding queries; saturation behavior; queue timeout; monitored `DB.Stats()` fields.

### Команды проверки

```bash
go test -run TestConnectionBudget -v ./...
go test -race ./...
```
