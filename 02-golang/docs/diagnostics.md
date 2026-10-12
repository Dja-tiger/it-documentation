---
title: "Диагностика"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/diagnostics.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Диагностика

## Введение {#introduction}

Go ecosystem предоставляет большой набор API и tools для диагностики logic и performance problems в Go programs. Эта страница кратко описывает доступные tools и помогает выбрать подходящий для конкретной проблемы.

Diagnostic solutions можно разделить на следующие группы:

- **Profiling** — profiling tools анализируют сложность и стоимость Go program, например memory usage и часто вызываемые functions, чтобы найти наиболее дорогие части программы.
- **Tracing** — tracing позволяет instrument code и анализировать latency на протяжении lifecycle вызова или user request. Traces показывают, какой вклад каждый component вносит в общую latency system. Trace может охватывать несколько Go processes.
- **Debugging** — debugging позволяет приостановить Go program и исследовать её execution. С его помощью можно проверить program state и flow.
- **Runtime statistics and events** — сбор и анализ runtime statistics и events даёт high-level представление о состоянии Go programs. Spikes и dips metrics помогают находить изменения throughput, utilization и performance.

> Некоторые diagnostic tools могут влиять друг на друга. Например, precise memory profiling искажает CPU profiles, а goroutine blocking profiling влияет на scheduler trace. Для более точных результатов используйте tools по отдельности.

## Profiling {#profiling}

