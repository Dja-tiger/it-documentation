# Practice 03 — Interfaces и generics

## Задание 1. Processing contracts

### Условие

Спроектировать минимальные interfaces для source/validator/sink pricing pipeline. Не копировать методы «на будущее».

### Входные данные

Batch `[]Price`.

### Ожидаемое поведение

Можно заменить in-memory source/sink test doubles реальными implementations без изменения processing function.

### Ограничения

- interfaces объявлять там, где ими пользуется consumer, если это упрощает design;
- не создавать interface для каждого struct автоматически.

### Acceptance criteria

Минимум две реализации одного contract; tests выполняются против обеих.

### Команды проверки

```bash
gofmt -w .
go test ./...
go vet ./...
```

## Задание 2. Generic `Chunk[T]`

### Условие

Написать generic batching helper, работающий с `[]Price`, `[]Store`, `[]string`.

### Ожидаемое поведение

Один contract для любого element type; boundary cases такие же, как в batching exercise.

### Ограничения

Не добавлять constraint сильнее необходимого.

## Intentional-break lab: typed nil

1. Создать type, удовлетворяющий interface pointer-receiver method'ом.
2. Присвоить nil `*T` переменной interface type.
3. Предсказать `iface == nil`.
4. Вызвать method и исследовать, зависит ли panic от body method.
5. Переписать API так, чтобы caller не полагался на ambiguous nil state.

## Intentional-break lab: method set

Поменять pointer receiver на value receiver и обратно. Для каждой комбинации `T`, `*T`, interface assignment составить таблицу compile/pass до запуска compiler.
