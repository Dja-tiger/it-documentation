---
title: "Руководство по Garbage Collector Go"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/gc-guide.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Руководство по Garbage Collector Go

## Введение {#Introduction}

Это руководство предназначено для опытных Go developers, которым нужно лучше понимать стоимость работы applications через понимание Go garbage collector. Оно также объясняет, как использовать эти знания для улучшения resource utilization applications.

Знание garbage collection заранее не предполагается, но предполагается знакомство с языком Go.

Go берёт на себя ответственность за размещение Go values. В большинстве случаев developer не должен заботиться, где именно они хранятся и почему. На практике values часто должны находиться в physical memory компьютера, а physical memory — конечный resource. Поэтому memory должна управляться и повторно использоваться, чтобы program не исчерпала её.

Ответственность за allocation и recycling memory лежит на implementation Go.

**Garbage collection** — автоматическое повторное использование memory. На высоком уровне garbage collector, или GC, освобождает memory от имени application, определяя, какие участки больше не нужны.

Standard Go toolchain поставляет runtime library вместе с каждой application; эта runtime library содержит garbage collector.

Наличие garbage collector в форме, описанной здесь, **не гарантируется Go specification**. Specification гарантирует только, что underlying storage Go values управляется языком. Это сделано намеренно, чтобы другие implementations могли применять принципиально другие memory-management techniques.

Поэтому этот guide описывает конкретную implementation Go и может не относиться к другим implementations. В частности, он относится к standard toolchain — `gc` compiler и tools. Gccgo и Gollvm используют очень похожие GC implementations, поэтому многие concepts применимы и к ним, но details могут различаться.

Это living document, который меняется со временем. Основы cost model в нём исторически были описаны для Go 1.19; более новые sections страницы отражают последующие releases, включая cleanups и weak pointers.

### Где живут Go values {#Where_Go_Values_Live}

Прежде чем обсуждать GC, рассмотрим memory, которой GC управлять не нужно.

Например, non-pointer Go values в local variables часто вообще не управляются GC. Go может выделить для них memory, привязанную к lexical scope, в котором value создана.

Это обычно эффективнее GC, потому что compiler заранее знает, когда memory можно освободить, и генерирует соответствующие machine instructions.

Такое размещение обычно называют **stack allocation**, поскольку memory находится на goroutine stack.

Go values, memory которых нельзя разместить таким способом, потому что compiler не может определить lifetime, **escape to the heap**.

Heap можно рассматривать как общий storage для cases, когда Go value нужно разместить где-то, но static lifetime неизвестен.

Allocation на heap обычно называют **dynamic memory allocation**, поскольку compiler/runtime могут делать мало assumptions о том, как долго memory будет нужна. Именно здесь необходим GC.

Причин escape может быть много. Например, размер backing array slice может определяться runtime variable, а не constant.

Escape также транзитивен: если reference на value записывается в другую value, уже определённую как escaping, referenced value тоже должна escape.

Будет ли value escape, зависит от context использования и escape-analysis algorithm compiler. Пытаться точно перечислить правила хрупко: algorithm сложный и меняется между Go releases.

