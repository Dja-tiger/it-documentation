# Stage 7 — Context и cancellation

## Цель

Научиться распространять cancellation/deadline через call chain и останавливать concurrent pipeline без утечек и orphan work.

## Перед началом

[[06-concurrency|Stage 6 — Concurrency]].

## Прочитать

1. [Package context](https://pkg.go.dev/context).
2. [[../../docs/database/cancel-operations|Отмена database operations]] — как concrete propagation example.
3. [Package net/http](https://pkg.go.dev/net/http): contract `Request.Context` — без необходимости изучать весь HTTP API сейчас.

## Что необходимо понять

- [ ] `context.Context` передаётся первым argument, не хранится произвольно в struct для request lifecycle.
- [ ] `context.Background()` как root application context.
- [ ] `WithCancel`, `WithTimeout`, `WithDeadline`.
- [ ] derived context отменяется при cancellation parent.
- [ ] `defer cancel()` освобождает resources.
- [ ] `Done()` и `Err()`.
- [ ] propagation через HTTP → service → DB.
- [ ] request-scoped values только для request metadata, не optional function parameters.
- [ ] graceful shutdown как coordinated cancellation + wait.

## Что НЕ нужно пока изучать

- custom Context implementations;
- tracing vendor APIs;
- сложные supervisor frameworks;
- context values как dependency injection.

## Практика

- [[../practice/07-context|Context & cancellation]].

## Эксперименты

- создать timeout, но не передать child context в worker — показать, почему работа продолжилась;
- забыть вызвать cancel и проанализировать lifecycle timer/resources;
- worker игнорирует `<-ctx.Done()` при blocked send — получить leak и исправить select;
- отменить parent во время simulated DB/API operation.

## Проверка себя

1. Что является источником cancellation в HTTP request?
2. Почему `context.Background()` внутри service method может быть bug?
3. Когда использовать timeout, а когда deadline?
4. Какие values допустимы в context?
5. Почему cancellation должна доходить до I/O boundary?
6. Чем «остановить intake» отличается от «дождаться уже принятой work»?

## Практическая проверка

Реализовать lifecycle:

```text
root context
   ↓
reader → worker pool → writer
   ↓          ↓          ↓
cancel propagates to every blocking operation
   ↓
WaitGroup waits
   ↓
process exits
```

Добавить test, который гарантирует завершение pipeline после cancel/timeout за bounded time.

## Критерий завершения

Я могу перейти дальше, если способен:

- провести context через несколько layers без замены parent на новый root;
- отменить blocked channel/I/O-like operation;
- корректно вызвать cancel functions;
- реализовать graceful stop worker pool;
- объяснить HTTP → service → DB cancellation chain.

## Следующий этап

[[08-database|Stage 8 — database/sql]].
