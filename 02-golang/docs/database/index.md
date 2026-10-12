---
title: "Доступ к реляционным базам данных"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/database/index.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Доступ к реляционным базам данных

С помощью Go можно использовать в приложениях самые разные базы данных и подходы к доступу к данным. Страницы этого раздела описывают работу со стандартным пакетом [`database/sql`](https://pkg.go.dev/database/sql) для доступа к реляционным базам данных.

Вводный end-to-end tutorial см. в [[../tutorial/database-access|Tutorial: доступ к реляционной базе данных]].

Go поддерживает и другие технологии доступа к данным, в том числе ORM-библиотеки для более высокоуровневой работы с реляционными БД и нереляционные NoSQL-хранилища.

- **Object-relational mapping (ORM) libraries.** Пакет `database/sql` предоставляет функции для более низкоуровневой логики доступа к данным, но Go также позволяет работать с хранилищами на более высоком уровне абстракции. Две популярные ORM-библиотеки: [GORM](https://gorm.io/index.html) ([package reference](https://pkg.go.dev/gorm.io/gorm)) и [ent](https://entgo.io/) ([package reference](https://pkg.go.dev/entgo.io/ent)).
- **NoSQL data stores.** Сообщество Go разработало drivers для большинства NoSQL-хранилищ, включая [MongoDB](https://docs.mongodb.com/drivers/go/) и [Couchbase](https://docs.couchbase.com/go-sdk/current/hello-world/overview.html). Другие packages можно найти через [pkg.go.dev](https://pkg.go.dev/).

### Поддерживаемые СУБД {#supported_dbms}

Go поддерживает наиболее распространённые реляционные СУБД, включая MySQL, Oracle, Postgres, SQL Server, SQLite и другие.

Полный список drivers находится на wiki-странице [SQLDrivers](https://go.dev/wiki/SQLDrivers).

### Функции для выполнения запросов и изменения данных {#functions}

Пакет `database/sql` содержит функции, рассчитанные на разные виды database operations.

Для запросов можно использовать `Query` и `QueryRow`. `QueryRow` предназначен для случая, когда ожидается только одна строка, и позволяет избежать overhead возврата `sql.Rows`, содержащего единственную строку.

Для изменения данных SQL statements вроде `insert`, `update` или `delete` выполняются через `Exec`.

Подробнее:

- [[change-data|Выполнение SQL statements, не возвращающих данные]];
- [[querying|Запрос данных]].

### Транзакции {#transactions}

Через `sql.Tx` можно выполнять database operations внутри transaction. Несколько операций выполняются как единое целое и завершаются либо `commit`, атомарно применяющим все изменения, либо `rollback`, отбрасывающим их.

Подробнее см. [[execute-transactions|Выполнение транзакций]].

### Отмена запросов {#query_cancellation}

`context.Context` позволяет отменять database operation — например, если клиент закрыл соединение или операция выполняется дольше допустимого.

Для database operations пакет `database/sql` предоставляет варианты функций, принимающие `Context`. Через `Context` можно задать timeout или deadline, а также распространить cancellation request по приложению до функции, выполняющей SQL statement, чтобы ненужные ресурсы освобождались как можно раньше.

Подробнее см. [[cancel-operations|Отмена выполняющихся операций]].

### Управляемый connection pool {#connection_pool}

При использовании database handle `sql.DB` приложение работает со встроенным connection pool, который создаёт и освобождает connections в соответствии с потребностями кода. `sql.DB` — основной и наиболее распространённый способ доступа к базе данных в Go. Подробнее см. [[open-handle|Открытие database handle]].

Пакет `database/sql` управляет pool автоматически. Для более сложных случаев параметры pool можно настроить; см. [[manage-connections#Настройка параметров connection pool|Настройка параметров connection pool]].

Когда требуется одна зарезервированная connection, `database/sql` предоставляет [`sql.Conn`](https://pkg.go.dev/database/sql#Conn). `Conn` особенно полезен в ситуациях, где transaction через `sql.Tx` — неподходящий выбор.

Например, приложению может потребоваться:

- выполнить DDL schema changes, содержащие собственную transaction semantics. Смешивать transaction functions пакета `sql` с SQL transaction statements — плохая практика, как описано в [[execute-transactions|Выполнение транзакций]];
- выполнить query locking operations, создающие temporary tables.

Подробнее см. [[manage-connections#Использование выделенных connections|Использование выделенных connections]].
