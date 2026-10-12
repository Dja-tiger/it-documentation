---
title: "Использование prepared statements"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/database/prepared-statements.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Использование prepared statements

Для многократного использования можно определить prepared statement. Это может немного ускорить код, поскольку DBMS не требуется заново создавать/разбирать statement при каждом выполнении database operation.

> [!note]
> Parameter placeholders в prepared statements зависят от DBMS и driver. Например, [pq driver](https://pkg.go.dev/github.com/lib/pq) для Postgres требует `$1` вместо `?`.

### Что такое prepared statement? {#what_prepared_statement}

Prepared statement — SQL, заранее parsed и сохранённый DBMS. Обычно он содержит placeholders, но не содержит конкретных parameter values. Позднее statement выполняется с набором значений parameters.

### Как использовать prepared statements {#use_prepared_statement}

Если один SQL выполняется многократно, можно заранее подготовить его в `sql.Stmt`, а затем выполнять по мере необходимости.

Следующий пример создаёт prepared statement для выбора конкретного album. [`DB.Prepare`](https://pkg.go.dev/database/sql#DB.Prepare) возвращает [`sql.Stmt`](https://pkg.go.dev/database/sql#Stmt), представляющий prepared statement для заданного SQL text. Parameters для placeholders передаются в `Stmt.Exec`, `Stmt.QueryRow` или `Stmt.Query`.

```go
// AlbumByID retrieves the specified album.
func AlbumByID(id int) (Album, error) {
	// Define a prepared statement. You'd typically define the statement
	// elsewhere and save it for use in functions such as this one.
	stmt, err := db.Prepare("select * from album where id = ?")
	if err != nil {
		log.Fatal(err)
	}
	defer stmt.Close()

	var album Album

	// Execute the prepared statement, passing in an id value for the
	// parameter whose placeholder is ?
	err := stmt.QueryRow(id).Scan(&album.ID, &album.Title, &album.Artist, &album.Price, &album.Quantity)
	if err != nil {
		if err == sql.ErrNoRows {
			// Handle the case of no rows returned.
		}
		return album, err
	}
	return album, nil
}
```

### Поведение prepared statement {#behavior}

Prepared [`sql.Stmt`](https://pkg.go.dev/database/sql#Stmt) предоставляет обычные methods `Exec`, `QueryRow` и `Query`. Подробнее об этих methods см. [[querying|Запрос данных]] и [[change-data|Выполнение SQL statements, не возвращающих данные]].

Поскольку `sql.Stmt` уже представляет заранее определённый SQL statement, его `Exec`, `QueryRow` и `Query` принимают только parameter values, соответствующие placeholders: SQL text повторно передавать не нужно.

Новый `sql.Stmt` можно создать разными способами в зависимости от intended use:

- `DB.Prepare` и `DB.PrepareContext` создают prepared statement, который можно выполнять самостоятельно вне transaction, аналогично `DB.Exec` и `DB.Query`.
- `Tx.Prepare`, `Tx.PrepareContext`, `Tx.Stmt` и `Tx.StmtContext` создают prepared statement для конкретной transaction. `Prepare`/`PrepareContext` принимают SQL text. `Stmt`/`StmtContext` принимают result `DB.Prepare` или `DB.PrepareContext`, то есть превращают обычный `sql.Stmt` в statement, привязанный к данной transaction.
- `Conn.PrepareContext` создаёт prepared statement через `sql.Conn`, представляющий reserved connection.

После завершения работы со statement обязательно вызывайте `stmt.Close`. Это освобождает связанные database resources, включая underlying connections, если они удерживаются implementation. Для statement, являющегося local variable function, обычно достаточно:

```go
defer stmt.Close()
```

#### Функции создания prepared statement {#prepared_statement_functions}

| Function | Назначение |
| --- | --- |
| [`DB.Prepare`](https://pkg.go.dev/database/sql#DB.Prepare), [`DB.PrepareContext`](https://pkg.go.dev/database/sql#DB.PrepareContext) | Подготовить statement для самостоятельного выполнения либо для последующего преобразования в transaction-scoped statement через `Tx.Stmt`. |
| [`Tx.Prepare`](https://pkg.go.dev/database/sql#Tx.Prepare), [`Tx.PrepareContext`](https://pkg.go.dev/database/sql#Tx.PrepareContext), [`Tx.Stmt`](https://pkg.go.dev/database/sql#Tx.Stmt), [`Tx.StmtContext`](https://pkg.go.dev/database/sql#Tx.StmtContext) | Подготовить statement для конкретной transaction. См. [[execute-transactions|Выполнение транзакций]]. |
| [`Conn.PrepareContext`](https://pkg.go.dev/database/sql#Conn.PrepareContext) | Prepared statement на reserved connection. См. [[manage-connections|Управление connections]]. |
