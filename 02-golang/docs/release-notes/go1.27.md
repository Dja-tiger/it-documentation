---
title: "Go 1.27 Release Notes"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/go1.27.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Go 1.27 Release Notes

Go 1.27 released in August 2026, спустя шесть месяцев после Go 1.26. Большая часть изменений — implementation/toolchain/library improvements, но release содержит и заметные language changes.

## Changes to the language

### Generic methods

Главное изменение языка: **methods теперь могут объявлять собственные type parameters**, аналогично functions.

```go
type List[E any] []E

func (l List[E]) Apply[F any](f func(E) F) List[F] {
    r := make(List[F], len(l))
    for i, x := range l {
        r[i] = f(x)
    }
    return r
}
```

`F` — type parameter самого method, а `E` — parameter receiver type.

Это снимает старое ограничение generics, при котором operation с новым result type часто приходилось оформлять top-level function.

Function literals по-прежнему не объявляют собственные type parameters.

### Keyed struct literals и promoted fields

В keyed struct literals field key теперь может быть valid selector, включая promoted field embedded struct, при соблюдении новых ambiguity/overlap restrictions.

Это позволяет задавать nested promoted fields более непосредственно, но overlapping initialization embedded value и promoted field запрещается, чтобы initialization оставалась однозначной.

Подробные normative rules: [[../spec|Go 1.27 Language Specification]].

## Ports

### Linux

Минимальное требование Linux kernel для поддерживаемых architectures повышено до **3.2**. Некоторые старые architectures/platform combinations могут иметь более высокий minimum.

### macOS

Go 1.27 — последний release, поддерживающий macOS 13 Ventura. Go 1.28 потребует macOS 14 Sonoma или новее.

### `loong64`

Поддержка LoongArch переведена на новый ABI **ABI2.0**. ABI0 был временным early port ABI и несовместим с ABI2.0.

- Go binaries, собранные Go 1.27+ для `loong64`, требуют ABI2.0 Linux userspace;
- cgo code использует ABI2.0;
- distribution/toolchain перестаёт поддерживать ABI0.

## Tools

### `go` command

Go command продолжает развитие toolchain/dependency workflows и поддерживает Go 1.27 language/toolchain requirements.

### `go vet`

Analyzers обновлены под новые language/API patterns. Как и прежде:

```bash
go vet ./...
```

остаётся standard static correctness check, но не заменяет compiler/tests/security tools.

## Compiler

Compiler получил optimization improvements, включая использование новых language/runtime capabilities и дальнейшее развитие PGO.

### PGO

Profile-guided optimization продолжает улучшаться. Existing profiles предыдущих builds сохраняют intended source-skew tolerance. Для production workflow см. [[../pgo|PGO guide]].

### Stack allocation / escape analysis / inlining

Go 1.27 включает compiler improvements, способные менять escape decisions, inlining и generated machine code. Не полагайтесь на specific allocation decision как на language guarantee; measure текущий binary/profile.

## Runtime

Runtime продолжает улучшения scheduler, GC и memory behavior.

### Garbage collector

Go 1.27 включает дальнейшие GC/runtime performance improvements. Existing `GOGC`/`GOMEMLIMIT` model остаётся основным tuning interface.

### Traceback labels

Default `GODEBUG=tracebacklabels=1`: runtime tracebacks могут включать goroutine labels. Это повышает diagnosability, но labels могут содержать sensitive application metadata; compatibility opt-out существует согласно [[../godebug|GODEBUG reference]].

### Runtime metrics/debugging

Обновлены runtime/metrics и diagnostics в соответствии с новыми runtime features. При upgrades dashboards следует сверять с current package docs, не предполагать появление/исчезновение metric names по старой version.

## Linker

Linker продолжает improvements binary generation/platform support. Architecture-specific users, особенно assembly/cgo, должны rebuild/retest native components при переходе major Go line.

## Standard library

Ниже — значимые user-visible изменения Go 1.27. Для exhaustive API symbol list source release notes остаются pinned upstream source этой страницы.

### `archive/zip`

Добавлены convenience helpers для работы с symlink metadata/reading symlink target в archive. Это упрощает безопасную обработку links без ручного разбора mode/external attributes.

