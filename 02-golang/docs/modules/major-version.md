---
title: "Разработка major version update"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/modules/major-version.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Разработка major version update

Необходимо переходить на новую major version, если изменения потенциального нового release не могут гарантировать backward compatibility для users module. Например, это требуется при изменении public API так, что client code предыдущих versions перестанет работать.

> [!note]
> Каждый release type — major, minor, patch или pre-release — имеет отдельный смысл для users module. Они используют эти различия, чтобы оценивать риск release для собственного code. Поэтому version number должен точно отражать nature изменений относительно предыдущего release. Подробнее см. [[version-numbers|Нумерация versions module]].

**См. также:**

- обзор module development: [[developing|Разработка и публикация modules]];
- end-to-end workflow: [[release-workflow|Module release and versioning workflow]].

## Что учитывать при major version update {#considerations}

Переходите на новую major version только когда это действительно необходимо. Major update создаёт значительный churn и для maintainer, и для users.

При планировании учитывайте следующее.

- **Чётко сообщите users, что новая major version означает для поддержки предыдущих major versions.**

  Предыдущие versions deprecated? Поддерживаются как раньше? Будете ли вы выпускать для них bug fixes?

- **Будьте готовы поддерживать две versions — старую и новую.**

  Например, bug fix в одной часто придётся port'ить в другую.

- **Помните: с точки зрения dependency management новая major version — новый module.**

  Users должны явно перейти на новый module, а не просто выполнить обычный upgrade.

  Причина — different module path. Например:

  ```text
  example.com/mymodule
  ```

  для v2 становится:

  ```text
  example.com/mymodule/v2
  ```

- **При разработке новой major version обновите import paths внутри нового module.**

  Users, переходящие на новый major, также должны обновить imports.

## Branching для major release {#branching}

Самый прямой подход — создать branch repository от последней version предыдущего major.

Например:

```text
$ cd mymodule
$ git checkout -b v2
Switched to a new branch "v2"
```

Официальная документация иллюстрирует это diagram: branch `v2` создаётся от текущей основной линии repository.

После branching внесите обязательные изменения.

### Обновите module path в `go.mod`

Добавьте major version suffix:

- существующая version:

  ```text
  example.com/mymodule
  ```

- новая v2:

  ```text
  example.com/mymodule/v2
  ```

### Обновите imports внутри module

Каждый import package из этого же module должен включать новый major suffix.

Старый import:

```go
import "example.com/mymodule/package1"
```

Новый import:

```go
import "example.com/mymodule/v2/package1"
```

Шаги публикации см. в [[publishing|Публикация module]].
