---
title: "Go / Golang — карта документации"
technology: "Go"
version: "1.27.1"
translation_status: "translated"
---

# Go / Golang

> [!info]
> Baseline: **Go 1.27.1**. Core/spec/runtime зафиксированы по `golang/go@go1.27.1`, User Manual и tutorials — по `golang/website@575a6925e2d55ad160ed77f402bfaa4ec7458749`.

## Обучение

- [[learning/README|Как изучать Go]]
- [[learning/roadmap|Roadmap]]
- [[learning/progress|Прогресс]]
- [[learning/projects/README|Практические проекты]]

## Старт

- [[docs/install|Установка Go]]
- [[docs/manage-install|Управление версиями Go]]
- [[docs/getting-started|Getting Started]]
- [[docs/code|Как писать Go-код]]
- [Сборка и установка Go из исходников](https://go.dev/doc/install/source)
- [[docs/editors|Editor plugins и IDE]]

## Язык и стиль

- [[docs/spec|Спецификация языка Go]]
- [[docs/memory-model|Модель памяти Go]]
- [[docs/effective-go|Effective Go]]
- [[docs/faq|FAQ]]
- [[docs/comment|Go Doc Comments]]

## Модули и toolchain

- [Go Modules Reference](https://go.dev/ref/mod)
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
- [[docs/tutorial/create-module|Создание модуля]]
- [[docs/tutorial/call-module-code|Вызов кода другого модуля]]
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

- [Contribution Guide](https://go.dev/doc/contribute)

## Release notes

- [[docs/release-notes/go1.27|Go 1.27 Release Notes]]

## Generated / external references

Эти ресурсы являются частью официальной документационной экосистемы, но не копируются как ручной Markdown-перевод, потому что генерируются из исходного кода или являются интерактивными:

- [Standard library API](https://pkg.go.dev/std)
- [Command documentation](https://pkg.go.dev/cmd)
- [A Tour of Go](https://go.dev/tour/)
- [История релизов Go](https://go.dev/doc/devel/release)

## Метаданные

- [[_meta/sync-rules|Правила синхронизации]]
- `_meta/manifest.json` — machine-readable coverage/status.

> [!note]
> Upstream FAQ исторически утверждал, что methods не могут иметь собственные type parameters. Начиная с Go 1.27 generic methods разрешены; в переводе это расхождение явно исправлено по спецификации Go 1.27.1.
