# Stage 1 — Foundations: toolchain, module, package

## Цель

Установить/проверить Go 1.27.1, создать module, понять `package main`, написать/запустить/собрать программу и пройти существующую tutorial-chain без создания параллельного учебника.

## Перед началом

Нужны terminal, editor и базовый опыт программирования. Знание Go не требуется.

## Прочитать

1. [[../../docs/install|Скачивание и установка Go]].
2. [[../../docs/getting-started|Getting Started]].
3. [[../../docs/tutorial/create-module|Create a module]].
4. [[../../docs/tutorial/call-module-code|Call module code]].
5. [[../../docs/tutorial/handle-errors|Handle errors]] — пока на уровне знакомства.
6. [[../../docs/tutorial/random-greeting|Random greeting / slice]].
7. [[../../docs/tutorial/greetings-multiple-people|Multiple people / map]].
8. [[../../docs/tutorial/add-a-test|Add a test]].
9. [[../../docs/tutorial/compile-install|Compile and install]].
10. [[../../docs/tutorial/module-conclusion|Module tutorial conclusion]].

## Что необходимо понять

- [ ] `go version`, `go env`, `go help`.
- [ ] source file → package → module.
- [ ] `package main` + `func main()` создают command.
- [ ] exported identifier начинается с uppercase.
- [ ] `go mod init`, `go mod tidy`, `go run`, `go test`, `go build`, `go install`.
- [ ] зачем нужны `go.mod` и `go.sum`.
- [ ] local dependency через `replace` — только как знакомство.
- [ ] как вся официальная цепочка tutorial связывает два modules и подводит к dependency/module documentation.

## Что НЕ нужно пока изучать

- Minimal Version Selection во всех деталях;
- workspaces/versioning/publishing;
- Specification целиком;
- runtime/GC/assembler;
- production project layout.

## Практика

- [[../practice/01-foundations|Foundations practice]].

## Эксперименты

- удалить `package main` или `func main()` и прочитать diagnostic;
- поменять exported `Hello` на `hello` и попытаться вызвать из другого package;
- удалить `replace` до публикации module и посмотреть, как Go пытается resolve dependency;
- намеренно сломать test из tutorial.

## Проверка себя

1. Чем package отличается от module?
2. Почему `go run .` знает, что запускать?
3. Когда возникает `go.sum`?
4. Чем `go build` отличается от `go install`?
5. Почему lowercase identifier недоступен из другого package?
6. К каким module/dependency guides направляет conclusion официального tutorial и почему их пока не нужно читать раньше базового языка?

## Практическая проверка

С нуля создать два local modules: library `pricing` с функцией validation и command `price-demo`, который её вызывает. Добавить test, собрать binary, не копируя tutorial.

## Критерий завершения

Я могу перейти дальше, если способен:

- создать module без подсказки;
- объяснить package/module/import path;
- запустить test/build;
- прочитать basic compiler error и исправить его;
- повторить основную tutorial-chain своими именами/types;
- объяснить, где заканчивается introductory module tutorial и начинается системное изучение modules/dependencies.

## Следующий этап

[[02-core-language|Stage 2 — Core language]].
