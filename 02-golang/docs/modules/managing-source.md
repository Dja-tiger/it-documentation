---
title: "Управление исходным кодом module"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/modules/managing-source.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Управление исходным кодом module

При разработке module для внешних пользователей соблюдение repository conventions делает module проще для загрузки, versioning и сопровождения.

Go поддерживает публикацию modules из Git, Subversion, Mercurial, Bazaar и Fossil repositories.

## Как Go tools находят опубликованный module

В децентрализованной модели Go source code остаётся в вашем repository. Go tools опираются на соглашения о module paths и repository tags.

Когда разработчик использует `go get` для package, команда в общих чертах:

1. По `import` statements определяет module path, которому принадлежит package.
2. По URL, производному от module path, ищет module через proxy или непосредственно repository.
3. Сопоставляет требуемую module version с repository tag. Если version явно не задана, выбирается подходящая latest release.
4. Загружает source code в local module cache.

## Организация кода в repository

Начальный commit module обычно включает:

| Файл/каталог | Назначение |
|---|---|
| `LICENSE` | Лицензия module. |
| `go.mod` | Module path, Go version и dependencies. Предпочтительно изменять через Go commands. |
| `go.sum` | Cryptographic hashes dependencies для проверки скачанных modules. При отсутствии dependencies может отсутствовать или быть пустым. Не следует редактировать вручную. |
| Package directories и `.go` files | Собственно packages и source code module. |

Пример начальной публикации через Git:

```bash
git init
git add --all
git commit -m "mycode: initial commit"
git push
```

## Выбор scope repository

Код стоит помещать в отдельный module, когда он должен versioned независимо от другого кода.

Один module в корне одного repository — самый простой для сопровождения вариант. Однако при необходимости один repository может содержать несколько modules.

### Один module на repository

`go.mod` находится в root repository, packages — в root и подкаталогах.

Преимущество: version tags не нужно prefix'ить путём подкаталога module.

### Несколько modules в одном repository

Каждый subdirectory, являющийся module root, должен иметь свой `go.mod`.

Если module находится в subdirectory, repository version tag должен быть prefix'ирован именем этого subdirectory.

Например, для module `example.com/mymodules/module1` версии `v1.2.3`:

- module path: `example.com/mymodules/module1`;
- version tag: `module1/v1.2.3`;
- package path пользователя: `example.com/mymodules/module1/package1`;
- `require`: `example.com/mymodules/module1 v1.2.3`.

Эта связь между physical repository layout, module path и tag name критична: Go tools должны однозначно определить, какой каталог repository соответствует конкретной module version.
