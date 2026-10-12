---
title: "Tutorial: создание Go module"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/create-module.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Создание Go module

Это первая часть tutorial, знакомящего с несколькими фундаментальными возможностями Go. Если вы только начинаете изучать Go, сначала пройдите [[../getting-started|Tutorial: начало работы с Go]], где вводятся команда `go`, Go modules и простой Go-код.

В этом tutorial вы создадите два modules:

1. library, предназначенную для импорта другими libraries или applications;
2. caller application, которая использует первую library.

Tutorial состоит из семи коротких этапов, каждый из которых показывает отдельную часть языка:

1. **Создать module** — написать небольшой module с functions, которые можно вызывать из другого module.
2. [[call-module-code|Вызвать код из другого module]] — импортировать и использовать созданный module.
3. [[handle-errors|Вернуть и обработать error]] — добавить простую error handling.
4. [[random-greeting|Вернуть случайное приветствие]] — работать с данными в slices, динамически изменяемых массивах Go.
5. [[greetings-multiple-people|Вернуть приветствия для нескольких людей]] — хранить key/value pairs в map.
6. [[add-a-test|Добавить test]] — использовать встроенные unit testing capabilities Go.
7. [[compile-install|Скомпилировать и установить application]] — собрать и локально установить код.

> [!note]
> Другие официальные tutorials перечислены на [go.dev/doc/tutorial](https://go.dev/doc/tutorial/).

## Предварительные требования

- **Некоторый programming experience.** Код здесь простой, но полезно понимать functions, loops и arrays.
- **Go.** Для tutorial рекомендуется использовать актуальную версию Go. Инструкции см. в [[../install|Установка Go]].
- **Редактор кода.** Подойдёт любой text editor. Популярные варианты с хорошей поддержкой Go — VS Code, GoLand и Vim.
- **Command terminal.** Go работает с обычными terminals в Linux/macOS и с PowerShell или `cmd` в Windows.

## Создайте module, который смогут использовать другие

Начните с создания Go module. Module объединяет один или несколько связанных packages, предоставляющих отдельный полезный набор functions. Например, можно создать module с packages для financial analysis, чтобы другие applications могли использовать этот код.

Подробнее о разработке modules см. [[../modules/developing|Разработка и публикация modules]].

Go source code объединяется в packages, а packages — в modules. Module описывает dependencies, необходимые коду, включая Go version и набор других требуемых modules.

По мере добавления или улучшения functionality module публикует новые versions. Developers, использующие его functions, могут импортировать updated packages и протестировать новую version до production deployment.

1. Откройте command prompt и перейдите в home directory.

   Linux/macOS:

   ```bash
   cd
   ```

   Windows:

   ```text
   cd %HOMEPATH%
   ```

2. Создайте directory `greetings` для source code module:

   ```bash
   mkdir greetings
   cd greetings
   ```

3. Инициализируйте module командой [`go mod init`](https://go.dev/ref/mod#go-mod-init), передав module path.

   В tutorial используется:

   ```text
   example.com/greetings
   ```

   Если module будет опубликован, module path **должен** указывать место, откуда Go tools смогут его скачать, то есть repository кода.

   Подробнее о module path см. [[../modules/managing-dependencies#Именование module|Управление dependencies]].

   Выполните:

   ```text
   $ go mod init example.com/greetings
   go: creating new go.mod: module example.com/greetings
   ```

   `go mod init` создаёт `go.mod`, используемый для отслеживания dependencies. На этом этапе file содержит только имя module и Go version, которую поддерживает код. По мере добавления dependencies в `go.mod` будут фиксироваться versions используемых modules. Это делает builds воспроизводимыми и даёт прямой контроль над выбранными dependency versions.

4. Создайте в text editor file `greetings.go`.

5. Вставьте следующий код и сохраните file:

   ```go
   package greetings

   import "fmt"

   // Hello returns a greeting for the named person.
   func Hello(name string) string {
       // Return a greeting that embeds the name in a message.
       message := fmt.Sprintf("Hi, %v. Welcome!", name)
       return message
   }
   ```

   Это первый код вашего module. Он возвращает greeting любому caller, который его запросит. На следующем шаге будет написан код, вызывающий эту function.

В этом коде:

- объявляется package `greetings`, объединяющий связанные functions;
- реализуется function `Hello`, возвращающая greeting;
- `Hello` принимает parameter `name` типа `string` и возвращает `string`;
- имя `Hello` начинается с заглавной буквы, поэтому function exported и может вызываться кодом из другого package. Подробнее см. [Exported names](https://go.dev/tour/basics/3) в Tour of Go;
- объявляется variable `message` для greeting;
- operator `:=` сокращает declaration + initialization в одной строке; Go выводит type из value справа;
- [`fmt.Sprintf`](https://pkg.go.dev/fmt/#Sprintf) создаёт formatted greeting: первый argument — format string, а value `name` подставляется вместо format verb `%v`;
- formatted greeting возвращается caller.

Длинный эквивалент declaration `message`:

```go
var message string
message = fmt.Sprintf("Hi, %v. Welcome!", name)
```

Следующий шаг — [[call-module-code|вызвать этот код из другого module]].
