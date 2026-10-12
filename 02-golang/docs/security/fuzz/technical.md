---
title: "Go Fuzzing — технические детали"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/fuzz/technical.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Техническое устройство native fuzzing

Документ предназначен главным образом contributors/tooling developers.

## Architecture

Fuzzer состоит из:

- одного **coordinator process** — corpus, scheduling, minimization/results;
- нескольких **worker processes** — mutation + execution fuzz target.

Coordinator создаёт goroutine на worker, запускает child process и настраивает IPC. Main coordinator loop выбирает corpus entries и отправляет work в shared worker channel.

Worker мутирует input и повторно выполняет target, пока:

- coverage counters расширились;
- произошёл recoverable panic/failure;
- истёк deadline.

При interesting input worker сообщает state coordinator'у. Coordinator reconstruct'ит mutated input, пытается minimize и:

- добавляет его в corpus, если найден новый coverage;
- сохраняет в `testdata`, если input вызывает failure.

При non-recoverable worker death (OOM, `os.Exit`, infinite loop/timeout и т. п.) minimization может не выполняться; failing input всё равно восстанавливается/сохраняется насколько возможно.

## IPC

Для каждого worker используются два механизма:

1. **pipe** с JSON-based RPC — commands/results;
2. **shared virtual-memory region** — corpus input и RNG state.

RNG state позволяет coordinator воспроизвести sequence mutations и reconstruct input даже после worker crash.

## Input selection

Текущий coordinator не применяет sophisticated priority scheduling: циклически проходит corpus. Отдельной global corpus minimization (не путать с minimization одного input) также нет в описанной implementation.

## Coverage guidance

Instrumentation использует libFuzzer-compatible inline 8-bit coverage counters на code edges.

Counters могут overflow; coverage interpretation quantizes counts к powers of two. Engine хранит bit information о достигнутых quantized counter levels и считает input interesting, если он расширяет такую coverage state.

Поскольку instrumentation вставляется широко, unrelated goroutines могут создавать noise. Worker уменьшает noise:

- resets counters непосредственно перед target;
- snapshots сразу после target;
- не инструментирует набор noisy foundational packages.

В documented exclusion list входят:

```text
context
internal/fuzz
reflect
runtime
sync
sync/atomic
syscall
testing
time
```

## Mutation engine

Для каждого corpus entry worker применяет последовательность mutations. После нескольких mutations input reset'ится к initial state, чтобы не уходить слишком далеко от useful seed.

Пример conceptual mutation chain:

```text
hello world
kello world
world kello
world ke
owrld ke
owrldx ke
ello world   // reset + new mutation
```

Mutators стараются bias'ить к меньшим inputs, чтобы corpus не разрастался слишком быстро.

`[]byte`/`string` имеют больше mutation strategies; integer/uint/float types — меньший специализированный набор.

В описанной implementation отсутствуют advanced execution-driven comparison solving и dictionary-based mutators.

## Input minimization

Interesting/recoverable failing input уменьшается, сохраняя исходный coverage/failure condition.

High-level strategy:

1. отрезать экспоненциально уменьшающиеся chunks с конца;
2. пробовать удалять отдельные bytes;
3. пробовать удалять subsets;
4. заменять non-human-readable bytes на printable ASCII там, где condition сохраняется.

Цель — smaller reproducible corpus: меньше disk/cache cost, быстрее future fuzzing и проще diagnosis.
