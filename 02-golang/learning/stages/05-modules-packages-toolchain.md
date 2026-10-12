# Stage 5 — Packages, modules, workspaces и toolchain

## Цель

Понимать physical/logical structure Go project, dependency graph и reproducible toolchain behavior.

## Перед началом

Небольшой тестируемый Go codebase.

## Прочитать

1. [[../../docs/code|How to Write Go Code]].
2. [[../../docs/modules/layout|Module layout]].
3. [[../../docs/modules/managing-dependencies|Managing dependencies]].
4. [[../../docs/modules/gomod-ref|go.mod reference]] — как быстрый reference по directives.
5. [[../../docs/modules/reference|Go Modules Reference]] — читать выборочно по module resolution, MVS, proxy/checksum/private modules; manifest отмечает дополнительный source-parity review, поэтому для спорных деталей сверять pinned upstream.
6. [[../../docs/tutorial/workspaces|Workspaces tutorial]].
7. [[../../docs/toolchain|Go Toolchains]].
8. Затем обзор lifecycle: [[../../docs/modules/developing|Developing]], [[../../docs/modules/version-numbers|Version numbers]], [[../../docs/modules/release-workflow|Release workflow]].
9. Publishing/source/major-version читать при реальной необходимости: [[../../docs/modules/managing-source|source]], [[../../docs/modules/publishing|publishing]], [[../../docs/modules/major-version|major version]].

## Что необходимо понять

- [ ] package path, import path, module path.
- [ ] `go.mod`/`go.sum` входят в source control.
- [ ] `require`, indirect requirements, `replace` как main-module policy.
- [ ] `go mod tidy` и dependency graph.
- [ ] Minimal Version Selection и причина выбора конкретной module version.
- [ ] semantic module versions, v2+ path suffix.
- [ ] workspace — dev configuration, не release dependency mechanism.
- [ ] module proxy, checksum database и private-module boundaries на уровне production usage.
- [ ] `cmd/` и `internal/` как useful conventions/visibility boundary.
- [ ] `go`/`toolchain` directives и `GOTOOLCHAIN`.

## Что НЕ нужно пока изучать

- custom module proxy implementation;
- внутреннюю реализацию checksum database;
- complex multi-module monorepo policy;
- compiler/linker internals.

## Практика

- [[../practice/05-modules-toolchain|Modules & toolchain]].

## Эксперименты

- добавить/remove dependency и сравнить `go.mod` до/после `go mod tidy`;
- локально заменить dependency через `replace`, затем через `go.work`;
- посмотреть `go mod graph` и объяснить, почему MVS выбрал фактические versions;
- изменить `go` directive на несовместимую version и посмотреть toolchain behavior;
- попытаться импортировать `internal` package из запрещённого scope.

## Проверка себя

1. Почему package и module — разные уровни?
2. Что гарантирует `go.sum`, а что не гарантирует?
3. Как MVS выбирает version и почему это не «самая новая версия вообще»?
4. Почему `replace` не должен случайно становиться release strategy?
5. Что меняется при переходе module v1 → v2?
6. Чем `go.work` отличается от `go.mod`?
7. Когда module proxy/checksum database влияют на production/CI build и как меняется поведение для private modules?

## Практическая проверка

Перестроить учебный `price-cli` как один module с `cmd/price-cli`, `internal/model`, `internal/parser`, `internal/aggregate`; подключить вторую локальную module через workspace и затем вернуть project к обычному reproducible build.

Дополнительно: по `go mod graph`, `go env GOPROXY GOSUMDB GOPRIVATE` и локальному Go Modules Reference объяснить dependency resolution своего проекта без догадок.

## Критерий завершения

Я могу перейти дальше, если способен:

- объяснить dependency resolution и MVS на уровне, достаточном для production review;
- организовать server/CLI repository без cargo-cult layout;
- отладить `go.mod`/workspace/toolchain/proxy mismatch;
- подготовить module к CI build без локальных hidden dependencies.

## Следующий этап

[[06-concurrency|Stage 6 — Concurrency]].