Profiling полезен для поиска дорогих или часто вызываемых sections code. Go runtime предоставляет [profiling data](https://pkg.go.dev/runtime/pprof) в формате, который понимает [pprof visualization tool](https://github.com/google/pprof/blob/master/doc/README.md).

Profiling data можно собирать во время tests через `go test` либо через endpoints package [`net/http/pprof`](https://pkg.go.dev/net/http/pprof). После сбора данных используйте pprof tools для filtering и visualization наиболее дорогих code paths.

Predefined profiles из package [`runtime/pprof`](https://pkg.go.dev/runtime/pprof):

- **cpu** — показывает, где program проводит время, активно потребляя CPU cycles, в отличие от sleep или ожидания I/O.
- **heap** — сообщает samples memory allocations; используется для monitoring текущего и исторического memory usage и поиска memory leaks.
- **threadcreate** — показывает sections program, приводящие к созданию новых OS threads.
- **goroutine** — показывает stack traces всех текущих goroutines.
- **block** — показывает, где goroutines блокируются, ожидая synchronization primitives, включая timer channels. По умолчанию profile выключен; включается через `runtime.SetBlockProfileRate`.
- **mutex** — показывает lock contention. Если CPU используется не полностью из-за mutex contention, используйте этот profile. По умолчанию он выключен; включается через `runtime.SetMutexProfileFraction`.

### Какие ещё profilers можно использовать?

В Linux для profiling Go programs можно использовать [perf](https://perf.wiki.kernel.org/index.php/Tutorial). Perf умеет profiling и unwinding cgo/SWIG code и kernel, поэтому полезен для поиска native/kernel performance bottlenecks.

В macOS можно использовать [Instruments](https://developer.apple.com/library/content/documentation/DeveloperTools/Conceptual/InstrumentsUserGuide/).

### Можно ли profile production services?

Да. Profiling production programs безопасен, но включение некоторых profiles, например CPU profile, создаёт overhead. Следует ожидать снижения performance. Его величину нужно оценить заранее, измерив overhead profiler на representative workload.

Production services можно profile периодически. В system с большим количеством replicas одного process безопасный вариант — периодически выбирать случайную replica, profile её в течение X seconds каждые Y seconds и сохранять результаты для visualization и analysis, повторяя это регулярно.

Profiles могут влиять друг на друга, поэтому рекомендуется собирать только один profile одновременно.

### Как лучше визуализировать profiling data?

Go tools предоставляют text, graph и [callgrind](http://valgrind.org/docs/manual/cl-manual.html) visualization через [`go tool pprof`](https://github.com/google/pprof/blob/master/doc/README.md).

Практические примеры см. в официальной статье [Profiling Go programs](https://go.dev/blog/profiling-go-programs).

Официальная страница показывает несколько вариантов visualization:

- text listing наиболее дорогих calls;
- graph наиболее дорогих calls;
- **weblist**, показывающий стоимость line-by-line в source code;
- **flame graph**, позволяющий переходить по ancestry path и zoom in/out отдельных sections code.

Upstream `pprof` поддерживает flame graphs.

### Ограничены ли мы встроенными profiles?

Нет. Помимо profiles, предоставляемых runtime, Go users могут создавать собственные profiles через [`pprof.Profile`](https://pkg.go.dev/runtime/pprof#Profile) и исследовать их теми же существующими tools.

### Можно ли разместить profiler handlers на другом path и port?

Да. Package `net/http/pprof` по умолчанию регистрирует handlers на default mux, но их можно зарегистрировать вручную через exported handlers package.

Например, следующий program размещает `pprof.Profile` на port `7777`, path `/custom_debug_path/profile`:

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

## Tracing {#tracing}

Tracing — способ instrument code для анализа latency на всём lifecycle chain calls.

Go предоставляет package [`golang.org/x/net/trace`](https://pkg.go.dev/golang.org/x/net/trace) как минимальный tracing backend для отдельного Go node и минимальную instrumentation library с простым dashboard. Go также предоставляет execution tracer для tracing runtime events внутри временного interval.

Tracing позволяет:

- instrument и анализировать application latency внутри Go process;
- измерять стоимость конкретных calls в длинной chain calls;
- находить возможности улучшения utilization и performance — bottlenecks часто не видны без tracing data.

В monolithic systems diagnostic data относительно легко собирать из разных components программы: все modules находятся в одном process и используют общие resources для reporting logs, errors и другой diagnostic information.

Когда system выходит за пределы одного process и становится distributed, проследить call от front-end web server через все backends до возврата response пользователю становится значительно сложнее. Здесь важную роль играет distributed tracing.

**Distributed tracing** — способ instrument code и анализировать latency на протяжении lifecycle user request. Когда system distributed и обычные profiling/debugging tools плохо масштабируются, distributed tracing помогает анализировать performance user requests и RPCs.

Distributed tracing позволяет:

- instrument и profile application latency в большой system;
- отслеживать все RPCs на протяжении lifecycle user request и видеть integration issues, проявляющиеся только в production;
- находить performance improvements, которые невозможно увидеть до сбора tracing data.

Go ecosystem предоставляет различные distributed tracing libraries — как привязанные к конкретным tracing systems, так и backend-agnostic.

### Можно ли автоматически перехватывать каждый function call и создавать traces?

Нет. Go не предоставляет способ автоматически intercept каждый function call и создавать trace spans. Code необходимо instrument вручную: создавать, завершать и annotate spans.

### Как передавать trace headers в Go libraries?

Trace identifiers и tags можно передавать через [`context.Context`](https://pkg.go.dev/context#Context).

Единого canonical trace key или общего representation trace headers в индустрии нет. Каждый tracing provider отвечает за propagation utilities в собственных Go libraries.

### Какие low-level events standard library/runtime можно включать в trace?

Standard library и runtime предоставляют дополнительные APIs для уведомлений о low-level internal events.

Например, [`httptrace.ClientTrace`](https://pkg.go.dev/net/http/httptrace#ClientTrace) предоставляет APIs для отслеживания low-level events lifecycle outgoing request.

Также существует runtime execution tracer, который предоставляет low-level runtime events и позволяет users определять и записывать user events.

## Debugging {#debugging}

Debugging — процесс определения причин неправильного поведения program. Debuggers позволяют понять execution flow и текущее state.

Существуют разные стили debugging; здесь рассматриваются attachment debugger к program и core dump debugging.

Go users чаще всего используют:

- [Delve](https://github.com/go-delve/delve) — debugger для Go, понимающий runtime concepts и built-in types Go. Его цель — быть полнофункциональным и надёжным debugger для Go programs.
- [GDB](https://go.dev/doc/gdb) — Go поддерживает GDB через standard Go compiler и Gccgo. Однако stack management, threading и runtime Go достаточно отличаются от execution model, ожидаемой GDB, поэтому debugger может путаться даже при build через gccgo. GDB можно использовать, но он не идеален для Go.

### Насколько хорошо debuggers работают с Go programs?

Compiler `gc` выполняет optimizations, включая function inlining и variable registerization. Эти optimizations иногда усложняют debugging.

Для code, который нужно debug'ить, рекомендуется отключить optimizations:

```text
$ go build -gcflags=all="-N -l"
```

В рамках улучшения DWARF support Go 1.10 добавил compiler flag `-dwarflocationlists`, заставляющий compiler добавлять location lists, помогающие debuggers работать с optimized binaries:

```text
$ go build -gcflags="-dwarflocationlists=true"
```

### Какой debugger UI рекомендуется?

Хотя Delve и GDB предоставляют CLI, большинство editor integrations и IDE имеют собственные debugging-specific user interfaces.

### Возможен ли postmortem debugging Go programs?

Core dump file содержит memory dump работающего process и его process status. Он используется прежде всего для postmortem debugging и анализа state program.

Из Go programs можно получать core files и анализировать их через Delve или GDB. Пошаговые инструкции приведены в [Core Dump Debugging](https://go.dev/wiki/CoreDumpDebugging).

## Runtime statistics and events {#runtime}

Runtime предоставляет statistics и reports о внутренних events для диагностики performance и utilization problems на runtime level.

Monitoring этих данных помогает понимать общее состояние и performance Go programs.

Часто отслеживаемые statistics и states:

- [`runtime.ReadMemStats`](https://pkg.go.dev/runtime#ReadMemStats) сообщает metrics, связанные с heap allocation и garbage collection. Memory stats помогают контролировать memory consumption, эффективность использования памяти и находить leaks.
- [`debug.ReadGCStats`](https://pkg.go.dev/runtime/debug#ReadGCStats) читает garbage collection statistics. Это позволяет видеть, сколько resources расходуется на GC pauses, а также timeline collector pauses и pause time percentiles.
- [`debug.Stack`](https://pkg.go.dev/runtime/debug#Stack) возвращает current stack trace. Stack trace помогает понять, сколько goroutines работает, что они делают и заблокированы ли они.
- [`debug.WriteHeapDump`](https://pkg.go.dev/runtime/debug#WriteHeapDump) приостанавливает execution всех goroutines и записывает heap dump в file. Heap dump — snapshot memory Go process в конкретный момент; он содержит allocated objects, goroutines, finalizers и другие данные.
- [`runtime.NumGoroutine`](https://pkg.go.dev/runtime#NumGoroutine) возвращает число текущих goroutines. Значение можно monitoring'ить для оценки utilization или поиска goroutine leaks.

### Execution tracer {#execution-tracer}

Go включает runtime execution tracer, который собирает широкий набор runtime events: scheduling, syscalls, garbage collections, heap size и другие events.

Эти данные доступны для visualization через `go tool trace`.

Execution tracer помогает находить latency и utilization problems. Можно исследовать, насколько эффективно используется CPU и когда network или syscalls становятся причиной preemption goroutines.

Tracer полезен, чтобы:

- понимать execution goroutines;
- видеть ключевые runtime events, например GC runs;
- находить плохо parallelized execution.

При этом tracer не очень подходит для поиска hot spots, например причины чрезмерного CPU или memory usage. Для таких задач сначала используйте profiling tools.

Официальный пример visualization показывает execution, который сначала идёт нормально, а затем становится serialized. Это указывает на возможный lock contention вокруг shared resource.

Для сбора и анализа runtime traces используйте [`go tool trace`](https://pkg.go.dev/cmd/trace).

### GODEBUG {#godebug}

Runtime также выводит дополнительные events и information, если соответствующим образом задан environment variable `GODEBUG`.

- `GODEBUG=gctrace=1` печатает garbage collector events при каждой collection, включая объём собранной memory и длительность pause.
- `GODEBUG=inittrace=1` печатает summary execution time и memory allocation для завершённой package initialization работы.
- `GODEBUG=schedtrace=X` печатает scheduling events каждые X milliseconds.

`GODEBUG` также можно использовать для отключения instruction set extensions в standard library и runtime:

- `GODEBUG=cpu.all=off` отключает все optional instruction set extensions;
- `GODEBUG=cpu.<extension>=off` отключает instructions указанного instruction set extension; `<extension>` — lowercase name extension, например `sse41` или `avx`.
