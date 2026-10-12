---
title: "Tutorial: REST API с Go и Gin"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/web-service-gin.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# RESTful API с Go и Gin

Tutorial показывает создание простого REST API на [Gin](https://gin-gonic.com/en/docs/): routing, path parameters, JSON request binding и JSON responses.

Будут реализованы endpoints:

| Method | Path | Назначение |
|---|---|---|
| `GET` | `/albums` | Получить все albums. |
| `POST` | `/albums` | Добавить album из JSON body. |
| `GET` | `/albums/:id` | Получить album по ID. |

## Создание module

```bash
mkdir web-service-gin
cd web-service-gin
go mod init example/web-service-gin
```

## Модель данных

Для простоты tutorial хранит state в memory. В production API обычно использует database/storage layer.

```go
type album struct {
    ID     string  `json:"id"`
    Title  string  `json:"title"`
    Artist string  `json:"artist"`
    Price  float64 `json:"price"`
}

var albums = []album{
    {ID: "1", Title: "Blue Train", Artist: "John Coltrane", Price: 56.99},
    {ID: "2", Title: "Jeru", Artist: "Gerry Mulligan", Price: 17.99},
    {ID: "3", Title: "Sarah Vaughan and Clifford Brown", Artist: "Sarah Vaughan", Price: 39.99},
}
```

Struct tags управляют JSON field names. Без tags exported Go fields сериализовались бы с именами `ID`, `Title`, `Artist`, `Price`.

## `GET /albums`

Handler:

```go
func getAlbums(c *gin.Context) {
    c.IndentedJSON(http.StatusOK, albums)
}
```

`gin.Context` содержит request/response context Gin, routing parameters, helpers для binding/serialization и т. п. Это **не** тот же type, что standard `context.Context`.

`IndentedJSON` сериализует value и отправляет HTTP status `200`. Для compact output можно использовать `c.JSON`.

Router:

```go
func main() {
    router := gin.Default()
    router.GET("/albums", getAlbums)

    router.Run("localhost:8080")
}
```

Imports:

```go
import (
    "net/http"

    "github.com/gin-gonic/gin"
)
```

Добавьте dependency и запустите:

```bash
go get .
go run .
```

Проверка:

```bash
curl http://localhost:8080/albums
```

## `POST /albums`

```go
func postAlbums(c *gin.Context) {
    var newAlbum album

    if err := c.BindJSON(&newAlbum); err != nil {
        return
    }

    albums = append(albums, newAlbum)
    c.IndentedJSON(http.StatusCreated, newAlbum)
}
```

`BindJSON` декодирует request body в struct. При успехе новый object добавляется к in-memory slice, а response получает `201 Created`.

Route:

```go
router.POST("/albums", postAlbums)
```

Test request:

```bash
curl http://localhost:8080/albums \
    --include \
    --header "Content-Type: application/json" \
    --request "POST" \
    --data '{"id":"4","title":"The Modern Sound of Betty Carter","artist":"Betty Carter","price":49.99}'
```

Ожидаемый status:

```text
HTTP/1.1 201 Created
```

## `GET /albums/:id`

```go
func getAlbumByID(c *gin.Context) {
    id := c.Param("id")

    for _, a := range albums {
        if a.ID == id {
            c.IndentedJSON(http.StatusOK, a)
            return
        }
    }

    c.IndentedJSON(
        http.StatusNotFound,
        gin.H{"message": "album not found"},
    )
}
```

`c.Param("id")` получает path parameter, объявленный через `:id`.

Route:

```go
router.GET("/albums/:id", getAlbumByID)
```

Проверка:

```bash
curl http://localhost:8080/albums/2
```

Если object найден — `200 OK`; если нет — `404 Not Found` и JSON error body.

## Полный код

```go
package main

import (
    "net/http"

    "github.com/gin-gonic/gin"
)

type album struct {
    ID     string  `json:"id"`
    Title  string  `json:"title"`
    Artist string  `json:"artist"`
    Price  float64 `json:"price"`
}

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

    if err := router.Run("localhost:8080"); err != nil {
        panic(err)
    }
}

func getAlbums(c *gin.Context) {
    c.IndentedJSON(http.StatusOK, albums)
}

func postAlbums(c *gin.Context) {
    var newAlbum album

    if err := c.BindJSON(&newAlbum); err != nil {
        return
    }

    albums = append(albums, newAlbum)
    c.IndentedJSON(http.StatusCreated, newAlbum)
}

func getAlbumByID(c *gin.Context) {
    id := c.Param("id")

    for _, a := range albums {
        if a.ID == id {
            c.IndentedJSON(http.StatusOK, a)
            return
        }
    }

    c.IndentedJSON(
        http.StatusNotFound,
        gin.H{"message": "album not found"},
    )
}
```

> [!note]
> Tutorial intentionally демонстрационный: in-memory slice не синхронизирован для concurrent writes, нет validation/ID generation/persistence/authentication. Для production эти concerns должны быть вынесены в соответствующие layers.
