---
title: "Поддержка coverage profiling для integration tests"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/build-cover.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Поддержка coverage profiling для integration tests

Содержание:

- [Обзор](#overview)
- [Сборка binary для coverage profiling](#building)
- [Запуск coverage-instrumented binary](#running)
- [Работа с coverage data files](#working)
- [Часто задаваемые вопросы](#FAQ)
- [Ресурсы](#resources)
- [Глоссарий](#glossary)

Начиная с Go 1.20 Go поддерживает сбор coverage profiles из applications и integration tests — более крупных и сложных tests для Go-программ.

## Обзор {#overview}

Go предоставляет простой механизм сбора coverage profiles на уровне package unit tests через команду:

```bash
go test -coverprofile=... <pkg_target>
```

Начиная с Go 1.20 пользователи также могут собирать coverage profiles для более крупных [integration tests](#glos-integration-test): более тяжёлых и сложных tests, которые выполняют несколько запусков одного application binary.

Для unit tests сбор coverage profile и генерация отчёта требуют двух шагов:

1. запустить `go test -coverprofile=...`;
2. выполнить `go tool cover {-func,-html}` для генерации отчёта.

Для integration tests нужны три шага:

1. [сборка](#building);
2. [запуск](#running), который может включать несколько запусков binary из предыдущего шага;
3. [формирование отчёта](#reporting).

## Сборка binary для coverage profiling {#building}

Чтобы собрать application для сбора coverage profiles, передайте flag `-cover` команде `go build`, собирающей application binary target.

Пример `go build -cover` приведён [ниже](#packageselection).

Полученный binary затем можно запустить с environment variable, задающей место для записи coverage profiles. Это описано в следующем разделе.

### Как выбираются packages для instrumentation {#packageselection}

Во время выполнения `go build -cover` команда Go выбирает для coverage profiling packages из **main module**.

Другие packages, участвующие в build, по умолчанию не включаются:

- dependencies из `go.mod`;
- packages стандартной библиотеки Go.

Рассмотрим пример программы с main package, локальным package `greetings` из main module и несколькими packages вне module, включая `rsc.io/quote` и `fmt`.

```text
$ cat go.mod
module mydomain.com

go 1.20

require rsc.io/quote v1.5.2

require (
	golang.org/x/text v0.0.0-20170915032832-14c0d48ead0c // indirect
	rsc.io/sampler v1.3.0 // indirect
)

$ cat myprogram.go
package main

import (
	"fmt"
	"mydomain.com/greetings"
	"rsc.io/quote"
)

func main() {
	fmt.Printf("I say %q and %q\n", quote.Hello(), greetings.Goodbye())
}
$ cat greetings/greetings.go
package greetings

func Goodbye() string {
	return "see ya"
}
$ go build -cover -o myprogram.exe .
$
```

Если собрать эту программу с flag `-cover` и запустить её, в coverage profile будут включены ровно два package:

- `main`;
- `mydomain.com/greetings`.

Остальные dependencies будут исключены.

Пользователи, которым нужен более точный контроль над тем, какие packages включаются в coverage, могут использовать flag `-coverpkg`.

Пример:

```text
$ go build -cover -o myprogramMorePkgs.exe -coverpkg=io,mydomain.com,rsc.io/quote .
$
```

В этой сборке для profiling выбраны:

- main package из `mydomain.com`;
- `rsc.io/quote`;
- `io`.

Package `mydomain.com/greetings` не перечислен явно, поэтому будет исключён из profile, хотя находится в main module.

## Запуск coverage-instrumented binary {#running}

Binaries, собранные с `-cover`, при завершении записывают coverage profile data files в directory, заданный environment variable `GOCOVERDIR`.

Пример:

```text
$ go build -cover -o myprogram.exe myprogram.go
$ mkdir somedata
$ GOCOVERDIR=somedata ./myprogram.exe
I say "Hello, world." and "see ya"
$ ls somedata
covcounters.c6de772f99010ef5925877a7b05db4cc.2424989.1670252383678349347
covmeta.c6de772f99010ef5925877a7b05db4cc
$
```

В directory `somedata` записаны два binary-файла с результатами coverage.

О том, как получить из них человекочитаемые результаты, см. раздел [формирование отчётов](#reporting).

Если `GOCOVERDIR` не установлен, coverage-instrumented binary всё равно корректно выполнится, но выведет warning.

```text
$ ./myprogram.exe
warning: GOCOVERDIR not set, no coverage data emitted
I say "Hello, world." and "see ya"
$
```

### Tests с несколькими запусками

Integration tests часто включают несколько запусков программы. Если программа собрана с `-cover`, каждый запуск создаёт новый data file.

Пример:

```text
$ mkdir somedata2
$ GOCOVERDIR=somedata2 ./myprogram.exe          // first run
I say "Hello, world." and "see ya"
$ GOCOVERDIR=somedata2 ./myprogram.exe -flag    // second run
I say "Hello, world." and "see ya"
$ ls somedata2
covcounters.890814fca98ac3a4d41b9bd2a7ec9f7f.2456041.1670259309405583534
covcounters.890814fca98ac3a4d41b9bd2a7ec9f7f.2456047.1670259309410891043
covmeta.890814fca98ac3a4d41b9bd2a7ec9f7f
$
```

Coverage output files бывают двух типов:

- **meta-data files** — содержат данные, которые не меняются между запусками, например source file names и function names;
- **counter data files** — содержат сведения о том, какие части программы выполнялись.

В примере выше первый запуск создал два файла — counter и meta, а второй только counter file.

Поскольку meta-data не меняются между запусками, их достаточно записать один раз.

## Работа с coverage data files {#working}

Go 1.20 добавил новый tool `covdata`, который умеет читать и обрабатывать coverage data files из directory, указанной через `GOCOVERDIR`.

`covdata` поддерживает несколько modes. Общая форма команды:

```text
$ go tool covdata <mode> -i=<dir1,dir2,...> ...flags...
```

Flag `-i` задаёт список directories для чтения. Каждая такая directory содержит данные, полученные при выполнении coverage-instrumented binary через `GOCOVERDIR`.

### Создание coverage reports {#reporting}

В этом разделе описано, как с помощью `go tool covdata` формировать человекочитаемые reports из coverage data files.

#### Процент покрытых statements

Чтобы вывести percentage покрытых statements для каждого instrumented package, используйте:

```text
go tool covdata percent -i=<directory>
```

Используя пример из раздела [запуска](#running):

```text
$ ls somedata
covcounters.c6de772f99010ef5925877a7b05db4cc.2424989.1670252383678349347
covmeta.c6de772f99010ef5925877a7b05db4cc
$ go tool covdata percent -i=somedata
	main	coverage: 100.0% of statements
	mydomain.com/greetings	coverage: 100.0% of statements
$
```

Значения `statements covered` напрямую соответствуют тем, которые показывает `go test -cover`.

### Преобразование в legacy text format

Binary coverage data files можно преобразовать в legacy text format, который создаётся командой:

```text
go test -coverprofile=<outfile>
```

Для этого используется selector `textfmt` у `covdata`.

Полученный text file затем можно передать `go tool cover -func` или `go tool cover -html`.

Пример:

```text
$ ls somedata
covcounters.c6de772f99010ef5925877a7b05db4cc.2424989.1670252383678349347
covmeta.c6de772f99010ef5925877a7b05db4cc
$ go tool covdata textfmt -i=somedata -o profile.txt
$ cat profile.txt
mode: set
mydomain.com/myprogram.go:10.13,12.2 1 1
mydomain.com/greetings/greetings.go:3.23,5.2 1 1
$ go tool cover -func=profile.txt
mydomain.com/greetings/greetings.go:3:	Goodbye		100.0%
mydomain.com/myprogram.go:10:		main		100.0%
total:					(statements)	100.0%
$
```

### Merge

Subcommand `merge` у `go tool covdata` позволяет объединять profiles из нескольких data directories.

Например, программа работает и на macOS, и на Windows. Автор может объединить coverage profiles из отдельных запусков на обеих operating systems в один corpus и получить cross-platform coverage summary.

```text
$ ls windows_datadir
covcounters.f3833f80c91d8229544b25a855285890.1025623.1667481441036838252
covcounters.f3833f80c91d8229544b25a855285890.1025628.1667481441042785007
covmeta.f3833f80c91d8229544b25a855285890
$ ls macos_datadir
covcounters.b245ad845b5068d116a4e25033b429fb.1025358.1667481440551734165
covcounters.b245ad845b5068d116a4e25033b429fb.1025364.1667481440557770197
covmeta.b245ad845b5068d116a4e25033b429fb
$ ls macos_datadir
$ mkdir merged
$ go tool covdata merge -i=windows_datadir,macos_datadir -o merged
$
```

Эта операция объединяет данные из указанных input directories и записывает новый набор merged data files в directory `merged`.

### Выбор packages

Большинство команд `go tool covdata` поддерживает flag `-pkg`, позволяющий выбрать packages, участвующие в операции.

Argument `-pkg` имеет тот же формат, что и flag `-coverpkg` у команды Go.

Пример:

```text
$ ls somedata
covcounters.c6de772f99010ef5925877a7b05db4cc.2424989.1670252383678349347
covmeta.c6de772f99010ef5925877a7b05db4cc
$ go tool covdata percent -i=somedata -pkg=mydomain.com/greetings
	mydomain.com/greetings	coverage: 100.0% of statements
$ go tool covdata percent -i=somedata -pkg=nonexistentpackage
$
```

Flag `-pkg` позволяет выбрать конкретное подмножество packages, представляющих интерес для данного report.

## Часто задаваемые вопросы {#FAQ}

1. [Как включить coverage instrumentation для всех imported packages, упомянутых в `go.mod`?](#gomodselect)
2. [Можно ли использовать `go build -cover` в режиме GOPATH / `GO111MODULE=off`?](#gopathmode)
3. [Будут ли записаны coverage data, если программа завершится panic?](#panicprof)
4. [Выберет ли `-coverpkg=main` мой main package для profiling?](#mainpkg)

### Как включить coverage instrumentation для всех imported packages из `go.mod`? {#gomodselect}

По умолчанию `go build -cover` instrument'ирует для coverage все packages main module, но не instrument'ирует imports за пределами main module, например standard library packages или imports из `go.mod`.

Один из способов запросить instrumentation всех non-stdlib dependencies — передать output `go list` в `-coverpkg`.

Используя тот же пример программы:

```text
$ go list -f '{{if not .Standard}}{{.ImportPath}}{{end}}' -deps . | paste -sd "," > pkgs.txt
$ go build -o myprogram.exe -coverpkg=`cat pkgs.txt` .
$ mkdir somedata
$ GOCOVERDIR=somedata ./myprogram.exe
$ go tool covdata percent -i=somedata
	golang.org/x/text/internal/tag	coverage: 78.4% of statements
	golang.org/x/text/language	coverage: 35.5% of statements
	mydomain.com	coverage: 100.0% of statements
	mydomain.com/greetings	coverage: 100.0% of statements
	rsc.io/quote	coverage: 25.0% of statements
	rsc.io/sampler	coverage: 86.7% of statements
$
```

### Можно ли использовать `go build -cover` в режиме `GO111MODULE=off`? {#gopathmode}

Да. `go build -cover` работает с `GO111MODULE=off`.

При сборке программы в режиме `GO111MODULE=off` для profiling instrument'ируется только package, явно указанный как target в command line.

Используйте flag `-coverpkg`, чтобы добавить в profile другие packages.

### Если программа завершится panic, будут ли записаны coverage data? {#panicprof}

Programs, собранные через `go build -cover`, записывают complete profile data в конце execution только если программа:

- вызывает `os.Exit()`;
- или нормально возвращается из `main.main`.

Если программа завершается unrecovered panic либо встречает fatal exception, например segmentation violation или divide by zero, profile data для statements, выполненных во время этого запуска, будут потеряны.

### Выберет ли `-coverpkg=main` мой main package для profiling? {#mainpkg}

Flag `-coverpkg` принимает список **import paths**, а не package names.

Если требуется выбрать main package для coverage instrumentation, укажите его import path, а не имя package.

Пример:

```text
$ go list -m
mydomain.com
$ go build -coverpkg=main -o oops.exe .
warning: no packages being built depend on matches for pattern main
$ go build -coverpkg=mydomain.com -o myprogram.exe .
$ mkdir somedata
$ GOCOVERDIR=somedata ./myprogram.exe
I say "Hello, world." and "see ya"
$ go tool covdata percent -i=somedata
	mydomain.com	coverage: 100.0% of statements
$
```

## Ресурсы {#resources}

- **Blog post о появлении unit test coverage в Go 1.2**
  - Coverage profiling для unit tests появился в Go 1.2; подробности см. в официальном [blog post](https://go.dev/blog/cover).
- **Документация**
  - Документация package [`cmd/go`](https://pkg.go.dev/cmd/go) описывает build/test flags, относящиеся к coverage.
- **Технические детали**
  - [Design draft](https://go.dev/design/51430-revamp-code-coverage)
  - [Proposal](https://go.dev/issue/51430)

## Глоссарий {#glossary}

<a id="glos-unit-test"></a>

**unit test:** tests в file `*_test.go`, связанном с конкретным Go package и использующем package `testing`.

<a id="glos-integration-test"></a>

**integration test:** более комплексный и тяжёлый test для application или binary. Integration tests обычно включают сборку программы или набора программ, а затем серию запусков с разными inputs и scenarios под управлением test harness, который может быть основан на Go package `testing`, но это не обязательно.
