---
title: "Tutorial: компиляция и установка application"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/compile-install.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Компиляция и установка application

На последнем практическом этапе tutorial познакомьтесь ещё с двумя командами `go`.

`go run` удобна при частых изменениях: она компилирует и запускает program, но не оставляет готовый binary executable.

Для build используются ещё две команды:

- [`go build`](https://pkg.go.dev/cmd/go#hdr-Compile_packages_and_dependencies) компилирует packages и их dependencies, но не устанавливает результат;
- [`go install`](https://go.dev/ref/mod#go-install) компилирует и устанавливает packages.

> [!note]
> Эта страница является частью многошагового tutorial, начинающегося с [[create-module|Создание Go module]].

1. В command line, находясь в directory `hello`, скомпилируйте code в executable:

```bash
go build
```

2. Запустите созданный `hello` executable и убедитесь, что application работает.

Конкретный output может отличаться, если после testing вы изменяли `greetings.go`.

Linux/macOS:

```text
$ ./hello
map[Darrin:Great to see you, Darrin! Gladys:Hail, Gladys! Well met! Samantha:Hail, Samantha! Well met!]
```

Windows:

```text
$ hello.exe
map[Darrin:Great to see you, Darrin! Gladys:Hail, Gladys! Well met! Samantha:Hail, Samantha! Well met!]
```

Application теперь скомпилирован в executable. Однако для запуска terminal должен либо находиться в directory executable, либо нужно указывать path к executable.

Далее установите executable в install directory, чтобы его можно было запускать без явного path.

3. Узнайте Go install path — directory, куда команда `go` установит текущий package.

Используйте [`go list`](https://pkg.go.dev/cmd/go#hdr-List_packages_or_modules):

```text
$ go list -f '{{.Target}}'
```

Например, output может быть:

```text
/home/gopher/bin/hello
```

Это означает, что binaries устанавливаются в `/home/gopher/bin`. Install directory понадобится на следующем шаге.

4. Добавьте Go install directory в shell `PATH`.

После этого executable можно будет запускать без указания его location.

Linux/macOS:

```bash
export PATH=$PATH:/path/to/your/install/directory
```

Windows:

```text
set PATH=%PATH%;C:\path\to\your\install\directory
```

Если в shell path уже есть directory вроде `$HOME/bin` и вы хотите устанавливать Go programs туда, install target можно изменить через `GOBIN` с помощью [`go env`](https://pkg.go.dev/cmd/go#hdr-Print_Go_environment_information):

Linux/macOS:

```bash
go env -w GOBIN=/path/to/your/bin
```

Windows:

```text
go env -w GOBIN=C:\path\to\your\bin
```

5. После обновления shell path выполните `go install`, чтобы скомпилировать и установить package:

```bash
go install
```

6. Теперь application можно запускать просто по имени. Для проверки откройте новый command prompt, перейдите в любой другой directory и выполните:

```text
$ hello
map[Darrin:Hail, Darrin! Well met! Gladys:Great to see you, Gladys! Samantha:Hail, Samantha! Well met!]
```

На этом практические шаги tutorial завершены.

Далее — [[module-conclusion|заключение и ссылки на дополнительные материалы]].
