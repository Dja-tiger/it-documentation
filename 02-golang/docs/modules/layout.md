---
title: "Организация Go-модуля"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/modules/layout.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Организация Go-модуля

Один из частых вопросов при знакомстве с Go — как организовать файлы и каталоги проекта. Go не требует единственного шаблона: layout зависит от того, является проект library package, executable command, набором нескольких packages/commands или server application.

## Базовый package

Простой Go package может целиком находиться в корне проекта. Проект состоит из одного module и одного package. Package name обычно совпадает с последним компонентом module path.

```text
project-root-directory/
  go.mod
  modname.go
  modname_test.go
```

Если repository расположен по адресу `github.com/someuser/modname`, `go.mod` содержит:

```text
module github.com/someuser/modname
```

`modname.go` объявляет:

```go
package modname
```

Пользователь импортирует package так:

```go
import "github.com/someuser/modname"
```

Один package можно разделять на несколько `.go` files одного каталога:

```text
project-root-directory/
  go.mod
  modname.go
  modname_test.go
  auth.go
  auth_test.go
  hash.go
  hash_test.go
```

Все эти файлы объявляют `package modname`.

## Базовый command

Самый простой executable может состоять из одного файла с `func main`. Более крупный command можно разделить на несколько файлов, каждый из которых объявляет `package main`:

```text
project-root-directory/
  go.mod
  auth.go
  auth_test.go
  client.go
  main.go
```

Наличие `func main` именно в `main.go` — соглашение, а не требование языка.

При module path `github.com/someuser/modname` пользователь устанавливает программу:

```bash
go install github.com/someuser/modname@latest
```

## Package или command со вспомогательными packages

Для более крупных проектов часть логики можно вынести во вспомогательные packages. На начальном этапе официальный guide рекомендует помещать такие packages в `internal/`.

Go запрещает packages из других modules импортировать код, находящийся за границей разрешённого `internal` scope. Поэтому internal API можно свободнее рефакторить без обязательства поддерживать его для внешних пользователей.

Пример library module:

```text
project-root-directory/
  internal/
    auth/
      auth.go
      auth_test.go
    hash/
      hash.go
      hash_test.go
  go.mod
  modname.go
  modname_test.go
```

Корневой package может импортировать internal package:

```go
import "github.com/someuser/modname/internal/auth"
```

Для command layout аналогичен, только root files объявляют `package main`.

## Несколько packages

Один module может содержать несколько importable packages, организованных иерархически:

```text
project-root-directory/
  go.mod
  modname.go
  modname_test.go
  auth/
    auth.go
    auth_test.go
    token/
      token.go
      token_test.go
  hash/
    hash.go
  internal/
    trace/
      trace.go
```

При module path:

```text
module github.com/someuser/modname
```

доступны import paths:

```go
import "github.com/someuser/modname"
import "github.com/someuser/modname/auth"
import "github.com/someuser/modname/auth/token"
import "github.com/someuser/modname/hash"
```

`internal/trace` нельзя импортировать извне допустимого internal scope. Рекомендуется оставлять непубличную функциональность в `internal` настолько долго, насколько это практично.

## Несколько commands

Несколько программ в одном repository обычно получают отдельные каталоги:

```text
project-root-directory/
  go.mod
  internal/
    ... shared internal packages
  prog1/
    main.go
  prog2/
    main.go
```

Каждый command directory содержит `package main`. Общий top-level `internal` может хранить shared code.

Установка:

```bash
go install github.com/someuser/modname/prog1@latest
go install github.com/someuser/modname/prog2@latest
```

Распространённое соглашение — складывать commands в каталог `cmd/`. Это особенно полезно, если repository одновременно содержит public packages и commands.

## Packages и commands в одном repository

Пример смешанного repository:

```text
project-root-directory/
  go.mod
  modname.go
  modname_test.go
  auth/
    auth.go
    auth_test.go
  internal/
    ... internal packages
  cmd/
    prog1/
      main.go
    prog2/
      main.go
```

Packages можно импортировать:

```go
import "github.com/someuser/modname"
import "github.com/someuser/modname/auth"
```

Commands — устанавливать:

```bash
go install github.com/someuser/modname/cmd/prog1@latest
go install github.com/someuser/modname/cmd/prog2@latest
```

## Server project

Go часто используется для servers. Единого server layout нет: реальные проекты включают REST/gRPC, deployment manifests, frontend assets, containers, scripts и другие компоненты.

Server обычно является self-contained binary или группой binaries и не обязан экспортировать reusable packages. Поэтому официальный guide рекомендует держать реализацию server logic в `internal`, а commands — в `cmd`:

```text
project-root-directory/
  go.mod
  internal/
    auth/
      ...
    metrics/
      ...
    model/
      ...
  cmd/
    api-server/
      main.go
    metrics-analyzer/
      main.go
  ... other non-Go project directories
```

Если со временем часть server code превращается в действительно reusable library для других проектов, её лучше вынести в отдельный module.
