# Practice 01 — Foundations

## Задание 1. Два module без копирования tutorial

### Условие

Создать library module `example.com/pricing` и command module `example.com/price-demo`. Library экспортирует `ValidatePrice(price float64) error`; command вызывает её для нескольких values.

### Входные данные

Минимальный набор: `99.90`, `0`, `-1`, `149.99`.

### Ожидаемое поведение

Valid prices печатаются как accepted. Invalid values дают non-nil error и не завершают весь batch преждевременно.

### Ограничения

- два отдельных module;
- local dependency подключить штатным Go mechanism из существующего tutorial;
- минимум один test для valid и один для invalid case;
- не копировать имена/functions из tutorial дословно, кроме стандартных Go-конструкций.

### Acceptance criteria

- command запускается через `go run .`;
- library tests проходят;
- command собирается в executable;
- можно объяснить каждую line обоих `go.mod`;
- можно объяснить, почему exported function доступна из второго package.

### Команды проверки

```bash
gofmt -w .
go test ./...
go vet ./...
go build .
```

## Intentional-break experiment

### Условие

Сначала сделать `ValidatePrice` unexported, затем в отдельном запуске удалить local replacement до публикации module.

### Входные данные

Тот же command и те же price values.

### Ожидаемое поведение

Оба изменения должны привести к диагностируемой проблеме, но на разных слоях: visibility и module resolution.

### Ограничения

Ломать только локальный учебный project. После каждого эксперимента возвращать working state.

### Acceptance criteria

Для каждого failure записаны: layer ошибки, точный diagnostic, причина и минимальное исправление.

### Команды проверки

```bash
go run .
go test ./...
go env GOMOD
```
