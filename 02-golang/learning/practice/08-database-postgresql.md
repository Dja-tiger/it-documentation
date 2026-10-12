# Practice 08 — PostgreSQL через `database/sql`

## Setup

Используйте локальный PostgreSQL/container. Schema для exercise можно сделать минимальной:

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

Создать DB handle из config/environment, настроить разумные local limits и выполнить `PingContext` с timeout.

### Ожидаемое поведение

Ошибочная DSN/недоступная DB дают controlled startup error. Credentials не hardcode’ятся.

### Ограничения

В application один shared handle на logical database configuration.

### Acceptance criteria

Логи/ошибки не печатают password. `db.Close()` вызывается при завершении process.

## Задание 2. Query + Scan

### Условие

Прочитать prices для списка/диапазона stores по выбранному безопасному query contract.

### Ожидаемое поведение

`Rows` всегда закрывается; после iteration проверяется `rows.Err()`; nullable columns, если добавлены, моделируются явно.

### Acceptance criteria

Integration test проверяет 0/1/N rows.

## Задание 3. Transaction

### Условие

В одной transaction обновить price и записать audit row/processing marker.

### Ожидаемое поведение

Ошибка второй operation откатывает первую.

### Ограничения

- `BeginTx(ctx, ...)`;
- внутри transaction только `tx.*` APIs;
- `defer tx.Rollback()`;
- commit error обрабатывается.

### Acceptance criteria

Integration test принудительно ломает second statement и проверяет rollback.

## Задание 4. Cancellation

### Условие

Выполнить безопасный local long query, например `select pg_sleep(5)`, с timeout существенно меньше 5 секунд.

### Ожидаемое поведение

Operation завершается по context раньше normal query duration.

### Команды проверки

```bash
go test -race ./...
go test -run TestRepository -v ./...
```

## Задание 5. Pool exhaustion lab

### Условие

Локально выставить `SetMaxOpenConns(1)`. Удержать connection через незакрытый/неисчерпанный `Rows`, затем запустить second query с коротким context timeout.

### Ожидаемое поведение

Second operation ждёт свободную connection и завершается по timeout. `DB.Stats()` показывает wait activity.

### Безопасность эксперимента

Только локальная test database, короткий timeout, никаких production endpoints.

### После эксперимента

Исправить lifecycle и доказать test’ом, что second operation больше не starve’ится.

## SQL injection check

Проверить, что values идут parameters. Для dynamic sort/column/table identifiers использовать enum/allowlist mapping, а не user string concatenation.
