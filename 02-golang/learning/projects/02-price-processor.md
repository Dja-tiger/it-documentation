# Project 2 — `price-processor`

## Цель

Превратить последовательную обработку price records в bounded concurrent pipeline с корректным cancellation/shutdown.

## После каких stages

[[../stages/06-concurrency|Concurrency]] + [[../stages/07-context-and-cancellation|Context]].

## Архитектура

```text
streaming reader
      ↓
validation
      ↓
batcher (max 3000)
      ↓
bounded jobs channel
      ↓
N workers
      ↓
results channel
      ↓
writer/report
```

## Функции

- читать input stream;
- валидировать;
- собирать batches;
- обрабатывать их параллельно;
- собирать result/error statistics;
- прекращать pipeline по context timeout/cancel;
- корректно закрывать channels и дожидаться workers.

## Обязательные design decisions

README должен отвечать:

- кто owner каждого channel;
- кто его закрывает;
- queue capacities;
- worker count;
- first-error vs collect-errors policy;
- drain vs abort policy после cancellation;
- порядок shutdown.

## Acceptance criteria

- no goroutine per record;
- max concurrency bounded;
- records/batches не теряются и не process’ятся дважды по contract;
- cancellation завершается за bounded time;
- slow consumer создаёт backpressure, а не unbounded memory growth;
- `go test -race -count=20 ./...` clean;
- intentional race/deadlock exercises существуют отдельно и не входят в normal suite.

## Failure drills

1. worker возвращает error на batch N;
2. writer замедляется;
3. input context timeout;
4. consumer прекращает чтение results;
5. один worker panic — самостоятельно определить policy: recover boundary или process failure, и обосновать.

## Проверка mastery

С нуля нарисовать goroutine/channel graph и объяснить termination condition каждого node.

## Следующий проект

[[03-price-storage|Project 3 — price-storage]].
