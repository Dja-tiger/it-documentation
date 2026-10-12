# Practice 02 — Core language на pricing data

Используйте базовую модель:

```go
type Price struct {
    StoreID string
    PLUID   string
    Price   float64
}
```

Готовые решения в этом файле отсутствуют.

## Задание 1. Batching 100000 → 3000

### Условие

Function принимает `[]Price` длиной до 100000 и возвращает последовательность batches не больше 3000 records.

### Входные данные

Сгенерировать datasets размером `0`, `1`, `2999`, `3000`, `3001`, `100000` records.

### Ожидаемое поведение

Все records встречаются ровно один раз; порядок сохраняется; последний batch содержит остаток.

### Ограничения

- не копировать каждый `Price` без необходимости;
- корректно обработать empty input;
- для batch size `<= 0` выбрать и документировать explicit contract;
- осознанно решить, допустимы ли shared backing arrays между source и batches.

### Acceptance criteria

Tests покрывают все boundary sizes. Можно объяснить `len`, `cap`, стоимость копирования и последствия shared backing array.

### Команды проверки

```bash
gofmt -w .
go test -run TestBatch -v ./...
go vet ./...
```

## Задание 2. Group by `store_id + plu_id`

### Условие

Сгруппировать records по составному ключу `StoreID + PLUID` без ненадёжной string concatenation.

### Входные данные

Минимум:

- duplicate pair `(store-1, plu-1)`;
- разные pairs, которые collision'ились бы при наивной concatenation, например `("ab", "c")` и `("a", "bc")`;
- несколько stores и PLU.

### Ожидаемое поведение

Разные pairs никогда не смешиваются. Duplicate pair обрабатывается по явно выбранному rule: например latest wins или collection of values.

### Ограничения

- key должен иметь естественную Go comparability;
- нельзя строить key простым `storeID + pluID` без separator/structure;
- aggregation rule должен быть deterministic.

### Acceptance criteria

Есть tests на collision-like input, duplicate key и normal multi-store data. Можно объяснить, почему выбранный key допустим как map key.

### Команды проверки

```bash
go test -run TestGroup -v ./...
go test ./...
```

## Задание 3. Streaming CSV

### Условие

Прочитать большой CSV как stream через `os`/`io`/`bufio` и подходящий standard parser, не загружая весь file bytes в память.

### Входные данные

CSV минимум с полями `store_id`, `plu_id`, `price`; подготовить valid rows, malformed row, invalid numeric value и empty identifiers.

### Ожидаемое поведение

Parser выдаёт `Price` по мере чтения. Malformed row возвращает контекстную error с номером row; caller выбирает stop/skip policy явно.

### Ограничения

- запрещён unbounded `io.ReadAll` для основного пути;
- file lifecycle закрывается owner’ом;
- parsing и domain validation разделены настолько, насколько это упрощает tests.

### Acceptance criteria

На synthetic large file peak memory не должен масштабироваться как полный размер input из-за намеренного full-file buffering. Есть tests на malformed/empty/boundary rows.

### Команды проверки

```bash
go test -run TestCSV -v ./...
go test ./...
go vet ./...
```

## Intentional-break lab

### Условие

Последовательно проверить четыре ошибки mental model:

1. subslice + `append` при spare capacity;
2. missing map key с обычным lookup и comma-ok;
3. dereference `var p *Price`;
4. mutation `[3]Price` и `[]Price`, переданных в functions.

### Входные данные

Минимальные toy values, достаточные для однозначного наблюдения `len/cap/value/panic`.

### Ожидаемое поведение

Перед запуском записать prediction; после запуска объяснить совпадение/расхождение через semantics Go.

### Ограничения

Panic-case запускать из isolated test/program; normal test suite после эксперимента остаётся green.

### Acceptance criteria

Для каждого случая зафиксированы прогноз, фактический result, причина и исправленная mental model.

### Команды проверки

```bash
go test -v ./...
go test -run TestIntentional -v ./...
```
