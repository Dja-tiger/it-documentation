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

### Ожидаемое поведение

`main` содержит wiring/process lifecycle, business logic тестируется в internal packages.

### Acceptance criteria

```bash
go test ./...
go vet ./...
go build ./cmd/price-cli
```

проходят из module root.

## Задание 2. Dependency lifecycle

### Условие

Добавить небольшую external dependency, проверить `go.mod`/`go.sum`, затем удалить import и выполнить tidy.

### Acceptance criteria

До команд предсказать, какие файлы/lines изменятся; после — объяснить diff.

### Команды проверки

```bash
go list -m all
go mod tidy
go mod verify
```

## Задание 3. Workspace vs replace

### Условие

Создать второй local module `price-rules`, подключить сначала `replace`, затем workspace.

### Ожидаемое поведение

Local development работает в обоих случаях, но release-ready `price-cli/go.mod` не зависит от случайного local path.

### Acceptance criteria

Объяснить, какую проблему решает `go.work` и почему он не заменяет normal module versioning.

## Intentional-break lab

- импортировать internal package из недопустимого module;
- задать `go` requirement выше имеющегося toolchain при режиме, запрещающем auto-switch;
- оставить stale dependency и проверить, что делает `go mod tidy`.
