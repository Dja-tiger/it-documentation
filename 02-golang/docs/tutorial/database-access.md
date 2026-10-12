---
title: "Tutorial: доступ к реляционной базе данных"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/database-access.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Доступ к реляционной базе данных

Этот tutorial показывает базовую работу с relational DBMS через стандартный package `database/sql`: создание database, подключение driver, `sql.DB`, запрос нескольких/одной строки и изменение данных.

Пример использует MySQL и небольшой каталог jazz recordings.

## Что будет сделано

1. Создать Go module.
2. Подготовить MySQL database/table.
3. Подключить database driver.
4. Получить `*sql.DB` и проверить соединение.
5. Выполнить query, возвращающий несколько rows.
6. Выполнить query одной row.
7. Добавить новую row через `Exec`.

## Создание module

```bash
mkdir data-access
cd data-access
go mod init example/data-access
```

## Подготовка database

В MySQL:

```sql
create database recordings;
use recordings;
```

Создайте `create-tables.sql`:

```sql
drop table if exists album;

create table album (
    id int auto_increment not null,
    title varchar(128) not null,
    artist varchar(255) not null,
    price decimal(5, 2) not null,
    primary key (id)
);

insert into album (title, artist, price)
values
    ('Blue Train', 'John Coltrane', 56.99),
    ('Giant Steps', 'John Coltrane', 63.99),
    ('Jeru', 'Gerry Mulligan', 17.99),
    ('Sarah Vaughan', 'Sarah Vaughan', 34.98);
```

Выполните script через MySQL CLI:

```text
mysql> source /path/to/create-tables.sql
```

Проверка:

```sql
select *
from album;
```

## Driver

Tutorial использует Go MySQL Driver:

```go
import "github.com/go-sql-driver/mysql"
```

Dependency будет добавлена после появления import:

```bash
go get .
```

## Database handle и connection

`*sql.DB` — handle над managed connection pool, а не одно физическое connection.

```go
package main

import (
    "database/sql"
    "fmt"
    "log"
    "os"

    "github.com/go-sql-driver/mysql"
)

var db *sql.DB

func main() {
    cfg := mysql.NewConfig()
    cfg.User = os.Getenv("DBUSER")
    cfg.Passwd = os.Getenv("DBPASS")
    cfg.Net = "tcp"
    cfg.Addr = "127.0.0.1:3306"
    cfg.DBName = "recordings"

    var err error
    db, err = sql.Open("mysql", cfg.FormatDSN())
    if err != nil {
        log.Fatal(err)
    }

    if err := db.Ping(); err != nil {
        log.Fatal(err)
    }

    fmt.Println("Connected!")
}
```

В tutorial `db` сделан global только для простоты. В production-коде обычно dependency передаётся явно — например, через struct/service constructor.

Credentials задаются вне source:

Linux/macOS:

```bash
export DBUSER=username
export DBPASS=password
```

После этого:

```text
$ go run .
Connected!
```

## Модель данных

```go
type Album struct {
    ID     int64
    Title  string
    Artist string
    Price  float32
}
```

## Query нескольких rows

```go
func albumsByArtist(name string) ([]Album, error) {
    var albums []Album

    rows, err := db.Query(
        "select * from album where artist = ?",
        name,
    )
    if err != nil {
        return nil, fmt.Errorf("albumsByArtist %q: %v", name, err)
    }
    defer rows.Close()

    for rows.Next() {
        var alb Album
        if err := rows.Scan(
            &alb.ID,
            &alb.Title,
            &alb.Artist,
            &alb.Price,
        ); err != nil {
            return nil, fmt.Errorf("albumsByArtist %q: %v", name, err)
        }
        albums = append(albums, alb)
    }

    if err := rows.Err(); err != nil {
        return nil, fmt.Errorf("albumsByArtist %q: %v", name, err)
    }

    return albums, nil
}
```

Ключевые детали:

- SQL text и parameter values передаются раздельно — это защищает values от SQL injection;
- `defer rows.Close()` освобождает связанные resources;
- `rows.Next()` перемещает cursor;
- `rows.Scan(...)` копирует column values в Go variables;
- после цикла обязательно проверяется `rows.Err()`.

В `main`:

```go
albums, err := albumsByArtist("John Coltrane")
if err != nil {
    log.Fatal(err)
}
fmt.Printf("Albums found: %v\n", albums)
```

## Query одной row

Когда ожидается максимум одна строка, используйте `QueryRow`:

