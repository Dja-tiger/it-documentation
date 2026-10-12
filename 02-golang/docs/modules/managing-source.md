---
title: "Управление source module"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/modules/managing-source.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Управление source module

При разработке modules для публикации другим developers соблюдение repository conventions делает modules проще в использовании.

Эта страница описывает actions при управлении module repository. Последовательный workflow перехода от version к version см. в [[release-workflow|Module release and versioning workflow]].

Часть conventions является обязательной, остальные — best practices. Предполагается знакомство с базовыми module practices из [[managing-dependencies|Управление dependencies]].

Go поддерживает публикацию modules из repositories следующих systems:

- Git;
- Subversion;
- Mercurial;
- Bazaar;
- Fossil.

Обзор module development: [[developing|Разработка и публикация modules]].

## Как Go tools находят опубликованный module {#tools}

Go использует децентрализованную модель публикации modules: code остаётся в repository. Go tools полагаются на naming rules, связывающие repository paths и repository tags с module name и version number.

Если repository соблюдает эти requirements, Go tools вроде [`go get`](https://go.dev/ref/mod#go-get) способны скачать module source.

Когда developer выполняет `go get` для packages, импортированных его code, command:

1. По `import` statements определяет module path внутри package path.
2. По URL, derived from module path, находит source module через module proxy server либо непосредственно в repository.
3. Находит source нужной module version, сопоставляя version number с repository tag. Если version заранее не указана, выбирается latest release version.
4. Получает module source и скачивает его в local module cache developer.

## Организация code в repository {#repository}

Соблюдение conventions упрощает maintenance и улучшает опыт users. Само размещение module code в repository обычно не отличается от другого source code.

Official guide показывает hierarchy простого module с двумя packages. Initial commit должен включать следующие files.

| File | Назначение |
| --- | --- |
| `LICENSE` | License module. |
| `go.mod` | Описывает module, включая module path и dependencies. Подробнее: [[gomod-ref|go.mod reference]]. Module path задаётся `module` directive, например `module example.com/mymodule`. Хотя `go.mod` можно редактировать вручную, надёжнее менять его через Go commands. |
| `go.sum` | Содержит cryptographic hashes dependencies. Go tools используют hashes для authentication скачанных modules. При mismatch Go сообщает security error. Если dependencies отсутствуют, file может быть пустым/отсутствовать. Не редактируйте вручную; лишние entries удаляются через `go mod tidy`. |
| Package directories и `.go` sources | Directories и files, составляющие packages/source module. |

Пример initial Git workflow:

```text
$ git init
$ git add --all
$ git commit -m "mycode: initial commit"
$ git push
```

## Выбор scope repository {#repository-scope}

Code следует публиковать в отдельном module, если он должен version'иться независимо от code других modules.

Repository с одним module в root проще поддерживать, особенно при выпуске minor/patch versions и branching новых major versions. Но при необходимости один repository может содержать несколько modules.

### Один module на repository {#one-module-source}

При single-module model `go.mod` находится в repository root, а subdirectories содержат Go packages.

Это самый простой layout: не требуется prefix'ить version tag path'ом subdirectory module.

Conceptually:

```text
repository-root/
├── go.mod
├── go.sum
├── package1/
└── package2/
```

### Несколько modules в одном repository {#multiple-module-source}

Один repository может содержать несколько independently versioned modules.

Каждый subdirectory, являющийся module root, должен иметь собственный `go.mod`.

В этом layout version tag **должен** быть prefixed именем subdirectory module root.

Для module `example.com/mymodules/module1` version `v1.2.3`:

- Module path: `example.com/mymodules/module1`
- Version tag: `module1/v1.2.3`
- Package path для user import: `example.com/mymodules/module1/package1`
- `require` в user module: `example.com/mymodules/module1 v1.2.3`

Official guide иллюстрирует этот layout diagram с двумя module roots в одном repository.
