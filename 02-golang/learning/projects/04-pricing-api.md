# Project 4 — `pricing-api`

## Цель

Собрать HTTP service вокруг domain/service/repository слоёв и довести его до production-shaped lifecycle.

## После каких stages

[[../stages/09-http-and-json|HTTP/JSON]], затем hardening через [[../stages/10-production-go|Production Go]] и [[../stages/11-security-and-hardening|Security]].

## Архитектура

```text
net/http
   ↓
JSON transport + validation
   ↓
service
   ↓
repository
   ↓
PostgreSQL
```

Bulk endpoint:

```text
HTTP stream/batch
      ↓
validation
      ↓
bounded worker pool
      ↓
repository
```

## Минимальные endpoints

- health/readiness по осознанному contract;
- `GET /prices/{store_id}/{plu_id}`;
- `POST /prices/validate`;
- `POST /prices/batch`.

## Production requirements

- `http.Server` с explicit timeouts;
- request body limits;
- `r.Context()` до repository;
- stable JSON error model;
- configuration validation;
- `log/slog` structured logs;
- DB pool budgets;
- retry только на классифицированные transient dependency errors;
- rate/concurrency limiting для expensive/external operations;
- signal-driven graceful shutdown;
- `govulncheck`, `go vet`, race tests;
- fuzz parser/input boundary.

## Acceptance criteria

- unit tests domain/service;
- handler tests через `httptest`;
- integration PostgreSQL tests;
- cancellation test client/request → DB fake/real boundary;
- graceful shutdown test/drill;
- no data race under concurrent handler workload;
- no secrets in logs;
- README содержит config/run/test and architecture.

## Operational questions

Перед завершением ответить:

1. максимальное число concurrent DB operations;
2. максимальное число in-flight bulk batches;
3. что происходит при downstream slowdown;
4. какой timeout на каждом boundary;
5. какие operations retryable/idempotent;
6. как service ведёт себя при shutdown;
7. какие metrics/log fields нужны on-call engineer.

## Следующий проект

[[05-pricing-pipeline|Final Project — pricing-pipeline]].
