---
title: "Вызов кода из другого Go module"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/call-module-code.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Вызов кода из другого module

После создания `example.com/greetings` создадим executable module `example.com/hello`, который импортирует library.

## Создайте второй module

Структура:

```text
<home>/
├── greetings/
└── hello/
```

```bash
cd ..
mkdir hello
cd hello
go mod init example.com/hello
```

Создайте `hello.go`:

```go
package main

import (
    "fmt"

    "example.com/greetings"
)

func main() {
    message := greetings.Hello("Gladys")
    fmt.Println(message)
}
```

Executable application объявляет `package main` и содержит `func main()`.

## Local unpublished dependency

`example.com/greetings` ещё не опубликован, поэтому Go tools не могут скачать его по module path. Перенаправьте dependency на соседний directory:

```bash
go mod edit -replace example.com/greetings=../greetings
```

В `go.mod` появится:

```text
module example.com/hello

go 1.16

replace example.com/greetings => ../greetings
```

Теперь синхронизируйте imports и module graph:

```text
$ go mod tidy
go: found example.com/greetings in example.com/greetings v0.0.0-00010101000000-000000000000
```

Получится requirement плюс local replacement:

```text
require example.com/greetings v0.0.0-00010101000000-000000000000
replace example.com/greetings => ../greetings
```

Для published module обычно `replace` отсутствует, а `require` содержит real tagged version:

```text
require example.com/greetings v1.1.0
```

Запустите:

```text
$ go run .
Hi, Gladys. Welcome!
```

Теперь два независимых modules работают совместно. Следующий шаг — [[handle-errors|error handling]].
