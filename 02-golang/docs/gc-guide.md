---
title: "Руководство по Garbage Collector Go"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/gc-guide.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Руководство по Garbage Collector Go

Этот guide предназначен для advanced Go users, которым нужно понимать стоимость GC и настраивать CPU/memory trade-off приложения. Документ относится к standard Go toolchain (`gc` compiler/runtime); specification языка не требует конкретного garbage collector implementation.

## Где живут Go values

Не вся memory управляется GC.

Local values, lifetime которых compiler может определить статически, часто размещаются на goroutine stack. Освобождение такой memory связано с lexical/control lifetime и не требует tracing GC.

Если lifetime определить нельзя, value **escapes to heap**. Причины включают dynamic lifetime/size, возврат references, сохранение pointer в escaping object и другие результаты escape analysis.

Escape behavior — implementation detail compiler и меняется между Go versions. Не стоит проектировать correctness, опираясь на точные эвристики escape analysis.

## Tracing garbage collection

Go runtime использует tracing, non-moving, mark-sweep GC.

Термины:

- **object** — dynamically allocated memory, содержащая один или несколько Go values;
- **pointer** — reference/address на value внутри object; GC также отслеживает pointer-like части strings, slices, maps, channels, interfaces и других runtime representations;
- **object graph** — objects + references между ними;
- **roots** — исходные references, однозначно используемые program: globals, active stacks и др.;
- **reachable/live** — object достижим из roots;
- **scan** — traversal object graph;
- **mark** — отметка live object;
- **sweep** — возврат unmarked memory allocator'у.

Go GC не перемещает обычные heap objects во время collection, в отличие от moving collectors.

## GC cycle

Broad phases:

1. **sweep** previous dead objects;
2. GC может быть **off** до следующего trigger;
3. **mark/scan** current live object graph;
4. завершение cycle и переход к следующему sweep.

Memory нельзя безопасно reclaim до завершения tracing: ещё не просканированный pointer может сделать object reachable.

## Cost model

Для reasoning guide использует три идеи.

### 1. Два основных ресурса

GC расходует:

- physical memory;
- CPU time.

### 2. Memory cost

Упрощённо:

```text
GC memory cost for cycle N =
    live heap from cycle N-1 + new heap allocated during cycle N
```

Metadata overhead существует, но обычно вторичен относительно heap.

Live heap определяется workload/program, а не напрямую GC.

### 3. CPU cost

Упрощённо:

```text
GC CPU time for cycle N =
    fixed cost per cycle +
    average scanning cost per byte * live heap
```

Dominant cost — mark/scan live object graph. Большое количество pointers, linked structures и плохо parallelizable graphs делают scanning дороже.

Sweep в current implementation существенно дешевле marking/scanning, поэтому модель обычно им пренебрегает.

## Fundamental trade-off CPU ↔ memory

Если GC запускается чаще:

- peak heap меньше;
- GC CPU overhead выше.

Если реже:

- memory footprint выше;
- GC CPU overhead ниже.

В steady-state пример guide показывает: при fixed live heap удвоение времени между cycles примерно вдвое снижает GC CPU overhead, но увеличивает new heap между cycles.

## `GOGC`

`GOGC` — основной proportional tuning parameter.

Target heap:

```text
Target heap memory =
    Live heap + (Live heap + GC roots) * GOGC / 100
```

Roots входят в pacing formula с Go 1.18.

Пример: live heap 8 MiB + roots 2 MiB.

- `GOGC=100` → примерно 10 MiB allowance new memory;
- `GOGC=50` → примерно 5 MiB;
- `GOGC=200` → примерно 20 MiB.

Practical intuition:

> Удвоение `GOGC` примерно удваивает heap overhead и примерно вдвое снижает GC CPU cost; уменьшение действует наоборот.

Настройка:

```bash
GOGC=200 ./service
```

или runtime API:

```go
debug.SetGCPercent(200)
```

Отключение GC, если memory limit не требует collection:

```bash
GOGC=off ./service
```

эквивалентно `debug.SetGCPercent(-1)`.

Target — цель, не absolute guarantee. Large allocations, concurrent pacing и scheduling могут привести к overshoot.

## Soft memory limit

Go 1.19 добавил runtime memory limit:

