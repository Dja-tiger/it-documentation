---
title: "Workflow релизов и versioning Go module"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/modules/release-workflow.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Workflow релизов и versioning Go module

При разработке module для других разработчиков последовательный release workflow помогает сделать upgrades предсказуемыми.

## Типичный workflow

1. **Создать module** и организовать source code.
2. **Писать локальный client code** против ещё не опубликованного module, используя `replace`.
3. Когда API готов к раннему тестированию, публиковать **v0 pre-releases**: alpha/beta.
4. Выпустить первый **нестабильный v0**.
5. Продолжать выпускать v0 patch/minor versions; в v0 breaking changes всё ещё допустимы.
6. Перед stable release выпускать pre-release versions.
7. Выпустить **v1** как первый stable release.
8. Внутри v1 выпускать patch bug fixes и backward-compatible minor API additions.
9. Если breaking change неизбежен, выпустить **новый major**, например v2.

## Разработка против неопубликованного module

Пока module не опубликован, обычный dependency flow через `go get` недоступен. Client module может указать local source через `replace` в `go.mod`.

Например:

```text
require example.com/theirmodule v0.0.0-unpublished
replace example.com/theirmodule v0.0.0-unpublished => ../theirmodule
```

Подробнее: [[managing-dependencies#разработка-и-тестирование-против-неопубликованного-module|локальная разработка dependencies]].

## Pre-release versions

Pre-release позволяет получить feedback до stable release и не гарантирует стабильность.

Примеры:

```text
v0.2.1-beta.1
v1.2.3-alpha
```

Поскольку `go` обычно предпочитает release versions, пользователь должен запросить pre-release явно:

```bash
go get example.com/theirmodule@v1.2.3-alpha
```

Публикация выполняется repository tag'ом с соответствующим identifier.

## Первый нестабильный v0

Versions `v0.x.x` не обещают stability/backward compatibility, но позволяют получать feedback до v1.

Пример:

```text
v0.1.3
```

Minor и patch компоненты v0 можно увеличивать по мере развития API. Breaking changes внутри v0 допустимы, однако их всё равно стоит документировать.

## Первый stable release

Первый stable release имеет `v1.x.x`, обычно начиная с:

```text
v1.0.0
```

С v1 maintainer фактически обещает пользователям:

- последующие minor и patch releases того же major не должны ломать существующий client code;
- не будут удаляться exported API элементы или намеренно ломаться signatures;
- backward-compatible additions попадут в minor releases;
- bug/security fixes — в patch либо minor release.

Переход v0 → v1 может включать breaking changes, потому что v0 не гарантировал compatibility.

## Patch releases

Patch release содержит bug fixes и не должен менять public API.

```text
v1.0.0 -> v1.0.1
```

Официальный guide также рекомендует не делать в patch release без необходимости значительные upgrades транзитивных dependencies: иначе пользователь, обновляя только patch вашего module, может неожиданно получить более рискованное изменение dependency graph.

## Minor releases

Minor release допускает backward-compatible изменения public API:

```text
v1.0.1 -> v1.1.0
```

Это могут быть новые functions, methods, fields или types, если существующий client code продолжает работать.

## Breaking API changes

Breaking changes требуют major release.

Переход `v1 -> v2` включает больше действий, чем простой tag:

1. Создать место для source нового major — часто отдельный branch.
2. Изменить module path:

```text
example.com/mymodule/v2
```

3. Обновить imports внутри самого module.
4. Выпустить pre-release и получить feedback.
5. Опубликовать tag, например `v2.0.0`.

Изменение module path специально предотвращает незаметное подтягивание breaking API: пользователь должен осознанно перейти на новый import path.
