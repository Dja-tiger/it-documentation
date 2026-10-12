---
title: "Prepared statements"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/database/prepared-statements.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Prepared statements

Prepared statement — SQL, который DBMS заранее parses/prepares и сохраняет для повторного выполнения с разными parameter values.

Это может уменьшить overhead повторной подготовки SQL и удобно, когда один statement выполняется много раз.

Placeholder syntax зависит от DBMS/driver: например, PostgreSQL часто использует `$1`, `$2`, тогда как в MySQL examples используется `?`.

## Использование

```go
func AlbumByID(id int) (Album, error) {
    stmt, err := db.Prepare("select * from album where id = ?")
    if err != nil {
        return Album{}, err
    }
    defer stmt.Close()

    var album Album

    err = stmt.QueryRow(id).Scan(
        &album.ID,
        &album.Title,
        &album.Artist,
        &album.Price,
        &album.Quantity,
    )
    if err != nil {
        if err == sql.ErrNoRows {
            // handle not found
        }
        return album, err
    }

    return album, nil
}
```

Поскольку `sql.Stmt` уже содержит SQL text, его `Exec`, `QueryRow`, `Query` получают только parameter values.

## Где prepare выполняется

- `DB.Prepare` / `DB.PrepareContext` — prepared statement на уровне `sql.DB` для обычных operations;
- `Tx.Prepare` / `Tx.PrepareContext` — statement внутри конкретной transaction;
- `Tx.Stmt` / `Tx.StmtContext` — привязать statement, созданный через DB, к конкретной transaction;
- `Conn.PrepareContext` — statement на dedicated connection.

Всегда закрывайте `Stmt`, когда он больше не нужен:

```go
defer stmt.Close()
```

Это освобождает связанные database resources.
