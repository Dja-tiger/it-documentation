---
title: "Открытие database handle"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/database/open-handle.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Открытие database handle

`database/sql` абстрагирует управление physical connections. В типичном коде вы не открываете connection перед каждой операцией и не закрываете его сразу после неё. Вместо этого создаётся `*sql.DB` — handle над connection pool.

`sql.DB` открывает/закрывает connections по мере необходимости и безопасен для concurrent use.

## Общий порядок

1. Найти подходящий database driver.
2. Импортировать driver.
3. Открыть `sql.DB` через `sql.Open` или `sql.OpenDB`.
4. При необходимости проверить реальное соединение через `Ping`/`PingContext`.
5. Закрывать полученные resources (`Rows`, `Stmt`), когда они больше не нужны.

## Database driver

Driver переводит запросы между generic `database/sql` API и конкретным DBMS protocol.

Пример обычного import:

```go
import "github.com/go-sql-driver/mysql"
```

Если package импортируется только ради регистрации driver в `database/sql`, применяется blank import:

```go
import _ "github.com/go-sql-driver/mysql"
```

> [!tip]
> Для business/data-access layer по возможности используйте `database/sql` API, а не proprietary driver API. Это уменьшает coupling. Driver-specific APIs оправданы, когда нужны возможности, отсутствующие в generic layer.

## `sql.Open`

`sql.Open` принимает driver name и connection string/DSN:

```go
db, err := sql.Open("mysql", "username:password@tcp(127.0.0.1:3306)/jazzrecords")
if err != nil {
    log.Fatal(err)
}
```

Driver-specific config object часто читаемее, чем ручная сборка DSN:

```go
cfg := mysql.NewConfig()
cfg.User = username
cfg.Passwd = password
cfg.Net = "tcp"
cfg.Addr = "127.0.0.1:3306"
cfg.DBName = "jazzrecords"

db, err = sql.Open("mysql", cfg.FormatDSN())
if err != nil {
    log.Fatal(err)
}
```

## `sql.OpenDB`

`sql.OpenDB` принимает `driver.Connector` и полезен, когда driver предоставляет расширенную connection configuration:

```go
cfg := mysql.NewConfig()
cfg.User = username
cfg.Passwd = password
cfg.Net = "tcp"
cfg.Addr = "127.0.0.1:3306"
cfg.DBName = "jazzrecords"

connector, err := mysql.NewConnector(&cfg)
if err != nil {
    log.Fatal(err)
}

db = sql.OpenDB(connector)
```

## Ошибки `Open`

Успешный `sql.Open` не означает, что network/database connection уже установлен. Ошибка на этом этапе обычно связана с инициализацией handle или parsing DSN.

## Проверка соединения

Чтобы заранее проверить, что DB доступна:

```go
db, err = sql.Open("mysql", connString)
if err != nil {
    log.Fatal(err)
}

if err := db.Ping(); err != nil {
    log.Fatal(err)
}
```

В request-oriented коде обычно предпочтителен `PingContext` с timeout.

## Credentials

Не храните credentials в Go source code.

Один из вариантов — получить secrets из environment, куда они попадают из secret manager/deployment system:

```go
username := os.Getenv("DB_USER")
password := os.Getenv("DB_PASS")
```

Production secret management должен учитывать rotation, access control, logging/redaction и lifecycle credentials.

## Освобождение resources

Хотя physical connections pool'ом управляет `sql.DB`, application обязана закрывать resources, которые удерживают connection/server-side state.

Например:

```go
rows, err := db.Query("select * from album where artist = ?", artist)
if err != nil {
    log.Fatal(err)
}
defer rows.Close()
```

То же относится к prepared statements (`Stmt.Close`). Невысвобожденный `Rows` способен удерживать pool connection и при высокой конкуренции привести к pool exhaustion.
