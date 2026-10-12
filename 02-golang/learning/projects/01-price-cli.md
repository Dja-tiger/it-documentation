# Project 1 — `price-cli`

## Цель

Закрепить core language, errors, files, JSON/CSV и tests без concurrency/DB complexity.

## После каких stages

Начать после [[../stages/04-errors-and-testing|Stage 4]], привести layout в порядок после [[../stages/05-modules-packages-toolchain|Stage 5]].

## Функции

CLI получает path к JSON или CSV с prices и:

1. читает input;
2. парсит records;
3. валидирует;
4. отделяет invalid records;
5. группирует по `(store_id, plu_id)`;
6. считает простой aggregate/report по выбранному contract;
7. выводит result в stdout/file.

Минимальная сущность:

```go
type Price struct {
    StoreID string
    PLUID   string
    Price   float64
}
```

Добавьте `Store`, `Product`, `PriceUpdate`, когда они реально нужны contract’у, а не ради количества structs.

## Ограничения

- input file может быть большим: не использовать unbounded `os.ReadFile`/`io.ReadAll` как единственный design;
- parse/validation errors должны содержать record/line context;
- duplicate key policy должна быть явно определена;
- no global mutable state;
- no goroutines — concurrency появится в следующем project.

## Acceptance criteria

- JSON и CSV happy path;
- malformed record;
- empty file;
- duplicate logical key;
- batch/grouping functions покрыты table tests;
- error chain сохраняет root cause;
- CLI возвращает meaningful non-zero exit status при fatal error;
- `go test ./...` и `go vet ./...` clean.

## Обязательные tests

- parser;
- validation;
- aggregation/grouping;
- error wrapping/identity;
- streaming boundary;
- минимум один fuzz target parser/decoder.

## Практическая защита

Без открытия старого code объяснить:

1. какие packages существуют и почему;
2. где ownership file resource;
3. почему выбранный key map comparable;
4. как обрабатываются malformed/invalid records;
5. где мог бы появиться excessive allocation и как это измерить позже.

## Следующий проект

[[02-price-processor|Project 2 — price-processor]].
