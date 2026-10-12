# Practice 03 — Interfaces и generics

## Задание 1. Processing contracts

### Условие

Спроектировать минимальные interfaces для source/validator/sink pricing pipeline. Не добавлять методы «на будущее».

### Входные данные

Batch `[]Price`, in-memory source и минимум два sink/validator variants для tests.

### Ожидаемое поведение

Processing function работает через contracts и допускает замену test doubles на реальные implementations без изменения orchestration logic.

### Ограничения

- interfaces объявлять со стороны consumer, если это упрощает design;
- не создавать interface для каждого struct автоматически;
- interface должен содержать только реально используемые methods.

### Acceptance criteria

Минимум две реализации одного contract; одинаковый behavioral test проходит против обеих; нет unnecessary marker interfaces.

### Команды проверки

```bash
gofmt -w .
go test ./...
go vet ./...
```

## Задание 2. Generic `Chunk[T]`

### Условие

Написать generic batching helper, работающий с `[]Price`, `[]Store`, `[]string`.

### Входные данные

Collections размеров `0`, `1`, `batchSize`, `batchSize+1`, а также три разных element types.

### Ожидаемое поведение

Один contract работает для любого element type; boundary behavior совпадает с batching exercise Stage 2.

### Ограничения

- не добавлять constraint сильнее необходимого;
- не использовать `any`-based type assertions внутри generic helper ради обхода type system;
- invalid batch size имеет explicit contract.

### Acceptance criteria

Один implementation проходит tests на всех типах и boundaries; можно объяснить, почему constraint минимален.

### Команды проверки

```bash
go test -run TestChunk -v ./...
go test ./...
```

## Intentional-break lab 1. Typed nil

### Условие

Создать type, удовлетворяющий interface pointer-receiver method'ом, присвоить nil `*T` interface variable и исследовать behavior.

### Входные данные

`var p *T = nil`, затем assignment в interface.

### Ожидаемое поведение

До запуска предсказать `iface == nil` и отдельно результат method call в зависимости от method body.

### Ограничения

Panic, если он возникает, должен быть isolated и ожидаем test’ом.

### Acceptance criteria

Можно объяснить две компоненты interface value и переписать API/caller так, чтобы не полагаться на ambiguous nil state.

### Команды проверки

```bash
go test -run TestTypedNil -v ./...
```

## Intentional-break lab 2. Method set

### Условие

Поменять receiver `T` ↔ `*T` и проверить interface assignments.

### Входные данные

Матрица `T`, `*T`, interface с одним required method.

### Ожидаемое поведение

Compile/pass matrix должна совпасть с заранее записанным прогнозом.

### Ограничения

Не путать automatic address-taking при method call с method set при interface assignment.

### Acceptance criteria

Составлена таблица всех комбинаций с объяснением через method-set rules.

### Команды проверки

```bash
go test ./...
go vet ./...
```
