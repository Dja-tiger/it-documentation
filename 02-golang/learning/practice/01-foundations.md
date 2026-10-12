# Practice 01 — Foundations

## Задание 1. Два module без копирования tutorial

### Условие

Создать library module `example.com/pricing` и command module `example.com/price-demo`. Library экспортирует `ValidatePrice(price float64) error`; command вызывает её для нескольких values.

### Входные данные

`99.90`, `0`, `-1`, `149.99`.

### Ожидаемое поведение

Valid prices печатаются как accepted, invalid дают non-nil error и не завершают весь batch преждевременно.

### Ограничения

- два отдельных module;
- local dependency подключить штатным Go mechanism из tutorial;
- минимум один test valid и один invalid case.

### Acceptance criteria

- `go test ./...` проходит в library;
- command запускается через `go run .`;
- `go build .` создаёт executable;
- можно объяснить каждую line `go.mod`.

### Команды проверки

```bash
gofmt -w .
go test ./...
go vet ./...
go build .
```

## Эксперимент

Сделать `ValidatePrice` unexported, затем удалить local replacement. Для каждого failure записать: layer ошибки, diagnostic, причина, исправление.
