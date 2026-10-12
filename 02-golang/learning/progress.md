# Progress — Go learning roadmap

Отмечайте пункт только после выполнения mastery criteria из [[study-rules|study-rules.md]], а не после простого чтения.

## Stage 1 — Foundations

- [ ] Go 1.27.1 установлен/проверен через `go version`.
- [ ] `go env` и базовый toolchain navigation понятны.
- [ ] `go mod init` без подсказки.
- [ ] `package main` / `func main`.
- [ ] import/export identifiers.
- [ ] `go run`.
- [ ] `go test`.
- [ ] `go build`.
- [ ] `go install` / GOBIN concept.
- [ ] пройдена существующая Create a module tutorial-chain.
- [ ] выполнен [[practice/01-foundations|Foundations practice]].
- [ ] practical check Stage 1 написан с нуля.

## Stage 2 — Core language

- [ ] variables / zero values.
- [ ] constants / basic types.
- [ ] functions.
- [ ] multiple return values.
- [ ] `if` / `for` / `range` / `switch`.
- [ ] `defer` на базовом уровне.
- [ ] pointers.
- [ ] structs.
- [ ] arrays.
- [ ] slices.
- [ ] `len` / `cap` / `append` mental model.
- [ ] maps / comma-ok.
- [ ] map key comparability.
- [ ] strings / bytes / runes distinction.
- [ ] batching 100000 → 3000.
- [ ] grouping by `(store_id, plu_id)`.
- [ ] streaming CSV exercise.
- [ ] intentional slice/map/nil-pointer experiments.
- [ ] выполнен [[practice/02-core-language|Core language practice]].

## Stage 3 — Methods / interfaces / generics

- [ ] value receiver.
- [ ] pointer receiver.
- [ ] method set `T` vs `*T`.
- [ ] implicit interface implementation.
- [ ] small consumer-side interfaces.
- [ ] type assertion one-result/comma-ok.
- [ ] type switch.
- [ ] typed nil in interface experiment.
- [ ] `any`.
- [ ] `comparable`.
- [ ] generic type parameters.
- [ ] constraints / type sets / `~T` / union.
- [ ] type inference basics.
- [ ] generic `Chunk[T]`.
- [ ] выполнен [[practice/03-interfaces-generics|Interfaces & generics practice]].

## Stage 4 — Errors / testing / fuzzing

- [ ] `error` value model.
- [ ] wrapping `%w`.
- [ ] `errors.Is`.
- [ ] `errors.As`.
- [ ] sentinel vs typed error decision.
- [ ] table-driven tests.
- [ ] subtests.
- [ ] boundary/error path tests.
- [ ] fuzz seed corpus.
- [ ] fuzz invariant.
- [ ] intentional `%w` → `%v` break experiment.
- [ ] fuzz-found regression exercise.
- [ ] выполнен [[practice/04-errors-testing|Errors & testing practice]].
- [ ] [[projects/01-price-cli|Project 1 — price-cli]] started/completed to checkpoint.

## Stage 5 — Packages / Modules / Toolchain

- [ ] package path / import path / module path.
- [ ] `go.mod`.
- [ ] `go.sum`.
- [ ] `go mod tidy`.
- [ ] `go mod verify`.
- [ ] dependency lifecycle.
- [ ] `replace`.
- [ ] workspace / `go.work`.
- [ ] semantic module versions.
- [ ] v2+ module path concept.
- [ ] `internal/` visibility.
- [ ] `cmd/` convention.
- [ ] `go` / `toolchain` directives.
- [ ] `GOTOOLCHAIN` basic behavior.
- [ ] выполнен [[practice/05-modules-toolchain|Modules/toolchain practice]].
- [ ] `price-cli` приведён к clean module layout.

## Stage 6 — Concurrency

- [ ] goroutine lifecycle.
- [ ] unbuffered channel.
- [ ] buffered channel.
- [ ] range over channel.
- [ ] close ownership.
- [ ] `select`.
- [ ] `sync.WaitGroup`.
- [ ] `sync.Mutex`.
- [ ] `sync.RWMutex` — understand use case, not mandatory everywhere.
- [ ] `sync/atomic` basics after mutex version.
- [ ] bounded worker pool.
- [ ] fan-out.
- [ ] fan-in.
- [ ] pipeline.
- [ ] backpressure.
- [ ] data race exercise.
- [ ] `go test -race`.
- [ ] deadlock exercise 1: send without receiver.
- [ ] deadlock exercise 2: receive nobody can satisfy.
- [ ] deadlock exercise 3: cyclic resource wait.
- [ ] goroutine leak exercise.
- [ ] concurrency mini-project / [[projects/02-price-processor|price-processor]].
- [ ] выполнен [[practice/06-concurrency|full concurrency track]].

