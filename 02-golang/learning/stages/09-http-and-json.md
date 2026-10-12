# Stage 9 — HTTP и JSON

## Цель

Построить context-aware HTTP API с typed JSON contracts, validation, service layer и database boundary.

## Перед началом

Context, `database/sql`, interfaces/errors/testing.

## Прочитать

1. [[../../docs/articles/wiki|Writing Web Applications]] — официальный пример на `net/http`.
2. [Package net/http](https://pkg.go.dev/net/http) — `Server`, `Handler`, `Request`, `Client`, timeout/lifecycle APIs по мере необходимости.
3. [[../../docs/tutorial/web-service-gin|REST API с Gin]] — как второй official tutorial, обращая внимание на distinction `gin.Context` vs `context.Context`.
4. [[../../docs/tutorial/json|JSON tutorial]].
5. [[../../docs/jsonv2-migration|Migration to encoding/json/v2]].
6. [encoding/json](https://pkg.go.dev/encoding/json) — canonical legacy API reference для чтения существующего ecosystem code.
7. Security note: [[../../docs/security/threat-model|Threat Model]] — JSON/HTTP input является trust boundary.

## Что необходимо понять

- [ ] `http.Handler`/`HandlerFunc`, request/response lifecycle.
- [ ] `r.Context()` и propagation в service/DB.
- [ ] status codes и structured error response contract.
- [ ] JSON struct tags, exported fields, typed request/response structs.
- [ ] streaming decode/encode через reader/writer where appropriate.
- [ ] validation после decode, до business operation.
- [ ] body/request size limits как production concern.
- [ ] difference между legacy `encoding/json` и текущим Go 1.27 `json/v2` path из local tutorial.
- [ ] server timeouts и graceful shutdown.

## Что НЕ нужно пока изучать

- framework ecosystem comparison;
- custom protocol/RPC implementation;
- reflection-heavy validation framework internals;
- HTTP/2/3 wire protocol internals.

## Практика

- [[../practice/10-http-json|HTTP/JSON pricing API]].

## Эксперименты

- отправить unknown/malformed/duplicate fields и зафиксировать выбранный JSON contract;
- прервать client request и проверить, доходит ли cancellation до simulated DB call;
- оставить request body неограниченным в toy version, затем добавить explicit limit;
- запустить concurrent writes к in-memory slice из tutorial под `-race` и объяснить, почему demo storage не production-safe;
- сравнить `null` и empty collection semantics там, где wire contract это различает.

## Проверка себя

1. Чем `http.Request.Context()` отличается от framework context object?
2. Где заканчивается decoding и начинается domain validation?
3. Почему `float64` для денежных production contracts требует осознанного решения?
4. Кто отвечает за timeout: client, server, context, DB — и как они сочетаются?
5. Какие JSON defaults v2 делают более строгими security semantics?
6. Что происходит с DB query при client disconnect, если context корректно propagated?

## Практическая проверка

С нуля реализовать на `net/http` flow:

```text
HTTP request
   ↓
JSON decode
   ↓
validation
   ↓
service
   ↓
PostgreSQL repository
   ↓
JSON response
```

Затем endpoint bulk processing:

```text
HTTP upload
   ↓
stream/batches
   ↓
bounded worker pool
   ↓
DB
```

## Критерий завершения

Я могу перейти дальше, если способен:

- написать small `net/http` service без framework dependency;
- провести context до DB;
- сформулировать stable JSON contract;
- ограничить resources/time;
- покрыть handlers/service integration tests;
- объяснить, когда Gin добавляет value, а когда скрывает fundamentals.

## Следующий этап

[[10-production-go|Stage 10 — Production Go]].
