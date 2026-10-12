---
title: "Module release and versioning workflow"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/modules/release-workflow.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Module release and versioning workflow

При разработке modules для использования другими developers можно следовать workflow, который обеспечивает предсказуемый и последовательный experience для users module. Здесь описаны high-level steps этого workflow.

Обзор module development: [[developing|Разработка и публикация modules]].

**См. также:**

- если нужно только использовать external packages, см. [[managing-dependencies|Управление dependencies]];
- каждая новая version через version number сообщает nature changes. См. [[version-numbers|Нумерация versions modules]].

## Общие шаги workflow {#common-steps}

Типичная последовательность для нового module:

1. **Начните module** и организуйте source так, чтобы он был удобен users и maintainers.

   Если module development незнаком, начните с [[../tutorial/create-module|Tutorial: Create a Go module]].

   В децентрализованной системе Go организация repository имеет значение. См. [[managing-source|Управление source module]].

2. Настройте **local client code**, вызывающий functions unpublished module.

   До публикации module недоступен через обычный dependency workflow (`go get`). Удобно тестировать его через local directory. См. [[#Разработка против unpublished module]].

3. Когда code готов для early users, **публикуйте v0 pre-releases** — alpha/beta. См. [[#Публикация pre-release versions]].

4. **Выпустите v0**, которая ещё не гарантирует stability, но позволяет users пробовать module. См. [[#Публикация первой unstable version]].

5. После v0 продолжайте **выпускать новые versions**:

   - bug fixes → patch releases;
   - backward-compatible API additions → minor releases;
   - во время v0 допускаются breaking changes, потому что v0 не обещает stability/backward compatibility.

6. Перед stable release публикуйте **alpha/beta pre-releases**. См. [[#Публикация pre-release versions]].

7. Выпустите v1 как **первый stable release**. См. [[#Публикация первой stable version]].

8. В v1 продолжайте bug fixes и при необходимости backward-compatible additions public API.

9. Если breaking changes невозможно избежать, публикуйте **новую major version**. Переход, например, v1 → v2 крайне disruptive и должен быть last resort. См. [[#Публикация breaking API changes]].

## Разработка против unpublished module {#unpublished}

Когда module или новая version только разрабатываются, они ещё не опубликованы. Поэтому другой module не может добавить их обычным `go get` workflow.

Client module может ссылаться на local copy через `replace` directive в своём `go.mod`.

Подробнее: [[managing-dependencies#Использование code module из local directory|Requiring module code in a local directory]].

## Публикация pre-release versions {#pre-release}

Pre-release позволяет дать module users для тестирования и feedback без guarantees stability.

Примеры:

```text
v0.2.1-beta.1
v1.2.3-alpha
```

Pre-release identifier добавляется к semantic version. Подробнее: [[version-numbers|Module version numbering]].

Users должны явно указать pre-release version в `go get`, потому что по умолчанию Go предпочитает обычный release pre-release version:

```bash
go get example.com/theirmodule@v1.2.3-alpha
```

Pre-release публикуется repository tag'ом с соответствующим identifier. См. [[publishing|Публикация module]].

## Публикация первой unstable version {#first-unstable}

Versions `v0.x.x` не гарантируют stability или backward compatibility, но позволяют users начать использовать module и давать feedback до v1.

После v0 можно increment'ить minor/patch numbers, продолжая развивать API.

Например:

```text
v0.1.3
```

Unstable release публикуется repository tag'ом v0. Подробнее: [[publishing|Публикация module]].

## Публикация первой stable version {#first-stable}

Первый stable release имеет version `v1.x.x`. Обычно ему предшествуют pre-release и v0 versions, где API получает feedback, fixes и стабилизируется.

С v1 maintainer берёт на себя commitments:

- users смогут upgrade'иться на последующие minor/patch releases того же major без breaking client code;
- public API, включая function/method signatures, не будет изменяться backward-incompatible способом;
- exported types не будут удаляться;
- backward-compatible API additions, например новые struct fields, будут выходить как minor releases;
- bug fixes, включая security fixes, будут выходить в patch или minor releases.

> [!note]
> v0 не гарантирует compatibility, поэтому при переходе v0 → v1 можно внести breaking changes: v0 изначально не считалась stable.

Пример первой stable version:

```text
v1.0.0
```

Stable release публикуется tag'ом v1. Подробнее: [[publishing|Публикация module]].

## Публикация bug fixes {#bug-fixes}

Release только с bug fixes называется **patch release**.

Patch release не должен содержать changes public API. Consumer code может безопасно upgrade'иться без изменений.

> [!important]
> Patch release по возможности не должен upgrade'ить собственные transitive dependencies более чем на patch release. Иначе user, обновляющий patch вашего module, может неожиданно получить более invasive change transitive dependency.

Пример:

```text
old: v1.0.0
new: v1.0.1
```

Публикация выполняется tag'ом с incremented patch version.

## Публикация non-breaking API changes {#non-breaking}

Backward-compatible changes public API публикуются как **minor release**.

Такая version может включать:

- changes dependencies самого module;
- новые functions;
- новые methods;
- новые struct fields;
- новые types.

Существующий calling code не должен ломаться.

Пример:

```text
old: v1.0.1
new: v1.1.0
```

Minor release публикуется tag'ом с incremented minor part.

## Публикация breaking API changes {#breaking}

Backward-incompatible changes публикуются как **major release**.

Major update может сильно повлиять на users и должен использоваться только при необходимости. Подробнее:

- [[major-version|Разработка major version update]];
- [Keeping your modules compatible](https://go.dev/blog/module-compatibility).

В отличие от обычного tagging patch/minor release, major update требует дополнительных steps.

1. Создайте отдельное место для source нового major — например, branch repository для новой major line и последующих minor/patch releases.

2. В `go.mod` измените module path, добавив новый major suffix:

   ```text
   example.com/mymodule/v2
   ```

   Module path — identifier module, поэтому фактически создаётся новый module. Изменение package path гарантирует, что users случайно не импортируют breaking version: upgrade требует явной замены старого path новым.

3. Обновите все imports packages этого module, включая internal imports внутри самого нового module.

4. Перед official release публикуйте pre-release versions для feedback и bug reports.

5. Опубликуйте major release repository tag'ом с incremented major number, например:

   ```text
   v1.5.2 -> v2.0.0
   ```

   Подробнее: [[publishing|Публикация module]].