## Stage 7 — Context / cancellation

- [ ] `context.Context` contract.
- [ ] `context.Background`.
- [ ] `context.WithCancel`.
- [ ] `context.WithTimeout`.
- [ ] `context.WithDeadline`.
- [ ] parent → child propagation.
- [ ] `Done` / `Err`.
- [ ] always call cancel when required.
- [ ] request-scoped values boundaries.
- [ ] cancellation-aware channel send/receive.
- [ ] HTTP → service → database propagation model.
- [ ] lost cancellation intentional experiment.
- [ ] blocked-send cancellation experiment.
- [ ] graceful shutdown worker pipeline.
- [ ] выполнен [[practice/07-context|Context practice]].
- [ ] `price-processor` shutdown/cancellation checkpoint completed.

## Stage 8 — Database

- [ ] `database/sql` package model.
- [ ] `*sql.DB` as shared pool handle.
- [ ] `PingContext`.
- [ ] `QueryRowContext`.
- [ ] `QueryContext` + `Rows` lifecycle.
- [ ] `rows.Scan`.
- [ ] `rows.Close`.
- [ ] `rows.Err`.
- [ ] `ExecContext`.
- [ ] prepared statements.
- [ ] `BeginTx` / commit / rollback.
- [ ] `defer tx.Rollback` safety pattern.
- [ ] context cancellation of query.
- [ ] parameterized PostgreSQL values.
- [ ] dynamic identifier allowlist.
- [ ] connection pool limits.
- [ ] `DB.Stats()`.
- [ ] safe local pool-exhaustion lab.
- [ ] forgotten `rows.Close` lab.
- [ ] выполнен [[practice/08-database-postgresql|PostgreSQL practice]].
- [ ] выполнен [[practice/09-database-greenplum|Greenplum practice]].
- [ ] [[projects/03-price-storage|Project 3 — price-storage]] completed.

## Stage 9 — HTTP / JSON

- [ ] `net/http` handler model.
- [ ] `http.Server` lifecycle.
- [ ] request context.
- [ ] JSON request/response structs.
- [ ] struct tags.
- [ ] streaming decode/encode decision.
- [ ] validation after decode.
- [ ] request/body size limits.
- [ ] stable HTTP error contract.
- [ ] legacy `encoding/json` basic literacy.
- [ ] `encoding/json/v2` local tutorial path.
- [ ] nil/empty collection wire semantics considered.
- [ ] client cancellation → service → DB test.
- [ ] tutorial in-memory race experiment.
- [ ] выполнен [[practice/10-http-json|HTTP/JSON practice]].
- [ ] [[projects/04-pricing-api|Project 4 — pricing-api]] started.

## Stage 10 — Production Go

- [ ] project/package lifecycle boundaries.
- [ ] config validation.
- [ ] secrets redaction rule.
- [ ] `log/slog` structured logging.
- [ ] retry classification.
- [ ] exponential backoff.
- [ ] retry cancellation.
- [ ] idempotency consideration.
- [ ] rate limiting.
- [ ] concurrency limiting vs rate limiting distinction.
- [ ] bounded queues.
- [ ] resource budget documented.
- [ ] graceful HTTP shutdown.
- [ ] graceful worker shutdown.
- [ ] health/readiness semantics.
- [ ] exported API doc comments where relevant.
- [ ] выполнен [[practice/11-production|Production practice]].

## Stage 11 — Security / hardening

- [ ] Go Security Best Practices read.
- [ ] `govulncheck` tutorial completed.
- [ ] module vulnerability vs reachable symbol distinction.
- [ ] `go vet` gate.
- [ ] race gate.
- [ ] targeted fuzz gate.
- [ ] dependency update review policy.
- [ ] HTTP/JSON trust boundaries documented.
- [ ] SQL value parameterization / identifier allowlist reviewed.
- [ ] input/resource limits reviewed.
- [ ] secrets/logging boundary reviewed.
- [ ] FIPS marked optional unless requirement exists.
- [ ] выполнен [[practice/12-security|Security practice]].
- [ ] threat model for pricing service written.

