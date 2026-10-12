# Practice 10 — HTTP + JSON pricing API

Используйте собственные request/response types. Минимальная entity может начинаться с:

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

Valid record, malformed JSON, missing identifiers, invalid price, extra/duplicate fields согласно выбранной v1/v2 policy.

### Ожидаемое поведение

HTTP status и JSON error body стабильны; internal DB/stack details не раскрываются.

### Ограничения

Body size ограничен; unbounded `io.ReadAll` запрещён; domain validation отделена от transport decoding.

### Acceptance criteria

Handler tests через `httptest`; business validation тестируется отдельно; boundary body size проверен.

### Команды проверки

```bash
go test -run TestValidateHandler -v ./...
go test -race -run TestValidateHandler ./...
```

## Задание 2. `POST /prices/batch`

### Условие

Принять collection/stream pricing updates, разделить на batches и передать service layer.

### Входные данные

0, 1, 3000, 3001+ records; invalid record; client cancellation mid-request.

### Ожидаемое поведение

Bounded worker pool; cancellation прекращает new work; accepted/in-flight policy documented.

### Ограничения

No goroutine per record; request context используется как parent; queue bounded.

### Acceptance criteria

Integration/handler test отменяет request и доказывает propagation в fake repository/service.

### Команды проверки

```bash
go test -run TestBatchHandler -v ./...
go test -race -run TestBatchHandler -count=20 ./...
```

## Задание 3. `GET /prices/{store_id}/{plu_id}`

### Условие

Получить price из PostgreSQL repository.

### Входные данные

Existing key, missing key, DB timeout/error и canceled request.

### Ожидаемое поведение

Found → `200`; not found → stable `404`; DB timeout не маскируется как validation error; canceled request прекращает downstream work.

### Ограничения

Transport не зависит от concrete DB driver error text; domain/repository errors маппятся осознанно.

### Acceptance criteria

Tests покрывают все four paths и stable response schema.

### Команды проверки

```bash
go test -run TestGetPriceHandler -v ./...
```

## Задание 4. Server lifecycle

### Условие

Создать `http.Server` с explicit timeouts и graceful shutdown по root cancellation/signal wiring.

### Входные данные

Normal requests, long request и shutdown while request is active.

### Ожидаемое поведение

New connections/requests перестают приниматься согласно server lifecycle; active work имеет bounded grace period; background components завершаются coordinated способом.

### Ограничения

Shutdown deadline обязателен; process не завершается через arbitrary sleep.

### Acceptance criteria

Shutdown test/drill завершается deterministic и не оставляет workers.

### Команды проверки

```bash
go test -run TestServerShutdown -v -timeout=10s ./...
go test -race -run TestServerShutdown ./...
```

## Задание 5. Kafka/API-like JSON payload без Kafka client

### Условие

Распарсить transport envelope, похожий на сообщение из Kafka или внешнего pricing API, и преобразовать его в domain `PriceUpdate`.

### Входные данные

Например envelope с `event_id`, `event_time`, `source`, `payload` и nested price fields; добавить unknown field, malformed timestamp и invalid domain payload.

### Ожидаемое поведение

Transport metadata разбирается отдельно от domain validation; malformed envelope и invalid domain record различаются; successful message даёт typed domain object.

### Ограничения

Не подключать Kafka library на этом этапе; задача проверяет JSON contract/decoding boundary, а не broker integration.

### Acceptance criteria

Table tests покрывают valid API-like/Kafka-like payload, malformed envelope, invalid timestamp и invalid `PriceUpdate`.

### Команды проверки

```bash
go test -run TestEventEnvelope -v ./...
go test ./...
```

## Intentional-break lab

### Условие

По очереди: хранить records в обычном shared map/slice под concurrent handlers; заменить `r.Context()` на `context.Background()`; убрать body limit.

### Входные данные

Parallel requests, canceled request и oversized request body.

### Ожидаемое поведение

Race detector обнаруживает shared-state bug; cancellation regression test ломается; body-limit removal формирует очевидный resource-exhaustion risk.

### Ограничения

Broken variants только isolated/local; oversized input bounded test tooling’ом.

### Acceptance criteria

Все три failure modes объяснены и исправлены; final suite green.

### Команды проверки

```bash
gofmt -w .
go test ./...
go test -race ./...
go vet ./...
```
