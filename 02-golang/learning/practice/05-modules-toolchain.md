# Practice 05 — Modules, packages, workspace, toolchain

## Задание 1. Project layout

### Условие

Организовать `price-cli`:

```text
price-cli/
├── go.mod
├── cmd/price-cli/main.go
└── internal/
    ├── aggregate/
    ├── model/
    └── parser/
```

### Входные данные

Код Project 1, который до рефакторинга может находиться в одном или нескольких простых packages.

### Ожидаемое поведение

`main` содержит wiring/process lifecycle, business logic находится в testable internal packages; CLI behavior не меняется.

### Ограничения

- не создавать package без отдельной ответственности;
- не вводить cyclic imports;
- `internal/` используется как visibility boundary, а не как формальность.

### Acceptance criteria

Build/tests проходят из module root; можно объяснить ответственность каждого package и dependency direction.

### Команды проверки

```bash
gofmt -w .
go test ./...
go vet ./...
go build ./cmd/price-cli
```

## Задание 2. Dependency lifecycle

### Условие

Добавить небольшую external dependency, проверить `go.mod`/`go.sum`, затем удалить import и выполнить tidy.

### Входные данные

Existing `price-cli` и одна безопасная dependency, которая реально используется в temporary exercise code.

### Ожидаемое поведение

До команд предсказать изменения `go.mod`/`go.sum`; после удаления usage `go mod tidy` удаляет ненужные requirements/checksums согласно graph.

### Ограничения

- dependency не должна быть добавлена только ради постоянного усложнения project;
- не редактировать `go.sum` вручную;
- baseline/toolchain Go 1.27.1 не менять.

### Acceptance criteria

Можно объяснить diff до/после и назначение `go.sum`; `go mod verify` проходит.

### Команды проверки

```bash
go list -m all
go mod tidy
go mod verify
go test ./...
```

## Задание 3. Workspace vs `replace`

### Условие

Создать второй local module `price-rules`, подключить его сначала через `replace`, затем через workspace.

### Входные данные

`price-cli` и local sibling module `price-rules` с одной public function/package.

### Ожидаемое поведение

Local development работает в обоих режимах, но release-ready `price-cli/go.mod` не зависит от случайного filesystem path.

### Ограничения

- workspace остаётся development configuration;
- после exercise project должен собираться в documented release configuration;
- нельзя использовать `go.work` как замену normal module versioning/publication semantics.

### Acceptance criteria

Можно объяснить difference `replace` vs workspace и показать reproducible build после удаления local-only configuration.

### Команды проверки

```bash
go work init
go work use ./price-cli ./price-rules
go env GOWORK
go list -m all
go test ./...
```

## Intentional-break lab

### Условие

По очереди: импортировать `internal` package из запрещённого scope; задать недоступный toolchain при запрещённом auto-switch; оставить stale dependency.

### Входные данные

Два local modules и текущий `go.mod`.

### Ожидаемое поведение

Получить три разных classes diagnostics: visibility, toolchain selection, dependency cleanup.

### Ограничения

Baseline files после lab вернуть в исходное состояние; upstream refs проекта документации не менять.

### Acceptance criteria

Каждый diagnostic классифицирован; stale dependency исправлена через `go mod tidy`, а не ручное редактирование checksum data.

### Команды проверки

```bash
go test ./...
go env GOTOOLCHAIN
go mod tidy
go mod verify
```
