---
title: "Tutorial: создание Go module"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/create-module.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Создание Go module

Это первая часть многошагового tutorial по базовым возможностям Go. Будут созданы два modules:

1. `greetings` — library module, который экспортирует функции;
2. `hello` — application module, вызывающий library.

Полная цепочка:

1. Создать module.
2. [[call-module-code|Вызвать его из другого module]].
3. [[handle-errors|Вернуть и обработать error]].
4. [[random-greeting|Вернуть случайное приветствие и познакомиться со slice]].
5. [[greetings-multiple-people|Обработать несколько имён через slice/map]].
6. [[add-a-test|Добавить unit tests]].
7. [[compile-install|Собрать и установить application]].

## Создание reusable module

Go source объединяется в packages, а packages — в modules. `go.mod` описывает module path, Go version и dependencies.

Создайте каталог:

```bash
mkdir greetings
cd greetings
```

Инициализируйте module:

```text
$ go mod init example.com/greetings
go: creating new go.mod: module example.com/greetings
```

Для реального публикуемого module path должен указывать на repository location, доступный Go tools.

`go mod init` создаёт `go.mod`. По мере появления dependencies файл будет хранить выбранные module versions и помогать делать builds воспроизводимыми.

## Первый package

Создайте `greetings.go`:

```go
package greetings

import "fmt"

// Hello returns a greeting for the named person.
func Hello(name string) string {
    message := fmt.Sprintf("Hi, %v. Welcome!", name)
    return message
}
```

Что здесь важно:

- `package greetings` объединяет связанные declarations;
- `Hello` принимает `string` и возвращает `string`;
- identifier, начинающийся с заглавной буквы, exported и доступен другим packages;
- `:=` одновременно объявляет и инициализирует local variable, выводя type из right-hand side;
- `fmt.Sprintf` форматирует значение без вывода на stdout;
- function возвращает сформированный `message` caller'у.

Эквивалент более длинной записи variable:

```go
var message string
message = fmt.Sprintf("Hi, %v. Welcome!", name)
```

Следующий шаг — [[call-module-code|вызвать `Hello` из второго module]].
