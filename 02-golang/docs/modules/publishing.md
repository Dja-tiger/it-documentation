---
title: "Публикация Go module"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/modules/publishing.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Публикация Go module

Чтобы другие разработчики могли разрешать dependency на ваш module через Go tools, module нужно опубликовать — то есть сделать versioned source доступным по module path.

> [!warning]
> Никогда не изменяйте содержимое уже опубликованного version tag. Go ecosystem аутентифицирует module content относительно ранее наблюдавшейся версии/checksum. Повторное использование того же version number с другим содержимым способно вызвать security error. Для любого изменения выпускайте новую version.

## Шаги публикации

1. Перейдите в root module локального repository.

2. Очистите dependency declarations:

```bash
go mod tidy
```

3. Финально запустите тесты:

```text
$ go test ./...
ok      example.com/mymodule       0.015s
```

4. Закоммитьте изменения и создайте semantic version tag, соответствующий характеру release:

```bash
git commit -m "mymodule: changes for v0.1.0"
git tag v0.1.0
```

5. Отправьте tag в origin:

```bash
git push origin v0.1.0
```

6. Чтобы proxy увидел опубликованную version, можно выполнить `go list` через публичный Go proxy:

```bash
GOPROXY=proxy.golang.org go list -m example.com/mymodule@v0.1.0
```

После этого пользователь может импортировать package и получить module:

```bash
go get example.com/mymodule@v0.1.0
```

Для выбора version number см. [[version-numbers|Module version numbering]].
