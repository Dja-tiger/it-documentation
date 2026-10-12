---
title: "Транзакции database/sql"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/database/execute-transactions.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Транзакции

`sql.Tx` представляет database transaction. Получить её можно через `DB.Begin` или `DB.BeginTx`.

Типичный lifecycle:

1. Begin transaction.
2. Выполнить несколько database operations.
3. При успехе — `Commit`.
4. При ошибке — `Rollback`.

## API внутри transaction

`sql.Tx` предоставляет:

- `Exec` / `ExecContext`;
- `Query` / `QueryContext`;
- `QueryRow` / `QueryRowContext`;
- `Prepare` / `PrepareContext`;
- `Stmt` / `StmtContext`.

Все эти operations относятся к transaction и используют её connection/context.

### Commit

Если `Tx.Commit()` возвращает `nil`, изменения применены. Если commit завершился ошибкой, результаты transaction нельзя считать подтверждёнными.

### Rollback

`Tx.Rollback()` завершает transaction без commit. После rollback объект `Tx` больше невалиден для новых operations.

## Best practices

> [!warning]
> Не управляйте transaction вручную SQL statements вроде `begin`, `commit`, `rollback` через обычный `DB.Exec`. Используйте `sql.Tx`. Иначе `database/sql` pool может выполнить statements на разных physical connections.

> [!warning]
> После `BeginTx` не вызывайте обычные `db.Query`/`db.Exec` для operations, которые должны входить в эту transaction. Они выполнятся вне `Tx`, что может дать inconsistent state или deadlock.

## Пример

```go
func CreateOrder(
    ctx context.Context,
    albumID, quantity, custID int,
) (orderID int64, err error) {
    fail := func(err error) (int64, error) {
        return 0, fmt.Errorf("CreateOrder: %v", err)
    }

    tx, err := db.BeginTx(ctx, nil)
    if err != nil {
        return fail(err)
    }
    defer tx.Rollback()

    var enough bool
    err = tx.QueryRowContext(
        ctx,
        "select (quantity >= ?) from album where id = ?",
        quantity,
        albumID,
    ).Scan(&enough)
    if err != nil {
        if err == sql.ErrNoRows {
            return fail(fmt.Errorf("no such album"))
        }
        return fail(err)
    }

    if !enough {
        return fail(fmt.Errorf("not enough inventory"))
    }

    _, err = tx.ExecContext(
        ctx,
        "update album set quantity = quantity - ? where id = ?",
        quantity,
        albumID,
    )
    if err != nil {
        return fail(err)
    }

    result, err := tx.ExecContext(
        ctx,
        "insert into album_order (album_id, cust_id, quantity, date) values (?, ?, ?, ?)",
        albumID,
        custID,
        quantity,
        time.Now(),
    )
    if err != nil {
        return fail(err)
    }

    orderID, err = result.LastInsertId()
    if err != nil {
        return fail(err)
    }

    if err = tx.Commit(); err != nil {
        return fail(err)
    }

    return orderID, nil
}
```

Паттерн `defer tx.Rollback()` безопасен: после успешного `Commit()` deferred rollback фактически становится no-op, а на любом early return transaction будет rollback.

Использование `BeginTx(ctx, ...)` позволяет cancellation request/timeout влиять на transaction lifecycle.
