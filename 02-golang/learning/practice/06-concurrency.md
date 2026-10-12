# Practice 06 — Concurrency track

Выполнять строго по порядку. Не начинайте с worker pool, пока не можете предсказать behavior базовых channels.

## 1. Goroutine + synchronization

### Условие

Запустить 10 independent price validation tasks и корректно дождаться их завершения.

### Ограничения

Сначала решение через `WaitGroup`, без `time.Sleep` как synchronization.

### Acceptance criteria

100 повторных запусков не теряют tasks.

## 2. Unbuffered channel

### Условие

Producer отправляет `Price`, consumer принимает и валидирует.

### Эксперимент

Убрать consumer. До запуска предсказать, где block/deadlock.

## 3. Buffered channel

### Условие

Повторить с capacity 1, 3, 100.

### Acceptance criteria

Объяснить, какие sends могут завершиться до receive и почему buffer не является автоматически worker limit.

## 4. Range + close

### Условие

Producer отправляет конечный stream и закрывает channel. Consumer читает `for v := range ch`.

### Ограничения

Receiver не закрывает input channel.

### Эксперимент

Double close и send after close выполнить только в локальном toy program; классифицировать panic.

## 5. Select

### Условие

Worker ждёт work либо cancellation-like stop channel/timer. Добавить non-blocking case только после понимания trade-off.

### Acceptance criteria

Нет busy loop.

## 6. Shared counter: race → Mutex → atomic

### Условие

100 goroutines увеличивают общий counter.

### Шаги

1. намеренно unsafe implementation;
2. запустить race detector;
3. исправить `Mutex`;
4. только затем реализовать equivalent atomic counter;
5. объяснить, почему atomic не масштабируется автоматически на multi-field invariant.

### Команды проверки

```bash
go test -race -count=20 ./...
```

## 7. Worker pool для batches

### Условие

100000 prices режутся по 3000 и обрабатываются максимум `N` workers.

### Входные данные

Генерируемые `Price`, в части records validation error.

### Ожидаемое поведение

- concurrency bounded;
- каждый accepted batch обработан ровно один раз;
- errors собираются по выбранной стратегии;
- pipeline завершается deterministic.

### Ограничения

- никаких goroutine per record;
- queue capacity задан явно;
- ownership/close rules описаны comment/README.

### Acceptance criteria

Tests на `N=1`, `N>1`, empty input, slow worker, worker error. `-race` clean.

## 8. Fan-out / fan-in

Один source → несколько workers → один result stream. Реализовать fan-in без зависания при завершении части workers.

## 9. Pipeline

```text
reader
  ↓
validator
  ↓
batcher
  ↓
workers
  ↓
results
  ↓
writer
```

Каждый stage имеет чёткий owner output channel.

## 10. Deadlock lab

Намеренно создать минимум три разных deadlock class:

- send без receiver;
- receive после того, как никто больше не send/close;
- goroutine ждёт lock/channel, удерживая resource, необходимый другой стороне.

Для каждого написать causal graph «кто кого ждёт».

## Финальная проверка

```bash
gofmt -w .
go test ./...
go test -race -count=20 ./...
go vet ./...
```
