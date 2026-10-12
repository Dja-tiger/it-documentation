# Practice 12 — Security hardening

## Задание 1. Security gate

### Условие

Для `pricing-api` собрать repeatable local/CI sequence.

### Acceptance criteria

Минимум:

```bash
gofmt -w .
go test ./...
go test -race ./...
go vet ./...
govulncheck ./...
```

Fuzz targets запускаются отдельным bounded job/budget.

## Задание 2. Threat model pricing API

### Условие

Описать таблицей:

- asset/data;
- entry point;
- trusted/untrusted side;
- failure/attack class;
- preventive control;
- detection/telemetry.

### Обязательные boundaries

HTTP JSON, file/CSV input, database, external pricing API, environment/secrets, logs, dependencies.

## Задание 3. Input limits

### Условие

Добавить explicit limits на HTTP body, batch size, string lengths/identifier format и processing timeout.

### Acceptance criteria

Boundary tests проверяют ровно limit, limit+1 и malformed input. Error contract не раскрывает internal stack/DSN.

## Задание 4. Dependency vulnerability drill

Использовать официальный isolated [[../../docs/tutorial/govulncheck|govulncheck tutorial]] или отдельный throwaway module. Не понижать dependencies production project намеренно.

### Acceptance criteria

Объяснить difference:

- module affected;
- package imported;
- vulnerable symbol reachable;
- fixed version available.

## Задание 5. Fuzz trust boundary

Fuzz JSON/CSV parser/validation boundary. Invariants:

- no unexpected panic;
- bounded work для bounded input;
- accepted object удовлетворяет domain validation;
- parser не создаёт impossible state.

## Review questions

- Можно ли attacker-controlled value попасть в SQL syntax?
- Может ли один request запустить unbounded goroutines/memory allocation?
- Может ли log содержать secret/raw payload?
- Как application ведёт себя при dependency timeout/failure?