```bash
GOMEMLIMIT=4GiB ./service
```

либо:

```go
debug.SetMemoryLimit(limit)
```

Runtime accounting соответствует примерно:

```text
runtime.MemStats.Sys - runtime.MemStats.HeapReleased
```

или `runtime/metrics`:

```text
/memory/classes/total:bytes
- /memory/classes/heap/released:bytes
```

Limit учитывает runtime-managed memory, но не всю memory process/environment. Например, memory внутри C library через cgo может быть runtime неизвестна.

### Взаимодействие `GOGC` и memory limit

GC использует более строгую из constraints:

- proportional heap target от `GOGC`;
- target, необходимый для удержания runtime memory около memory limit.

Даже `GOGC=off` не отключает GC, если soft memory limit требует collection.

### Thrashing

Слишком низкий limit при большом live heap может заставлять GC работать почти постоянно, не позволяя application сделать progress. Это называется **thrashing**.

Чтобы снизить риск полного stall, memory limit **soft**, а не hard. Runtime ограничивает GC CPU примерно 50% на rolling window порядка `2 * GOMAXPROCS` CPU-seconds и при необходимости может превысить memory limit.

Идея: лучше временно использовать больше memory, чем бесконечно тратить CPU на невозможную цель.

### Рекомендованные случаи

Хорошо использовать memory limit, когда execution environment контролируется, например container с фиксированным memory reservation.

Официальный guide предлагает оставлять примерно **5–10% headroom** на memory, которую Go runtime не учитывает.

Limit можно менять динамически, например при временном росте cgo/C memory.

Не рекомендуется:

- hard-code'ить limit в CLI/desktop app, где environment/input неизвестны;
- использовать `GOGC=off + memory limit` при некоординированных co-tenants;
- выставлять limit вплотную к already high live working set только ради предотвращения OOM — это может заменить fast OOM на severe slowdown.

## Latency

Go GC делает большую часть mark work **concurrently** с application, чтобы не превращать heap size в proportional stop-the-world latency.

Concurrent GC платит некоторым throughput overhead, но значительно улучшает latency predictability.

Lower GC frequency часто улучшает и latency, не только CPU throughput.

Источники GC-related latency:

1. short stop-the-world transitions между phases;
2. CPU scheduling competition с mark workers;
3. **GC assists** — allocating goroutine сама выполняет GC work, если allocation опережает collector;
4. write-barrier work на pointer writes во время marking;
5. suspension goroutines для scanning roots/stacks.

Для анализа используйте execution traces.

## Finalizers, cleanups и weak pointers

Обычный GC создаёт illusion, что death object не наблюдаема. Но runtime предоставляет low-level mechanisms:

- `runtime.AddCleanup`;
- `weak.Pointer`;
- `runtime.SetFinalizer`.

Они позволяют реагировать на object death и поэтому усложняют GC semantics.

### General advice

- Пишите tests: timing nondeterministic.
- Не используйте эти mechanisms напрямую в обычном application code без сильной причины.
- Encapsulate их внутри package.
- Не exposing raw objects с cleanup/finalizer без необходимости.
- Non-memory resources лучше освобождать deterministic API (`Close`), а cleanup/finalizer оставить safety net.
- Для Go 1.24+ **предпочитайте cleanup finalizer'у**, если finalizer-specific ordering/resurrection semantics не нужны.

### Почему finalizers сложнее

Finalizer получает object и тем самым временно **resurrects** его. Consequences:

- object memory нельзя reuse до следующего GC cycle;
- cycles с finalizers могут вообще не освобождаться;
- chains finalizer objects могут требовать многих GC cycles;
- один object имеет ограниченный finalizer model.

Cleanups гибче и не требуют resurrection.

### Cleanup traps

Cleanup function/argument не должны удерживать object reachable.

Плохо:

```go
f := new(myFile)
f.fd = syscall.Open(...)
runtime.AddCleanup(f, func(fd int) {
    syscall.Close(f.fd) // captures f: cleanup не сможет выполниться
}, f.fd)
```

Cleanup order не гарантирован; cleanups могут выполняться concurrently. Long-running cleanup должна быстро delegate'ить длительную work, например goroutine.

`runtime.GC()` только queue'ит cleanups/finalizers, но не ждёт их completion.

