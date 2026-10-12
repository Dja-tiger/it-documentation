---
title: "Go Fuzzing technical details"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/fuzz/technical.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Go Fuzzing technical details

Этот документ даёт обзор technical details native fuzzing implementation и предназначен как resource для contributors.

## Общая architecture

Fuzzer использует:

- один coordinator process, управляющий corpus;
- несколько worker processes, которые mutating inputs и выполняют fuzz target.

Coordinator и workers взаимодействуют через piped JSON-based RPC protocol и shared regions virtual memory.

Для каждого worker coordinator создаёт goroutine, которая запускает worker process и настраивает cross-process communication. Затем каждая такая goroutine читает shared channel, который заполняется main coordinator loop, и передаёт прочитанные instructions соответствующему worker process.

Main coordinator loop выбирает inputs из corpus и отправляет их в shared worker channel. Worker, получивший input, отправляет fuzzing request соответствующему worker process.

Worker process выполняет loop: изменяет input и запускает fuzz target до тех пор, пока execution:

- не увеличит coverage counters;
- не вызовет panic или crash;
- либо не превысит заранее заданный deadline.

Если worker process выполняет mutated input, который увеличивает coverage counters или вызывает recoverable panic, он сообщает об этом coordinator. Coordinator способен reconstruct mutated input.

Coordinator пытается [minimize input](#input-minimization), после чего:

- при increased coverage добавляет его в corpus для дальнейшего fuzzing;
- при error/panic записывает его в `testdata`.

Если во время fuzzing происходит non-recoverable error, завершающий worker process — например infinite loop, `os.Exit`, memory exhaustion и т. п. — minimization не выполняется. Failing input записывается в `testdata` и report'ится.

Upstream document сопровождает этот flow sequence diagram coordinator ↔ worker: `/security/fuzz/seq-diagram.png`.

### Cross-process communication

При запуске child worker process coordinator настраивает два communication mechanisms:

1. pipe для JSON-based RPC messages;
2. shared memory region для inputs и RNG state.

У каждого worker process собственные pipe и shared memory region.

RPC pipe используется coordinator для управления worker process: передачи fuzzing/minimization instructions. Worker через тот же channel возвращает results: expanded ли coverage, произошёл ли crash, успешно ли выполнена minimization и т. д.

Shared memory region используется для передачи specific information между coordinator и worker.

Coordinator записывает туда corpus entry для fuzzing, а worker сохраняет current RNG state.

RNG state позволяет coordinator reconstruct mutations, применённые worker к input после завершения target. Reconstruction работает как при clean worker exit, так и после crash.

## Input selection

Coordinator сейчас не реализует advanced input prioritization. Он циклически проходит весь corpus и после последнего entry начинает сначала.

Также coordinator не выполняет corpus minimization — это не то же самое, что [input minimization](#input-minimization), описанная ниже.

## Coverage guidance

Fuzzer использует [libFuzzer-compatible inline 8-bit coverage counters](https://clang.llvm.org/docs/SanitizerCoverage.html#inline-8bit-counters).

Counters вставляются compiler на каждом code edge и increment'ятся при входе.

Counters специально не защищены от overflow, чтобы не насыщаться.

Как в AFL и libFuzzer, при tracking coverage counter values quantize'ятся до ближайшей power of two. Это позволяет отличать незначительные от значимых изменений execution flow.

Для tracking этих changes fuzzer хранит slice bytes, mapped на inline counters. Bits каждого byte показывают, существует ли хотя бы один corpus input, который increment'ит соответствующий counter не менее `2^bit-position` раз.

Если inputs достигают всех quantized values, bytes могут saturate'иться, после чего соответствующий counter больше не даёт полезной coverage information.

Поскольку counters вставляются на every edge при compilation, instrumented оказывается и code вне fuzz target. Поэтому worker может увидеть coverage expansion, не связанную с target — например, когда новая branch выполняется в unrelated goroutine.

Worker уменьшает noise двумя способами:

1. reset'ит все counters непосредственно перед fuzz target и snapshot'ит их сразу после return target;
2. explicit исключает packages, которые особенно likely создавать noise.

Counters не вставляются в следующие packages:

- `context`;
- `internal/fuzz`;
- `reflect`;
- `runtime`;
- `sync`;
- `sync/atomic`;
- `syscall`;
- `testing`;
- `time`.

## Mutation engine

Когда worker получает новый input, он применяет mutation перед execution target.

После каждой mutation target запускается с новым input. Если coverage не расширилась, применяются дополнительные mutations.

Чтобы input не отклонялся слишком далеко от initial state, после **пяти mutations** он reset'ится в original state, после чего mutation sequence продолжается заново.

Для input `hello world` strategy может выглядеть так:

```text
0. hello world [initial state]
1. kello world [replace first byte]
2. world kello [swap two chunks]
3. world ke    [delete last three bytes]
4. owrld ke    [shuffle first three bytes]
5. owrldx ke   [insert random byte]
6. ello world  [reset to initial state, delete first byte]
...
```

Mutators имеют bias в сторону smaller inputs, а не larger, чтобы corpus size не рос слишком быстро.

Для `[]byte` и `string` существует много mutators; для `int`, `uint` и `float` types — меньше специализированных mutators.

Сейчас не реализованы:

- execution-driven mutation strategies, например input-to-comparison correspondence;
- dictionary-based mutators.

## Input minimization

Чтобы corpus не разрастался и не замедлял fuzzer как с точки зрения performance, так и с точки зрения probability mutation попасть в interesting data, каждый discovered input, который расширяет coverage или вызывает recoverable crash, пытаются minimize.

Non-recoverable crashes, например memory exhaustion, не minimiz'ятся, поскольку process был бы слишком медленным.

Minimization strategy достаточно проста: последовательно удалять bytes из input, сохраняя initial coverage/failure condition.

Порядок:

1. попытаться удалить с конца input exponentially decreasing chunk bytes;
2. попытаться удалить каждый individual byte;
3. попытаться удалить каждый possible subset bytes;
4. попытаться заменить каждый non-human-readable byte на human-readable byte, то есть byte из ASCII set.
