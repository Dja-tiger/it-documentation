---
title: "Выполнение запросов"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/database/querying.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Выполнение запросов

Для SQL, возвращающего данные, используйте `Query` APIs. Результаты представлены `Row` или `Rows`, а column values копируются в Go variables через `Scan`.

Если statement не возвращает rows, используйте `Exec`/`ExecContext` — см. [[change-data|Изменение данных]].

> [!warning]
> Не собирайте SQL с user values через `fmt.Sprintf` или string concatenation. Передавайте values отдельными query arguments. См. [[sql-injection|SQL injection]].

## Одна строка: `QueryRow`

`QueryRow` возвращает максимум один logical result `Row`. Если DB вернула несколько rows, `Scan` использует только первую.

`QueryRowContext` дополнительно принимает `context.Context`.

```go
func canPurchase(id int, quantity int) (bool, error) {
    var enough bool

    err := db.QueryRow(
        "select (quantity >= ?) from album where id = ?",
        quantity,
        id,
    ).Scan(&enough)
    if err != nil {
        if err == sql.ErrNoRows {
            return false, fmt.Errorf("canPurchase %d: unknown album", id)
        }
        return false, fmt.Errorf("canPurchase %d: %v", id, err)
    }

    return enough, nil
}
```

`QueryRow` сам не возвращает error. Error query/scan приходит из `Scan`. Если строк нет — `sql.ErrNoRows`.

Placeholder syntax зависит от driver: MySQL-style примеры часто используют `?`, PostgreSQL drivers — `$1`, `$2`, ... .

Single-row APIs:

| API | Scope |
|---|---|
| `DB.QueryRow`, `DB.QueryRowContext` | Обычная операция через pool. |
| `Tx.QueryRow`, `Tx.QueryRowContext` | В transaction. |
| `Stmt.QueryRow`, `Stmt.QueryRowContext` | Prepared statement. |
| `Conn.QueryRowContext` | Dedicated connection. |

## Несколько строк: `Query`

`Query` / `QueryContext` возвращают `*sql.Rows`. Итерируйте через `Next`, а значения копируйте `Scan`.

```go
func albumsByArtist(artist string) ([]Album, error) {
    rows, err := db.Query("select * from album where artist = ?", artist)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    var albums []Album

    for rows.Next() {
        var alb Album
        if err := rows.Scan(
            &alb.ID,
            &alb.Title,
            &alb.Artist,
            &alb.Price,
            &alb.Quantity,
        ); err != nil {
            return albums, err
        }
        albums = append(albums, alb)
    }

    if err := rows.Err(); err != nil {
        return albums, err
    }

    return albums, nil
}
```

Два обязательных production-паттерна:

1. `defer rows.Close()` после успешного `Query`.
2. `rows.Err()` после завершения iteration.

`Rows` может закрыться автоматически при полном чтении, но explicit `defer` защищает early returns/error paths.

Multiple-row APIs:

| API | Scope |
|---|---|
| `DB.Query`, `DB.QueryContext` | Обычная операция. |
| `Tx.Query`, `Tx.QueryContext` | Transaction. |
| `Stmt.Query`, `Stmt.QueryContext` | Prepared statement. |
| `Conn.QueryContext` | Dedicated connection. |

## Nullable columns

Для SQL `null` стандартный package предоставляет nullable wrappers с полем `Valid`, например:

- `sql.NullBool`;
- `sql.NullFloat64`;
- `sql.NullInt32`;
- `sql.NullInt64`;
- `sql.NullString`;
- `sql.NullTime`.

Пример:

```go
var s sql.NullString
err := db.QueryRow("select name from customer where id = ?", id).Scan(&s)
if err != nil {
    log.Fatal(err)
}

name := "Valued Customer"
if s.Valid {
    name = s.String
}
```

## Conversion column values

`Scan` поддерживает базовые conversions между SQL и Go types. Например, SQL `char`/`varchar`/`text` могут сканироваться в `string`, числовые значения — в подходящие numeric types.

Некоторые conversions driver-specific. Всегда проверяйте driver docs, особенно для timestamps, decimals, arrays, JSON, UUID и custom types.

## Несколько result sets

Если DB/driver возвращает несколько result sets, используйте `Rows.NextResultSet`:

```go
rows, err := db.Query("select * from album; select * from song;")
if err != nil {
    log.Fatal(err)
}
defer rows.Close()

for rows.Next() {
    // first result set
}

if rows.NextResultSet() {
    for rows.Next() {
        // second result set
    }
}

if err := rows.Err(); err != nil {
    log.Fatal(err)
}
```
