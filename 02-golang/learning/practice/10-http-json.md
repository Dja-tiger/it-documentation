# Practice 10 — HTTP + JSON pricing API

## Domain contract

Используйте собственные request/response types. Минимальная business entity может начинаться с:

```go
type Price struct {
    StoreID string
    PLUID   string
    Price   float64
}
```

Для production-like variant самостоятельно решите, подходит ли `float64` денежному contract или нужен другой representation.

## Задание 1. `POST /prices/validate`

### Условие

Принять JSON price, decode, validate и вернуть structured response.

### Входные данные

- valid record;
- malformed JSON;
- missing identifiers;
- invalid price;
- extra/duplicate fields согласно выбранной v1/v2 policy.

### Ожидаемое поведение

HTTP status и JSON error body стабильны и не раскрывают internal DB/stack details.

### Ограничения

- ограничить body size;
- не читать arbitrary request через unbounded `io.ReadAll`;
- validation отделена от transport decoding.

### Acceptance criteria

Handler tests используют `httptest`; business validation тестируется отдельно.

## Задание 2. `POST /prices/batch`

### Условие

Принять collection/stream pricing updates, разделить на batches и передать service layer.

### Ожидаемое поведение

Client cancellation прекращает new work; in-flight policy явно определена.

### Ограничения

Bounded worker pool; no goroutine-per-record; context из request.

### Acceptance criteria

Integration test отменяет request и доказывает propagation в fake repository.

## Задание 3. `GET /prices/{store_id}/{plu_id}`

### Условие

Получить price из PostgreSQL repository.

### Ожидаемое поведение

- found → `200`;
- not found → выбранный stable `404` error contract;
- DB timeout → не маскируется как validation error;
- canceled request не продолжает бессмысленную DB work.

## Задание 4. Server lifecycle

### Условие

Создать `http.Server` с explicit timeouts и graceful shutdown по root cancellation/signal wiring.

### Acceptance criteria

Новые requests перестают приниматься; active requests получают bounded grace period; process ждёт background components по выбранному lifecycle.

## Intentional-break lab

1. Хранить records в обычном shared slice/map и выполнить parallel handler test под `-race`.
2. Заменить `r.Context()` на `context.Background()` перед repository и показать broken cancellation test.
3. Убрать body limit и сформулировать resource-exhaustion risk.

## Команды проверки

```bash
gofmt -w .
go test ./...
go test -race ./...
go vet ./...
```