При extraction untrusted ZIP всё равно необходимо самостоятельно обеспечить destination/path policy — archive API не является sandbox.

### `bufio`

Добавлены API improvements вокруг scanning/read behavior, включая более явные возможности управления/инспекции reader state в новых methods release.

### `bytes`

Package получил incremental API/performance improvements. Existing semantics `Buffer`, search/split/compare сохраняются согласно compatibility promise.

### `crypto`

#### FIPS 140

Go 1.27 развивает native FIPS 140-3 infrastructure и Go Cryptographic Module. Доступны current/frozen module versions и связанные build/runtime controls.

См. [[../security/fips140|FIPS 140-3 Compliance]].

#### `crypto/rand`

Cryptographic randomness продолжает использовать platform CSPRNG, а в FIPS mode — approved DRBG construction согласно current crypto module.

#### `crypto/tls`

TLS behavior обновлён в соответствии с security policy и современными algorithms. Некоторые compatibility changes управляются `GODEBUG` только на transition period.

Go 1.27 release/GODEBUG history включает post-quantum/FIPS-related controls, актуальные supported defaults и удаление истёкших legacy switches.

#### `crypto/x509`

Обновлены certificate parsing/verification/platform-root behaviors. На Windows/Darwin появился compatibility control, определяющий использование `SSL_CERT_FILE`/`SSL_CERT_DIR` вместо platform store (`x509sslcertoverrideplatform`).

### `encoding/base64`

Добавлены/расширены APIs для encoding/decoding непосредственно в buffers/append-oriented workflows, уменьшающие intermediate allocations для hot paths.

### `encoding/json/v2`

Экспериментальный/new-generation JSON stack продолжает развитие. API v2 и `encoding/json/jsontext` получили additional methods/options/performance work.

Migration guide: [[../jsonv2-migration|encoding/json/v2 Migration Guide]].

Особенно важно проверять:

- duplicate names;
- case matching;
- invalid UTF-8;
- nil collection representation;
- custom marshalers;
- deterministic ordering.

### `errors`

Error traversal/wrapping APIs остаются compatibility foundation (`Is`, `As`, `Join`, wrapping `%w` через `fmt`). Go 1.27 включает incremental implementation/API documentation improvements.

### `fmt`

Formatter продолжает поддерживать generic/new types через existing interfaces (`Stringer`, `Formatter`, `GoStringer`). Performance fixes не меняют formatting contract.

### `go/ast`, `go/parser`, `go/token`, `go/types`

Tooling packages обновлены для syntax/type-system Go 1.27, в том числе **generic methods** и новые struct-literal semantics.

Tools, которые анализируют Go source собственными AST/type assumptions, должны быть протестированы на 1.27 syntax и не ограничиваться parser старой version.

### `hash/*`

Некоторые hash implementations получили append/marshal/state improvements и optimizations. Cryptographic suitability алгоритма не меняется от того, что package находится под `hash`; security use должен выбирать crypto primitives намеренно.

### `html/template`

Contextual escaping/security behavior продолжает hardened defaults. При security fixes compatibility может быть subordinated безопасному behavior согласно Go security policy.

### `io`

Добавлены/улучшены utility APIs и optimizations вокруг common Reader/Writer flows. Small interfaces `Reader`, `Writer`, `ReaderAt`, `WriterTo`, `ReaderFrom` остаются центральным composability contract.

### `log/slog`

Structured logging продолжает развитие handler/value API/performance. Production users должны учитывать, что handlers могут удерживать groups/attrs и что source attribution имеет cost.

### `math`

Floating-point/math implementation получила performance/accuracy improvements, включая architecture-specific optimizations. IEEE edge behavior следует current package docs.

### `net`

Networking stack получил incremental improvements, включая platform/runtime integration и resolver/socket behavior.

### `net/http`

Go 1.27 содержит значительные HTTP changes/hardening, включая ограничения ресурсов, связанные с cookie/query parsing в поддерживаемых security backports, и further HTTP/2/HTTP behavior improvements.