## Stage 12 — Performance / diagnostics

- [ ] benchmark basics.
- [ ] `-benchmem`.
- [ ] CPU profile.
- [ ] heap profile.
- [ ] `alloc_*` vs `inuse_*` distinction.
- [ ] goroutine profile.
- [ ] block/mutex profile.
- [ ] runtime trace.
- [ ] allocation hotspot found from evidence.
- [ ] escape analysis used only on hotspot.
- [ ] stack vs heap mental model.
- [ ] GC cost model.
- [ ] `GOGC` conceptual trade-off.
- [ ] `GOMEMLIMIT` conceptual trade-off.
- [ ] PGO workflow understood.
- [ ] representative profile requirement understood.
- [ ] выполнен [[practice/13-performance|Performance lab]].
- [ ] one benchmark/profile optimization cycle documented.

## Stage 13 — Language Specification

- [ ] lexical/constants/variables pass.
- [ ] type system pass.
- [ ] type identity / underlying types.
- [ ] method sets.
- [ ] assignability / representability.
- [ ] comparison/comparability.
- [ ] declarations / type parameters.
- [ ] expressions / selectors / assertions.
- [ ] generic instantiation/inference.
- [ ] operators/conversions/evaluation order.
- [ ] `for` / `range`.
- [ ] `go` / channels / `select`.
- [ ] `defer` exact semantics.
- [ ] built-ins.
- [ ] package initialization / `main` lifecycle.
- [ ] errors/runtime panics.
- [ ] `unsafe` reviewed only at overview level.
- [ ] 10 prediction drills with spec references completed.
- [ ] Specification part of [[practice/14-spec-runtime-labs|spec/runtime labs]] completed.

## Stage 14 — Runtime internals

- [ ] memory model read systematically.
- [ ] happens-before.
- [ ] DRF-SC practical meaning.
- [ ] goroutine start vs termination synchronization distinction.
- [ ] stack growth concept.
- [ ] heap escape concept.
- [ ] allocation rate vs live heap.
- [ ] tracing mark/sweep GC model.
- [ ] GC assists understood conceptually.
- [ ] `GOGC`.
- [ ] `GOMEMLIMIT`.
- [ ] GC thrashing risk.
- [ ] scheduler G/M/P model.
- [ ] runnable/running/blocked states.
- [ ] preemption as runtime implementation concern.
- [ ] `GODEBUG=schedtrace` experiment.
- [ ] runtime trace experiment.
- [ ] assembler marked optional unless concrete need.
- [ ] runtime part of [[practice/14-spec-runtime-labs|spec/runtime labs]] completed.

## Projects

### Project 1 — price-cli
- [ ] input contract.
- [ ] CSV.
- [ ] JSON.
- [ ] validation.
- [ ] grouping/aggregation.
- [ ] errors.
- [ ] tests/fuzz.
- [ ] README.

### Project 2 — price-processor
- [ ] streaming reader.
- [ ] batching.
- [ ] bounded workers.
- [ ] fan-out/fan-in.
- [ ] context cancellation.
- [ ] graceful shutdown.
- [ ] `-race` clean.

### Project 3 — price-storage
- [ ] PostgreSQL repository.
- [ ] transaction tests.
- [ ] context query cancellation.
- [ ] pool configuration/stats.
- [ ] Greenplum batch exercise.

### Project 4 — pricing-api
- [ ] `net/http` API.
- [ ] JSON validation.
- [ ] service/repository separation.
- [ ] DB integration.
- [ ] structured logging/config.
- [ ] retries/rate limits where justified.
- [ ] graceful shutdown.
- [ ] security gate.

### Final Project — pricing-pipeline
- [ ] config.
- [ ] structured logging.
- [ ] streaming source.
- [ ] validation.
- [ ] batcher.
- [ ] bounded worker pool.
- [ ] business processing.
- [ ] PostgreSQL/Greenplum sink.
- [ ] context cancellation.
- [ ] retry/backoff.
- [ ] rate limiting.
- [ ] graceful shutdown.
- [ ] metrics/operational counters.
- [ ] unit tests.
- [ ] fuzz tests.
- [ ] race tests.
- [ ] DB integration tests.
- [ ] benchmarks.
- [ ] CPU/heap profiles.
- [ ] runtime trace.
- [ ] Docker.
- [ ] README.
- [ ] architecture diagram.
- [ ] failure drills.
- [ ] optional Kafka source after stable source abstraction.
