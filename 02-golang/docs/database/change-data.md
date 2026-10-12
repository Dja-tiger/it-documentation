---
title: "Выполнение SQL statements, не возвращающих данные"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/database/change-data.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Выполнение SQL statements, не возвращающих данные

Для database actions, которые не возвращают данные, используйте methods `Exec` или `ExecContext` из пакета `database/sql`. Типичные SQL statements для такого выполнения — `insert`, `delete` и `update`.

Если query может вернуть rows, используйте `Query` или `QueryContext`. Подробнее см. [[querying|Запрос данных]].

`ExecContext` работает так же, как `Exec`, но дополнительно принимает `context.Context`; см. [[cancel-operations|Отмена выполняющихся операций]].

Следующий пример использует [`DB.Exec`](https://pkg.go.dev/database/sql#DB.Exec), чтобы добавить новый album в table `album`:

```go
func AddAlbum(alb Album) (int64, error) {
	result, err := db.Exec("insert into album (title, artist) values (?, ?)", alb.Title, alb.Artist)
	if err != nil {
		return 0, fmt.Errorf("AddAlbum: %v", err)
	}

	// Get the new album's generated ID for the client.
	id, err := result.LastInsertId()
	if err != nil {
		return 0, fmt.Errorf("AddAlbum: %v", err)
	}
	// Return the new album's ID.
	return id, nil
}
```

`DB.Exec` возвращает два значения: [`sql.Result`](https://pkg.go.dev/database/sql#Result) и `error`.

Если `error == nil`, через `Result` можно:

- получить ID последней вставленной записи, как в примере, через `LastInsertId`;
- получить число rows, затронутых операцией, через `RowsAffected`.

> [!note]
> Parameter placeholders зависят от DBMS и driver. Например, [pq driver](https://pkg.go.dev/github.com/lib/pq) для Postgres требует placeholder `$1`, а не `?`.

Если один и тот же SQL statement выполняется многократно, рассмотрите reusable prepared statement `sql.Stmt`. Подробнее см. [[prepared-statements|Использование prepared statements]].

> [!warning]
> Не собирайте SQL statement через string-formatting functions вроде `fmt.Sprintf`. Это может создать SQL injection vulnerability. См. [[sql-injection|Предотвращение SQL injection]].

#### Функции для SQL statements, не возвращающих rows {#no_rows_functions}

| Function | Назначение |
| --- | --- |
| [`DB.Exec`](https://pkg.go.dev/database/sql#DB.Exec), [`DB.ExecContext`](https://pkg.go.dev/database/sql#DB.ExecContext) | Выполнить одиночный SQL statement вне transaction. |
| [`Tx.Exec`](https://pkg.go.dev/database/sql#Tx.Exec), [`Tx.ExecContext`](https://pkg.go.dev/database/sql#Tx.ExecContext) | Выполнить SQL statement внутри transaction. См. [[execute-transactions|Выполнение транзакций]]. |
| [`Stmt.Exec`](https://pkg.go.dev/database/sql#Stmt.Exec), [`Stmt.ExecContext`](https://pkg.go.dev/database/sql#Stmt.ExecContext) | Выполнить уже подготовленный SQL statement. См. [[prepared-statements|Prepared statements]]. |
| [`Conn.ExecContext`](https://pkg.go.dev/database/sql#Conn.ExecContext) | Выполнить statement через reserved connection. См. [[manage-connections|Управление connections]]. |
