# Stage 10 — Production Go

## Цель

Перевести учебный service из состояния «работает» в состояние «имеет управляемый lifecycle, bounded resources и понятную operational model».

## Перед началом

Работающий concurrent HTTP/DB service.

## Прочитать

1. [[../../docs/effective-go|Effective Go]] — перечитать после реальной практики; не воспринимать как exhaustive modern reference.
2. [[../../docs/modules/layout|Организация Go module]].
3. [[../../docs/comment|Go Doc Comments]].
4. [[../../docs/editors|Editor/tooling baseline]] — `gopls`, gofmt, tests, vet, Delve.
5. [Package log/slog](https://pkg.go.dev/log/slog).
6. [Package os/signal](https://pkg.go.dev/os/signal) для process shutdown wiring.
7. [Package time](https://pkg.go.dev/time) для retry/backoff/rate timing primitives.

## Что необходимо понять

- [ ] `main` выполняет wiring/lifecycle, а не содержит business logic.
- [ ] configuration отделена от code; secrets не логируются.
- [ ] structured logs содержат operation/request/job identifiers и error context.
- [ ] retry разрешён только для классифицированных transient failures и имеет limit/backoff/jitter policy.
- [ ] rate limiting и concurrency limiting — разные controls.
- [ ] every queue/pool имеет capacity/budget.
- [ ] graceful shutdown координирует HTTP, workers, DB и background goroutines.
- [ ] health/readiness semantics отражают реальные dependencies/lifecycle.
- [ ] exported API документирует concurrency/zero-value guarantees.

## Что НЕ нужно пока изучать

- огромные framework/platform abstractions;
- distributed tracing vendor details;
- Kubernetes operator development;
- micro-optimization без profile.

## Практика

- [[../practice/11-production|Production engineering practice]].

## Эксперименты

- сделать retry без limit и показать amplification risk на падающем dependency;
- сделать unbounded queue и сравнить memory/backpressure behavior с bounded queue;
- завершить process без ожидания workers, затем исправить coordinated shutdown;
- случайно логировать DSN/secret в toy config и добавить redaction rule/test.

## Проверка себя

1. Какие goroutines существуют после startup и кто отвечает за их stop?
2. Чем retry budget отличается от request timeout?
3. Где должен применяться rate limit — до или после expensive work — и почему?
4. Что означает readiness во время shutdown?
5. Какие поля structured log нужны для расследования одного pricing batch?
6. Как понять, что configuration invalid до начала обработки traffic?

## Практическая проверка

Довести `pricing-api` до состояния, где есть config validation, `slog`, root context, signal-driven shutdown, bounded worker pool, retry policy, rate limit и documented resource budgets. Любая background goroutine имеет owner и termination path.

## Критерий завершения

Я могу перейти дальше, если способен:

- нарисовать startup/shutdown lifecycle process;
- объяснить budgets connections/goroutines/queues/retries/timeouts;
- добавить operational logging без leakage secrets;
- безопасно остановить service под load;
- отделить transport/wiring от domain/storage logic.

## Следующий этап

[[11-security-and-hardening|Stage 11 — Security and hardening]].
