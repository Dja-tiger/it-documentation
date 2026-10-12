# Practice 07 — Context, cancellation, graceful shutdown

## Задание 1. Timeout-aware worker

### Условие

Worker обрабатывает batch с simulated latency и прекращает работу при `ctx.Done()`.

### Входные данные

Несколько batches: быстрые и заведомо медленнее configured timeout.

### Ожидаемое поведение

Function возвращает context-related error/cause по выбранному contract и не оставляет goroutines после timeout.

### Ограничения

- context первым parameter;
- caller создаёт timeout и вызывает `cancel`;
- blocking channel operations cancellation-aware через `select`;
- test имеет independent safety timeout.

### Acceptance criteria

Repeated tests доказывают bounded completion и отсутствие race.

### Команды проверки

```bash
go test -race -run TestCancellation -count=20 ./...
go test -run TestCancellation -timeout=5s ./...
```

## Задание 2. Propagation chain

### Условие

Реализовать call chain `handler(ctx) → service.Process(ctx) → repository.Store(ctx)`.

### Входные данные

Root context с timeout/cancel и fake repository, который умеет наблюдать `Done()`.

### Ожидаемое поведение

Отмена root наблюдается в repository без создания нового root context внутри layers.

### Ограничения

Incoming context нельзя заменять на `context.Background()`; values, если используются, только request-scoped metadata.

### Acceptance criteria

Test доказывает propagation через все layers и корректный returned error/cause.

### Команды проверки

```bash
go test -run TestContextPropagation -v ./...
go test -race -run TestContextPropagation ./...
```

## Задание 3. Graceful shutdown pipeline

### Условие

Source генерирует work постоянно. По cancel прекратить intake, применить documented drain/abort policy, дождаться goroutines и вернуть итоговую cause.

### Входные данные

Continuous synthetic source, bounded worker pool, slow worker и cancellation signal.

### Ожидаемое поведение

New work не принимается после stop boundary; accepted work ведёт себя согласно policy; output channels закрывают owner’ы; process завершается до deadline.

### Ограничения

No goroutine leak; all blocking points observe context; shutdown deadline bounded.

### Acceptance criteria

Repeated test не показывает устойчивого роста goroutines; `-race` clean; drain/abort semantics зафиксированы.

### Команды проверки

```bash
go test -run TestGracefulShutdown -count=20 -timeout=10s ./...
go test -race -run TestGracefulShutdown ./...
```

## Intentional-break lab 1. Потерянная cancellation

### Условие

Временно заменить incoming context на `context.Background()` перед repository.

### Входные данные

Parent с коротким timeout и repository operation длиннее timeout.

### Ожидаемое поведение

Broken test показывает, что repository продолжает работу после parent cancellation.

### Ограничения

Только isolated exercise; затем propagation восстановить.

### Acceptance criteria

Regression test красный в broken version и green после исправления.

### Команды проверки

```bash
go test -run TestContextPropagation -v ./...
```

## Intentional-break lab 2. Blocked send

### Условие

Worker проверяет `ctx.Err()` только в начале, затем делает blocking `out <- result`; consumer остановлен.

### Входные данные

Unconsumed output channel и canceled context.

### Ожидаемое поведение

Broken worker зависает до test safety timeout; исправленный send через `select` завершается по cancellation.

### Ограничения

Обязателен safety timeout.

### Acceptance criteria

Можно указать точную blocking point и показать исправление без polling/sleep.

### Команды проверки

```bash
go test -run TestBlockedSendCancellation -timeout=3s -v ./...
```
