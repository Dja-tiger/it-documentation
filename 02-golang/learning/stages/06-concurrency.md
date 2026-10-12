# Stage 6 — Concurrency

## Цель

Построить корректную mental model goroutines, channels и synchronization, затем применить её в bounded pricing pipeline.

## Перед началом

Core language, methods/interfaces, testing.

## Прочитать

1. [A Tour of Go — Concurrency](https://go.dev/tour/concurrency/1).
2. [Package sync](https://pkg.go.dev/sync): `WaitGroup`, `Mutex`, `RWMutex`, `Once`, `Cond` — приоритет первым трём.
3. [Package sync/atomic](https://pkg.go.dev/sync/atomic) — после mutex-based решения.
4. [[../../docs/race-detector|Data Race Detector]].
5. [[../../docs/memory-model|Memory Model]]: practical advice + synchronization sections. Полное формальное чтение будет позже.
6. Reference: [[../../docs/spec#go|go statement]], [[../../docs/spec#Channel types|channels]], [[../../docs/spec#select|select]].

## Что необходимо понять

Последовательность mastery:

- [ ] goroutine lifecycle;
- [ ] unbuffered channel;
- [ ] buffered channel;
- [ ] receive через `range`;
- [ ] ownership и `close`;
- [ ] `select`;
- [ ] `sync.WaitGroup`;
- [ ] `sync.Mutex` / `RWMutex`;
- [ ] `sync/atomic` только для подходящего low-level state;
- [ ] bounded worker pool;
- [ ] fan-out;
- [ ] fan-in;
- [ ] pipeline;
- [ ] race condition;
- [ ] deadlock;
- [ ] race detector;
- [ ] goroutine leak как lifecycle bug.

## Что НЕ нужно пока изучать

- scheduler G/M/P internals;
- lock-free algorithms ради производительности;
- тонкие memory-order tricks;
- unsafe;
- premature `sync.Pool` optimization.

## Практика

- [[../practice/06-concurrency|Concurrency track]].

## Эксперименты

- создать deadlock на unbuffered channel и объяснить отсутствующий communication partner;
- concurrent increment shared counter без synchronization и поймать `-race`;
- concurrent write в map и исследовать failure/race;
- закрыть channel не со стороны owner/sender и получить invalid lifecycle;
- изменить buffer capacity `0 → 1 → N` и предсказать blocking behavior;
- забыть дождаться goroutines и увидеть, что возврат `main` завершает process.

## Проверка себя

1. Когда channel — communication/ownership tool, а когда mutex проще и честнее?
2. Кто должен закрывать channel и почему receiver обычно этого не делает?
3. Что гарантирует unbuffered send/receive по happens-before?
4. Почему завершение goroutine само по себе не гарантирует visibility?
5. Чем buffer capacity ограничивает или не ограничивает число goroutines?
6. Почему race detector не может доказать отсутствие всех races?

## Практическая проверка

С нуля написать pipeline:

```text
reader
  ↓
channel batches
  ↓
N workers
  ↓
results channel
  ↓
writer
```

Он должен иметь bounded queues, корректное закрытие channels, deterministic completion, tests и чистый `go test -race ./...`.

## Критерий завершения

Я могу перейти дальше, если способен:

- написать worker pool без goroutine/channel leak;
- объяснить ownership каждого channel;
- найти и исправить race/deadlock;
- выбрать между channel и mutex по модели state, а не по лозунгу;
- нарисовать lifecycle goroutines до написания кода.

## Следующий этап

[[07-context-and-cancellation|Stage 7 — Context and cancellation]].
