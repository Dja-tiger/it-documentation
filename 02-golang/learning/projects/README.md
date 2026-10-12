# Практические проекты

Проекты идут от небольшого single-process CLI к production-oriented Data Engineering service. Каждый следующий reuse’ит идеи предыдущего, но не требует тащить весь старый code без рефакторинга.

## Правило проекта

До начала реализации:

1. сформулировать input/output contract;
2. нарисовать package/lifecycle boundaries;
3. определить failure/cancellation policy;
4. записать acceptance criteria;
5. только затем писать code.

Готовое решение здесь намеренно отсутствует.

## Последовательность

1. [[01-price-cli|Project 1 — price-cli]] — structs, slices, maps, files, JSON/CSV, errors, tests.
2. [[02-price-processor|Project 2 — price-processor]] — goroutines, channels, worker pool, context, shutdown.
3. [[03-price-storage|Project 3 — price-storage]] — PostgreSQL, `database/sql`, transactions, pool, context.
4. [[04-pricing-api|Project 4 — pricing-api]] — `net/http`, JSON, DB, logging, config, graceful shutdown.
5. [[05-pricing-pipeline|Final Project — pricing-pipeline]] — production-oriented data processing service с PostgreSQL/Greenplum, observability, performance work и optional Kafka source.

## Quality gate для всех проектов

Минимум:

```bash
gofmt -w .
go test ./...
go vet ./...
```

Начиная с Project 2:

```bash
go test -race ./...
```

Для каждого repository/project README фиксирует:

- purpose;
- architecture;
- run/test commands;
- config;
- failure/cancellation policy;
- known limitations.

## Когда проект считается checkpoint’ом

Не когда «happy path работает», а когда можно удалить implementation и по README/tests восстановить contract заново.
