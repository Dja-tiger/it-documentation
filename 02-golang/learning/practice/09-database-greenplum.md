# Practice 09 — Greenplum workload из Go

Это не tutorial по Greenplum. Цель — применить Go `database/sql`, batching, context и bounded concurrency к знакомой MPP-системе.

## Задание 1. Batch writer

### Условие

Взять 100000 `PriceUpdate`, разбить по 3000 и загрузить в staging table Greenplum выбранным driver-supported способом.

### Ожидаемое поведение

- bounded number concurrent database operations;
- cancellation прекращает новые batches;
- error содержит batch identity/context;
- повторный запуск имеет явную idempotency policy.

### Ограничения

Не запускать goroutine на row. Максимальная DB concurrency — configuration parameter и должна учитывать cluster/connection limits.

### Acceptance criteria

Есть metrics/counters как минимум: rows attempted, rows accepted, batches succeeded/failed, duration, pool wait stats.

## Задание 2. Read → process → write

### Архитектура

```text
Greenplum source query
        ↓
rows.Scan stream
        ↓
validation/batcher
        ↓
bounded workers
        ↓
Greenplum/PostgreSQL sink
```

### Ожидаемое поведение

Не материализовать весь source result в RAM без причины. `Rows`/context lifecycle корректны. Backpressure ограничивает in-flight data.

## Задание 3. Cancellation drill

Отменить job во время long-running DB operation. Проверить:

- Go goroutines завершились;
- connection вернулась/закрылась согласно driver behavior;
- new batches не стартовали;
- partial work соответствует заранее выбранной transaction/idempotency model.

## Задание 4. Connection budget

### Условие

Задать application concurrency budget исходя из DB connection limit и других workloads.

### Acceptance criteria

В README ответить:

1. сколько максимальных open connections у process;
2. сколько workers одновременно могут держать query;
3. что происходит при saturation;
4. какой timeout защищает очередь;
5. какие `DB.Stats()` показатели мониторить.

## Команды проверки

```bash
go test -race ./...
go test ./...
```

Integration tests с реальным Greenplum запускать отдельным profile/tag/environment, не делая unit suite зависимым от production cluster.