### Weak pointers

`weak.Pointer.Value()` может начать возвращать `nil` в неожиданное с точки зрения application время — всегда нужен `nil` handling.

Weak pointer как map key не делает map value weak. Если value сохраняет strong path назад к pointed object, object остаётся reachable.

### Finalizer traps

- object не должен быть в self/reference cycle;
- finalizer closure не должен capture object через outer variable;
- chain из N finalized objects может потребовать минимум N GC cycles;
- long-running finalizer не должен блокировать other finalizers;
- `runtime.GC` не ждёт execution finalizers.

### Testing object death

- не запускайте такие tests параллельно без необходимости;
- используйте `runtime.GC` для baseline/queueing;
- добавляйте explicit test synchronization с cleanup/finalizer (channel/state);
- для chain finalizers потребуется несколько GC calls;
- запускайте tests с `-race`.

## Virtual memory

Virtual address space ≠ physical memory. Go runtime может резервировать большой VSS дешёво и освобождать backing physical pages отдельно.

Поэтому VSS часто плохая metric Go memory footprint. Для operational monitoring обычно полезнее:

- RSS/process working set;
- runtime memory classes;
- heap/live allocation metrics;
- container/cgroup memory.

Runtime не обязан unmap'ить всю virtual region при освобождении physical memory. На 64-bit systems большие address-space reservations нормальны.

## Optimization guide

### Сначала докажите, что GC — проблема

Не оптимизируйте allocations вслепую.

Порядок диагностики:

1. CPU profile.
2. Execution trace для latency/scheduling.
3. Heap profiles.
4. При глубокой runtime diagnostics — `gctrace`/`gcpacertrace`.

### CPU profile symbols

Полезные cumulative paths:

- `runtime.gcBgMarkWorker` — background mark work;
- `runtime.mallocgc` — heap allocator path; высокий cumulative share указывает на heavy allocation;
- `runtime.gcAssistAlloc` — application goroutines помогают GC; значительный share означает allocation rate, опережающий GC pacing.

Idle mark workers могут занимать «свободный» CPU при low application utilization, поэтому profile interpretation требует context.

### GC traces

```bash
GODEBUG=gctrace=1 ./service
```

Deep pacer diagnostics:

```bash
GODEBUG=gcpacertrace=1 ./service
```

Pacer trace предназначен прежде всего для runtime-level debugging и требует знания implementation.

## Уменьшение heap allocations

Снижение allocation rate снижает GC frequency, а значит может дать крупный CPU/latency выигрыш.

### Heap profile views

Memory profile можно анализировать по:

- `inuse_objects` — число live objects;
- `inuse_space` — bytes live objects;
- `alloc_objects` — cumulative count allocations;
- `alloc_space` — cumulative allocated bytes.

Для GC pressure особенно важны cumulative allocation rate (`alloc_*`), а для memory retention — `inuse_*`.

### Escape analysis

Compiler может показать причины heap escape:

```bash
go build -gcflags=-m=3
```

Output очень verbose. Используйте его после profile-driven identification hot allocation sites, а не как global optimization target.

### API design

Allocations могут быть следствием API shape:

- возвращаемый pointer/heap-owned object;
- interface boxing;
- growing slices/maps;
- conversions strings/bytes;
- closures;
- temporary buffers.

Но reducing allocations ценой сложного ownership, pooling или incorrect lifecycle часто не оправдан. Benchmark before/after.

### `sync.Pool`

`sync.Pool` может amortize temporary allocation cost, но:

- entries могут быть удалены GC в любой момент;
- Pool не предназначен для deterministic cache;
- выигрыш зависит от allocation pattern;
- pooled objects нужно reset'ить корректно.

## Additional resources

Upstream guide рекомендует:

- GC Handbook;
- TCMalloc design;
- Go 1.5 concurrent GC announcement;
- “Getting to Go” GC evolution talk;
- concurrent GC pacing design;
- smarter scavenging design;
- scalable page allocator design;
- Go 1.18 GC pacer redesign;
- Go 1.19 soft memory limit design.

Главная operational идея: настройка GC — это workload-specific CPU/memory/latency trade-off. Начинайте с measurements, а не с магических `GOGC` values.
