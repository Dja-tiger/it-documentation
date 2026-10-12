---
title: "Tutorial: доступ к реляционной базе данных"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/database-access.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Доступ к реляционной базе данных

Этот tutorial знакомит с основами доступа к реляционной базе данных из Go через standard library package `database/sql`.

Tutorial предполагает базовое знакомство с Go и его tooling. Если это первое знакомство с Go, сначала см. [[../getting-started|Tutorial: начало работы с Go]].

Package [`database/sql`](https://pkg.go.dev/database/sql) содержит types и functions для подключения к базам данных, выполнения transactions, отмены выполняющихся operations и других database tasks. Более подробный guide находится в [[../database/index|Работа с реляционными базами данных]].

В tutorial вы создадите database, затем напишете код для доступа к ней. Example project хранит данные о vintage jazz records.

Последовательность:

1. создать folder для code;
2. подготовить database;
3. импортировать database driver;
4. получить database handle и проверить connection;
5. запросить несколько rows;
6. запросить одну row;
7. добавить data.

> [!note]
> Другие tutorials см. на [go.dev/doc/tutorial](https://go.dev/doc/tutorial/).

## Предварительные требования {#prerequisites}

- установленная реляционная СУБД [MySQL](https://dev.mysql.com/doc/mysql-installation-excerpt/5.7/en/);
- установленный Go; см. [[../install|Установка Go]];
- text editor;
- terminal Linux/macOS или PowerShell/`cmd` в Windows.

## Создайте folder для code {#create_folder}

1. Перейдите в home directory.

Linux/macOS:

```text
$ cd
```

Windows:

```text
C:\> cd %HOMEPATH%
```

Далее prompt показывается как `$`; используемые команды также работают в Windows.

2. Создайте directory `data-access`:

```text
$ mkdir data-access
$ cd data-access
```

3. Создайте module для dependencies tutorial:

```text
$ go mod init example/data-access
go: creating new go.mod: module example/data-access
```

Команда создаёт `go.mod`, где будут отслеживаться added dependencies. Подробнее см. [[../modules/managing-dependencies|Управление dependencies]].

> [!note]
> В реальной разработке module path должен быть специфичен для вашего project и обычно соответствовать repository location. Подробнее см. [[../modules/managing-dependencies|Управление dependencies]].

Далее создайте database.

## Подготовьте database {#set_up_database}

На этом шаге создаётся database, table и initial data через CLI самой СУБД.

В примере используется MySQL CLI, но у большинства DBMS есть CLI с аналогичными возможностями.

1. Откройте новый terminal.
2. Войдите в MySQL:

```text
$ mysql -u root -p
Enter password:

mysql>
```

3. Создайте database:

```sql
create database recordings;
```

4. Переключитесь на неё:

```text
mysql> use recordings;
Database changed
```

5. В directory `data-access` создайте `create-tables.sql`.
6. Добавьте SQL:

```sql
drop table if exists album;
create table album (
  id         int auto_increment not null,
  title      varchar(128) not null,
  artist     varchar(255) not null,
  price      decimal(5,2) not null,
  primary key (`id`)
);

insert into album
  (title, artist, price)
values
  ('Blue Train', 'John Coltrane', 56.99),
  ('Giant Steps', 'John Coltrane', 63.99),
  ('Jeru', 'Gerry Mulligan', 17.99),
  ('Sarah Vaughan', 'Sarah Vaughan', 34.98);
```

Этот SQL:

- удаляет table `album`, если она уже существует, чтобы script можно было безопасно запускать повторно;
- создаёт table `album` с fields `id`, `title`, `artist`, `price`; `id` генерируется DBMS автоматически;
- вставляет четыре rows.

7. Выполните script из MySQL CLI:

```text
mysql> source /path/to/create-tables.sql
```

8. Проверьте data:

```text
mysql> select * from album;
+----+---------------+----------------+-------+
| id | title         | artist         | price |
+----+---------------+----------------+-------+
|  1 | Blue Train    | John Coltrane  | 56.99 |
|  2 | Giant Steps   | John Coltrane  | 63.99 |
|  3 | Jeru          | Gerry Mulligan | 17.99 |
|  4 | Sarah Vaughan | Sarah Vaughan  | 34.98 |
+----+---------------+----------------+-------+
4 rows in set (0.00 sec)
```

Теперь можно подключаться из Go.

## Найдите и импортируйте database driver {#import_driver}

Database driver переводит requests `database/sql` в protocol конкретной DBMS.

1. Откройте wiki [SQLDrivers](https://go.dev/wiki/SQLDrivers) и выберите driver.
2. Для MySQL tutorial использует [Go-MySQL-Driver](https://github.com/go-sql-driver/mysql/).
3. Его package path: `github.com/go-sql-driver/mysql`.
4. Создайте `main.go` в `data-access` и добавьте:

```go
package main

import "github.com/go-sql-driver/mysql"
```

Здесь:

- code находится в package `main`, чтобы program можно было запускать самостоятельно;
- импортируется MySQL driver.

## Получите database handle и подключитесь {#get_handle}

Теперь создайте database handle. Pointer `*sql.DB` представляет доступ к конкретной database и управляемый connection pool.

#### Напишите код

Под imports добавьте:

```go
var db *sql.DB

func main() {
	// Capture connection properties.
	cfg := mysql.NewConfig()
	cfg.User = os.Getenv("DBUSER")
	cfg.Passwd = os.Getenv("DBPASS")
	cfg.Net = "tcp"
	cfg.Addr = "127.0.0.1:3306"
	cfg.DBName = "recordings"

	// Get a database handle.
	var err error
	db, err = sql.Open("mysql", cfg.FormatDSN())
	if err != nil {
		log.Fatal(err)
	}

	pingErr := db.Ping()
	if pingErr != nil {
		log.Fatal(pingErr)
	}
	fmt.Println("Connected!")
}
```

В этом коде:

- global variable `db` имеет type [`*sql.DB`](https://pkg.go.dev/database/sql#DB) и является database handle;
- global variable используется только для упрощения tutorial. В production лучше передавать handle в functions или хранить его в struct;
- MySQL [`Config`](https://pkg.go.dev/github.com/go-sql-driver/mysql#Config) и [`FormatDSN`](https://pkg.go.dev/github.com/go-sql-driver/mysql#Config.FormatDSN) собирают connection properties и формируют DSN. Это читаемее, чем manually assembled connection string;
- [`sql.Open`](https://pkg.go.dev/database/sql#Open) инициализирует `db` через DSN;
- error из `sql.Open` проверяется: он может возникнуть, например, если connection settings malformed;
- tutorial использует `log.Fatal` для простоты. Production code обычно должен обрабатывать errors более контролируемо;
- [`DB.Ping`](https://pkg.go.dev/database/sql#DB.Ping) проверяет, что connection реально может быть установлена. `sql.Open` в зависимости от driver может не подключаться немедленно;
- error из `Ping` также проверяется;
- при успехе выводится `Connected!`.

Добавьте imports:

```go
package main

import (
	"database/sql"
	"fmt"
	"log"
	"os"

	"github.com/go-sql-driver/mysql"
)
```

Сохраните `main.go`.

#### Запустите код

1. Добавьте driver dependency:

```text
$ go get .
go: added filippo.io/edwards25519 v1.1.0
go: added github.com/go-sql-driver/mysql v1.8.1
```

Go скачивает dependency, потому что package добавлен в `import`. Подробнее см. [[../modules/managing-dependencies|Управление dependencies]].

2. Задайте credentials через environment variables.

Linux/macOS:

```bash
export DBUSER=username
export DBPASS=password
```

Windows:

```text
C:\Users\you\data-access> set DBUSER=username
C:\Users\you\data-access> set DBPASS=password
```

3. Запустите:

```text
$ go run .
Connected!
```

Connection работает. Далее запросите несколько rows.

## Запросите несколько rows {#multiple_rows}

Для SQL statements, способных вернуть несколько rows, используйте `DB.Query`, затем перебирайте returned `Rows`.

#### Напишите код

1. Перед `func main` добавьте struct:

```go
type Album struct {
	ID     int64
	Title  string
	Artist string
	Price  float32
}
```

2. После `main` добавьте:

```go
// albumsByArtist queries for albums that have the specified artist name.
func albumsByArtist(name string) ([]Album, error) {
	// An albums slice to hold data from returned rows.
	var albums []Album

	rows, err := db.Query("select * from album where artist = ?", name)
	if err != nil {
		return nil, fmt.Errorf("albumsByArtist %q: %v", name, err)
	}
	defer rows.Close()
	// Loop through rows, using Scan to assign column data to struct fields.
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
```

Здесь:

- `albums` — slice `Album`, куда складываются rows;
- [`DB.Query`](https://pkg.go.dev/database/sql#DB.Query) выполняет `select` с artist parameter;
- SQL text и parameter values передаются отдельно. Это позволяет `database/sql` отправлять values отдельно от SQL и предотвращает SQL injection, в отличие от concatenation через `fmt.Sprintf`;
- `rows.Close()` вызывается через `defer`, чтобы гарантированно освободить resources;
- [`Rows.Scan`](https://pkg.go.dev/database/sql#Rows.Scan) получает pointers на Go values и записывает в них column values;
- каждый `Album` append'ится в result slice;
- после loop обязательно проверяется `rows.Err()`. Error query/iteration может проявиться именно здесь, и без этой проверки partial results можно ошибочно принять за complete.

3. Добавьте в конец `main`:

```go
albums, err := albumsByArtist("John Coltrane")
if err != nil {
	log.Fatal(err)
}
fmt.Printf("Albums found: %v\n", albums)
```

#### Запустите

```text
$ go run .
Connected!
Albums found: [{1 Blue Train John Coltrane 56.99} {2 Giant Steps John Coltrane 63.99}]
```

## Запросите одну row {#single_row}

Если SQL statement гарантированно возвращает не более одной row, `QueryRow` проще, чем `Query` + loop.

#### Напишите код

Добавьте:

```go
// albumByID queries for the album with the specified ID.
func albumByID(id int64) (Album, error) {
	// An album to hold data from the returned row.
	var alb Album

	row := db.QueryRow("select * from album where id = ?", id)
	if err := row.Scan(&alb.ID, &alb.Title, &alb.Artist, &alb.Price); err != nil {
		if err == sql.ErrNoRows {
			return alb, fmt.Errorf("albumsById %d: no such album", id)
		}
		return alb, fmt.Errorf("albumsById %d: %v", id, err)
	}
	return alb, nil
}
```

Здесь:

- [`DB.QueryRow`](https://pkg.go.dev/database/sql#DB.QueryRow) выполняет `select` по ID;
- `QueryRow` специально не возвращает error. Query error откладывается и возвращается позднее из `Row.Scan`, что упрощает calling code;
- [`Row.Scan`](https://pkg.go.dev/database/sql#Row.Scan) копирует column values в struct fields;
- `sql.ErrNoRows` означает отсутствие matching row. Tutorial заменяет его более понятным domain message `no such album`.

Добавьте в `main`:

```go
// Hard-code ID 2 here to test the query.
alb, err := albumByID(2)
if err != nil {
	log.Fatal(err)
}
fmt.Printf("Album found: %v\n", alb)
```

Запуск:

```text
$ go run .
Connected!
Albums found: [{1 Blue Train John Coltrane 56.99} {2 Giant Steps John Coltrane 63.99}]
Album found: {2 Giant Steps John Coltrane 63.99}
```

## Добавьте data {#add_data}

Для SQL statements, которые не возвращают rows, используется `Exec`.

#### Напишите код

Добавьте `addAlbum`:

```go
// addAlbum adds the specified album to the database,
// returning the album ID of the new entry
func addAlbum(alb Album) (int64, error) {
	result, err := db.Exec("insert into album (title, artist, price) values (?, ?, ?)", alb.Title, alb.Artist, alb.Price)
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

Здесь:

- [`DB.Exec`](https://pkg.go.dev/database/sql#DB.Exec) выполняет `insert`;
- как и `Query`, `Exec` принимает SQL отдельно от parameter values;
- error insertion проверяется;
- [`Result.LastInsertId`](https://pkg.go.dev/database/sql#Result.LastInsertId) получает ID inserted row;
- error получения ID также проверяется.

В `main` добавьте:

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

Запуск:

```text
$ go run .
Connected!
Albums found: [{1 Blue Train John Coltrane 56.99} {2 Giant Steps John Coltrane 63.99}]
Album found: {2 Giant Steps John Coltrane 63.99}
ID of added album: 5
```

## Заключение {#conclusion}

Вы выполнили основные операции с реляционной database из Go.

Рекомендуемые следующие материалы:

- [[../database/index|Полный database/sql guide]];
- [[../effective-go|Effective Go]];
- [[../code|Как писать Go-код]];
- [Tour of Go](https://go.dev/tour/).

## Полный код {#completed_code}

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
	// Capture connection properties.
	cfg := mysql.NewConfig()
	cfg.User = os.Getenv("DBUSER")
	cfg.Passwd = os.Getenv("DBPASS")
	cfg.Net = "tcp"
	cfg.Addr = "127.0.0.1:3306"
	cfg.DBName = "recordings"

	// Get a database handle.
	var err error
	db, err = sql.Open("mysql", cfg.FormatDSN())
	if err != nil {
		log.Fatal(err)
	}

	pingErr := db.Ping()
	if pingErr != nil {
		log.Fatal(pingErr)
	}
	fmt.Println("Connected!")

	albums, err := albumsByArtist("John Coltrane")
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Albums found: %v\n", albums)

	// Hard-code ID 2 here to test the query.
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

// albumsByArtist queries for albums that have the specified artist name.
func albumsByArtist(name string) ([]Album, error) {
	// An albums slice to hold data from returned rows.
	var albums []Album

	rows, err := db.Query("select * from album where artist = ?", name)
	if err != nil {
		return nil, fmt.Errorf("albumsByArtist %q: %v", name, err)
	}
	defer rows.Close()
	// Loop through rows, using Scan to assign column data to struct fields.
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

// albumByID queries for the album with the specified ID.
func albumByID(id int64) (Album, error) {
	// An album to hold data from the returned row.
	var alb Album

	row := db.QueryRow("select * from album where id = ?", id)
	if err := row.Scan(&alb.ID, &alb.Title, &alb.Artist, &alb.Price); err != nil {
		if err == sql.ErrNoRows {
			return alb, fmt.Errorf("albumsById %d: no such album", id)
		}
		return alb, fmt.Errorf("albumsById %d: %v", id, err)
	}
	return alb, nil
}

// addAlbum adds the specified album to the database,
// returning the album ID of the new entry
func addAlbum(alb Album) (int64, error) {
	result, err := db.Exec("insert into album (title, artist, price) values (?, ?, ?)", alb.Title, alb.Artist, alb.Price)
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
