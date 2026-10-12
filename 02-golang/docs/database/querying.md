---
title: "Запрос данных"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/database/querying.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Запрос данных

При выполнении SQL statement, возвращающего данные, используйте один из `Query` methods пакета `database/sql`. Они возвращают `Row` или `Rows`, данные из которых можно скопировать в переменные через `Scan`. В частности, эти methods используются для `select` statements.

Если statement не возвращает данные, вместо этого можно использовать `Exec` или `ExecContext`. Подробнее см. [[change-data|Выполнение statements, не возвращающих данные]].

Пакет `database/sql` предоставляет два основных способа получить query result:

- **Запрос одной строки.** `QueryRow` возвращает не более одного `Row`. См. [[#Запрос одной строки]].
- **Запрос нескольких строк.** `Query` возвращает все подходящие строки в `Rows`, по которому можно выполнить iteration. См. [[#Запрос нескольких строк]].

Если один SQL statement будет выполняться много раз, рассмотрите prepared statement. Подробнее см. [[prepared-statements|Использование prepared statements]].

> [!warning]
> Не собирайте SQL statement через string-formatting functions вроде `fmt.Sprintf`. Это может создать SQL injection vulnerability. См. [[sql-injection|Предотвращение SQL injection]].

### Запрос одной строки {#single_row}

`QueryRow` получает не более одной database row, например при поиске записи по unique ID. Если query возвращает несколько rows, `Scan` отбрасывает все кроме первой.

`QueryRowContext` работает как `QueryRow`, но принимает `context.Context`. Подробнее см. [[cancel-operations|Отмена выполняющихся операций]].

Следующий пример проверяет, достаточно ли inventory для покупки. SQL statement возвращает `true`, если quantity достаточно, иначе `false`. [`Row.Scan`](https://pkg.go.dev/database/sql#Row.Scan) записывает boolean value через pointer в переменную `enough`.

```go
func canPurchase(id int, quantity int) (bool, error) {
	var enough bool
	// Query for a value based on a single row.
	if err := db.QueryRow("select (quantity >= ?) from album where id = ?",
		quantity, id).Scan(&enough); err != nil {
		if err == sql.ErrNoRows {
			return false, fmt.Errorf("canPurchase %d: unknown album", id)
		}
		return false, fmt.Errorf("canPurchase %d: %v", id, err)
	}
	return enough, nil
}
```

> [!note]
> Parameter placeholders зависят от DBMS и driver. Например, [pq driver](https://pkg.go.dev/github.com/lib/pq) для Postgres использует `$1` вместо `?`.

#### Обработка errors {#single_row_errors}

Сам `QueryRow` error не возвращает. Любой error совместной операции lookup + scan возвращается из `Scan`.

Если query не нашёл ни одной строки, `Scan` возвращает [`sql.ErrNoRows`](https://pkg.go.dev/database/sql#ErrNoRows).

#### Функции, возвращающие одну строку {#single_row_functions}

| Function | Назначение |
| --- | --- |
| [`DB.QueryRow`](https://pkg.go.dev/database/sql#DB.QueryRow), [`DB.QueryRowContext`](https://pkg.go.dev/database/sql#DB.QueryRowContext) | Выполнить single-row query самостоятельно. |
| [`Tx.QueryRow`](https://pkg.go.dev/database/sql#Tx.QueryRow), [`Tx.QueryRowContext`](https://pkg.go.dev/database/sql#Tx.QueryRowContext) | Выполнить single-row query внутри более крупной transaction. См. [[execute-transactions|Выполнение транзакций]]. |
| [`Stmt.QueryRow`](https://pkg.go.dev/database/sql#Stmt.QueryRow), [`Stmt.QueryRowContext`](https://pkg.go.dev/database/sql#Stmt.QueryRowContext) | Выполнить single-row query через уже подготовленный statement. См. [[prepared-statements|Prepared statements]]. |
| [`Conn.QueryRowContext`](https://pkg.go.dev/database/sql#Conn.QueryRowContext) | Использовать с reserved connection. См. [[manage-connections|Управление connections]]. |

### Запрос нескольких строк {#multiple_rows}

Для нескольких rows используются `Query` или `QueryContext`. Они возвращают `Rows`, представляющий query result.

Returned rows перебираются через [`Rows.Next`](https://pkg.go.dev/database/sql#Rows.Next). На каждой iteration `Scan` копирует значения columns в переменные.

`QueryContext` работает как `Query`, но принимает `context.Context`. Подробнее см. [[cancel-operations|Отмена выполняющихся операций]].

Следующий пример возвращает albums указанного artist. Данные находятся в `sql.Rows`; [`Rows.Scan`](https://pkg.go.dev/database/sql#Rows.Scan) копирует columns в поля struct через pointers.

```go
func albumsByArtist(artist string) ([]Album, error) {
	rows, err := db.Query("select * from album where artist = ?", artist)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	// An album slice to hold data from returned rows.
	var albums []Album

	// Loop through rows, using Scan to assign column data to struct fields.
	for rows.Next() {
		var alb Album
		if err := rows.Scan(&alb.ID, &alb.Title, &alb.Artist,
			&alb.Price, &alb.Quantity); err != nil {
			return albums, err
		}
		albums = append(albums, alb)
	}
	if err = rows.Err(); err != nil {
		return albums, err
	}
	return albums, nil
}
```

Обратите внимание на deferred call [`rows.Close`](https://pkg.go.dev/database/sql#Rows.Close). Он освобождает ресурсы `Rows` независимо от того, каким образом завершится function.

Полный проход до конца rows также implicitly закрывает `Rows`, однако `defer` лучше гарантирует освобождение ресурса при любом control flow.

> [!note]
> Parameter placeholders зависят от DBMS и driver. Например, `pq` для Postgres использует `$1` вместо `?`.

#### Обработка errors {#multiple_rows_errors}

После завершения iteration обязательно проверяйте `sql.Rows` на error через `Rows.Err()`. Если query завершился ошибкой во время чтения результатов, именно так приложение узнает о ней.

#### Функции, возвращающие несколько строк {#multiple_rows_functions}

| Function | Назначение |
| --- | --- |
| [`DB.Query`](https://pkg.go.dev/database/sql#DB.Query), [`DB.QueryContext`](https://pkg.go.dev/database/sql#DB.QueryContext) | Выполнить query самостоятельно. |
| [`Tx.Query`](https://pkg.go.dev/database/sql#Tx.Query), [`Tx.QueryContext`](https://pkg.go.dev/database/sql#Tx.QueryContext) | Выполнить query внутри transaction. См. [[execute-transactions|Выполнение транзакций]]. |
| [`Stmt.Query`](https://pkg.go.dev/database/sql#Stmt.Query), [`Stmt.QueryContext`](https://pkg.go.dev/database/sql#Stmt.QueryContext) | Выполнить query через prepared statement. См. [[prepared-statements|Prepared statements]]. |
| [`Conn.QueryContext`](https://pkg.go.dev/database/sql#Conn.QueryContext) | Использовать reserved connection. См. [[manage-connections|Управление connections]]. |

### Обработка nullable column values {#nullable_columns}

Пакет `database/sql` предоставляет специальные types, которые можно передавать в `Scan`, когда database column может содержать `null`.

Каждый из этих types содержит:

- field `Valid`, показывающий, является ли value ненулевым;
- field с самим value, если `Valid == true`.

Пример получает customer name. Если column содержит `null`, приложение подставляет fallback value:

```go
var s sql.NullString
err := db.QueryRow("select name from customer where id = ?", id).Scan(&s)
if err != nil {
	log.Fatal(err)
}

// Find customer name, using placeholder if not present.
name := "Valued Customer"
if s.Valid {
	name = s.String
}
```

Соответствующие types:

- [`NullBool`](https://pkg.go.dev/database/sql#NullBool);
- [`NullFloat64`](https://pkg.go.dev/database/sql#NullFloat64);
- [`NullInt32`](https://pkg.go.dev/database/sql#NullInt32);
- [`NullInt64`](https://pkg.go.dev/database/sql#NullInt64);
- [`NullString`](https://pkg.go.dev/database/sql#NullString);
- [`NullTime`](https://pkg.go.dev/database/sql#NullTime).

### Получение данных из columns {#column_data}

При iteration по query rows `Scan` копирует column values в Go values. Подробный contract описан в [`Rows.Scan`](https://pkg.go.dev/database/sql#Rows.Scan).

Все drivers поддерживают базовый набор data conversions, например SQL `INT` → Go `int`. Некоторые drivers расширяют этот набор; дополнительные conversions следует проверять в documentation конкретного driver.

Обычно `Scan` преобразует database types в близкие Go types: например, SQL `CHAR`, `VARCHAR` и `TEXT` в Go `string`.

Но `Scan` также умеет преобразовывать значение в другой подходящий Go type. Например, если `VARCHAR` гарантированно содержит число, destination можно сделать `int`, и `Scan` выполнит conversion, эквивалентную использованию `strconv.Atoi`.

Полный набор правил см. в [`Rows.Scan`](https://pkg.go.dev/database/sql#Rows.Scan).

### Обработка нескольких result sets {#multiple_result_sets}

Если database operation может вернуть несколько result sets, переходите между ними через [`Rows.NextResultSet`](https://pkg.go.dev/database/sql#Rows.NextResultSet).

Это полезно, например, когда один запрос отдельно выбирает данные из нескольких tables и возвращает отдельный result set для каждого query.

`Rows.NextResultSet` подготавливает следующий result set так, чтобы последующий `Rows.Next` получил его первую row. Return value `bool` показывает, существует ли следующий set.

Пример выполняет два SQL statements. Первый result set возвращает rows из `album`, второй — из `song`:

```go
rows, err := db.Query("select * from album; select * from song;")
if err != nil {
	log.Fatal(err)
}
defer rows.Close()

// Loop through the first result set.
for rows.Next() {
	// Handle result set.
}

// Advance to next result set.
rows.NextResultSet()

// Loop through the second result set.
for rows.Next() {
	// Handle second set.
}

// Check for any error in either result set.
if err := rows.Err(); err != nil {
	log.Fatal(err)
}
```
