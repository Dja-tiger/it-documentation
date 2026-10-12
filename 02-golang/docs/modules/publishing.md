---
title: "Публикация module"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/modules/publishing.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Публикация module

Чтобы module стал доступен другим developers, его необходимо опубликовать так, чтобы Go tools могли его обнаружить. После публикации developers, импортирующие packages этого module, смогут разрешить dependency через commands вроде `go get`.

> [!warning]
> Не изменяйте tagged version module после её публикации. Go tools authenticate скачанный module относительно первой известной copy. Если содержимое одной и той же version изменилось, tools вернут security error. Вместо изменения уже опубликованной version выпускайте новую version.

**См. также:**

- overview module development: [[developing|Разработка и публикация modules]];
- общий workflow, включающий publishing: [[release-workflow|Module release and versioning workflow]].

## Шаги публикации

1. Откройте terminal и перейдите в module root внутри local repository.

2. Выполните `go mod tidy`, чтобы удалить dependencies, которые больше не нужны:

```text
$ go mod tidy
```

3. В последний раз выполните tests всего module:

```text
$ go test ./...
ok      example.com/mymodule       0.015s
```

Это запускает unit tests, написанные через Go testing framework.

4. Tag'ните project новой version через `git tag`.

Version number должен отражать nature изменений. Подробнее см. [[version-numbers|Нумерация versions module]].

```text
$ git commit -m "mymodule: changes for v0.1.0"
$ git tag v0.1.0
```

5. Push'ните tag в origin repository:

```text
$ git push origin v0.1.0
```

6. Сделайте module доступным через Go ecosystem, выполнив [`go list`](https://pkg.go.dev/cmd/go#hdr-List_packages_or_modules), чтобы Go proxy/index получил информацию о published module.

Перед command задайте `GOPROXY=proxy.golang.org`, чтобы request гарантированно дошёл до proxy:

```text
$ GOPROXY=proxy.golang.org go list -m example.com/mymodule@v0.1.0
```

После публикации developers импортируют package и используют `go get` так же, как для других modules. Можно получить latest version либо конкретную version:

```text
$ go get example.com/mymodule@v0.1.0
```
