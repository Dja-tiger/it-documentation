# Practice 11 — Production engineering

## Задание 1. Configuration contract

### Условие

Определить config для HTTP address/timeouts, DB DSN/pool, worker count/queue capacity, external API rate/retry limits.

### Ожидаемое поведение

Invalid config отклоняется до startup processing. Secrets читаются из environment/secret boundary и не выводятся целиком.

### Acceptance criteria

Есть tests на invalid timeout, worker count, pool size и missing required fields.

## Задание 2. Structured logging

### Условие

Через `log/slog` логировать минимум `operation`, `store_id`/batch id, duration, record count, error classification.

### Ограничения

Не логировать raw credentials/full sensitive payload автоматически.

### Acceptance criteria

Test handler/collector может проверить presence ключевых attributes.

## Задание 3. Retry with exponential backoff

### Условие

Сымитировать transient external API failures.

### Ожидаемое поведение

Retry имеет maximum attempts/elapsed budget, backoff, optional jitter и немедленно прекращается по context cancellation.

### Ограничения

Permanent validation/auth errors не retry’ятся. Operation должна быть безопасной относительно duplicates либо иметь idempotency mechanism.

### Acceptance criteria

Tests проверяют success after transient failures, permanent failure, exhausted budget, cancellation during backoff.

## Задание 4. Rate limiting

### Условие

Ограничить обращения к simulated external API по RPS/concurrency policy.

### Ожидаемое поведение

Burst не создаёт unbounded goroutines/queue; waiting operation отменяется по context.

## Задание 5. Graceful shutdown drill

Запустить HTTP requests + background batch workers, инициировать shutdown и доказать:

- listener перестал принимать new traffic;
- root context отменён;
- workers obey выбранную drain/abort policy;
- DB закрывается только после завершения пользователей;
- process завершился до shutdown deadline.

### Команды проверки

```bash
gofmt -w .
go test ./...
go test -race ./...
go vet ./...
```
