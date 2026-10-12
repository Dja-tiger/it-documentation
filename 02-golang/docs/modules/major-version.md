---
title: "Разработка major-version update"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/modules/major-version.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Разработка major-version update

Новый major version необходим, когда изменения не могут гарантировать backward compatibility пользователям module — например, когда public API изменён так, что существующий client code перестаёт компилироваться или работать по прежнему контракту.

> [!note]
> Major, minor, patch и pre-release несут разные обещания. Номер release должен точно соответствовать характеру изменений.

## Что учитывать перед major update

Переход на новый major version следует делать только когда это действительно необходимо. Он создаёт существенную стоимость и для maintainer, и для пользователей.

Перед release определите:

- что произойдёт с предыдущим major: deprecated ли он, продолжится ли support, будут ли backport bug/security fixes;
- готовы ли вы одновременно поддерживать старый и новый major;
- понимаете ли вы, что с точки зрения Go dependency management новый major — новый module;
- готовы ли вы изменить module path и все соответствующие imports.

Например:

- старый module: `example.com/mymodule`;
- новый v2 module: `example.com/mymodule/v2`.

Пользователи v2 также должны изменить imports.

## Branch для major release

Прямолинейный подход — создать branch от последней версии предыдущего major:

```text
$ cd mymodule
$ git checkout -b v2
Switched to a new branch "v2"
```

Затем:

1. В `go.mod` добавьте major suffix к module path:

```text
module example.com/mymodule/v2
```

2. Во всём Go source code измените imports packages этого же module:

```go
// раньше
import "example.com/mymodule/package1"

// v2
import "example.com/mymodule/v2/package1"
```

После подготовки и тестирования публикуйте module по обычному release workflow с tag нового major version.
