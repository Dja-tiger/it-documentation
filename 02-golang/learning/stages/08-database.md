# Stage 8 — `database/sql`: PostgreSQL и Greenplum

## Цель

Научиться использовать `database/sql` как production database boundary: connection pool, query/scan, transactions, prepared statements, context cancellation и resource lifecycle.

## Перед началом

Errors/testing, concurrency и context.

## Прочитать

Проходить именно существующий local layer:

1. [[../../docs/tutorial/database-access|Tutorial: доступ к реляционной БД]].
2. [[../../docs/database/index|database/sql overview]].
3. [[../../docs/database/open-handle|Открытие DB handle]].
4. [[../../docs/database/querying|Querying]].
5. [[../../docs/database/change-data|Change data]].
6. [[../../docs/database/prepared-statements|Prepared statements]].
7. [[../../docs/database/execute-transactions|Transactions]].
8. [[../../docs/database/cancel-operations|Cancellation]].
9. [[../../docs/database/manage-connections|Connection pool]].
10. [[../../docs/database/sql-injection|SQL injection]].
11. [Package database/sql](https://pkg.go.dev/database/sql) — API reference.

Официальный tutorial использует MySQL для примера. Практику этого stage выполнять на PostgreSQL, затем отдельно на Greenplum.

## Что необходимо понять

- [ ] `*sql.DB` — concurrency-safe pool handle, а не одна connection.
- [ ] `sql.Open` не обязан устанавливать connection немедленно; `PingContext` проверяет доступность.
- [ ] `QueryRowContext`, `QueryContext`, `ExecContext` и scopes `DB`/`Tx`/`Stmt`.
- [ ] `rows.Close()` и `rows.Err()` как обязательный lifecycle.
- [ ] PostgreSQL placeholders `$1`, `$2`, ... .
- [ ] transaction lifecycle `BeginTx` → operations through `Tx` → commit/rollback.
- [ ] `defer tx.Rollback()` safety pattern.
- [ ] connection pool limits и `DB.Stats()`.
- [ ] cancellation должна доходить до database operation.
- [ ] parameterization защищает values от injection; dynamic identifiers требуют allowlist.

## Что НЕ нужно пока изучать

- ORM как замена пониманию `database/sql`;
- driver internals/protocol implementation;
- distributed transaction protocols;
- Greenplum query planner internals — они относятся к DB expertise, не к Go basics.

## Практика

1. [[../practice/08-database-postgresql|PostgreSQL practice]].
2. [[../practice/09-database-greenplum|Greenplum practice]].

## Эксперименты

- безопасно локально ограничить pool до 1–2 connections и показать ожидание/timeout;
- намеренно удержать `Rows`, не закрывая его, и наблюдать `DB.Stats()`/pool starvation; затем исправить;
- отменить `pg_sleep` через `QueryContext` timeout;
- внутри `Tx` ошибочно вызвать `db.ExecContext` вместо `tx.ExecContext`, объяснить почему operation вне transaction;
- собрать небезопасный dynamic identifier only в toy example и заменить allowlist mapping.

## Проверка себя

1. Почему `sql.DB` нужно переиспользовать, а не создавать на каждый request?
2. Чем `QueryRowContext` отличается от `QueryContext` по lifecycle?
3. Почему `rows.Close` влияет на pool?
4. Почему ограниченный pool может вести себя как semaphore и где возникает deadlock?
5. Что именно отменяет context: Go waiting, driver operation или DB statement — и от чего зависит эффект?
6. Почему parameter placeholder нельзя использовать вместо table name?

## Практическая проверка

С нуля реализовать PostgreSQL repository для `PriceUpdate` с методами чтения batch, upsert/write по выбранному contract и transaction для atomic multi-step operation. Все public operations получают `context.Context`; pool configured явно; integration tests проверяют rollback и cancellation.

После этого адаптировать read/write workload к Greenplum с осознанным batching и без assumptions о `LastInsertId`.

## Критерий завершения

Я могу перейти дальше, если способен:

- объяснить lifecycle pool/Rows/Tx;
- написать context-aware repository;
- не смешивать `DB` и `Tx` внутри transaction;
- диагностировать pool exhaustion через stats;
- корректно параметризовать PostgreSQL SQL;
- описать, какие части Greenplum workload нужно менять относительно OLTP PostgreSQL.

## Следующий этап

[[09-http-and-json|Stage 9 — HTTP and JSON]].
