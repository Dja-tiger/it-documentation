---
title: "Открытие database handle"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/database/open-handle.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Открытие database handle

Пакет [`database/sql`](https://pkg.go.dev/database/sql) упрощает доступ к базе данных, уменьшая объём ручного управления connections. В отличие от многих data access API, с `database/sql` приложение обычно не открывает connection явно, не выполняет работу, а затем не закрывает connection вручную. Вместо этого код открывает database handle, представляющий connection pool, и выполняет database operations через этот handle. `Close` вызывается тогда, когда необходимо освободить конкретные ресурсы, например полученные rows или prepared statement.

Иными словами, именно database handle [`sql.DB`](https://pkg.go.dev/database/sql#DB) управляет connections, открывая и закрывая их от имени приложения. Operations, выполняемые через handle, могут иметь concurrent access к базе данных. Подробнее см. [[manage-connections|Управление connections]].

> [!note]
> Можно также зарезервировать отдельную database connection. Подробнее см. [[manage-connections#Использование выделенных connections|Использование выделенных connections]].

Помимо API пакета `database/sql`, сообщество Go разработало drivers для всех наиболее распространённых и многих редких СУБД.

При открытии database handle обычно выполняются следующие шаги:

1. **Найдите driver.** Driver преобразует requests и responses между Go-кодом и базой данных. См. [[#Поиск и импорт database driver]].
2. **Откройте database handle.** После импорта driver можно открыть handle конкретной базы. См. [[#Открытие database handle]].
3. **Подтвердите connection.** После открытия handle код может проверить доступность connection. См. [[#Проверка connection]].

Обычно код приложения не открывает и не закрывает database connections явно — этим занимается database handle. Однако приложение должно освобождать полученные по ходу работы ресурсы, например `sql.Rows`, содержащий результаты query. См. [[#Освобождение ресурсов]].

### Поиск и импорт database driver {#database_driver}

Необходим driver, поддерживающий используемую СУБД. Список drivers см. на [SQLDrivers](https://go.dev/wiki/SQLDrivers).

Чтобы driver стал доступен коду, импортируйте его как обычный Go package. Например:

```go
import "github.com/go-sql-driver/mysql"
```

Если функции driver package напрямую не вызываются — например, package используется неявно пакетом `sql` — нужен blank import с `_` перед import path:

```go
import _ "github.com/go-sql-driver/mysql"
```

> [!note]
> В качестве best practice не используйте собственный API database driver для обычных database operations, если те же операции доступны через `database/sql`. Использование API `database/sql` уменьшает coupling к конкретной СУБД и упрощает возможную миграцию на другой DBMS.

### Открытие database handle {#opening_handle}

Database handle `sql.DB` позволяет читать и записывать данные как отдельными operations, так и внутри transaction.

Получить handle можно двумя способами:

- [`sql.Open`](https://pkg.go.dev/database/sql#Open) — принимает connection string;
- [`sql.OpenDB`](https://pkg.go.dev/database/sql#OpenDB) — принимает `driver.Connector`.

Обе функции возвращают `*sql.DB`.

> [!warning]
> Не храните database credentials в Go source. См. [[#Хранение database credentials]].

#### Открытие через connection string {#open_connection_string}

[`sql.Open`](https://pkg.go.dev/database/sql#Open) используется для подключения через connection string. Формат строки зависит от driver.

Пример для MySQL:

```go
db, err = sql.Open("mysql", "username:password@tcp(127.0.0.1:3306)/jazzrecords")
if err != nil {
	log.Fatal(err)
}
```

Обычно более структурированное описание connection properties делает код понятнее. Конкретные API зависят от driver.

Например, тот же connection для MySQL можно собрать через [`mysql.Config`](https://pkg.go.dev/github.com/go-sql-driver/mysql#Config) и [`FormatDSN`](https://pkg.go.dev/github.com/go-sql-driver/mysql#Config.FormatDSN):

```go
// Specify connection properties.
cfg := mysql.NewConfig()
cfg.User = username
cfg.Passwd = password
cfg.Net = "tcp"
cfg.Addr = "127.0.0.1:3306"
cfg.DBName = "jazzrecords"

// Get a database handle.
db, err = sql.Open("mysql", cfg.FormatDSN())
if err != nil {
	log.Fatal(err)
}
```

#### Открытие через Connector {#open_connector}

[`sql.OpenDB`](https://pkg.go.dev/database/sql#OpenDB) используется, когда нужны driver-specific connection features, которые невозможно выразить обычной connection string. Каждый driver определяет собственный набор connection properties, в том числе DBMS-specific настройки connection request.

Адаптация предыдущего примера для `sql.OpenDB`:

```go
// Specify connection properties.
cfg := mysql.NewConfig()
cfg.User = username
cfg.Passwd = password
cfg.Net = "tcp"
cfg.Addr = "127.0.0.1:3306"
cfg.DBName = "jazzrecords"

// Get a driver-specific connector.
connector, err := mysql.NewConnector(&cfg)
if err != nil {
	log.Fatal(err)
}

// Get a database handle.
db = sql.OpenDB(connector)
```

#### Обработка errors {#handle_errors}

Проверяйте error, возвращённый при создании handle, например из `sql.Open`.

Это **не** connection error. `sql.Open` возвращает error, если не удалось инициализировать сам handle — например, если driver не смог разобрать указанный DSN.

### Проверка connection {#confirm_connection}

При открытии database handle пакет `sql` может не создавать новую физическую connection немедленно. Connection может быть создана только тогда, когда она впервые понадобится коду.

Если база не будет использоваться сразу, но требуется убедиться, что connection может быть установлена, вызовите [`Ping`](https://pkg.go.dev/database/sql#DB.Ping) или [`PingContext`](https://pkg.go.dev/database/sql#DB.PingContext).

Пример:

```go
db, err = sql.Open("mysql", connString)

// Confirm a successful connection.
if err := db.Ping(); err != nil {
	log.Fatal(err)
}
```

### Хранение database credentials {#store_credentials}

Не храните database credentials в Go source: это может раскрыть доступ к содержимому базы.

Credentials следует хранить вне кода, но в месте, доступном приложению. Например, secret manager может хранить credentials и предоставлять API для их получения перед authentication к DBMS.

Распространённый вариант — загрузить secrets в environment до запуска процесса, например из secret manager, а затем прочитать их в Go через [`os.Getenv`](https://pkg.go.dev/os#Getenv):

```go
username := os.Getenv("DB_USER")
password := os.Getenv("DB_PASS")
```

Тот же подход удобен для local testing, где environment variables можно задать вручную.

### Освобождение ресурсов {#free_resources}

Хотя при работе с `database/sql` приложение обычно не управляет physical connections и не закрывает их вручную, оно должно освобождать полученные ресурсы, когда они больше не нужны.

К таким ресурсам относятся, например:

- `sql.Rows`, представляющий данные query result;
- `sql.Stmt`, представляющий prepared statement.

Обычно `Close` вызывается через `defer`, чтобы ресурс гарантированно освободился перед выходом из enclosing function.

Пример с [`sql.Rows`](https://pkg.go.dev/database/sql#Rows):

```go
rows, err := db.Query("select * from album where artist = ?", artist)
if err != nil {
	log.Fatal(err)
}
defer rows.Close()

// Loop through returned rows.
```
