# Practice 06 — Concurrency track

Выполнять строго по порядку. Не начинайте с worker pool, пока не можете предсказать behavior базовых channels.

## Задание 1. Goroutine + `WaitGroup`

### Условие

Запустить 10 independent price validation tasks и корректно дождаться их завершения.

### Входные данные

10 `Price`, включая valid и invalid records.

### Ожидаемое поведение

Все 10 tasks завершаются; result count стабилен между запусками.

### Ограничения

- synchronization через `WaitGroup`;
- `time.Sleep` запрещён как способ «подождать goroutines»;
- ошибки должны быть собраны deterministic способом.

### Acceptance criteria

100 повторных test runs не теряют tasks; `-race` clean.

### Команды проверки

```bash
go test -run TestWaitGroup -count=100 ./...
go test -race -run TestWaitGroup ./...
```

## Задание 2. Unbuffered channel

### Условие

Producer отправляет `Price`, consumer принимает и валидирует.

### Входные данные

Несколько records и channel capacity `0`.

### Ожидаемое поведение

Send синхронизируется с receive; consumer получает каждый отправленный record.

### Ограничения

Один owner отвечает за создание/закрытие lifecycle; никаких sleeps для coordination.

### Acceptance criteria

Можно объяснить, в какой точке send/receive block и какой synchronization edge возникает.

### Команды проверки

```bash
go test -run TestUnbuffered -v ./...
go test -race -run TestUnbuffered ./...
```

## Задание 3. Buffered channel

### Условие

Повторить producer/consumer с capacities `1`, `3`, `100`.

### Входные данные

Один и тот же finite set prices и разные capacities.

### Ожидаемое поведение

До запуска предсказать, сколько sends могут завершиться без одновременного receiver.

### Ограничения

Не считать buffer автоматически worker/concurrency limit.

### Acceptance criteria

Для каждого capacity объяснено blocking behavior и distinction «queue capacity vs active workers».

### Команды проверки

```bash
go test -run TestBuffered -v ./...
go test -race -run TestBuffered ./...
```

## Задание 4. `range` + `close`

### Условие

Producer отправляет finite stream и закрывает output; consumer читает `for v := range ch`.

### Входные данные

0, 1 и N price records.

### Ожидаемое поведение

Consumer завершается после закрытия и drain channel.

### Ограничения

Receiver не закрывает input channel; close делает owner/send side после завершения всех sends.

### Acceptance criteria

Tests не зависают на empty/non-empty streams; ownership можно объяснить словами.

### Команды проверки

```bash
go test -run TestRangeClose -v ./...
go test -race -run TestRangeClose ./...
```

## Задание 5. `select`

### Условие

Worker ждёт work либо stop/cancellation signal.

### Входные данные

Jobs channel, stop channel/timer и scenarios: work ready, stop ready, оба ready.

### Ожидаемое поведение

Worker реагирует на available cases без busy loop; code не зависит от deterministic priority при нескольких ready cases.

### Ограничения

`default` добавлять только если нужен non-blocking behavior; запрещён spin loop.

### Acceptance criteria

Tests покрывают work/stop paths; можно объяснить semantics выбора ready case.

### Команды проверки

```bash
go test -run TestSelect -count=50 ./...
go test -race -run TestSelect ./...
```

## Задание 6. Shared counter: race → Mutex → atomic

### Условие

100 goroutines увеличивают общий counter. Реализовать unsafe version, затем исправить `Mutex`, затем equivalent atomic counter.

### Входные данные

100 goroutines × N increments.

### Ожидаемое поведение

Unsafe version обнаруживается race detector; synchronized versions дают exact count и race-clean result.

### Ограничения

- unsafe variant только isolated test/lab;
- atomic использовать после понимания mutex solution;
- multi-field invariant нельзя «исправить» набором независимых atomics без доказательства.

### Acceptance criteria

Есть сохранённое объяснение race и trade-off mutex/atomic.

### Команды проверки

```bash
go test -race -run TestCounterRace ./...
go test -race -run TestCounterMutex -count=20 ./...
go test -race -run TestCounterAtomic -count=20 ./...
```

## Задание 7. Worker pool для batches

### Условие

100000 prices режутся по 3000 и обрабатываются максимум `N` workers.

### Входные данные

Generated prices, часть с validation error; `N=1`, `N>1`, slow-worker scenario.

### Ожидаемое поведение

Concurrency bounded; каждый accepted batch обработан ровно один раз; pipeline завершается deterministic; backpressure появляется при saturated queue.

### Ограничения

- никаких goroutine per record;
- queue capacity задан явно;
- worker count configuration-bound;
- ownership/close rules описаны.

### Acceptance criteria

Tests покрывают empty input, `N=1`, parallel workers, slow worker и worker error; `-race` clean.

### Команды проверки

```bash
go test -run TestWorkerPool -v ./...
go test -race -run TestWorkerPool -count=20 ./...
```

## Задание 8. Fan-out / fan-in

### Условие

Один source распределяет jobs нескольким workers, затем results объединяются в один stream.

### Входные данные

N batches, 3+ workers с разной simulated latency.

### Ожидаемое поведение

Все results доходят до sink; fan-in закрывается только после завершения всех producer workers.

### Ограничения

Не полагаться на порядок завершения workers; ordering guarantee, если нужен, задаётся отдельно.

### Acceptance criteria

No hang при раннем завершении одного worker; exact result cardinality; `-race` clean.

### Команды проверки

```bash
go test -run TestFanOutFanIn -count=20 ./...
go test -race -run TestFanOutFanIn ./...
```

## Задание 9. Full pipeline

### Условие

Собрать:

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

### Входные данные

Synthetic stream от 0 до 100000 `Price`, включая invalid records и slow sink scenario.

### Ожидаемое поведение

Каждый stage имеет owner output channel; finite input приводит к complete finite shutdown; slow downstream создаёт bounded backpressure.

### Ограничения

Все queues bounded; нет hidden goroutines без termination path.

### Acceptance criteria

Cardinality/invariants сходятся; goroutine topology описана; repeated `-race` suite green.

### Команды проверки

```bash
go test -run TestPipeline -count=20 ./...
go test -race -run TestPipeline -count=20 ./...
```

## Задание 10. Deadlock lab

### Условие

Намеренно создать три deadlock classes: send без receiver; receive, который никто больше не удовлетворит/close; cyclic wait через lock/channel/resource.

### Входные данные

Минимальные isolated toy programs/tests с safety timeout.

### Ожидаемое поведение

Каждый scenario воспроизводится controlled способом; можно нарисовать wait-for graph.

### Ограничения

Deadlocks не должны попадать в normal suite без timeout/subprocess isolation.

### Acceptance criteria

Для каждого случая описаны «кто кого ждёт», diagnostic/timeout symptom и исправляющий design.

### Команды проверки

```bash
go test -run TestDeadlockLab -timeout=5s -v ./...
```

## Финальная проверка track

```bash
gofmt -w .
go test ./...
go test -race -count=20 ./...
go vet ./...
```
