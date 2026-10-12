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

Сгенерировать 100000 records.

### Ожидаемое поведение

Все records встречаются ровно один раз; порядок сохраняется; последний batch имеет остаток.

### Ограничения

- не копировать каждый `Price` без необходимости;
- корректно обработать empty input и batch size `<= 0` выбранным explicit contract.

### Acceptance criteria

Tests на 0, 1, 2999, 3000, 3001, 100000 records. Объяснить trade-off shared backing arrays.

### Команды проверки

```bash
go test ./...
go test -run TestBatch -v ./...
```

## Задание 2. Group by store_id + plu_id

### Условие

Сгруппировать records по составному ключу `StoreID + PLUID` без ненадёжной string concatenation.

### Ожидаемое поведение

Два разных pair не collision'ятся; duplicate pair агрегируется по явно выбранному rule (например latest wins или slice values).

### Ограничения

Key должен иметь естественную Go comparability.

### Acceptance criteria

Есть tests на collision-like input (`ab`+`c` против `a`+`bc`) и duplicate key.

## Задание 3. Streaming CSV

### Условие

Прочитать большой CSV как stream через `os`/`io`/`bufio`/подходящий standard parser, не загружая весь file bytes в память.

### Acceptance criteria

Parser выдаёт `Price` по мере чтения; malformed row возвращает контекстную error с номером row.

## Intentional-break lab

1. Создать slice с spare capacity, сделать subslice, выполнить `append` и проверить mutation соседнего view.
2. Прочитать missing map key как обычный lookup и через comma-ok.
3. Dereference `var p *Price`.
4. Передать `[3]Price` и `[]Price` в functions, изменить element и объяснить разницу.

Перед каждым запуском записать прогноз `len/cap/value/panic`.
