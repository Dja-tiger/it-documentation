---
title: "Изменение данных через SQL"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/database/change-data.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Выполнение SQL statements без result rows

Для операций, не возвращающих rows, используйте `Exec` или `ExecContext`. Типичные statements: `insert`, `update`, `delete`.

Если SQL возвращает data rows, используйте `Query` APIs.

`ExecContext` аналогичен `Exec`, но принимает `context.Context`.

```go
func AddAlbum(alb Album) (int64, error) {
    result, err := db.Exec(
        "insert into album (title, artist) values (?, ?)",
        alb.Title,
        alb.Artist,
    )
    if err != nil {
        return 0, fmt.Errorf("AddAlbum: %v", err)
    }

    id, err := result.LastInsertId()
    if err != nil {
        return 0, fmt.Errorf("AddAlbum: %v", err)
    }

    return id, nil
}
```

`Exec` возвращает `sql.Result` и `error`. В зависимости от DB/driver через Result доступны:

- `LastInsertId()`;
- `RowsAffected()`.

Не все DBMS поддерживают `LastInsertId`; PostgreSQL обычно использует `returning` с query API.

Placeholder syntax также driver-specific (`?` против `$1` и т. п.).

Если один statement выполняется многократно, рассмотрите prepared `sql.Stmt`.

> [!warning]
> Не используйте `fmt.Sprintf` для подстановки values в SQL.

Доступные scopes:

| API | Scope |
|---|---|
| `DB.Exec`, `DB.ExecContext` | Обычная операция. |
| `Tx.Exec`, `Tx.ExecContext` | Transaction. |
| `Stmt.Exec`, `Stmt.ExecContext` | Prepared statement. |
| `Conn.ExecContext` | Dedicated connection. |
