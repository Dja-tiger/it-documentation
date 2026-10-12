# Practice 12 — Security hardening

## Задание 1. Security gate

### Условие

Собрать repeatable local/CI security-oriented quality sequence для `pricing-api`.

### Входные данные

Текущий source tree и dependencies project.

### Ожидаемое поведение

Formatting/tests/race/vet/vulnerability checks имеют reproducible commands и ненулевой exit code при finding/failure.

### Ограничения

Fuzzing запускается отдельным bounded job/time budget; scanner output не заменяет manual risk review.

### Acceptance criteria

Минимальный gate документирован и запускается одной CI/job последовательностью.

### Команды проверки

```bash
gofmt -w .
go test ./...
go test -race ./...
go vet ./...
govulncheck ./...
```

## Задание 2. Threat model pricing API

### Условие

Описать assets, entry points, trust boundaries, failure/attack classes, preventive controls и telemetry.

### Входные данные

HTTP JSON, file/CSV, DB, external pricing API, environment/secrets, logs и dependencies.

### Ожидаемое поведение

Получается компактная model, связанная с реальной архитектурой, а не generic checklist.

### Ограничения

Обязательно включить resource exhaustion, integrity/idempotency и secret leakage; не требуется формальный enterprise framework.

### Acceptance criteria

Для каждого обязательного boundary есть минимум один risk и control/detection strategy.

### Команды проверки

```bash
grep -n "HTTP\|CSV\|database\|secret\|dependenc" README.md
```

## Задание 3. Input limits

### Условие

Добавить explicit limits на HTTP body, batch size, identifier/string length/format и processing timeout.

### Входные данные

Values ровно на limit, limit+1, malformed identifiers и oversized body.

### Ожидаемое поведение

Boundary input принимается/отклоняется согласно contract; oversized workload останавливается до expensive processing.

### Ограничения

Error response не раскрывает stack/DSN/internal details; limits configurable только в безопасном диапазоне.

### Acceptance criteria

Tests на `limit-1`, `limit`, `limit+1` для ключевых boundaries.

### Команды проверки

```bash
go test -run TestInputLimits -v ./...
go test -race -run TestInputLimits ./...
```

## Задание 4. Dependency vulnerability drill

### Условие

Использовать официальный isolated [[../../docs/tutorial/govulncheck|govulncheck tutorial]] или throwaway module для vulnerable dependency experiment.

### Входные данные

Dependency/version из official tutorial с известным finding и fixed version.

### Ожидаемое поведение

Уметь различить affected module, imported package, reachable vulnerable symbol и available fixed version.

### Ограничения

Не понижать production project dependency намеренно; experiment isolated.

### Acceptance criteria

После scan можно объяснить reachability и remediation; isolated project обновлён/удалён после lab.

### Команды проверки

```bash
govulncheck ./...
go list -m all
```

## Задание 5. Fuzz trust boundary

### Условие

Fuzz JSON/CSV parser + validation boundary.

### Входные данные

Valid seeds и arbitrary mutations, включая empty/oversized-ish bounded strings, malformed Unicode/number formats и truncated payload.

### Ожидаемое поведение

No unexpected panic; accepted object удовлетворяет domain invariants; bounded input не запускает явно unbounded work.

### Ограничения

Fuzz time bounded; discovered crash сохраняется как regression; никакого network/production DB в fuzz loop.

### Acceptance criteria

Fuzz target стабильно запускается, имеет meaningful seeds/invariants и regression path.

### Команды проверки

```bash
go test -fuzz=Fuzz -fuzztime=30s ./...
go test ./...
```
