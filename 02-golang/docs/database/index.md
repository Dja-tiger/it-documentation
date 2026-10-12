---
title: "Доступ к реляционным базам данных"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/database/index.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Доступ к реляционным базам данных

Стандартный package [`database/sql`](https://pkg.go.dev/database/sql) предоставляет общий API для работы с relational DBMS через database drivers.

Для первого end-to-end примера см. [[../tutorial/database-access|Tutorial: Accessing a relational database]].

Помимо `database/sql`, Go ecosystem включает:

- ORM libraries, например GORM и ent;
- drivers/clients для NoSQL systems, включая MongoDB и Couchbase.

## Поддерживаемые DBMS

Через соответствующие drivers Go работает с большинством распространённых relational systems: MySQL, Oracle, PostgreSQL, SQL Server, SQLite и др. Список drivers поддерживается на Go Wiki SQLDrivers.

## Какой метод использовать

`database/sql` разделяет APIs по типу операции:

- `QueryRow` / `QueryRowContext` — когда ожидается максимум одна строка;
- `Query` / `QueryContext` — когда ожидается набор rows;
- `Exec` / `ExecContext` — statements без result rows, например `insert`, `update`, `delete`.

Использование более конкретного API уменьшает лишние allocations/объекты и делает intent очевиднее.

## Transactions

`sql.Tx` представляет database transaction. Несколько операций выполняются в одном transaction context и завершаются:

- `Commit()` — атомарно применить изменения;
- `Rollback()` — отказаться от изменений.

Подробнее: [[execute-transactions|Транзакции]].

## Cancellation

Context-aware методы позволяют ограничивать database operation timeout/deadline и распространять cancellation из внешнего request lifecycle:

- `QueryContext`;
- `ExecContext`;
- `BeginTx`;
- и другие APIs с `context.Context`.

Подробнее: [[cancel-operations|Отмена операций]].

## Managed connection pool

`sql.DB` — не одно физическое соединение. Это concurrency-safe handle, управляющий connection pool.

Обычно application хранит один long-lived `*sql.DB` на logical database/configuration и переиспользует его из многих goroutines.

Pool автоматически создаёт и возвращает connections. Для tuning доступны:

- `SetMaxOpenConns`;
- `SetMaxIdleConns`;
- `SetConnMaxIdleTime`;
- `SetConnMaxLifetime`.

Подробнее: [[manage-connections|Управление соединениями]].

## Dedicated connection

Если последовательность операций обязана выполняться на одном конкретном physical connection, можно получить `*sql.Conn` через `DB.Conn`.

Это полезно для connection-local semantics, temporary objects или DB-specific behavior, которые не подходят под обычный pool. Для transactions предпочтительнее использовать `sql.Tx`.
