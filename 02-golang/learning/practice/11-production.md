# Practice 11 — Production engineering

## Задание 1. Configuration contract

### Условие

Определить config для HTTP address/timeouts, DB DSN/pool, worker count/queue capacity, external API rate/retry limits.

### Входные данные

Valid config и invalid variants: zero/negative timeout, zero workers, pool size ниже required concurrency, missing required field.

### Ожидаемое поведение

Invalid config отклоняется до начала processing/listening; valid config даёт полностью определённые resource budgets.

### Ограничения

Secrets читаются через environment/secret boundary и не выводятся целиком; defaults должны быть явными и безопасными.

### Acceptance criteria

Tests покрывают invalid timeout, worker count, pool size и missing fields; startup не создаёт partial service при invalid config.

### Команды проверки

```bash
go test -run TestConfig -v ./...
go test ./...
```

## Задание 2. Structured logging

### Условие

Через `log/slog` логировать operation, batch/request identifier, record count, duration и error classification.

### Входные данные

Success, validation error, dependency timeout и retry scenario.

### Ожидаемое поведение

Logs структурированы и позволяют связать lifecycle одного batch/request без parsing arbitrary text.

### Ограничения

Не логировать raw credentials, authorization headers и full sensitive payload автоматически.

### Acceptance criteria

Test handler/collector проверяет presence required attributes и отсутствие secret value.

### Команды проверки

```bash
go test -run TestLogging -v ./...
```

## Задание 3. Retry with exponential backoff

### Условие

Сымитировать transient external API failures и реализовать bounded retry.

### Входные данные

Success first try; two transient failures then success; permanent validation/auth failure; endless transient failure; cancellation during backoff.

### Ожидаемое поведение

Transient failures retry’ятся в рамках budget; permanent — нет; cancellation немедленно прекращает ожидание/следующую попытку.

### Ограничения

Maximum attempts/elapsed budget, backoff, optional jitter; operation должна быть idempotent или иметь explicit dedup/idempotency mechanism.

### Acceptance criteria

Tests детерминированно проверяют attempt count и cancellation без реального long sleep, используя injectable clock/backoff strategy при необходимости.

### Команды проверки

```bash
go test -run TestRetry -v ./...
go test -race -run TestRetry ./...
```

## Задание 4. Rate limiting

### Условие

Ограничить обращения к simulated external API по RPS и/или concurrent-request policy.

### Входные данные

Burst выше лимита, steady flow ниже лимита и context cancellation во время ожидания permit.

### Ожидаемое поведение

Burst не создаёт unbounded goroutines/queue; requests допускаются согласно policy; canceled waiter выходит быстро.

### Ограничения

Rate limit и concurrency limit рассматриваются отдельно; очередь ожидания bounded или ограничена context/deadline.

### Acceptance criteria

Test измеряет верхнюю границу admitted concurrency/rate с разумным tolerance и проверяет cancellation.

### Команды проверки

```bash
go test -run TestRateLimit -v ./...
go test -race -run TestRateLimit ./...
```

## Задание 5. Graceful shutdown drill

### Условие

Запустить HTTP requests и background batch workers, затем инициировать shutdown.

### Входные данные

Normal request, slow request, active batch, queued batch и shutdown signal/root cancel.

### Ожидаемое поведение

Listener перестаёт принимать new work; root context отменён; workers следуют drain/abort policy; DB закрывается после завершения users; process укладывается в shutdown deadline.

### Ограничения

No arbitrary sleep as lifecycle mechanism; каждый background component имеет owner и wait path.

### Acceptance criteria

Shutdown test deterministic, `-race` clean, после завершения нет known goroutine leak.

### Команды проверки

```bash
gofmt -w .
go test -run TestGracefulShutdown -v -timeout=15s ./...
go test -race ./...
go vet ./...
```
