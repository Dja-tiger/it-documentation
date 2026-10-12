# Roadmap самостоятельного изучения Go

Roadmap построен по mastery: календарное число дней не фиксируется. Каждый stage завершается только после практической проверки.

## Как пользоваться

Для каждого этапа:

1. открыть stage-файл;
2. прочитать материалы в указанном порядке;
3. выполнить practice и intentional-break experiments;
4. пройти self-check без подсказок;
5. выполнить practical check с нуля;
6. отметить пункты в [[progress|progress.md]].

## Stage 1 — Foundations

**Prerequisites:** опыт программирования и terminal/Linux.

**Документы:** [[../docs/install|Install]] → [[../docs/getting-started|Getting Started]] → полная существующая цепочка `Create a module` по указаниям stage.

**Упражнения:** [[practice/01-foundations|Foundations practice]].

**Project checkpoint:** подготовить чистый Go workspace и уметь собрать/запустить два локальных module.

**Проходной критерий:** без инструкции создать module, `package main`, импортировать package, выполнить `go run`, `go test`, `go build`.

→ [[stages/01-foundations|Stage 1]]

## Stage 2 — Core language и data structures

**Prerequisites:** Stage 1.

**Документы:** локальная tutorial chain для slice/map + A Tour of Go: Basics, Flow control, More types; Specification только точечно.

**Упражнения:** [[practice/02-core-language|Core language / pricing data]].

**Project checkpoint:** подготовить модели `Price`, `Store`, `Product`, `PriceUpdate`, streaming CSV reader и batcher 100000→3000.

**Проходной критерий:** уверенно использовать functions, pointers, structs, arrays/slices/maps и объяснить `len/cap`, backing array, zero values и map lookup.

→ [[stages/02-core-language|Stage 2]]

## Stage 3 — Methods, interfaces, generics

**Prerequisites:** structs, pointers, maps/slices.

**Документы:** A Tour of Go Methods/Interfaces/Generics + [[../docs/tutorial/generics|Generics tutorial]]; Specification как reference для method sets/type assertions/comparability.

**Упражнения:** [[practice/03-interfaces-generics|Interfaces & generics]].

**Project checkpoint:** выделить processing/storage contracts и generic batching helper там, где generics действительно уменьшают duplication.

**Проходной критерий:** читать типичный Go-код с methods/interfaces и предсказывать, реализует ли `T`/`*T` interface.

→ [[stages/03-methods-interfaces-generics|Stage 3]]

## Stage 4 — Errors, testing, fuzzing

**Prerequisites:** Stage 3.

**Документы:** существующие `handle-errors`/`add-a-test`, [[../docs/code|How to Write Go Code]], [[../docs/tutorial/fuzz|Fuzz tutorial]], pkg.go.dev/errors/testing.

**Упражнения:** [[practice/04-errors-testing|Errors & tests]].

**Project checkpoint:** начать [[projects/01-price-cli|Project 1 — price-cli]].

**Проходной критерий:** error wrapping/identity, table-driven tests, fuzz invariant, regression test после найденного input.

→ [[stages/04-errors-and-testing|Stage 4]]

## Stage 5 — Packages, modules, workspaces, toolchain

**Prerequisites:** небольшой тестируемый Go project.

**Документы:** фактически существующий `docs/modules/*`, [[../docs/tutorial/workspaces|Workspaces]], [[../docs/toolchain|Toolchains]], [[../docs/modules/layout|Module layout]].

**Упражнения:** [[practice/05-modules-toolchain|Modules & toolchain]].

**Project checkpoint:** привести `price-cli` к `cmd/` + `internal/` layout и воспроизводимому `go.mod`/`go.sum`.

**Проходной критерий:** объяснить package vs module, `go.mod`, `go.sum`, MVS, `replace`, workspace и toolchain selection.

→ [[stages/05-modules-packages-toolchain|Stage 5]]

## Stage 6 — Concurrency

**Prerequisites:** уверенный core language.

**Документы:** A Tour concurrency → pkg.go.dev/sync и sync/atomic → [[../docs/race-detector|Race Detector]] → выбранные части [[../docs/memory-model|Memory Model]].

**Упражнения:** [[practice/06-concurrency|Concurrency track]].

**Project checkpoint:** начать [[projects/02-price-processor|Project 2 — price-processor]].

**Проходной критерий:** goroutine → channels → select → WaitGroup/Mutex → worker pool/fan-out/fan-in/pipeline → race/deadlock diagnosis.

→ [[stages/06-concurrency|Stage 6]]

## Stage 7 — Context и cancellation

**Prerequisites:** Stage 6.

**Документы:** pkg.go.dev/context + [[../docs/database/cancel-operations|DB cancellation]] как конкретный propagation example.

**Упражнения:** [[practice/07-context|Context & cancellation]].

**Project checkpoint:** `price-processor` прекращает intake/work/output по cancellation и корректно shutdown’ится.

**Проходной критерий:** передать parent context через service layers, различать timeout/deadline/cancel и не терять cancellation.

→ [[stages/07-context-and-cancellation|Stage 7]]

