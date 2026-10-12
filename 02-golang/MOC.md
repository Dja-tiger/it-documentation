---
title: "Go / Golang — карта документации"
technology: "Go"
version: "1.27.1"
translation_status: "in_progress"
---

# Go / Golang

> [!info]
> Baseline: **Go 1.27.1**. Core/spec/runtime зафиксированы по `golang/go@go1.27.1`, User Manual и tutorials — по `golang/website@575a6925e2d55ad160ed77f402bfaa4ec7458749`.

> [!warning]
> После технического ревью 2026-10-12 раздел переведён в статус `in_progress`: файловая целостность и навигация исправлены, но выборочная сверка с upstream показала, что часть страниц сейчас является сокращённым переводом, а не полным зеркалом исходного документа. Для нормативных утверждений до завершения full-fidelity review приоритет имеет указанный upstream.

## Старт

- [[docs/install|Установка Go]]
- [[docs/manage-install|Управление версиями Go]]
- [[docs/getting-started|Getting Started]]
- [[docs/code|Как писать Go-код]]
- [[docs/install-source|Сборка и установка Go из исходников]]
- [[docs/editors|Editor plugins и IDE]]

## Язык и стиль

- [[docs/spec|Спецификация языка Go]]
- [[docs/memory-model|Модель памяти Go]]
- [[docs/effective-go|Effective Go]]
- [[docs/faq|FAQ]]
- [[docs/comment|Go Doc Comments]]

> [!note]
> Локальный `docs/spec.md` пока не прошёл полный построчный full-fidelity review. Нормативным источником остаётся `golang/go@go1.27.1:doc/go_spec.html`.

## Модули и toolchain

- [Go Modules Reference — upstream](https://go.dev/ref/mod) — локальное зеркало пока отсутствует.
- [[docs/modules/developing|Разработка и публикация модулей]]
- [[docs/modules/managing-dependencies|Управление зависимостями]]
- [[docs/modules/gomod-ref|Справочник go.mod]]
- [[docs/modules/layout|Организация Go-модуля]]
- [[docs/modules/managing-source|Организация исходного кода]]
- [[docs/modules/publishing|Публикация module]]
- [[docs/modules/version-numbers|Нумерация версий]]
- [[docs/modules/major-version|Major versions]]
- [[docs/modules/release-workflow|Release workflow]]
- [[docs/toolchain|Go toolchains]]

## Runtime, diagnostics и performance

- [[docs/gc-guide|Руководство по GC]]
- [[docs/pgo|Profile-guided optimization]]
- [[docs/diagnostics|Диагностика]]
- [[docs/race-detector|Data Race Detector]]
- [[docs/godebug|GODEBUG]]
- [[docs/asm|Go assembler]]
- [[docs/build-cover|Coverage для приложений и integration tests]]

## Tutorials

- [[docs/getting-started|Начало работы]]

### Create a Go module — полная цепочка файлов

1. [[docs/tutorial/create-module|Создание модуля]]
2. [[docs/tutorial/call-module-code|Вызов кода другого модуля]]
3. [[docs/tutorial/handle-errors|Возврат и обработка error]]
4. [[docs/tutorial/random-greeting|Случайное приветствие и slice]]
5. [[docs/tutorial/greetings-multiple-people|Несколько имён и map]]
6. [[docs/tutorial/add-a-test|Добавление unit test]]
7. [[docs/tutorial/compile-install|Сборка и установка приложения]]

### Остальные tutorials

- [[docs/tutorial/generics|Generics]]
- [[docs/tutorial/workspaces|Workspaces]]
- [[docs/tutorial/fuzz|Fuzzing]]
- [[docs/tutorial/database-access|Доступ к реляционной БД]]
- [[docs/tutorial/web-service-gin|REST API с Gin]]
- [[docs/tutorial/json|Работа с JSON]]
- [[docs/tutorial/govulncheck|Поиск уязвимостей govulncheck]]
- [[docs/articles/wiki|Writing Web Applications]]

## Database / SQL

- [[docs/database/index|Работа с базами данных]]
- [[docs/database/open-handle|Открытие DB handle]]
- [[docs/database/querying|Выполнение запросов]]
- [[docs/database/change-data|Изменение данных]]
- [[docs/database/prepared-statements|Prepared statements]]
- [[docs/database/execute-transactions|Транзакции]]
- [[docs/database/cancel-operations|Отмена операций]]
- [[docs/database/manage-connections|Управление соединениями]]
- [[docs/database/sql-injection|Защита от SQL injection]]

## JSON

- [[docs/jsonv2-migration|Миграция с encoding/json на encoding/json/v2]]

## Security

- [[docs/security/index|Безопасность Go]]
- [[docs/security/best-practices|Security best practices]]
- [[docs/security/policy|Security policy]]
- [[docs/security/fips140|FIPS 140]]
- [[docs/security/decisions|Security decisions]]
- [[docs/security/threat-model|Threat model]]
- [[docs/security/vuln/editor|Vulnerability scanning в IDE]]
- [[docs/security/vuln/cna|Go CNA policy]]
- [[docs/security/fuzz/index|Fuzzing]]
- [[docs/security/fuzz/technical|Техническая реализация fuzzing]]
- [[docs/security/vuln/index|Go vulnerability management]]
- [[docs/security/vuln/database|Go vulnerability database]]

## Проект Go

- [Contribution Guide — upstream](https://go.dev/doc/contribute) — локальное зеркало пока отсутствует.

## Release notes

- [[docs/release-notes/go1.27|Go 1.27 Release Notes]]

## Generated / external references

Эти ресурсы являются частью официальной документационной экосистемы, но не копируются как ручной Markdown-перевод, потому что генерируются из исходного кода или являются интерактивными:

- [Standard library API](https://pkg.go.dev/std)
- [Command documentation](https://pkg.go.dev/cmd)
- [A Tour of Go](https://go.dev/tour/)
- [История релизов Go](https://go.dev/doc/devel/release)

## Метаданные и контроль качества

- [[_meta/sync-rules|Правила синхронизации]]
- [[_meta/review-2026-10-12|Техническое ревью раздела]]
- `_meta/manifest.json` — machine-readable inventory/status.
- `_meta/validate.py` — проверка manifest, WikiLinks и обязательного frontmatter.

> [!note]
> Upstream FAQ исторически утверждал, что methods не могут иметь собственные type parameters. В Go 1.27 grammar `MethodDecl` включает `[ TypeParameters ]`; при расхождениях с историческими guides ориентируйтесь на спецификацию `go1.27.1`.
