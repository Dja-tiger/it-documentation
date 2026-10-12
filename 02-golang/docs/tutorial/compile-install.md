---
title: "Компиляция и установка Go application"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/compile-install.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Компиляция и установка application

`go run` компилирует и сразу запускает program, но не оставляет обычный executable для дальнейшего использования.

Для build/install применяются:

- `go build` — компилирует packages/dependencies, но не устанавливает результат в Go bin directory;
- `go install` — компилирует и устанавливает command.

## `go build`

В каталоге `hello`:

```bash
go build
```

После этого запускайте binary напрямую.

Linux/macOS:

```bash
./hello
```

Windows:

```text
hello.exe
```

## Куда устанавливает `go install`

Узнать target текущего package:

```bash
go list -f '{{.Target}}'
```

Например, result `/home/gopher/bin/hello` означает install directory `/home/gopher/bin`.

Добавьте directory в `PATH` либо настройте `GOBIN`:

```bash
go env -w GOBIN=/path/to/your/bin
```

Windows example:

```text
go env -w GOBIN=C:\path\to\your\bin
```

## `go install`

```bash
go install
```

После того как install directory присутствует в `PATH`, program можно запускать из любого working directory:

```bash
hello
```

На этом базовый module tutorial завершён: создан library module, отдельный caller module, local dependency через `replace`, error handling, slices/maps, tests, build и installation.
