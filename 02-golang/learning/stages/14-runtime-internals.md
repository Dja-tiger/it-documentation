# Stage 14 — Runtime internals

## Цель

Связать наблюдаемое production behavior с runtime model: happens-before, allocation/escape, stack/heap, GC, scheduling, preemption и low-level diagnostics. Цель — уметь диагностировать, а не переписывать runtime.

## Перед началом

Concurrency, context, performance profiling и [[13-language-specification|Specification stage]].

## Прочитать

Порядок принципиален:

1. [[../../docs/memory-model|Go Memory Model]] — системно.
2. Повторить [[../../docs/diagnostics|Diagnostics]]: goroutine/block/mutex profiles и runtime trace.
3. [[../../docs/gc-guide|GC Guide]] — allocation/escape → stack/heap → GC cost model → `GOGC`/`GOMEMLIMIT`.
4. [[../../docs/godebug|GODEBUG]] — `gctrace`, `schedtrace`, `inittrace` и compatibility model.
5. [Package runtime](https://pkg.go.dev/runtime) и [runtime/pprof](https://pkg.go.dev/runtime/pprof) как API reference.
6. Scheduler source — официальный pinned Go source, только после diagnostics: [runtime/proc.go at go1.27.1](https://github.com/golang/go/blob/go1.27.1/src/runtime/proc.go).
7. [[../../docs/asm|Go assembler]] — optional deep dive, когда нужно читать compiler/runtime/assembly output.
8. [[../../docs/security/fuzz/technical|Fuzzing technical details]] — optional example tool/runtime architecture.

## Что необходимо понять

- [ ] happens-before и DRF-SC practical consequences.
- [ ] goroutine creation synchronizes start, но termination само по себе не является synchronization.
- [ ] stack grows/runtime manages goroutine stacks; heap placement определяется escape/lifetime analysis implementation.
- [ ] escape to heap ≠ автоматически performance bug.
- [ ] GC mark/sweep cost связан с live heap, pointer graph и allocation rate.
- [ ] `GOGC` — proportional CPU/memory trade-off.
- [ ] `GOMEMLIMIT` — soft runtime memory limit и риск thrashing при unrealistic target.
- [ ] scheduler concepts G/M/P как implementation model, а не language semantics.
- [ ] blocked/runnable/running goroutines и связь с trace/schedtrace.
- [ ] preemption нужна runtime для fairness/GC/scheduling; exact mechanics version-specific.
- [ ] runtime source/assembler — implementation details baseline Go 1.27.1.

## Что НЕ нужно пока изучать

- менять runtime source;
- писать production assembly без измеренной необходимости;
- полагаться на undocumented scheduler behavior для correctness;
- ручное «управление stack vs heap» через cargo-cult tricks;
- GC tuning до profiling/metrics.

## Практика

- [[../practice/14-spec-runtime-labs|Specification/runtime labs]] — runtime section.

## Эксперименты

- data race → race detector → synchronization → объяснение happens-before edge;
- profile allocation-heavy workload, затем посмотреть escape analysis только hotspot;
- собрать execution trace при worker contention;
- сравнить `GODEBUG=schedtrace=...` с фактическим workload;
- controlled experiment `GOGC`/`GOMEMLIMIT`, наблюдая CPU/memory, без переноса выводов напрямую в prod;
- посмотреть compiler output/objdump одной маленькой function только после high-level understanding.

## Проверка себя

1. Что из G/M/P гарантирует language spec? Ничего: это runtime implementation model — почему это важно?
2. Какие события создают happens-before через channel/mutex?
3. Почему `main` return может оборвать другие goroutines?
4. Чем allocation rate отличается от live heap?
5. Когда GC assist становится заметным symptom?
6. Что выбрать при latency spike: pprof, trace, block/mutex profile или DB metrics?
7. Чем `GOGC` отличается от `GOMEMLIMIT`?
8. Почему VSS не равен Go heap/RSS?

## Практическая проверка

Для final pricing pipeline подготовить runtime diagnosis report:

- goroutine topology;
- synchronization edges;
- CPU/heap profile;
- один runtime trace;
- pool/queue saturation observation;
- GC/runtime metrics interpretation;
- минимум одна evidence-based optimization или обоснованный вывод «optimization не нужна».

## Критерий завершения

Я завершаю базовый маршрут, если способен:

- объяснить correctness concurrent code через synchronization, а не timing;
- диагностировать CPU/memory/contention/goroutine symptoms правильными tools;
- объяснить stack/heap/escape/GC на уровне production engineer;
- читать `schedtrace`/trace без превращения runtime internals в API contract;
- применять эти знания к [[../projects/05-pricing-pipeline|final project]].

## Следующий этап

[[../projects/05-pricing-pipeline|Final Project — production pricing pipeline]].