```go
func albumByID(id int64) (Album, error) {
    var alb Album

    row := db.QueryRow(
        "select * from album where id = ?",
        id,
    )

    if err := row.Scan(
        &alb.ID,
        &alb.Title,
        &alb.Artist,
        &alb.Price,
    ); err != nil {
        if err == sql.ErrNoRows {
            return alb, fmt.Errorf("albumsByID %d: no such album", id)
        }
        return alb, fmt.Errorf("albumsByID %d: %v", id, err)
    }

    return alb, nil
}
```

`QueryRow` намеренно не возвращает `error` отдельно: query error откладывается до `Scan`. Если rows нет, `Scan` возвращает `sql.ErrNoRows`.

Caller:

```go
alb, err := albumByID(2)
if err != nil {
    log.Fatal(err)
}
fmt.Printf("Album found: %v\n", alb)
```

## Добавление данных

Statements без result rows выполняются через `Exec`:

```go
func addAlbum(alb Album) (int64, error) {
    result, err := db.Exec(
        "insert into album (title, artist, price) values (?, ?, ?)",
        alb.Title,
        alb.Artist,
        alb.Price,
    )
    if err != nil {
        return 0, fmt.Errorf("addAlbum: %v", err)
    }

    id, err := result.LastInsertId()
    if err != nil {
        return 0, fmt.Errorf("addAlbum: %v", err)
    }

    return id, nil
}
```

Caller:

```go
albID, err := addAlbum(Album{
    Title:  "The Modern Sound of Betty Carter",
    Artist: "Betty Carter",
    Price:  49.99,
})
if err != nil {
    log.Fatal(err)
}
fmt.Printf("ID of added album: %v\n", albID)
```

> [!note]
> `LastInsertId()` поддерживается не всеми DBMS/drivers. В PostgreSQL типичный pattern — `insert ... returning ...` с `QueryRow`/`Scan`.

## Полный код

```go
package main

import (
    "database/sql"
    "fmt"
    "log"
    "os"

    "github.com/go-sql-driver/mysql"
)

var db *sql.DB

type Album struct {
    ID     int64
    Title  string
    Artist string
    Price  float32
}

func main() {
    cfg := mysql.NewConfig()
    cfg.User = os.Getenv("DBUSER")
    cfg.Passwd = os.Getenv("DBPASS")
    cfg.Net = "tcp"
    cfg.Addr = "127.0.0.1:3306"
    cfg.DBName = "recordings"

    var err error
    db, err = sql.Open("mysql", cfg.FormatDSN())
    if err != nil {
        log.Fatal(err)
    }

    if err := db.Ping(); err != nil {
        log.Fatal(err)
    }
    fmt.Println("Connected!")

    albums, err := albumsByArtist("John Coltrane")
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("Albums found: %v\n", albums)

    alb, err := albumByID(2)
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("Album found: %v\n", alb)

    albID, err := addAlbum(Album{
        Title:  "The Modern Sound of Betty Carter",
        Artist: "Betty Carter",
        Price:  49.99,
    })
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("ID of added album: %v\n", albID)
}

func albumsByArtist(name string) ([]Album, error) {
    var albums []Album

    rows, err := db.Query("select * from album where artist = ?", name)
    if err != nil {
        return nil, fmt.Errorf("albumsByArtist %q: %v", name, err)
    }
    defer rows.Close()

    for rows.Next() {
        var alb Album
        if err := rows.Scan(&alb.ID, &alb.Title, &alb.Artist, &alb.Price); err != nil {
            return nil, fmt.Errorf("albumsByArtist %q: %v", name, err)
        }
        albums = append(albums, alb)
    }

    if err := rows.Err(); err != nil {
        return nil, fmt.Errorf("albumsByArtist %q: %v", name, err)
    }

    return albums, nil
}

func albumByID(id int64) (Album, error) {
    var alb Album

    row := db.QueryRow("select * from album where id = ?", id)
    if err := row.Scan(&alb.ID, &alb.Title, &alb.Artist, &alb.Price); err != nil {
        if err == sql.ErrNoRows {
            return alb, fmt.Errorf("albumsByID %d: no such album", id)
        }
        return alb, fmt.Errorf("albumsByID %d: %v", id, err)
    }

    return alb, nil
}

func addAlbum(alb Album) (int64, error) {
    result, err := db.Exec(
        "insert into album (title, artist, price) values (?, ?, ?)",
        alb.Title,
        alb.Artist,
        alb.Price,
    )
    if err != nil {
        return 0, fmt.Errorf("addAlbum: %v", err)
    }

    id, err := result.LastInsertId()
    if err != nil {
        return 0, fmt.Errorf("addAlbum: %v", err)
    }

    return id, nil
}
```

Детальный reference по production patterns находится в [[../database/index|разделе `database/sql`]].
