# Practice 04 — Errors, tests и fuzzing

## Задание 1. Error chain pricing parser

### Условие

Parser принимает raw record и различает validation failure, parse failure и I/O boundary error. Upper layer добавляет operation context, не уничтожая causal error.

### Входные данные

Valid record, malformed numeric field, missing required field и simulated reader error.

### Ожидаемое поведение

Caller может классифицировать wrapped error через `errors.Is`/`errors.As`, не анализируя message string.

### Ограничения

- минимум один typed error или sentinel только там, где caller действительно меняет behavior;
- wrapping через `%w`;
- string matching для error classification запрещён.

### Acceptance criteria

Tests доказывают success, validation/parse/I/O failures и сохранение error identity/type после нескольких layers wrapping.

### Команды проверки

```bash
go test -run TestParse -v ./...
go test ./...
```

## Задание 2. Table-driven validation

### Условие

Построить table-driven suite для domain validation `Price`.

### Входные данные

Cases:

- valid normal price;
- zero;
- negative;
- empty `StoreID`;
- empty `PLUID`;
- duplicate logical key, если validator отвечает за это правило;
- extreme numeric value по выбранному domain contract.

### Ожидаемое поведение

Каждый case имеет deterministic result/error classification и readable subtest name.

### Ограничения

- table содержит input и expected semantics, а не hidden logic;
- boundary cases не объединяются в один opaque test;
- tests не зависят от wall-clock/network.

### Acceptance criteria

Добавление нового validation rule требует добавить/изменить явный test case; failure показывает конкретное имя сценария.

### Команды проверки

```bash
go test -run TestValidate -v ./...
go test -count=20 ./...
```

## Задание 3. Fuzz parser boundary

### Условие

Создать fuzz target для parser/validator boundary.

### Входные данные

Seed corpus минимум из valid record, empty input, malformed separators/JSON-like bytes и edge numeric representation.

### Ожидаемое поведение

Arbitrary input не приводит к unexpected panic; accepted record всегда проходит validation; encode/decode round trip сохраняет выбранные fields, если invariant применим.

### Ограничения

- fuzz property формулируется как invariant, а не как бессмысленная проверка «не упало» только для одного seed;
- найденный reproducer сохраняется как regression case;
- fuzz run ограничен временем.

### Acceptance criteria

Fuzzer проходит bounded run; хотя бы один manual adversarial seed добавлен; найденные bugs, если появились, закреплены обычным test’ом.

### Команды проверки

```bash
go test ./...
go test -fuzz=Fuzz -fuzztime=30s ./...
```

## Intentional-break lab

### Условие

Заменить `%w` на `%v`, затем отдельно добавить panic для определённой последовательности bytes.

### Входные данные

Wrapped known error и fuzz input, достигающий panic branch.

### Ожидаемое поведение

`errors.Is` regression test ломается после `%v`; fuzzing находит/minimize panic input.

### Ограничения

Intentional bug живёт только во временной/local branch или isolated exercise state.

### Acceptance criteria

Обе ошибки воспроизведены инструментами, причины объяснены, working implementation восстановлен, regression tests green.

### Команды проверки

```bash
go test ./...
go test -fuzz=Fuzz -fuzztime=30s ./...
```