Как исследовать escape decisions compiler, описано в section [Escape analysis](#Escape_analysis).

### Tracing garbage collection {#Tracing_Garbage_Collection}

Garbage collection может означать разные методы автоматического recycling memory, например reference counting.

В этом документе под GC понимается **tracing garbage collection**: collector определяет используемые, то есть **live**, objects, транзитивно проходя по pointers.

Основные термины:

- **Object** — динамически allocated участок memory, содержащий одну или несколько Go values.
- **Pointer** — memory address, указывающий на value внутри object. Это не только values формы `*T`: strings, slices, channels, maps и interfaces содержат addresses, которые GC должен trace.

Objects и pointers между ними образуют **object graph**.

Чтобы найти live memory, GC обходит graph начиная с **roots** — pointers на objects, которые заведомо используются program. Примеры roots: local variables активных goroutines и global variables.

Процесс обхода graph называется **scanning**.

Object считается **reachable**, если его можно найти таким scanning.

За исключением mechanisms, обсуждаемых в [Finalizers, cleanups and weak pointers](#Finalizers_cleanups_and_weak_pointers), после того как memory стала unreachable, она остаётся unreachable.

Этот basic algorithm общий для tracing GCs. Отличие collectors — что они делают после обнаружения live memory.

Go GC использует **mark-sweep**:

1. GC **marks** encountered values как live;
2. после tracing GC проходит heap;
3. unmarked memory становится доступной allocator'у.

Последний этап называется **sweeping**.

Альтернативные collectors могут перемещать live objects в новую область memory и оставлять forwarding pointers. Такие collectors называются **moving**.

Go использует **non-moving GC**.

## GC cycle {#The_GC_cycle}

Поскольку Go GC — mark-sweep collector, он в широком смысле работает в двух phases: mark и sweep.

Важно следствие: memory нельзя вернуть allocator'у, пока tracing всего live graph не завершён, потому что ещё не scanned pointer может указывать на object, который пока выглядит dead.

Поэтому sweeping отделён от marking.

Также GC может вообще не быть active, если GC work отсутствует.

GC постоянно проходит cycle из трёх состояний:

1. sweeping;
2. off;
3. marking.

Для reasoning в этом guide GC cycle считается начинающимся со sweep, затем GC выключается, затем начинается mark.

Следующие sections строят intuition о стоимости GC и tuning parameters.

### Понимание стоимости {#Understanding_costs}

GC — сложная system поверх ещё более сложных systems. Чтобы не утонуть в implementation details, guide использует простую cost model с тремя assumptions.

1. GC использует два основных resources:
   - physical memory;
   - CPU time.

2. Memory cost GC состоит из:
   - live heap memory;
   - new heap memory, allocated до mark phase;
   - metadata, пропорциональной этим значениям, но обычно существенно меньшей.

Упрощённо:

```text
GC memory cost for cycle N = live heap from cycle N-1 + new heap
```

**Live heap** — memory, определённая предыдущим cycle как live.

**New heap** — memory, allocated в текущем cycle; к его концу она может оказаться как live, так и dead.

Размер live heap — property program, а не параметр, которым GC может непосредственно управлять.

3. CPU cost GC моделируется как:
   - fixed cost на cycle;
   - marginal cost, приблизительно proportional размеру live heap.

```text
GC CPU time for cycle N =
    Fixed CPU time cost per cycle
    + average CPU time cost per byte * live heap memory found in cycle N
```

Fixed cost включает work, происходящую constant number раз на cycle, например initialization internal data structures. Обычно это малая часть total cost.

Основная CPU стоимость — marking и scanning.

Average cost per byte зависит и от GC implementation, и от program. Больше pointers означает больше GC work. Linked lists и trees хуже parallelize'ятся при traversal, увеличивая average scanning cost.

Модель игнорирует sweep cost, который proportional total heap, включая dead memory. В current Go GC sweeping значительно быстрее marking/scanning, поэтому им обычно можно пренебречь.

Эта простая модель хорошо классифицирует dominant costs.

Она также показывает:

- total GC CPU cost зависит от количества GC cycles за period времени;
- существует фундаментальный **time/space trade-off**.

### Steady state example

Для понимания trade-off рассмотрим **steady state** application.

С точки зрения GC steady state означает:

- allocation rate, bytes/sec, приблизительно constant;
- marginal GC costs приблизительно constant: distribution object sizes, number of pointers и depth data structures существенно не меняются от cycle к cycle.

Предположим application:

- allocates `10 MiB/s`;
- GC scans со скоростью `100 MiB/cpu-second`;
- live heap постоянно `10 MiB`;
- fixed GC cost для простоты равен zero.

Если GC cycle происходит каждые `1 cpu-second`, application успевает allocate 10 MiB new heap, поэтому total heap перед collection будет около 20 MiB.

GC сканирует 10 MiB live heap за `0.1 cpu-second`, то есть GC overhead составляет около 10%.

GC сканирует только live heap, а не весь 20 MiB heap. Constant live heap не означает, что вся new memory dead: между cycles умирает некоторый mix old/new objects, но после collection остаётся 10 MiB live.

Теперь пусть collection происходит каждые `2 cpu-seconds`.

Application успевает allocate 20 MiB new heap, и total heap перед cycle достигает 30 MiB.

Но scan всё ещё требует `0.1 cpu-second`, поскольку live heap всё ещё 10 MiB.

GC overhead падает примерно с 10% до 5%, но memory use возрастает с 20 MiB до 30 MiB.

Это и есть фундаментальный trade-off:

> Чем реже GC запускается, тем больше memory используется, но тем меньше CPU уходит на GC. Чем чаще GC запускается — наоборот.

**GC frequency** находится в центре этого trade-off.

### `GOGC` {#GOGC}

`GOGC` определяет trade-off между GC CPU и memory.

После каждого GC cycle runtime вычисляет target total heap size следующего cycle.

GC стремится завершить следующий collection до превышения target.

Total heap определяется как live heap предыдущего cycle плюс new heap, allocated после него.

Target heap:

```text
Target heap memory = Live heap + (Live heap + GC roots) * GOGC / 100
```

Пример:

- live heap = 8 MiB;
- goroutine stacks = 1 MiB;
- pointers в globals = 1 MiB.

При `GOGC=100` GC разрешает около 10 MiB new memory и target total heap около 18 MiB.

При `GOGC=50` — около 5 MiB new memory.

При `GOGC=200` — около 20 MiB new memory.

> [!note]
> GC roots включаются в pacing formula начиная с Go 1.18. Раньше учитывался только live heap. Обычно stacks невелики, но programs с сотнями тысяч goroutines могли приводить к poor pacing decisions.

Heap target управляет GC frequency: больший target позволяет дольше ждать следующего mark phase.

Главная practical intuition:

> **Удвоение `GOGC` удваивает heap-memory overhead и примерно вдвое уменьшает GC CPU cost; уменьшение действует наоборот.**

Полное математическое объяснение находится в [Appendix](#Additional_notes_on_GOGC).

Target — именно target, а не жёсткая гарантия. Large allocation может мгновенно превысить его; concurrent GC implementation также может закончить cycle немного позже target.

Настроить GOGC можно environment variable:

```bash
GOGC=200 ./service
```

или API:

```go
debug.SetGCPercent(200)
```

GC можно отключить — если [memory limit](#Memory_limit) не требует collection:

```bash
GOGC=off ./service
```

или:

```go
debug.SetGCPercent(-1)
```

Conceptually это `GOGC = infinity`: new heap неограничен GC target.

Official page содержит interactive visualizations этой cost model. В первой model application без GC требует 10 CPU-seconds, в начале увеличивает live heap, затем работает steady-state; total allocations — 200 MiB, live heap — 20 MiB. Изменение GOGC показывает, как уменьшается GC CPU overhead и растёт peak memory.

> [!note]
> Визуализация показывает CPU time, а не wall time. Для single fully-utilized CPU они совпадают; в multi-core real application wall-time impact GC обычно ниже.

> [!note]
> Go GC имеет minimum total heap size около 4 MiB. Если target от GOGC ниже, он округляется вверх.

Вторая official visualization показывает dynamic workload: allocation rate резко возрастает во второй половине execution, а live heap меняется в первой. Она демонстрирует, что higher allocation rate приводит к более frequent GC cycles даже при том же GOGC.

### Memory limit {#Memory_limit}

До Go 1.19 `GOGC` был единственным user tuning parameter GC.

Он хорошо выбирает trade-off, но сам по себе не учитывает, что available memory конечна.

При transient spike live heap proportional target GOGC тоже резко увеличивается. Поэтому без memory limit GOGC приходится настраивать под **peak** live heap, даже если большую часть времени более высокий GOGC был бы выгоднее.

Go 1.19 добавил runtime memory limit.

Environment:

```bash
GOMEMLIMIT=4GiB ./service
```

или API:

```go
debug.SetMemoryLimit(limit)
```

Memory limit задаёт maximum total memory, которой может управлять Go runtime.

В терминах `runtime.MemStats` учитываемая memory приблизительно равна:

```text
Sys - HeapReleased
```

В `runtime/metrics`:

```text
/memory/classes/total:bytes - /memory/classes/heap/released:bytes
```

Поскольку runtime явно управляет размером heap, GC может уменьшать heap target исходя из memory limit и объёма other runtime memory.

При memory limit ниже target, рассчитанного GOGC, GC запускается чаще, чтобы удерживать peak runtime memory около limit.

При этом GOGC не перестаёт действовать: когда memory limit не является constraining factor, heap продолжает следовать proportional GOGC rule.

Даже `GOGC=off` **не отключает GC**, если memory limit требует collections.

Такая configuration максимизирует resource economy: GC запускается с минимальной frequency, необходимой для удержания memory около limit.

Но memory limit не бесплатен и не отменяет пользу GOGC.

#### Thrashing

Если live heap приблизится к memory limit, GC может быть вынужден запускаться почти непрерывно.

Состояние, где program почти не делает progress из-за постоянных GC cycles, называется **thrashing**.

Transient heap spike способен привести к этому же состоянию.

Indefinite stall часто хуже, чем быстрый out-of-memory failure.

Поэтому Go memory limit **soft**, а не hard.

Runtime не гарантирует соблюдение limit при любых circumstances; он гарантирует разумное effort.

Чтобы избежать thrashing, GC имеет upper limit CPU time, которое он может отбирать в некотором rolling window. Сейчас это примерно:

- 50% CPU;
- window около `2 * GOMAXPROCS` CPU-seconds;
- с некоторым hysteresis для кратких spikes.

Если удержание memory limit потребовало бы больше GC CPU, runtime разрешает memory превысить limit, чтобы application продолжила progress.

Intuition 50% cap: даже при ошибочно слишком низком limit GC сам по себе должен замедлить application не более чем примерно в 2 раза.

Official interactive graphs страницы не моделируют этот CPU cap.

#### Рекомендуемое использование {#Suggested_uses}

**Используйте memory limit**, когда execution environment полностью контролируется и Go program — единственный consumer некоторого reserved memory resource.

Хороший example — web service в container с фиксированным memory allocation.

В такой configuration reasonable rule:

> Оставляйте примерно **5–10% headroom** на memory sources, которые Go runtime не учитывает.

**Можно менять memory limit во время execution**, если external memory pressure меняется. Пример — cgo application, где C library временно требует значительно больше memory.

**Не используйте `GOGC=off` + memory limit**, если Go process делит limited memory с другими loosely coupled processes. Вместо этого сохраните memory limit как guard against spikes, но используйте finite GOGC для normal steady-state behavior.

Пытаться «зарезервировать» memory loosely coupled co-tenants через ultra-tight limit ненадёжно: в какой-то момент несколько processes могут одновременно потребовать больше memory.

Это относится и к overcommit environments, где сумма container limits превышает physical RAM.

**Не hard-code'ьте memory limit в library или command-line tool**, если execution environment неизвестен. Memory limit — responsibility той entity, которая знает available resources.

**Не ставьте memory limit только ради предотвращения OOM**, если program уже вплотную подходит к environment limit. Это меняет risk OOM на risk severe slowdown. Лучше увеличить available memory либо уменьшить GOGC, получив более clean CPU/memory trade-off.

### Latency {#Latency}

Предыдущие cost visualizations для простоты изображают application paused во время GC. Такой collector называется stop-the-world.

Go GC **не является полностью stop-the-world**: большую часть work он выполняет concurrently с application.

Главная причина — уменьшение latency individual units of work, например web requests.

Stop-the-world GC мог бы останавливать request на время полного mark и sweep, potentially proportional heap size.

Go GC старается не делать global pauses proportional heap size: core tracing выполняется concurrent с application.

Pause cost algorithmically сильнее связан с `GOMAXPROCS`, а практически часто определяется временем остановки running goroutines.

Concurrent GC имеет cost: design может иметь ниже throughput, чем equivalent stop-the-world collector. Но lower latency не означает автоматически lower throughput; Go GC постепенно улучшался и по latency, и по throughput.

Concurrent nature не отменяет cost model этого guide.

GC frequency остаётся главным рычагом CPU/memory trade-off и влияет также на latency, поскольку большая часть GC costs возникает во время mark phase.

> **Снижение GC frequency может улучшить latency.**

Это справедливо как при increasing GOGC/memory limit, так и при reducing allocation pressure.

Источники latency, связанные с GC:

1. короткие stop-the-world pauses при переходах между mark и sweep;
2. scheduling delays, поскольку GC использует около 25% CPU resources во время mark phase;
3. allocating goroutines могут выполнять **GC assists**, если allocation outpaces collector;
4. pointer writes требуют дополнительной work во время mark phase;
5. running goroutines приходится suspend'ить для scanning roots/stacks.

Все эти effects, кроме extra pointer-write work, видимы в [[diagnostics#execution-tracer|execution traces]].

### Finalizers, cleanups и weak pointers {#Finalizers_cleanups_and_weak_pointers}

GC создаёт illusion infinite memory поверх finite memory: program allocates memory, но обычно не frees её явно.

Live objects — objects, reachable из globals или computation какой-либо goroutine — могут влиять на behavior program. После death object обычно может быть safely recycled, и сама death не observable на language level.

Но runtime предоставляет три features, нарушающие эту abstraction:

- [`runtime.AddCleanup`](https://pkg.go.dev/runtime#AddCleanup);
- [`weak.Pointer`](https://pkg.go.dev/weak#Pointer);
- [`runtime.SetFinalizer`](https://pkg.go.dev/runtime#SetFinalizer).

Они позволяют наблюдать/reaction на object death, а finalizers даже могут resurrect object.

Это усложняет и program, и GC implementation, но mechanisms полезны в определённых low-level cases.

#### Общие рекомендации {#General_advice}

**Пишите unit tests.** Timing cleanups, weak pointers и finalizers трудно предсказать. Code может казаться корректным после многих runs, но всё равно содержать subtle bug.

**Не используйте эти features напрямую в обычном application code без необходимости.** Это low-level APIs с тонкими restrictions. Нет guarantee, что cleanup/finalizer вообще будет выполнен до program exit.

**Encapsulate mechanisms внутри package.** Не позволяйте их usage leak'иться в public API, если этого можно избежать.

**Ограничивайте direct access к objects с finalizers/cleanups/weak pointers package, который их создал.** Например, package `unique` использует weak pointers internally, но полностью скрывает underlying objects.

**Для non-memory resources предпочитайте deterministic cleanup.**

Cleanups/finalizers хорошо подходят для external memory вроде C `malloc` или `mmap`, поскольку memory resource тесно связан с object lifetime.

Для file descriptors и других scarce OS resources лучше предоставить explicit `Close`-подобный API, а cleanup/finalizer использовать только как safety net против programmer mistakes.

**Начиная с Go 1.24 предпочитайте cleanups finalizers**, кроме rare cases, где нужна ordering/resurrection semantics finalizers.

Historically finalizers появились для wrapping C resources, но имеют ограничения:

- только один finalizer на object;
- он привязан к началу object;
- finalizer resurrects object;
- reference cycles могут сделать reclamation невозможной;
- memory object нельзя reuse как минимум до следующего GC cycle.

Cleanups более flexible, less error-prone и более efficient.

Finalizers всё ещё иногда полезны, когда destruction order действительно важен.

#### Common cleanup issues {#Common_cleanup_issues}

Object с cleanup не должен быть reachable из cleanup function, например через captured variable:

```go
f := new(myFile)
f.fd = syscall.Open(...)
runtime.AddCleanup(f, func(fd int) {
	syscall.Close(f.fd) // Ошибка: cleanup удерживает f reachable.
}, f.fd)
```

Cleanup argument также не должен удерживать object:

```go
f := new(myFile)
f.fd = syscall.Open(...)
runtime.AddCleanup(f, func(f *myFile) {
	syscall.Close(f.fd)
}, f) // Ошибка; этот конкретный case также panic'ит.
```

Finalizers имеют defined execution order, а cleanups — нет. Cleanups могут выполняться concurrently.

Long-running cleanup должна создать goroutine, чтобы не блокировать другие cleanups.

`runtime.GC()` ждёт только queueing cleanups unreachable objects, но не их execution.

#### Common weak-pointer issues {#Common_weak_pointer_issues}

`weak.Pointer.Value()` может начать возвращать `nil` в неожиданное время. Всегда проверяйте result и имейте fallback plan.

Weak pointer в качестве map key не делает map value weak.

Если map value имеет strong path обратно к object, на который указывает weak key, object остаётся reachable.

#### Common finalizer issues {#Common_finalizer_issues}

Object с finalizer не должен быть reachable из самого себя, то есть не должен входить в reference cycle:

```go
f := new(myCycle)
f.self = f // Ошибка: finalizer никогда не запустится.
runtime.SetFinalizer(f, func(f *myCycle) {
	...
})
```

Finalizer function не должна capture object через outer variable:

```go
f := new(myFile)
f.fd = syscall.Open(...)
runtime.SetFinalizer(f, func(_ *myFile) {
	syscall.Close(f.fd) // Ошибка: outer f делает object reachable.
})
```

Reference chain из N objects с finalizers требует минимум N GC cycles, чтобы освободить всю chain.

```go
// Ошибка: reclamation этой list требует минимум 10 GC cycles.
node := new(linkedListNode)
for range 10 {
	tmp := new(linkedListNode)
	tmp.next = node
	node = tmp
	runtime.SetFinalizer(node, func(node *linkedListNode) {
		...
	})
}
```

Избегайте finalizers на objects, возвращаемых через package boundary: user может вызвать `runtime.SetFinalizer` и изменить finalizer неожиданным для package образом.

Long-running finalizer должна запускать goroutine, чтобы не блокировать другие finalizers.

`runtime.GC()` не ждёт execution finalizers, только их queueing.

#### Testing object death {#Testing_object_death}

- Не запускайте такие tests parallel с другими tests без необходимости.
- Используйте `runtime.GC()` для baseline state и для принудительного transition weak pointers к `nil`/queueing cleanups/finalizers.
- Поскольку `runtime.GC()` не ждёт execution, добавляйте test synchronization: например channel, в который cleanup/finalizer пишет после completion.
- Если это невозможно, можно poll'ить post-cleanup state с `runtime.Gosched()`.
- Для chains с finalizers требуется как минимум столько `runtime.GC()` calls, сколько глубина chain.
- Запускайте tests с race detector.

### Additional resources {#Additional_resources}

Official guide рекомендует следующие resources:

- [The GC Handbook](https://gchandbook.org/) — общий reference по garbage-collector design.
- [TCMalloc](https://google.github.io/tcmalloc/design.html) — allocator design, на котором основан Go memory allocator.
- [Go 1.5 GC announcement](https://go.dev/blog/go15gc) — описание concurrent GC algorithm.
- [Getting to Go](https://go.dev/blog/ismmkeynote) — evolution Go GC до 2018.
- [Go 1.5 concurrent GC pacing design](https://docs.google.com/document/d/1wmjrocXIWTr1JxU-3EQBI6BK6KgtiFArkG47XK73xIQ/edit).
- [Smarter scavenging](https://go.dev/issue/30333).
- [Scalable page allocator](https://go.dev/issue/35112).
- [GC pacer redesign, Go 1.18](https://go.dev/issue/44167).
- [Soft memory limit, Go 1.19](https://go.dev/issue/48409).

## Примечание о virtual memory {#A_note_about_virtual_memory}

Guide в основном говорит о physical memory, но важно различать её и virtual memory, которую tools вроде `top` часто показывают как `VSS`.

Physical memory — реальная RAM.

Virtual memory — OS abstraction над physical memory, которая изолирует processes. Program может reserve virtual address space, вообще не backed physical pages.

> **Большие reservations virtual memory, не backed physical memory, обычно очень дешёвы.**

Go runtime использует это свойство несколькими способами.

- Runtime обычно не удаляет virtual mappings полностью. Вместо этого OS-specific operations освобождают physical backing pages. Этот mechanism используется для memory limit и background scavenging.
- На 32-bit platforms runtime заранее reserves примерно 128–512 MiB address space для heap, чтобы уменьшить fragmentation.
- Runtime использует большие virtual reservations для внутренних data structures. На 64-bit platforms minimum virtual footprint этих structures обычно около 700 MiB; на 32-bit platforms он negligible.

Поэтому VSS обычно плохая metric фактического memory footprint Go program.

Сосредоточьтесь на RSS и аналогичных measurements physical memory.

## Optimization guide {#Optimization_guide}

### Identifying costs {#Identifying_costs}

Перед optimization interaction с GC сначала докажите, что GC действительно significant cost.

Общий overview tools — [[diagnostics|Диагностика]].

Для GC полезен следующий порядок.

#### 1. CPU profiles

CPU profiling — хорошая starting point.

В default `pprof top` non-leaf functions могут быть неочевидны, поэтому для runtime symbols используйте `top -cum` либо `list` и смотрите cumulative percentage.

Полезные symbols:

**`runtime.gcBgMarkWorker`** — entrypoint background mark worker goroutines.

Time здесь scales с GC frequency, size и complexity object graph и отражает baseline marking/scanning cost.

Внутри встречаются:

- `runtime.gcDrainMarkWorkerDedicated`;
- `runtime.gcDrainMarkWorkerFractional`;
- `runtime.gcDrainMarkWorkerIdle`.

Последний показывает использование idle CPU. В mostly idle application GC старается быстрее выполнить work за счёт свободных CPUs, поэтому `idle` workers могут занимать большую долю samples, хотя это capacity, которую application не использовала.

Common example — application фактически работает одной goroutine, но `GOMAXPROCS > 1`.

**`runtime.mallocgc`** — entrypoint heap allocator.

Large cumulative time, условно больше ~15%, обычно означает высокий allocation volume.

**`runtime.gcAssistAlloc`** — path, где allocating goroutines отдают CPU на GC marking/scanning.

Large cumulative time, условно больше ~5%, означает, что application allocation rate outpaces collector и GC оказывает существенное влияние.

`gcAssistAlloc` находится внутри call tree `mallocgc`, поэтому увеличивает его cumulative value.

#### 2. Execution traces

CPU profiles показывают aggregate cost, но хуже показывают rare events и latency.

Execution trace даёт detailed view короткого interval execution. GC events помечены в trace viewer и позволяют видеть конкретное interaction application с collector.

См. [`runtime/trace`](https://pkg.go.dev/runtime/trace).

#### 3. GC traces

Для deeper debugging runtime предоставляет GC-specific text traces на STDERR, по одной line на cycle.

Основной:

```bash
GODEBUG=gctrace=1 ./service
```

Format описан в `runtime` environment-variable documentation.

Более глубокий pacer trace:

```bash
GODEBUG=gcpacertrace=1 ./service
```

Он требует понимания GC pacer internals и в основном предназначен для runtime-level diagnostics.

### Eliminating heap allocations {#Eliminating_heap_allocations}

Один из наиболее сильных способов уменьшить GC cost — заставить GC управлять меньшим количеством values.

Allocation rate — один из главных факторов GC frequency, поэтому reducing heap allocations может давать большой effect.

#### Heap profiling {#Heap_profiling}

После того как GC identified как cost, используйте memory/heap profiles для поиска allocation sites.

Memory profiles разбивают data четырьмя способами:

- `inuse_objects` — number live objects;
- `inuse_space` — bytes live objects;
- `alloc_objects` — total objects allocated с начала program;
- `alloc_space` — total bytes allocated с начала program.

Переключаться между views можно `pprof -sample_index` либо interactive option `sample_index`.

> [!note]
> Memory profiles по default sample'ят subset heap objects, а не каждый allocation. Для hotspots этого обычно достаточно. Sampling rate настраивается через `runtime.MemProfileRate`.

Для reducing GC pressure наиболее полезен `alloc_space`, поскольку он непосредственно отражает allocation rate.

#### Escape analysis {#Escape_analysis}

После identification hot allocation sites можно выяснить, почему compiler отправляет values на heap.

Command:

```bash
go build -gcflags=-m=3 [package]
```

Compiler объясняет применённые и неприменённые optimizations, включая escape decisions.

Эту information можно показывать как overlay в LSP-capable editor.

Например, в VS Code:

```text
Source Action... > Show compiler optimization details
```

либо command:

```text
Go: Toggle compiler optimization details
```

Setting `ui.diagnostic.annotations` может включать annotation `escape`.

Compiler также предоставляет machine-readable JSON optimization data для custom tooling.

### Implementation-specific optimizations {#Implementation-specific_optimizations}

Go GC чувствителен к structure live object graph. Complex pointer graph ограничивает parallelism и создаёт больше scanning work.

Следующие implementation details иногда полезны для optimization, но могут ухудшать readability и меняться между releases. Применяйте их только после profiling.

**Pointer-free values segregated от values с pointers.**

Если data structure может хранить indices вместо pointers, GC испытывает меньше cache pressure и scanning work. Это имеет смысл только для доказанного GC hotspot.

**GC прекращает scanning value после последнего pointer field.**

Поэтому grouping pointer fields в начале struct может уменьшить scanned bytes. Compiler теоретически мог бы rearrange fields, но сейчас fields остаются в source order.

В целом использование slice indices вместо pointers иногда уменьшает GC cost.

### Linux transparent huge pages (THP) {#Linux_transparent_huge_pages}

CPU переводит virtual addresses в physical через page tables.

Transparent Huge Pages — Linux feature, которая автоматически объединяет ordinary physical pages, backing contiguous virtual regions, в larger huge pages.

Плюс: меньше page-table entries и быстрее lookups.

Минус: больше wasted physical memory, если реально используется только часть huge page.

Для production Go programs THP может улучшить throughput и latency ценой memory overhead.

- small heaps часто почти не выигрывают и могут использовать до ~50% дополнительной memory;
- large heaps, примерно 1 GiB+, могут получить до ~10% throughput improvement с порядка 1–2% или меньшим overhead.

Настройка Linux:

```text
/sys/kernel/mm/transparent_hugepage/enabled
```

Если THP включён, official guide рекомендует дополнительно:

1. Настроить `/sys/kernel/mm/transparent_hugepage/defrag` в `defer` или `defer+madvise`.

`defer` заставляет kernel coalesce huge pages lazily/background. Более aggressive modes способны вызывать stalls в memory-constrained systems и ухудшать latency.

`defer+madvise` похож на `defer`, но лучше сосуществует с applications, явно requesting huge pages.

2. Настроить `/sys/kernel/mm/transparent_hugepage/khugepaged/max_ptes_none` в `0`.

Default Linux может быть maximally aggressive и undo work Go runtime по возврату memory OS.

До Go 1.21 runtime пытался компенсировать этот kernel behavior ценой CPU.

С Go 1.21+ и Linux 6.2+ runtime больше не изменяет huge-page state.

Если после upgrade к Go 1.21.1+ вырос memory use, эта kernel setting часто исправляет issue.

Additional workaround — `PR_SET_THP_DISABLE` через `golang.org/x/sys/unix.Prctl`, либо:

```text
GODEBUG=disablethp=1
```

для heap memory. Setting может быть удалён в future Go release.

## Appendix {#Appendix}

### Additional notes on GOGC {#Additional_notes_on_GOGC}

Выше было заявлено, что doubling GOGC примерно удваивает memory overhead и halving GC CPU cost. Ниже вывод.

Heap target:

```text
Target heap memory = Live heap + (Live heap + GC roots) * GOGC / 100
```

Total heap:

```text
Total heap memory = Live heap + New heap memory
```

Следовательно:

```text
New heap memory = (Live heap + GC roots) * GOGC / 100
```

Отсюда видно, что удвоение GOGC удваивает amount new heap, который application allocates между cycles, то есть приблизительно удваивает heap-memory overhead.

`Live heap + GC roots` здесь является approximation memory, которую GC должен scan.

Теперь CPU cost.

За time interval `T`:

```text
Total GC CPU cost =
    (GC CPU cost per cycle) * (GC frequency) * T
```

Из cost model:

```text
GC CPU cost per cycle =
    (Live heap + GC roots) * (Cost per byte) + Fixed cost
```

Sweep cost здесь снова игнорируется, поскольку mark/scan dominates.

В steady state allocation rate и cost per byte constant.

GC frequency:

```text
GC frequency =
    Allocation rate / New heap memory
```

Подставляя formula new heap:

```text
GC frequency =
    Allocation rate / ((Live heap + GC roots) * GOGC / 100)
```

Полная formula total GC cost:

```text
Total GC CPU cost =
    Allocation rate
    / ((Live heap + GC roots) * GOGC / 100)
    * ((Live heap + GC roots) * Cost per byte + Fixed cost)
    * T
```

Для достаточно large heap marginal cost значительно больше fixed cost, поэтому formula упрощается:

```text
Total GC CPU cost =
    Allocation rate / (GOGC / 100) * Cost per byte * T
```

Следовательно, при прочих равных doubling GOGC halves total GC CPU cost.

Official visualizations учитывают fixed costs, поэтому их measured overhead не обязан уменьшаться ровно вдвое.

Formula также показывает, что GC CPU cost в основном определяется:

- allocation rate;
- cost per scanned byte.

> [!note]
> Размер live heap не полностью совпадает с объёмом memory, который GC реально должен scan. Два heaps одинакового size, но разной structure могут иметь разный CPU scanning cost при одинаковой memory cost. Именно поэтому heap structure входит в definition steady state.
>
> Казалось бы, target стоило бы считать только от scannable live heap. Но при tiny scannable heap и large pointer-free live heap это приводит к degenerate behavior, поэтому current formula использует полный live heap плюс roots.
