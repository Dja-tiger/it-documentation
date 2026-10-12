---
title: "Организация Go module"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/modules/layout.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Организация Go module

Частый вопрос developers, недавно пришедших в Go: «Как организовать Go project с точки зрения files и folders?» Цель этого документа — дать guidelines, помогающие на него ответить.

Чтобы извлечь максимум пользы, сначала ознакомьтесь с основами Go modules через [[../tutorial/create-module|tutorial]] и [[managing-source|Управление source module]].

Go projects могут включать packages, command-line programs или сочетание того и другого. Guide организован по type проекта.

### Базовый package

Простой Go package может хранить весь code в root directory проекта. Project состоит из одного module, который состоит из одного package. Package name совпадает с последним component module path.

Для самого простого package с одним Go file:

```text
project-root-directory/
  go.mod
  modname.go
  modname_test.go
```

> [!note]
> Во всём документе file/package names выбраны произвольно.

Если directory опубликован в GitHub repository `github.com/someuser/modname`, `module` line в `go.mod` должна быть:

```text
module github.com/someuser/modname
```

`modname.go` объявляет:

```go
package modname

// ... package code here
```

Users импортируют package:

```go
import "github.com/someuser/modname"
```

Package можно разделить на несколько files в одном directory:

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

Все files в directory объявляют `package modname`.

### Базовая command

Структура executable program / command-line tool зависит от complexity и объёма code.

Самая простая program может состоять из одного Go file с `func main`. Более крупная program может быть разделена на несколько files, все с `package main`:

```text
project-root-directory/
  go.mod
  auth.go
  auth_test.go
  client.go
  main.go
```

`main.go` содержит `func main`, но имя file — только convention. Он может называться `modname.go` или как угодно ещё.

Если repository находится по `github.com/someuser/modname`, `go.mod` содержит:

```text
module github.com/someuser/modname
```

User может установить command:

```bash
go install github.com/someuser/modname@latest
```

### Package или command с supporting packages

Крупному package или command может быть удобно вынести часть functionality в supporting packages.

На первом этапе рекомендуется помещать такие packages в directory `internal`. Go [запрещает](https://pkg.go.dev/cmd/go#hdr-Internal_Directories) другим modules импортировать packages, которые вы не обязательно хотите публично expose и поддерживать.

Поскольку external projects не могут импортировать code из `internal`, его API можно refactor'ить и перемещать без breaking changes для external users.

Пример package project:

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

`modname.go` объявляет `package modname`, `auth.go` — `package auth` и т. д.

Root package может импортировать internal package:

```go
import "github.com/someuser/modname/internal/auth"
```

Layout command с supporting packages в `internal` почти тот же, кроме того, что root Go files объявляют `package main`.

### Несколько packages

Module может содержать несколько importable packages. Каждый package находится в собственном directory, а hierarchy может быть вложенной:

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

При:

```text
module github.com/someuser/modname
```

root package `modname` импортируется:

```go
import "github.com/someuser/modname"
```

Subpackages:

```go
import "github.com/someuser/modname/auth"
import "github.com/someuser/modname/auth/token"
import "github.com/someuser/modname/hash"
```

Package `internal/trace` нельзя импортировать за пределами module. Рекомендуется сохранять packages в `internal`, пока не требуется сознательно поддерживать их как public API.

### Несколько commands

Несколько programs в одном repository обычно имеют отдельные directories:

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

В каждом command directory Go files объявляют `package main`. Top-level `internal` может содержать shared packages всех commands repository.

Installation:

```bash
go install github.com/someuser/modname/prog1@latest
go install github.com/someuser/modname/prog2@latest
```

Распространённая convention — хранить все commands в directory `cmd`. Это не строго необходимо, если repository состоит только из commands, но особенно полезно в mixed repository с importable packages и commands.

### Packages и commands в одном repository

Пример mixed repository:

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

Если module называется `github.com/someuser/modname`, users могут импортировать packages:

```go
import "github.com/someuser/modname"
import "github.com/someuser/modname/auth"
```

и устанавливать programs:

```bash
go install github.com/someuser/modname/cmd/prog1@latest
go install github.com/someuser/modname/cmd/prog2@latest
```

### Server project

Go часто используется для servers. Структуры таких projects сильно различаются из-за множества дополнительных аспектов: REST/gRPC protocols, deployments, frontend files, containers, scripts и другое. Здесь рассматривается только Go-part проекта.

Server projects обычно не предоставляют packages для external import: server чаще является self-contained binary или набором binaries. Поэтому Go packages, реализующие server logic, рекомендуется хранить в `internal`.

Так как repository server часто содержит множество directories с non-Go files, commands удобно собирать в `cmd`:

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
    ...
  ... the project's other directories with non-Go code
```

Если в server repository со временем появляются packages, полезные другим projects, их лучше выделить в отдельные modules.
