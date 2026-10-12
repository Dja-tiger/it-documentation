# Stage 12 — Performance и diagnostics

## Цель

Научиться оптимизировать Go service по evidence: benchmark/profile/trace → hypothesis → change → повторное измерение.

## Перед началом

Concurrency, HTTP, DB, tests и production lifecycle.

## Прочитать

Порядок важен:

1. [[../../docs/diagnostics|Диагностика Go-программ]].
2. [Package testing — benchmarks](https://pkg.go.dev/testing#hdr-Benchmarks).
3. [runtime/pprof](https://pkg.go.dev/runtime/pprof) и `go tool pprof` по необходимости.
4. [[../../docs/build-cover|Application coverage]] — test diagnostics, не performance tool, но полезен для realistic workloads.
5. [[../../docs/gc-guide|GC Guide]]: сначала sections про allocations/escape/CPU-memory trade-off, только после profiles.
6. [[../../docs/pgo|Profile-guided optimization]] — после устойчивого representative workload.
7. [[../../docs/godebug|GODEBUG]] как diagnostics reference (`gctrace`, `schedtrace`, `inittrace`).

## Что необходимо понять

- [ ] benchmark до оптимизации и после неё.
- [ ] CPU profile — где тратится CPU.
- [ ] heap `alloc_*` vs `inuse_*` — allocation pressure vs retention.
- [ ] goroutine/block/mutex profiles — lifecycle/contention.
- [ ] runtime trace отвечает на timing/scheduling questions, а не заменяет pprof.
- [ ] escape analysis — compiler diagnostic после найденного hotspot, не global target.
- [ ] stack vs heap с точки зрения compiler/runtime, а не ручного memory management.
- [ ] `GOGC`/`GOMEMLIMIT` — CPU↔memory controls, а не magic tuning knobs.
- [ ] PGO требует representative profile и проверяемого benefit.

## Что НЕ нужно пока изучать

- assembler optimization;
- GC pacer internals;
- hand-written lock-free code;
- PGO до появления representative workload;
- «zero allocations» как универсальную цель.

## Практика

- [[../practice/13-performance|Performance lab]].

## Эксперименты

- benchmark naive vs preallocated batching, сравнить `allocs/op`, но выбрать design по evidence/readability;
- создать allocation-heavy parser и найти hotspot через profile;
- намеренно создать mutex contention и найти его profile/trace;
- выполнить `go build -gcflags=-m=3` только для найденного hotspot и сопоставить escape message с profile;
- сравнить GC behavior при разных controlled workloads, не делая production tuning conclusions из microbenchmark.

## Проверка себя

1. Как отличить memory retention от высокой allocation rate?
2. Когда нужен CPU profile, heap profile, block/mutex profile, trace?
3. Почему escape to heap не является автоматически bug?
4. Как `GOMEMLIMIT` взаимодействует с GC pressure?
5. Почему representative profile критичен для PGO?
6. Что должно входить в performance regression benchmark?

## Практическая проверка

Выбрать один measurable bottleneck `price-processor`, снять baseline benchmark/profile, сформулировать hypothesis, оптимизировать, повторить измерение и сохранить краткий report с trade-offs. Изменение принимается только при доказанном benefit без нарушения tests/race checks.

## Критерий завершения

Я могу перейти дальше, если способен:

- выбрать правильный diagnostic tool по symptom;
- читать top/call graph/alloc profile на базовом уровне;
- измерить allocation/CPU change;
- объяснить stack/heap/escape без мифов;
- не менять GC/PGO knobs без workload evidence.

## Следующий этап

[[13-language-specification|Stage 13 — Specification]].
