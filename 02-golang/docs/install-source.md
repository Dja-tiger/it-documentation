---
title: "Установка Go из исходного кода"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/install/source.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Установка Go из исходного кода

В этой статье описано, как собрать и запустить Go из исходного кода. Если требуется обычная установка с помощью готового установщика, см. [[install|Скачивание и установка Go]].

## Введение

Go — проект с открытым исходным кодом, распространяемый по BSD-style license. В этой статье объясняется, как получить исходный код, собрать его на своей машине и запустить получившийся Go toolchain.

Большинству пользователей делать это не требуется: значительно проще установить готовые предварительно собранные binary packages, как описано в [[install|Скачивание и установка Go]]. Сборка из исходников в первую очередь нужна тем, кто хочет разрабатывать сам Go или проверять изменения, которые позднее попадут в официальные binary distributions.

Существуют два официальных Go compiler toolchains. Эта статья посвящена compiler `gc` и связанным с ним tools. Для `gccgo`, использующего GCC back end, официальный upstream содержит отдельную инструкцию [Setting up and using gccgo](https://go.dev/doc/install/gccgo).

Go compilers поддерживают следующие instruction sets:

| GOARCH | Архитектура |
| --- | --- |
| `amd64`, `386` | x86, соответственно 64- и 32-бит |
| `arm64`, `arm` | ARM, соответственно 64-bit AArch64 и 32-bit |
| `loong64` | 64-bit LoongArch |
| `mips64`, `mips64le`, `mips`, `mipsle` | MIPS, big- и little-endian, 64- и 32-bit |
| `ppc64`, `ppc64le` | 64-bit PowerPC, big- и little-endian |
| `riscv64` | 64-bit RISC-V |
| `s390x` | IBM z/Architecture |
| `wasm` | [WebAssembly](https://webassembly.org) |

Compilers могут создавать binaries для AIX, Android, DragonFly BSD, FreeBSD, Illumos, Linux, macOS/iOS (Darwin), NetBSD, OpenBSD, Plan 9, Solaris и Windows, хотя не каждая операционная система поддерживает каждую архитектуру.

Список портов, считающихся first-class, приведён на странице [first class ports](https://go.dev/wiki/PortingPolicy#first-class-ports). Полный список поддерживаемых комбинаций `GOOS/GOARCH` приведён ниже в разделе [[#Необязательные переменные окружения]]. Общие системные требования см. на странице [MinimumRequirements](https://go.dev/wiki/MinimumRequirements).

## Установите Go compiler binaries для bootstrap

Go toolchain написан на Go. Поэтому, чтобы собрать Go, уже требуется установленный Go compiler.

Scripts первоначальной сборки ищут команду `go` в `$PATH`. Если Go уже установлен и находится в `$PATH`, можно сразу собирать Go из исходников.

Вместо этого можно задать `$GOROOT_BOOTSTRAP`, указывающий на корень Go installation, которая будет использоваться для bootstrap. Команда `$GOROOT_BOOTSTRAP/bin/go` должна быть рабочей командой `go`.

Минимально необходимая версия bootstrap compiler зависит от версии Go, которую вы собираете:

- Go <= 1.4 — C toolchain;
- 1.5 <= Go <= 1.19 — Go 1.4 compiler;
- 1.20 <= Go <= 1.21 — Go 1.17 compiler;
- 1.22 <= Go <= 1.23 — Go 1.20 compiler;
- далее Go `1.N` требует Go `1.M`, где `M = N - 2`, округлённое вниз до чётного числа. Например, Go 1.24 и 1.25 требуют Go 1.22.

Bootstrap toolchain можно получить четырьмя способами:

1. скачать недавний binary release Go;
2. cross-compile toolchain на системе с уже работающим Go;
3. использовать `gccgo`;
4. собрать toolchain из Go 1.4 — последнего релиза Go, compiler которого был написан на C.

### Bootstrap toolchain из binary release

Используйте [страницу загрузок Go](https://go.dev/dl/) либо другой packaged Go distribution, удовлетворяющий минимальному требованию к версии.

### Bootstrap toolchain из cross-compiled source

Для систем, которые Go 1.4 не поддерживал, например `linux/ppc64le`, bootstrap toolchain можно cross-compile на другой машине с рабочей Go installation. Для этого используется `bootstrap.bash`.

Например:

```bash
GOOS=linux GOARCH=ppc64 ./bootstrap.bash
```

`bootstrap.bash` cross-compile'ит toolchain для указанной комбинации `GOOS/GOARCH` и сохраняет полученное дерево в:

```text
../../go-${GOOS}-${GOARCH}-bootstrap
```

Это дерево можно скопировать на машину соответствующего target type и использовать как `GOROOT_BOOTSTRAP` для локальной сборки.

### Bootstrap toolchain с помощью gccgo

При использовании `gccgo` необходимо сделать так, чтобы `$GOROOT_BOOTSTRAP/bin/go` указывал на `go` tool из `gccgo 5`.

Например, для Ubuntu Vivid:

```bash
sudo apt-get install gccgo-5
sudo update-alternatives --set go /usr/bin/go-5
GOROOT_BOOTSTRAP=/usr ./make.bash
```

### Bootstrap toolchain из C source code

Чтобы собрать bootstrap toolchain из исходного кода на C, используйте либо Git branch `release-branch.go1.4`, либо архив [go1.4-bootstrap-20171003.tar.gz](https://dl.google.com/go/go1.4-bootstrap-20171003.tar.gz). В нём находится исходный код Go 1.4 и накопленные исправления, позволяющие tools продолжать работать на более новых операционных системах.

Go 1.4 был последним distribution, где toolchain был написан на C.

После распаковки Go 1.4:

1. перейдите в подкаталог `src`;
2. установите `CGO_ENABLED=0`;
3. выполните `make.bash`, а в Windows — `make.bat`.

После распаковки Go 1.4 в `GOROOT_BOOTSTRAP` этот clone должен оставаться на branch `release-branch.go1.4`. Не используйте этот же clone позднее на этапе получения текущего repository: bootstrap toolchain Go 1.4 должен иметь возможность обходить исходники Go 1.4, наличие которых он предполагает под этим repository root.

Go 1.4 работает не на всех системах, которые поддерживаются более новыми версиями Go. В частности, Go 1.4 не поддерживает современные версии macOS. На таких системах bootstrap toolchain необходимо получить одним из других способов.

## Установите Git, если он ещё не установлен

Для дальнейших шагов необходим Git. Перед продолжением убедитесь, что команда `git` доступна.

Если Git не установлен, воспользуйтесь официальной [страницей загрузки Git](https://git-scm.com/downloads).

## Необязательно: установите C compiler

Чтобы собрать Go installation с поддержкой `cgo`, позволяющей Go programs импортировать C libraries, необходим C compiler, например `gcc` или `clang`. Установите его стандартным для вашей операционной системы способом.

Чтобы собрать Go без `cgo`, перед запуском `all.bash` или `make.bash` задайте:

```bash
export CGO_ENABLED=0
```

## Получите repository

Перейдите в каталог, где планируется установить Go, и убедитесь, что каталога `goroot` ещё нет. Затем clone'ируйте repository и checkout'ните release tag или release branch нужной версии:

```bash
git clone https://go.googlesource.com/go goroot
cd goroot
git checkout <tag>
```

`<tag>` — version string релиза.

Go будет установлен непосредственно в каталог checkout. Например, если repository расположен в `$HOME/goroot`, executables будут находиться в `$HOME/goroot/bin`.

Каталог может называться произвольно, однако checkout в `$HOME/go` будет конфликтовать с default location `$GOPATH`.

Если bootstrap binaries также собирались из исходников Go 1.4, на этом этапе всё равно необходимо выполнить новый `git clone`: repository Go 1.4 и repository текущей версии должны оставаться раздельными.

## Необязательно: переключитесь на master branch

Если вы планируете изменять исходный код Go и отправлять изменения в проект, перейдите с release tag на development branch:

```bash
git checkout master
```

Если вы только собираете release, этот шаг не требуется.

## Установите Go

Перейдите в `src` и запустите сборку:

```bash
cd src
./make.bash
```

В Windows используйте:

```text
make.bat
```

При успешной сборке финальный output будет похож на:

```text
---
Installed Go for linux/amd64 in /home/you/go.
Installed commands in /home/you/go/bin.
*** You need to add /home/you/go/bin to your $PATH. ***
```

Конкретные значения последних строк зависят от OS, архитектуры и root directory installation.

Для дополнительных способов управления сборкой см. [[#Необязательные переменные окружения]]. Можно также запустить `all.bash` (или `all.bat`), чтобы выполнить важные tests Go. Это занимает больше времени, чем простая сборка через `make.bash`.

## Проверка installation

Проверьте установку простой программой.

Создайте `hello.go`:

```go
package main

import "fmt"

func main() {
	fmt.Printf("hello, world\n")
}
```

Запустите:

```text
$ go run hello.go
hello, world
```

Если выводится `hello, world`, Go установлен корректно.

## Настройте рабочее окружение

После сборки остаётся настроить рабочее окружение Go. Основные инструкции приведены в [[code|Как писать Go-код]]. Этот документ описывает обязательную базовую настройку и использование Go tools.

## Установите дополнительные tools

Исходники ряда дополнительных Go tools, включая [`gopls`](https://pkg.go.dev/golang.org/x/tools/gopls), находятся в repository `golang.org/x/tools`.

Например, установить `gopls` можно командой:

```bash
go install golang.org/x/tools/gopls@latest
```

## Ресурсы сообщества

На официальной [странице помощи](https://go.dev/help/) перечислены ресурсы сообщества, где активные разработчики помогают с проблемами установки и разработки.

Mailing list [golang-checkins](https://groups.google.com/group/golang-checkins) получает сообщение с краткой информацией о каждом check-in в Go repository.

Bugs можно сообщать через [Go issue tracker](https://go.dev/issue/new).

## Обновление до новых releases

Новые releases объявляются в mailing list [golang-announce](https://groups.google.com/group/golang-announce). В каждом announcement указывается актуальный release tag.

Для обновления существующего source tree:

```bash
cd go/src
git fetch
git checkout <tag>
./all.bash
```

`<tag>` — version string нужного release.

## Необязательные переменные окружения

Go tools можно настраивать через environment variables. Для самой сборки ни одна из них не является обязательной, однако ими можно переопределять default values.

Если задать эти переменные при выполнении `make.bash`, они станут defaults для только что собранных tools. При использовании tools defaults можно переопределять для конкретной сборки. Подробнее см. [Go command documentation: Environment variables](https://pkg.go.dev/cmd/go#hdr-Environment_variables).

### `GOROOT`

Root Go tree, часто `$HOME/go1.X`.

Значение встраивается в tree при compilation и по умолчанию является parent directory каталога, из которого выполнялся `all.bash`. Обычно задавать `GOROOT` вручную не требуется, кроме случаев, когда необходимо переключаться между несколькими локальными copies repository.

### `GOOS` и `GOARCH`

`GOOS` определяет target operating system, а `GOARCH` — target compilation architecture.

`GOOS` по умолчанию берётся из `runtime.GOOS` bootstrap toolchain. `GOARCH` по умолчанию соответствует `GOHOSTARCH`.

В upstream для этой версии перечислены следующие значения `GOOS`:

`android`, `darwin`, `dragonfly`, `freebsd`, `illumos`, `ios`, `js`, `linux`, `netbsd`, `openbsd`, `plan9`, `solaris`, `wasip1`, `windows`.

Возможные `GOARCH`:

- `amd64` — 64-bit x86;
- `386` — 32-bit x86;
- `arm` — 32-bit ARM;
- `arm64` — 64-bit ARM;
- `ppc64le`, `ppc64` — PowerPC 64-bit little-/big-endian;
- `mips64le`, `mips64` — MIPS 64-bit little-/big-endian;
- `mipsle`, `mips` — MIPS 32-bit little-/big-endian;
- `s390x` — IBM System z 64-bit big-endian;
- `wasm` — WebAssembly 32-bit.

Валидные комбинации `GOOS/GOARCH`, перечисленные upstream:

| GOOS | GOARCH |
| --- | --- |
| `aix` | `ppc64` |
| `android` | `386` |
| `android` | `amd64` |
| `android` | `arm` |
| `android` | `arm64` |
| `darwin` | `amd64` |
| `darwin` | `arm64` |
| `dragonfly` | `amd64` |
| `freebsd` | `386` |
| `freebsd` | `amd64` |
| `freebsd` | `arm` |
| `illumos` | `amd64` |
| `ios` | `arm64` |
| `js` | `wasm` |
| `linux` | `386` |
| `linux` | `amd64` |
| `linux` | `arm` |
| `linux` | `arm64` |
| `linux` | `loong64` |
| `linux` | `mips` |
| `linux` | `mipsle` |
| `linux` | `mips64` |
| `linux` | `mips64le` |
| `linux` | `ppc64` |
| `linux` | `ppc64le` |
| `linux` | `riscv64` |
| `linux` | `s390x` |
| `netbsd` | `386` |
| `netbsd` | `amd64` |
| `netbsd` | `arm` |
| `openbsd` | `386` |
| `openbsd` | `amd64` |
| `openbsd` | `arm` |
| `openbsd` | `arm64` |
| `plan9` | `386` |
| `plan9` | `amd64` |
| `plan9` | `arm` |
| `solaris` | `amd64` |
| `wasip1` | `wasm` |
| `windows` | `386` |
| `windows` | `amd64` |
| `windows` | `arm` |
| `windows` | `arm64` |

### `GOHOSTARCH`

Host compilation architecture. По умолчанию соответствует архитектуре локальной системы.

Допустимы те же значения, что и для `GOARCH`, но они должны быть совместимы с локальной системой. Например, не следует устанавливать `GOHOSTARCH=arm` на x86 host.

### `GO386`

Только для `386`; default — `sse2`.

Определяет реализацию floating-point computations в `gc`:

- `GO386=softfloat` — software floating-point; должен работать на всех x86 chips начиная с Pentium MMX;
- `GO386=sse2` — SSE2 floating-point; производительнее, но требует Pentium 4, Opteron, Athlon 64 или более новый CPU.

### `GOARM`

Только для `arm`. Если сборка выполняется на target processor, значение определяется автоматически; иначе default — `7`.

Задаёт ARM floating-point coprocessor architecture version, на которую ориентируется runtime:

- `GOARM=5` — software floating point для CPU без VFP coprocessor;
- `GOARM=6` — VFPv1; в upstream это указано как default при cross-compilation; обычно ARM11 или новее, VFPv2+ также поддерживается;
- `GOARM=7` — VFPv3, обычно Cortex-A cores.

Если есть сомнения, оставьте переменную unset и при необходимости скорректируйте после первого запуска Go executable. Подробнее см. [GoARM](https://go.dev/wiki/GoArm).

### `GOARM64`

Только для `arm64`; default — `v8.0`.

Определяет ARM64 architecture version для compilation. Допустимые варианты описаны на [MinimumRequirements — arm64](https://go.dev/wiki/MinimumRequirements#arm64).

### `GOAMD64`

Только для `amd64`; default — `v1`.

Определяет microarchitecture level:

- `v1`;
- `v2`;
- `v3`;
- `v4`.

Подробнее см. [MinimumRequirements — amd64](https://go.dev/wiki/MinimumRequirements#amd64).

### `GOMIPS` и `GOMIPS64`

`GOMIPS` применяется к `mips`/`mipsle`, `GOMIPS64` — к `mips64`/`mips64le`.

- `hardfloat` — использовать floating-point instructions; default;
- `softfloat` — использовать software floating point.

### `GOPPC64`

Только для `ppc64` и `ppc64le`. Определяет target processor level / ISA version. Default — `power8`.

- `GOPPC64=power8` — генерировать ISA v2.07 instructions;
- `GOPPC64=power9` — генерировать ISA v3.00 instructions.

### `GORISCV64`

Только для `riscv64`. Определяет RISC-V user-mode application profile. Default — `rva20u64`.

- `GORISCV64=rva20u64` — использовать только RISC-V extensions, обязательные в [RVA20U64](https://github.com/riscv/riscv-profiles/blob/main/src/profiles.adoc#51-rva20u64-profile);
- `GORISCV64=rva22u64` — только extensions, обязательные в [RVA22U64](https://github.com/riscv/riscv-profiles/blob/main/src/profiles.adoc#rva22u64-profile);
- `GORISCV64=rva23u64` — только extensions, обязательные в [RVA23U64](https://github.com/riscv/riscv-profiles/blob/main/src/rva23-profile.adoc#rva23u64-profile).

### `GOWASM`

Только для `wasm`.

Comma-separated list [experimental WebAssembly features](https://github.com/WebAssembly/proposals), которые разрешено использовать compiled WebAssembly binary. По умолчанию experimental features не включены.

- `GOWASM=satconv` — генерировать saturating/non-trapping float-to-int conversions;
- `GOWASM=signext` — генерировать sign-extension operators.

`GOARCH` и `GOOS` определяют target environment, а не host environment, на котором выполняется compiler. Фактически Go build всегда имеет модель cross-compilation.

Под architecture здесь понимается тип binaries, которые способен выполнить target environment. Например, x86-64 machine с 32-bit-only operating system должна использовать `GOARCH=386`, а не `GOARCH=amd64`.

Для обычной сборки, установки и разработки Go tree ни одну из перечисленных переменных задавать не требуется.
