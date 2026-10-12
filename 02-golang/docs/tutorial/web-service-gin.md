---
title: "Tutorial: разработка RESTful API с Go и Gin"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/web-service-gin.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Разработка RESTful API с Go и Gin

Этот tutorial знакомит с основами написания RESTful web service API на Go с использованием [Gin Web Framework](https://gin-gonic.com/en/docs/) (Gin).

Tutorial будет понятнее при базовом знакомстве с Go и его tooling. Если это первое знакомство с Go, сначала см. [[../getting-started|Tutorial: начало работы с Go]].

Gin упрощает многие задачи, связанные с web applications и web services. Здесь он используется для routing requests, получения request details и marshaling JSON responses.

В tutorial будет построен RESTful API server с двумя endpoint paths для repository данных о vintage jazz records.

Последовательность:

1. спроектировать API endpoints;
2. создать folder для code;
3. создать data;
4. написать handler, возвращающий все items;
5. написать handler, добавляющий item;
6. написать handler, возвращающий конкретный item.

> [!note]
> Другие tutorials см. на [go.dev/doc/tutorial](https://go.dev/doc/tutorial/).

Официальный tutorial также можно проходить интерактивно в Google Cloud Shell через [Open in Cloud Shell](https://ide.cloud.google.com/?cloudshell_workspace=~&walkthrough_tutorial_url=https://raw.githubusercontent.com/golang/tour/master/tutorial/web-service-gin.md).

## Предварительные требования

- **Go.** Рекомендуется актуальная версия Go. Установка: [[../install|Установка Go]].
- **Редактор.** Подойдёт любой text editor.
- **Terminal.** Подойдёт terminal Linux/macOS или PowerShell/`cmd` в Windows.
- **curl.** В Linux/macOS обычно уже установлен. В Windows он включён начиная с Windows 10 Insider build 17063; для более старых versions может потребоваться установка. Подробнее: [Tar and Curl Come to Windows](https://docs.microsoft.com/en-us/virtualization/community/team-blog/2017/20171219-tar-and-curl-come-to-windows).

## Спроектируйте API endpoints {#design_endpoints}

API предоставляет доступ к store с vintage vinyl records. Client должен уметь получать и добавлять albums.

При разработке API обычно сначала проектируют endpoints. Чем понятнее endpoints, тем проще пользователям API.

Создадим:

### `/albums`

- `GET` — получить list всех albums в JSON;
- `POST` — добавить новый album из JSON request body.

### `/albums/:id`

- `GET` — получить album по ID и вернуть его как JSON.

Далее создайте project directory.

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

2. Создайте directory `web-service-gin`:

```text
$ mkdir web-service-gin
$ cd web-service-gin
```

3. Создайте module для управления dependencies:

```text
$ go mod init example/web-service-gin
go: creating new go.mod: module example/web-service-gin
```

Команда создаёт `go.mod`, где будут отслеживаться добавляемые dependencies. Подробнее о module path см. [[../modules/managing-dependencies|Управление dependencies]].

## Создайте data {#create_data}

Для простоты tutorial хранит данные в памяти. Типичный production API, скорее всего, работал бы с database.

Поскольку data хранится только в памяти, после остановки server все добавленные albums потеряются и при новом запуске исходный набор будет создан заново.

#### Напишите код

1. Создайте `main.go` в project directory.
2. Добавьте package declaration:

```go
package main
```

Standalone program находится в package `main`.

3. Добавьте struct `album`:

```go
// album represents data about a record album.
type album struct {
	ID     string  `json:"id"`
	Title  string  `json:"title"`
	Artist string  `json:"artist"`
	Price  float64 `json:"price"`
}
```

Struct tags вроде `json:"artist"` задают имя field при serialization в JSON. Без tags JSON использовал бы capitalized Go field names, что менее типично для JSON APIs.

4. Добавьте initial data:

```go
// albums slice to seed record album data.
var albums = []album{
	{ID: "1", Title: "Blue Train", Artist: "John Coltrane", Price: 56.99},
	{ID: "2", Title: "Jeru", Artist: "Gerry Mulligan", Price: 17.99},
	{ID: "3", Title: "Sarah Vaughan and Clifford Brown", Artist: "Sarah Vaughan", Price: 39.99},
}
```

Теперь реализуйте первый endpoint.

## Напишите handler, возвращающий все items {#all_items}

Для request `GET /albums` API должно вернуть все albums как JSON.

Нужно добавить:

- logic подготовки response;
- routing request path к этой logic.

В tutorial сначала пишется dependency code, а затем код, который его использует, хотя runtime execution идёт в обратном порядке.

#### Напишите код

1. Добавьте handler:

```go
// getAlbums responds with the list of all albums as JSON.
func getAlbums(c *gin.Context) {
	c.IndentedJSON(http.StatusOK, albums)
}
```

Здесь:

- `getAlbums` принимает [`*gin.Context`](https://pkg.go.dev/github.com/gin-gonic/gin#Context). Function name может быть любым: Gin и Go не требуют конкретной naming convention;
- `gin.Context` — центральный type Gin: он содержит request details, помогает с validation, JSON serialization и другими web tasks. Несмотря на похожее имя, это не стандартный package [`context`](https://pkg.go.dev/context/);
- [`Context.IndentedJSON`](https://pkg.go.dev/github.com/gin-gonic/gin#Context.IndentedJSON) serializes struct/slice в JSON и записывает response;
- первый argument — HTTP status code. [`http.StatusOK`](https://pkg.go.dev/net/http#StatusOK) означает `200 OK`.

Вместо `IndentedJSON` можно использовать [`Context.JSON`](https://pkg.go.dev/github.com/gin-gonic/gin#Context.JSON), чтобы отправлять compact JSON. Indented output удобнее при debugging, а difference в размере для tutorial обычно несущественна.

2. Добавьте `main`, связывающий route с handler:

```go
func main() {
	router := gin.Default()
	router.GET("/albums", getAlbums)

	router.Run("localhost:8080")
}
```

Здесь:

- [`gin.Default`](https://pkg.go.dev/github.com/gin-gonic/gin#Default) создаёт router;
- [`router.GET`](https://pkg.go.dev/github.com/gin-gonic/gin#RouterGroup.GET) связывает HTTP method `GET` и path `/albums` с handler;
- передаётся **function value** `getAlbums`, а не result call `getAlbums()`;
- [`Run`](https://pkg.go.dev/github.com/gin-gonic/gin#Engine.Run) подключает router к `http.Server` и запускает server.

3. Добавьте imports:

```go
package main

import (
	"net/http"

	"github.com/gin-gonic/gin"
)
```

4. Сохраните `main.go`.

#### Запустите код

1. Добавьте Gin module как dependency:

```text
$ go get .
go get: added github.com/gin-gonic/gin v1.7.2
```

Dot означает dependencies для code текущего directory. Go разрешит и скачает dependency из import declaration.

2. Запустите server:

```bash
go run .
```

3. В другом terminal выполните:

```bash
curl http://localhost:8080/albums
```

Ожидаемый response:

```json
[
        {
                "id": "1",
                "title": "Blue Train",
                "artist": "John Coltrane",
                "price": 56.99
        },
        {
                "id": "2",
                "title": "Jeru",
                "artist": "Gerry Mulligan",
                "price": 17.99
        },
        {
                "id": "3",
                "title": "Sarah Vaughan and Clifford Brown",
                "artist": "Sarah Vaughan",
                "price": 39.99
        }
]
```

API уже работает. Далее добавьте `POST` endpoint.

## Напишите handler для добавления нового item {#add_item}

При `POST /albums` API должно добавить album из JSON request body к текущему набору albums.

Нужно добавить:

- logic добавления album;
- route `POST /albums` к этой logic.

#### Напишите код

1. Добавьте handler:

```go
// postAlbums adds an album from JSON received in the request body.
func postAlbums(c *gin.Context) {
	var newAlbum album

	// Call BindJSON to bind the received JSON to
	// newAlbum.
	if err := c.BindJSON(&newAlbum); err != nil {
		return
	}

	// Add the new album to the slice.
	albums = append(albums, newAlbum)
	c.IndentedJSON(http.StatusCreated, newAlbum)
}
```

Здесь:

- [`Context.BindJSON`](https://pkg.go.dev/github.com/gin-gonic/gin#Context.BindJSON) binds request body в `newAlbum`;
- decoded `album` append'ится в slice `albums`;
- response получает HTTP status `201 Created` и JSON добавленного album.

2. Добавьте POST route:

```go
func main() {
	router := gin.Default()
	router.GET("/albums", getAlbums)
	router.POST("/albums", postAlbums)

	router.Run("localhost:8080")
}
```

Gin связывает handler с combination HTTP method + path, поэтому один path может иметь разные handlers для разных methods.

#### Запустите код

1. Остановите предыдущий server, если он ещё работает.
2. Снова выполните:

```bash
go run .
```

3. В другом terminal отправьте POST:

```bash
curl http://localhost:8080/albums \
    --include \
    --header "Content-Type: application/json" \
    --request "POST" \
    --data '{"id": "4","title": "The Modern Sound of Betty Carter","artist": "Betty Carter","price": 49.99}'
```

Ожидаемый response:

```text
HTTP/1.1 201 Created
Content-Type: application/json; charset=utf-8
Date: Wed, 02 Jun 2021 00:34:12 GMT
Content-Length: 116

{
    "id": "4",
    "title": "The Modern Sound of Betty Carter",
    "artist": "Betty Carter",
    "price": 49.99
}
```

4. Получите полный list и убедитесь, что новый album добавлен:

```bash
curl http://localhost:8080/albums \
    --header "Content-Type: application/json" \
    --request "GET"
```

Response должен содержать уже четыре records, включая:

```json
{
        "id": "4",
        "title": "The Modern Sound of Betty Carter",
        "artist": "Betty Carter",
        "price": 49.99
}
```

Далее реализуйте получение конкретного album.

## Напишите handler для конкретного item {#specific_item}

При `GET /albums/[id]` API должно вернуть album с соответствующим path parameter `id`.

Для этого:

- добавьте lookup logic;
- свяжите parameterized path с handler.

#### Напишите код

1. Добавьте `getAlbumByID`:

```go
// getAlbumByID locates the album whose ID value matches the id
// parameter sent by the client, then returns that album as a response.
func getAlbumByID(c *gin.Context) {
	id := c.Param("id")

	// Loop over the list of albums, looking for
	// an album whose ID value matches the parameter.
	for _, a := range albums {
		if a.ID == id {
			c.IndentedJSON(http.StatusOK, a)
			return
		}
	}
	c.IndentedJSON(http.StatusNotFound, gin.H{"message": "album not found"})
}
```

Здесь:

- [`Context.Param`](https://pkg.go.dev/github.com/gin-gonic/gin#Context.Param) получает path parameter `id` из URL;
- code перебирает slice и ищет album с `a.ID == id`;
- найденный album serializes в JSON и возвращается с `200 OK`;
- production service обычно сделал бы database query вместо linear scan in-memory slice;
- если album не найден, возвращается `404 Not Found` через [`http.StatusNotFound`](https://pkg.go.dev/net/http#StatusNotFound).

2. Добавьте route `/albums/:id`:

```go
func main() {
	router := gin.Default()
	router.GET("/albums", getAlbums)
	router.GET("/albums/:id", getAlbumByID)
	router.POST("/albums", postAlbums)

	router.Run("localhost:8080")
}
```

Colon перед `id` обозначает path parameter в Gin.

#### Запустите код

1. Перезапустите server:

```bash
go run .
```

2. В другом terminal:

```bash
curl http://localhost:8080/albums/2
```

Ожидаемый JSON:

```json
{
        "id": "2",
        "title": "Jeru",
        "artist": "Gerry Mulligan",
        "price": 17.99
}
```

Если ID не существует, API вернёт JSON error message с status 404.

## Заключение {#conclusion}

Вы написали простой RESTful web service с Go и Gin.

Рекомендуемые следующие материалы:

- [[../effective-go|Effective Go]];
- [[../code|Как писать Go-код]];
- [Tour of Go](https://go.dev/tour/);
- [Gin package documentation](https://pkg.go.dev/github.com/gin-gonic/gin);
- [Gin documentation](https://gin-gonic.com/en/docs/).

## Полный код {#completed_code}

```go
package main

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

// album represents data about a record album.
type album struct {
	ID     string  `json:"id"`
	Title  string  `json:"title"`
	Artist string  `json:"artist"`
	Price  float64 `json:"price"`
}

// albums slice to seed record album data.
var albums = []album{
	{ID: "1", Title: "Blue Train", Artist: "John Coltrane", Price: 56.99},
	{ID: "2", Title: "Jeru", Artist: "Gerry Mulligan", Price: 17.99},
	{ID: "3", Title: "Sarah Vaughan and Clifford Brown", Artist: "Sarah Vaughan", Price: 39.99},
}

func main() {
	router := gin.Default()
	router.GET("/albums", getAlbums)
	router.GET("/albums/:id", getAlbumByID)
	router.POST("/albums", postAlbums)

	router.Run("localhost:8080")
}

// getAlbums responds with the list of all albums as JSON.
func getAlbums(c *gin.Context) {
	c.IndentedJSON(http.StatusOK, albums)
}

// postAlbums adds an album from JSON received in the request body.
func postAlbums(c *gin.Context) {
	var newAlbum album

	// Call BindJSON to bind the received JSON to
	// newAlbum.
	if err := c.BindJSON(&newAlbum); err != nil {
		return
	}

	// Add the new album to the slice.
	albums = append(albums, newAlbum)
	c.IndentedJSON(http.StatusCreated, newAlbum)
}

// getAlbumByID locates the album whose ID value matches the id
// parameter sent by the client, then returns that album as a response.
func getAlbumByID(c *gin.Context) {
	id := c.Param("id")

	// Loop through the list of albums, looking for
	// an album whose ID value matches the parameter.
	for _, a := range albums {
		if a.ID == id {
			c.IndentedJSON(http.StatusOK, a)
			return
		}
	}
	c.IndentedJSON(http.StatusNotFound, gin.H{"message": "album not found"})
}
```
