# Practice 04 — Errors, tests и fuzzing

## Задание 1. Error chain pricing parser

### Условие

Parser принимает raw record и различает validation failure, parse failure и I/O boundary error.

### Ожидаемое поведение

Upper layer добавляет operation context, не уничтожая causal error.

### Ограничения

- минимум один typed error или sentinel только там, где caller действительно меняет behavior;
- wrapping через `%w`;
- caller проверяет identity/type через `errors.Is`/`errors.As`, а не string matching.

### Acceptance criteria

Tests доказывают успешный parse, malformed input и сохранение error identity после нескольких layers wrapping.

### Команды проверки

```bash
go test ./...
go test -run TestParse -v ./...
```

## Задание 2. Table-driven validation

### Входные cases

- valid normal price;
- zero;
- negative;
- empty `StoreID`;
- empty `PLUID`;
- duplicate logical key;
- extreme numeric value по выбранному domain contract.

### Acceptance criteria

Каждый case имеет readable name и проверяет result/error contract.

## Задание 3. Fuzz JSON-like parser boundary

### Условие

Создать fuzz target для parser/validator.

### Invariants

- arbitrary input не приводит к unexpected panic;
- accepted record всегда проходит validation;
- encode/decode round trip сохраняет выбранные fields, если это применимо.

### Команды проверки

```bash
go test ./...
go test -fuzz=Fuzz -fuzztime=30s ./...
```

## Intentional-break lab

Заменить `%w` на `%v`, запустить test `errors.Is`; затем вернуть wrapping. Намеренно добавить panic на определённый byte sequence и убедиться, что fuzzing его находит/минимизирует.