Важно: HTTP parser/resource limits могут повлиять на приложения, которые исторически принимали экстремально большие valid inputs. Compatibility toggles существуют как transition mechanism, но application-level limits лучше задавать явно.

### `net/url`

Добавлен/усилен лимит на количество query parameters для защиты от resource-exhaustion attacks и более строгая обработка malformed host/colon cases. Transition behavior отражён в `GODEBUG` (`urlmaxqueryparams`, `urlstrictcolons`).

### `os`

File/process APIs получили platform fixes и incremental helpers. Behavior path/file permissions остаётся platform-dependent; portable code не должен предполагать Unix semantics на всех targets.

### `os/exec`

Command execution сохраняет security rule, введённое предыдущими Go releases: implicit current-directory lookup не должен молча превращать относительное имя executable в `./name`; `ErrDot`/PATH semantics защищают от common path-hijack pattern.

### `path/filepath`

Platform path processing обновляется совместно с OS security behavior. Для URL paths используйте `path`, не `filepath`.

### `reflect`

Reflect обновлён для language/type-system 1.27, включая generic method metadata/handling где применимо. Reflection code должен быть тестирован с instantiated generic types/methods.

### `regexp`

Implementation/performance improvements сохраняют RE2-style guarantees: regexp engine избегает catastrophic exponential backtracking semantics common в некоторых regex engines.

### `runtime/debug`

Diagnostics/build info/runtime tuning APIs продолжают evolution. `debug.SetGCPercent`, `debug.SetMemoryLimit`, stack/GC stats остаются key runtime controls.

### `slices`

Generic slices utilities получили новые helpers/optimizations. Как и другие generic stdlib packages, они уменьшают необходимость повторять manual loops, когда semantics совпадает.

### `strings`

Добавлены/улучшены append-oriented/string processing APIs и optimizations. Strings остаются immutable byte sequences; UTF-8 semantics требуют `unicode/utf8`/range/runes в зависимости от задачи.

### `sync`

Synchronization primitives получили runtime/performance improvements. Memory-order guarantees определяются package docs и [[../memory-model|memory model]]. Не выводите synchronization semantics из observed implementation.

### `sync/atomic`

Typed atomics и operations сохраняют sequentially-consistent guarantees Go memory model. Используйте atomic только когда lock-free design действительно оправдан и его invariant понятен.

### `testing`

Testing/fuzzing/benchmark infrastructure расширена под новые toolchain capabilities. Native fuzzing остаётся integrated с `go test`; current behavior описан в [[../security/fuzz/index|Fuzzing]].

### `time`

Timer/ticker semantics продолжают modern synchronous-channel model, перешедшую в previous releases. Исторический `asynctimerchan` compatibility switch удалён в Go 1.27.

### `unicode`

Unicode tables обновлены до version, указанной current package `unicode` docs. Программы, которые зависят от category/case tables exact version, должны учитывать это при reproducible processing.

## `go/types` / tooling impact generic methods

Наиболее потенциально breaking для custom source-analysis tools изменение — method type parameters. Tooling, ранее предполагавший grammar:

```text
func (recv) Method(args)
```

должен принимать:

```text
func (recv) Method[T constraint](args)
```

и корректно работать с instantiation/inference method values/calls.

Используйте current `go/parser`, `go/ast`, `go/types` вместо собственного incomplete grammar, если это возможно.

## Assembly/ABI

Architecture-specific changes, особенно `loong64` ABI2, требуют rebuild native/assembly/cgo dependencies. Handwritten assembly необходимо перепроверить против Go 1.27 `cmd/internal/obj/<arch>` conventions и [[../asm|assembler guide]].

## Compatibility

Go 1 compatibility promise сохраняется, но не означает отсутствие behavioral changes:

- security fixes могут intentionally harden defaults;
- `GODEBUG` transition settings временно дают old semantics;
- platform minimums могут повышаться;
- compiler/runtime optimization decisions не API;
- experimental APIs не имеют той же stability, что stable stdlib.

Перед production upgrade:

```bash
go test ./...
go test -race ./...
go vet ./...
govulncheck ./...
```

и обязательно прогоните integration/load tests под Go 1.27.1.
