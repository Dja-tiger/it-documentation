---
title: "Выполнение транзакций"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/database/execute-transactions.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Выполнение транзакций

Database transactions выполняются через [`sql.Tx`](https://pkg.go.dev/database/sql#Tx), представляющий transaction.

Помимо transaction-specific methods `Commit` и `Rollback`, `sql.Tx` предоставляет methods обычных database operations. Получить `sql.Tx` можно через `DB.Begin` или `DB.BeginTx`.

[Database transaction](https://en.wikipedia.org/wiki/Database_transaction) объединяет несколько operations в рамках одной общей цели. Либо все operations должны завершиться успешно, либо ни одна из них не должна быть применена, сохраняя data integrity в обоих случаях.

Обычный transaction workflow:

1. начать transaction;
2. выполнить набор database operations;
3. если errors не возникли — выполнить commit и применить changes;
4. если возник error — выполнить rollback и оставить database без изменений.

Пакет `database/sql` предоставляет methods как для начала/завершения transaction, так и для operations внутри неё.

### Начало transaction

[`DB.Begin`](https://pkg.go.dev/database/sql#DB.Begin) или [`DB.BeginTx`](https://pkg.go.dev/database/sql#DB.BeginTx) начинают новую database transaction и возвращают `sql.Tx`.

### Database operations внутри transaction

Через `sql.Tx` можно выполнять последовательность queries и updates с использованием **одной connection**.

`Tx` предоставляет:

- [`Exec`](https://pkg.go.dev/database/sql#Tx.Exec) и [`ExecContext`](https://pkg.go.dev/database/sql#Tx.ExecContext) для SQL statements, изменяющих данные, например `insert`, `update`, `delete`. См. [[change-data|Выполнение SQL statements, не возвращающих данные]].
- [`Query`](https://pkg.go.dev/database/sql#Tx.Query), [`QueryContext`](https://pkg.go.dev/database/sql#Tx.QueryContext), [`QueryRow`](https://pkg.go.dev/database/sql#Tx.QueryRow), [`QueryRowContext`](https://pkg.go.dev/database/sql#Tx.QueryRowContext) для operations, возвращающих rows. См. [[querying|Запрос данных]].
- [`Prepare`](https://pkg.go.dev/database/sql#Tx.Prepare), [`PrepareContext`](https://pkg.go.dev/database/sql#Tx.PrepareContext), [`Stmt`](https://pkg.go.dev/database/sql#Tx.Stmt), [`StmtContext`](https://pkg.go.dev/database/sql#Tx.StmtContext) для prepared statements. См. [[prepared-statements|Использование prepared statements]].

### Завершение transaction

Transaction завершается **одним** из двух способов.

#### Commit

[`Tx.Commit`](https://pkg.go.dev/database/sql#Tx.Commit) применяет transaction.

Если `Commit` успешен (`error == nil`), все query results считаются valid, а выполненные updates применяются к database как одно atomic change.

Если `Commit` завершился error, все results, полученные через `Query` и `Exec` этого `Tx`, следует считать invalid и отбросить.

#### Rollback

[`Tx.Rollback`](https://pkg.go.dev/database/sql#Tx.Rollback) откатывает transaction.

Даже если сам `Tx.Rollback` возвращает error, transaction после этого больше не valid и не считается committed в database.

### Best practices {#best_practices}

Transaction semantics и connection management могут быть сложными, поэтому придерживайтесь следующих правил.

- Управляйте transactions только через API `database/sql`, описанный в этом разделе. **Не выполняйте напрямую** transaction SQL statements вроде `begin` и `commit`: особенно в concurrent programs это может оставить database в непредсказуемом состоянии.
- Во время работы с transaction не вызывайте напрямую non-transaction methods `sql.DB`. Такие calls выполняются **вне** текущей transaction и могут дать коду inconsistent view database state или даже привести к deadlock.

### Пример {#example}

Следующий пример использует transaction для создания customer order на album.

Последовательность:

1. Начать transaction.
2. Отложить `Rollback` через `defer`. Если transaction завершится успешно, `Commit` выполнится раньше выхода из function, и deferred rollback станет no-op. При failure commit не произойдёт, и rollback сработает при выходе.
3. Проверить достаточный inventory для заказанного album.
4. Если inventory достаточно, уменьшить quantity на число заказанных albums.
5. Создать order и получить его generated ID.
6. Выполнить commit и вернуть ID.

В примере используются `Tx` methods с `context.Context`. Это позволяет отменить выполнение function вместе с database operations, если оно идёт слишком долго или client connection закрылась. Подробнее см. [[cancel-operations|Отмена выполняющихся операций]].

```go
// CreateOrder creates an order for an album and returns the new order ID.
func CreateOrder(ctx context.Context, albumID, quantity, custID int) (orderID int64, err error) {

	// Create a helper function for preparing failure results.
	fail := func(err error) (int64, error) {
		return 0, fmt.Errorf("CreateOrder: %v", err)
	}

	// Get a Tx for making transaction requests.
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return fail(err)
	}
	// Defer a rollback in case anything fails.
	defer tx.Rollback()

	// Confirm that album inventory is enough for the order.
	var enough bool
	if err = tx.QueryRowContext(ctx, "select (quantity >= ?) from album where id = ?",
		quantity, albumID).Scan(&enough); err != nil {
		if err == sql.ErrNoRows {
			return fail(fmt.Errorf("no such album"))
		}
		return fail(err)
	}
	if !enough {
		return fail(fmt.Errorf("not enough inventory"))
	}

	// Update the album inventory to remove the quantity in the order.
	_, err = tx.ExecContext(ctx, "update album set quantity = quantity - ? where id = ?",
		quantity, albumID)
	if err != nil {
		return fail(err)
	}

	// Create a new row in the album_order table.
	result, err := tx.ExecContext(ctx, "insert into album_order (album_id, cust_id, quantity, date) values (?, ?, ?, ?)",
		albumID, custID, quantity, time.Now())
	if err != nil {
		return fail(err)
	}
	// Get the ID of the order item just created.
	orderID, err = result.LastInsertId()
	if err != nil {
		return fail(err)
	}

	// Commit the transaction.
	if err = tx.Commit(); err != nil {
		return fail(err)
	}

	// Return the order ID.
	return orderID, nil
}
```
