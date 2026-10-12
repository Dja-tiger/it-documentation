# Practice 08 — PostgreSQL через `database/sql`

## Setup

Используйте только локальный PostgreSQL/container. Минимальная schema:

```sql
create table price_update (
    store_id text not null,
    plu_id text not null,
    price numeric(14, 2) not null,
    updated_at timestamptz not null,
    primary key (store_id, plu_id)
);
```

## Задание 1. Long-lived `*sql.DB`

### Условие

Создать DB handle из config/environment, настроить local pool limits и выполнить `PingContext` с timeout.

### Входные данные

Valid DSN, invalid DSN и недоступный endpoint scenario.

### Ожидаемое поведение

Valid connection проходит ping; invalid/unavailable DB даёт controlled startup error.

### Ограничения

Один shared handle на logical DB config; credentials не hardcode’ятся и не логируются.

### Acceptance criteria

Startup path покрыт tests/controlled integration checks; `db.Close()` вызывается owner’ом при завершении.

### Команды проверки

```bash
go test -run TestDBOpen -v ./...
go test -race ./...
```

## Задание 2. Query + Scan

### Условие

Прочитать prices для выбранного store/list/range через `QueryContext`.

### Входные данные

Fixtures для 0, 1 и N rows; при необходимости nullable column fixture.

### Ожидаемое поведение

`Rows` закрывается; iteration завершается проверкой `rows.Err()`; mapping в domain type deterministic.

### Ограничения

Values parameterized; nullable fields моделируются явно; весь result не материализуется без нужды.

### Acceptance criteria

Integration test покрывает 0/1/N rows и scan failure scenario.

### Команды проверки

```bash
go test -run TestRepositoryQuery -v ./...
```

## Задание 3. Transaction

### Условие

В одной transaction обновить price и записать audit/processing marker.

### Входные данные

Success fixture и fixture, где второй statement намеренно ломается.

### Ожидаемое поведение

Success commit сохраняет обе операции; second-step failure откатывает первую.

### Ограничения

`BeginTx(ctx, ...)`; внутри только `tx.*`; `defer tx.Rollback()`; commit error обрабатывается.

### Acceptance criteria

Integration tests доказывают atomicity и rollback.

### Команды проверки

```bash
go test -run TestTransaction -v ./...
```

## Задание 4. Query cancellation

### Условие

Выполнить локальный long query, например `select pg_sleep(5)`, с timeout существенно меньше 5 секунд.

### Входные данные

Context timeout 100–500 ms и local PostgreSQL.

### Ожидаемое поведение

Operation завершается раньше normal query duration с context/driver-related cancellation error.

### Ограничения

Только local/test DB; exact error text не использовать как единственный contract.

### Acceptance criteria

Measured elapsed time bounded; после cancellation pool остаётся usable для следующего query.

### Команды проверки

```bash
go test -run TestQueryCancellation -v -timeout=10s ./...
```

## Задание 5. Pool exhaustion lab

### Условие

Локально выставить `SetMaxOpenConns(1)`, удержать connection через незакрытый/неисчерпанный `Rows`, затем запустить second query с коротким context timeout.

### Входные данные

Local PostgreSQL, pool size 1, first rows-holder и second concurrent query.

### Ожидаемое поведение

Second operation ждёт connection и завершается по timeout; `DB.Stats()` показывает wait activity. После исправления lifecycle starvation исчезает.

### Ограничения

Только local test DB; короткий timeout; никаких production endpoints.

### Acceptance criteria

Broken и fixed behavior воспроизводятся test’ом; можно объяснить связь `Rows` lifecycle и pool capacity.

### Команды проверки

```bash
go test -run TestPoolExhaustion -v -timeout=10s ./...
go test -race -run TestPoolExhaustion ./...
```

## Дополнительная проверка SQL injection

### Условие

Проверить values и dynamic identifiers в repository queries.

### Входные данные

Обычные values, quote-containing value и invalid user-controlled sort/column identifier.

### Ожидаемое поведение

Values передаются placeholders; dynamic identifiers проходят enum/allowlist mapping и не конкатенируются напрямую.

### Ограничения

Не выполнять destructive injection payloads даже локально без необходимости.

### Acceptance criteria

Tests показывают безопасную обработку special characters и отклонение unknown identifier.

### Команды проверки

```bash
go test -run TestSQLSafety -v ./...
```
