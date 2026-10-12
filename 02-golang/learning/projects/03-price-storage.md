# Project 3 — `price-storage`

## Цель

Освоить production patterns `database/sql` на PostgreSQL и затем перенести batch workload на Greenplum.

## После какого stage

[[../stages/08-database|Stage 8 — Database]].

## Архитектура

```text
service/use case
      ↓
repository interface
      ↓
database/sql
      ↓
PostgreSQL
```

Отдельный integration scenario:

```text
batch source/process
      ↓
Greenplum staging/sink
```

## Функции PostgreSQL variant

- open + `PingContext`;
- pool configuration;
- get price by key;
- query N prices;
- insert/upsert price update;
- atomic multi-step transaction;
- context timeout/cancellation;
- pool stats exposure/logging for lab.

## Ограничения

- public repository methods принимают `context.Context`;
- `Rows`/`Stmt`/`Tx` resources имеют явный lifecycle;
- values parameterized;
- dynamic identifiers только allowlist;
- no `sql.Open` per request;
- integration DB отделена от unit tests.

## Acceptance criteria

- integration test success/rollback;
- query cancellation test;
- pool exhaustion lab безопасно воспроизводится локально;
- DB errors получают operation context без leakage DSN/password;
- connection budget documented;
- PostgreSQL-specific behavior (`returning`, placeholders) не маскируется MySQL assumptions tutorial.

## Greenplum checkpoint

Добавить workload 100000+ records batches по 3000 и bounded DB concurrency. Зафиксировать:

- distribution/staging contract считается внешним DB concern;
- Go layer отвечает за streaming, batch size, retries/cancellation, connection budget и error context;
- idempotency/restart semantics описаны.

## Следующий проект

[[04-pricing-api|Project 4 — pricing-api]].