## Stage 8 — database/sql: PostgreSQL → Greenplum

**Prerequisites:** context + errors/testing.

**Документы:** [[../docs/tutorial/database-access|DB tutorial]] → весь фактически существующий [[../docs/database/index|database/sql guide]].

**Упражнения:** [[practice/08-database-postgresql|PostgreSQL]] → [[practice/09-database-greenplum|Greenplum]].

**Project checkpoint:** [[projects/03-price-storage|Project 3 — price-storage]].

**Проходной критерий:** правильно управлять `sql.DB`, rows/tx/context/pool limits и объяснить pool exhaustion.

→ [[stages/08-database|Stage 8]]

## Stage 9 — HTTP и JSON

**Prerequisites:** context + DB basics.

**Документы:** [[../docs/articles/wiki|Writing Web Applications]] → [[../docs/tutorial/web-service-gin|REST API with Gin]] → [[../docs/tutorial/json|JSON tutorial]] → [[../docs/jsonv2-migration|json/v2 migration]] + pkg.go.dev/net/http.

**Упражнения:** [[practice/10-http-json|HTTP/JSON pricing API]].

**Project checkpoint:** начать [[projects/04-pricing-api|Project 4 — pricing-api]].

**Проходной критерий:** request→validation→service→DB→JSON response с request context и корректным shutdown.

→ [[stages/09-http-and-json|Stage 9]]

## Stage 10 — Production Go

**Prerequisites:** работающий API и processor.

**Документы:** [[../docs/effective-go|Effective Go]] выборочно, [[../docs/comment|Doc Comments]], [[../docs/modules/layout|Layout]], pkg.go.dev/log/slog.

**Упражнения:** [[practice/11-production|Production engineering]].

**Project checkpoint:** config, structured logging, retry/backoff, rate limiting, graceful shutdown и observability boundaries в `pricing-api`.

**Проходной критерий:** сервис имеет явный lifecycle, bounded resources, operational diagnostics и понятную package structure.

→ [[stages/10-production-go|Stage 10]]

## Stage 11 — Security и hardening

**Prerequisites:** production-shaped service.

**Документы:** [[../docs/security/index|Security]] → [[../docs/security/best-practices|Best Practices]] → [[../docs/tutorial/govulncheck|govulncheck]] → [[../docs/security/threat-model|Threat Model]]; fuzz/race уже знакомы.

**Упражнения:** [[practice/12-security|Security hardening]].

**Project checkpoint:** security gate для `pricing-api`/final project.

**Проходной критерий:** `govulncheck`, `go vet`, race/fuzz checks, dependency review и documented trust boundaries.

→ [[stages/11-security-and-hardening|Stage 11]]

## Stage 12 — Performance и diagnostics

**Prerequisites:** tests, concurrency, HTTP, DB.

**Документы:** [[../docs/diagnostics|Diagnostics]] → pkg.go.dev/testing benchmarks → runtime/pprof → [[../docs/gc-guide|GC Guide]] нужными разделами → [[../docs/pgo|PGO]].

**Упражнения:** [[practice/13-performance|Performance lab]].

**Project checkpoint:** profile-driven optimization final service; минимум один benchmark до/после.

**Проходной критерий:** отличать CPU/heap/contention problem, собирать pprof и не оптимизировать allocations без evidence.

→ [[stages/12-performance|Stage 12]]

## Stage 13 — Системное чтение Specification

**Prerequisites:** практический опыт предыдущих stages.

**Документ:** [[../docs/spec|Specification Go 1.27]].

**Упражнения:** [[practice/14-spec-runtime-labs|Spec/runtime labs]].

**Project checkpoint:** review своего кода по method sets, assignability, comparability, initialization, range/select/defer semantics.

**Проходной критерий:** уметь находить нормативный ответ в spec и объяснить ключевые language rules без чтения её как beginner tutorial.

→ [[stages/13-language-specification|Stage 13]]

## Stage 14 — Runtime internals

**Prerequisites:** profiling + Specification + concurrency.

**Документы:** [[../docs/memory-model|Memory Model]] системно → [[../docs/gc-guide|GC Guide]] → [[../docs/diagnostics|Diagnostics/trace]] → [[../docs/godebug|GODEBUG]] → [[../docs/asm|Assembler]] как optional deep dive.

**Упражнения:** [[practice/14-spec-runtime-labs|Spec/runtime labs]].

**Project checkpoint:** [[projects/05-pricing-pipeline|Final Project — production pricing pipeline]].

**Проходной критерий:** объяснить stack/heap/escape, GC trade-offs, scheduler-level symptoms, happens-before и выбрать правильный diagnostic tool.

→ [[stages/14-runtime-internals|Stage 14]]

## Финальный результат

После Stage 14 final project должен объединять:

```text
source
  ↓
streaming reader
  ↓
validation
  ↓
batcher
  ↓
bounded worker pool
  ↓
business processing
  ↓
PostgreSQL / Greenplum
  ↓
metrics + structured logs
```

См. [[projects/README|проекты]]. Kafka добавляется только после устойчивой версии source abstraction, чтобы не подменять изучение Go интеграционным boilerplate.
