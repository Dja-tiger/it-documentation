# Practice 07 — Context, cancellation, graceful shutdown

## Задание 1. Timeout-aware worker

### Условие

Worker обрабатывает batch с simulated latency и должен прекращать работу при `ctx.Done()`.

### Входные данные

Несколько batches, часть дольше timeout.

### Ожидаемое поведение

Function возвращает `context.DeadlineExceeded`/контекстную cause по выбранному contract и не оставляет goroutines.

### Ограничения

- context первым parameter;
- caller создаёт timeout и вызывает `cancel`;
- все potentially blocking channel operations cancellation-aware через `select`.

### Acceptance criteria

Test имеет свой safety timeout и доказывает bounded completion.

### Команды проверки

```bash
go test -race -run TestCancellation -count=20 ./...
```

## Задание 2. Propagation chain

### Условие

Реализовать signatures уровня:

```text
handler(ctx)
  → service.Process(ctx)
    → repository.Store(ctx)
```

Repository пока simulated. Отмена root должна наблюдаться на нижнем уровне.

### Acceptance criteria

Ни один layer не заменяет incoming context на `Background()`.

## Задание 3. Graceful shutdown pipeline

### Условие

Source генерирует work постоянно. По cancel:

1. прекратить принимать новую work;
2. выбрать и документировать policy: drain accepted work или abort;
3. дождаться goroutines;
4. закрыть outputs только owner’ами;
5. вернуть итоговую error/cause.

### Acceptance criteria

Repeated test не увеличивает goroutine count устойчиво после завершения; `-race` clean.

## Intentional-break lab

### Потерянная cancellation

В service layer вызвать repository с `context.Background()`. Test должен показать, что timeout верхнего уровня больше не останавливает repository. Исправить propagation.

### Blocked send

Worker проверяет `ctx.Err()` только в начале, затем делает blocking `out <- result`. Отменить pipeline, когда consumer остановлен. Исправить send через `select`.

## Data Engineering scenario

Смоделировать NiFi/Airflow-like job execution:

```text
job context
   ↓
CSV/API source
   ↓
worker pool
   ↓
external sink
```

При cancellation job новые batches не стартуют, текущие operations получают context, shutdown bounded.
