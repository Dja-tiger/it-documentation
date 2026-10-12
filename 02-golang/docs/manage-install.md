---
title: "Управление установками Go"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/manage-install.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Управление установками Go

В этом разделе описано, как установить несколько версий Go на одной машине и как удалить Go.

См. также:

- [[install|Скачивание и установка Go]] — самый простой способ установить Go;
- [Installing Go from source](https://go.dev/doc/install/source) — сборка Go из исходного кода.

## Установка нескольких версий Go

На одной машине можно установить несколько версий Go. Это полезно, например, для тестирования кода на разных версиях toolchain. Доступные версии перечислены на [странице загрузок](https://go.dev/dl/).

> [!note]
> Для описанного здесь способа требуется установленный `git`.

Чтобы установить дополнительную версию Go, используйте `go install`, указав специальный модуль `golang.org/dl/goX.Y.Z`. Например, для Go 1.10.7:

```bash
go install golang.org/dl/go1.10.7@latest
go1.10.7 download
```

Чтобы выполнять команды через скачанную версию, добавляйте номер версии к имени команды `go`:

```text
$ go1.10.7 version
go version go1.10.7 linux/amd64
```

При нескольких установленных версиях каталог конкретной версии можно определить через её `GOROOT`:

```bash
go1.10.7 env GOROOT
```

Чтобы удалить скачанную таким способом версию, удалите каталог, указанный в её `GOROOT`, и бинарный файл `goX.Y.Z`.

## Удаление Go

### Удаление пользовательских настроек и данных

Go хранит пользовательскую конфигурацию в каталоге `go` внутри системного user configuration directory, который возвращает `os.UserConfigDir`. Этот каталог также можно определить как каталог файла конфигурации, возвращаемого командой:

```bash
go env GOENV
```

Промежуточные build artifacts хранятся в каталоге:

```bash
go env GOCACHE
```

Очистить их можно командой:

```bash
go clean -cache
```

Скачанные зависимости находятся в каталоге:

```bash
go env GOMODCACHE
```

Очистка module cache:

```bash
go clean -modcache
```

Бинарные файлы, установленные через `go install`, находятся в Go bin directory, возвращаемом `go env GOBIN`. Если `GOBIN` не задан, типичное значение — `$HOME/go/bin`. Для удаления этих binaries удалите каталог. Если вы вручную добавляли его в `PATH`, удалите соответствующую запись из shell profile.

### Linux

1. Удалите `/usr/local/go` — это стандартный installation directory.
2. Удалите `/usr/local/go` из `PATH`. В Linux и FreeBSD обычно редактируют `/etc/profile` или `$HOME/.profile`.
3. Если вы вручную добавляли Go bin directory, обычно `$HOME/go/bin`, например строкой:

```bash
export PATH="$PATH:$(go env GOPATH)/bin"
```

удалите эту запись из shell profile.

4. Перезапустите terminal sessions.

### macOS

1. Удалите `/usr/local/go`.
2. Удалите `/usr/local/go` из `PATH`. Если Go устанавливался через macOS package, удалите `/etc/paths.d/go`.
3. Если вы вручную добавляли Go bin directory (`$HOME/go/bin`) в shell profile, удалите эту запись.
4. Перезапустите terminal sessions.

### Windows

Go можно удалить одним из двух способов.

#### Метод 1: Control Panel

1. Откройте Control Panel и раздел **Add/Remove Programs**.
2. Выберите **Go Programming Language**, нажмите **Uninstall** и следуйте инструкциям.

#### Метод 2: command line

Выполните:

```text
msiexec /x go{{version}}.windows-{{cpu-arch}}.msi /q
```

При таком удалении Windows environment variables, созданные исходной установкой, удаляются автоматически.
