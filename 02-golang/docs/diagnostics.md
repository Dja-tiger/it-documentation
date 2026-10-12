---
title: "Диагностика Go-программ"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/diagnostics.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Диагностика Go-программ

Go ecosystem предоставляет набор APIs/tools для logic и performance diagnostics. Основные категории:

1. **Profiling** — где расходуются CPU/memory и какие code paths дорогие.
2. **Tracing** — latency/lifecycle calls и runtime scheduling/events.
3. **Debugging** — pause/inspect execution state.
4. **Runtime statistics/events** — high-level health, utilization, GC, goroutines.

Некоторые diagnostic tools влияют друг на друга: precise memory profiling может искажать CPU profile, block profiling — scheduler behavior. Для точных измерений собирайте profiles изолированно.

## Profiling

Runtime выдаёт profiles в формате, понимаемом `pprof`. Собирать можно через:

- `go test` flags;
- `runtime/pprof`;
- HTTP endpoints `net/http/pprof`.

### Built-in profiles

| Profile | Что показывает |
|---|---|
| `cpu` | Где program активно расходует CPU cycles. |
| `heap` | Samples allocations/current/live memory, полезен для leaks и allocation pressure. |
| `threadcreate` | Code paths, приводящие к созданию OS threads. |
| `goroutine` | Stack traces текущих goroutines. |
| `block` | Где goroutines блокируются на synchronization primitives/timers; включается `runtime.SetBlockProfileRate`. |
| `mutex` | Lock contention; включается `runtime.SetMutexProfileFraction`. |

### External profilers

Linux `perf` полезен для native/cgo/kernel bottlenecks. На macOS доступен Instruments.

### Production profiling

Profiling production services допустим, но имеет overhead. Перед включением оцените cost на representative workload.

Для replicated service практичный pattern — периодически profiling одной случайной replica ограниченное время и сохранение результатов для анализа. Не собирайте одновременно все expensive profile types без необходимости.

### Visualization

`go tool pprof` поддерживает:

- text top;
- call graphs;
- source/web lists;
- flame graphs;
- callgrind-oriented views.

Custom profile можно создать через `pprof.Profile`.

### Custom pprof endpoint

`net/http/pprof` не обязан использовать default mux/path. Например:

```go
package main

import (
    "log"
    "net/http"
    "net/http/pprof"
)

func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("/custom_debug_path/profile", pprof.Profile)
    log.Fatal(http.ListenAndServe(":7777", mux))
}
```

В production diagnostic endpoints должны быть защищены network/auth policy: profiles могут раскрывать sensitive operational data.

## Tracing

Tracing анализирует latency по цепочке calls. Go предоставляет runtime execution trace и APIs в standard library; distributed tracing обычно подключается через ecosystem instrumentation.

Tracing помогает:

- измерять latency отдельных components;
- видеть RPC chain user request;
- находить serialization/contention/under-utilization;
- диагностировать integration issues, заметные только в distributed production environment.

Go не перехватывает автоматически каждый function call для создания spans. Application/library instrumentation должна явно создавать и завершать spans.

Trace IDs/context обычно передаются через `context.Context`. Конкретный representation/propagation определяет tracing system/library.

Low-level HTTP client lifecycle можно instrument через `net/http/httptrace.ClientTrace`.

## Debugging

Наиболее распространённый Go-native debugger — **Delve**. GDB поддерживается, но Go runtime scheduling/stacks/types отличаются от модели, на которую GDB ориентирован, поэтому Delve обычно удобнее.

Compiler optimizations (inlining, registerization) могут затруднять inspection variables/frames.

Build без optimizations:

```bash
go build -gcflags=all="-N -l"
```

Для optimized builds Go генерирует DWARF; historically использовались location-list options для улучшения debugger experience.

### Postmortem/core dump

Core dump содержит process memory/state и полезен для postmortem analysis production crashes. Go processes можно анализировать Delve/GDB при наличии подходящего core и matching binary/debug info.

## Runtime statistics и events

### Memory/GC

`runtime.ReadMemStats` сообщает heap allocation и GC statistics. Для modern monitoring также важен `runtime/metrics`, который предоставляет stable runtime metrics API.

`runtime/debug.ReadGCStats` даёт GC pause statistics/timeline.

### Stack

```go
stack := debug.Stack()
```

Stack traces помогают увидеть active/blocked goroutines и call paths.

### Heap dump

```go
debug.WriteHeapDump(fd)
```

Операция останавливает goroutines на время snapshot и записывает heap state. Использовать в production нужно осознанно из-за stop-the-world/IO cost и потенциально sensitive data.

### Goroutine count

```go
n := runtime.NumGoroutine()
```

Trend помогает находить goroutine leaks или неожиданные concurrency changes, но single number без workload context малоинформативен.

## Runtime execution tracer

Execution tracer собирает:

- goroutine scheduling;
- syscalls;
- GC events;
- heap-related events;
- blocking/parallelism information.

Анализ:

```bash
go tool trace trace.out
```

Trace особенно полезен для:

- понимания scheduling goroutines;
- GC/runtime events;
- under-parallelization;
- serialized execution и lock contention;
- latency, вызванной syscalls/network scheduling.

Для поиска CPU/memory hot spots сначала обычно лучше pprof; trace отвечает на другой класс вопросов — **как execution распределено во времени**.

## Runtime `GODEBUG`

Runtime может печатать дополнительные diagnostics:

```bash
GODEBUG=gctrace=1 ./service
```

GC events: memory before/after collection, pause/work information.

```bash
GODEBUG=inittrace=1 ./service
```

Package initialization time/allocations.

```bash
GODEBUG=schedtrace=1000 ./service
```

Scheduler snapshot примерно каждые 1000 ms.

Optional CPU instruction extensions можно отключать:

```bash
GODEBUG=cpu.all=off ./service
```

или конкретно:

```bash
GODEBUG=cpu.avx=off ./service
```

Полный compatibility-oriented reference: [[godebug|GODEBUG]].

## Как выбрать tool

| Симптом | Начать с |
|---|---|
| Высокий CPU | CPU pprof |
| Memory growth / allocations | heap pprof + runtime metrics |
| Suspected goroutine leak | goroutine profile + `NumGoroutine` trend |
| Lock contention | mutex/block profiles, execution trace |
| Latency spikes | distributed trace + runtime trace/profile correlation |
| Scheduler/parallelism issue | `go tool trace`, `schedtrace` |
| Logic bug/state | Delve/tests/logging |
| Suspected data race | `go test -race` / [[race-detector|Race Detector]] |
| GC pressure | heap profile, `gctrace`, [[gc-guide|GC guide]] |
