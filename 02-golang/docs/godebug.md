---
title: "Go, backward compatibility и GODEBUG"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/go"
upstream_path: "doc/godebug.md"
upstream_ref: "go1.27.1"
translation_status: "translated"
---

# Go, backward compatibility и `GODEBUG`

Backward compatibility — одно из основных свойств Go, но полная совместимость не всегда возможна: исправление buggy/insecure behavior или включение новой protocol feature иногда ломает программы, которые зависели от старого поведения.

`GODEBUG` позволяет новому toolchain временно вернуть отдельные historical semantics для конкретной программы.

## Формат

Setting — pair:

```text
key=value
```

Environment variable содержит comma-separated list:

```bash
GODEBUG=http2client=0,http2server=0 ./service
```

Unknown environment settings игнорируются. Defaults также можно задавать compile-time через `go.mod`/`go.work` и `//go:debug`.

Compatibility settings обычно поддерживаются минимум два года (четыре Go releases), некоторые — существенно дольше или indefinitely.

Когда возможно, non-default behavior имеет runtime metric:

```text
/godebug/non-default-behavior/<name>:events
```

Она показывает, сколько раз программа реально воспользовалась compatibility behavior.

## Откуда берётся default

Если key отсутствует в environment `GODEBUG`, effective value формируется из:

1. defaults текущего Go toolchain;
2. корректировок по Go version main module/workspace;
3. `godebug` directives;
4. `//go:debug` directives main package.

Например, Go 1.21 изменил `panic(nil)` behavior (`panicnil=0`). Если module declares older Go 1.20, newer toolchain старается использовать compatibility default `panicnil=1`.

Security backports являются исключением: новый secure behavior может применяться независимо от declared old Go version.

Для `go` versions старше 1.20 compatibility baseline фактически начинается с Go 1.20, потому что compile-time default selection появился в Go 1.21.

## `godebug` в `go.mod` / `go.work`

Начиная с Go 1.23:

```text
godebug (
    default=go1.21
    panicnil=1
    asynctimerchan=0
)
```

`default=go1.21` выбирает baseline unspecified settings отдельно от language version.

Правила:

- учитывается только main module `go.mod`;
- directives dependencies игнорируются;
- в workspace mode используются `godebug` из `go.work`, а module-level directives игнорируются;
- unknown setting — error;
- toolchains до Go 1.23 вообще не понимают `godebug` directive.

## `//go:debug`

Начиная с Go 1.21 main package может точечно переопределить default до `package` declaration:

```go
//go:debug default=go1.21
//go:debug panicnil=1
//go:debug asynctimerchan=0

package main
```

Duplicate directive одного key или unknown setting invalid для modern toolchain.

В `*_test.go` directives применяются к generated test main. В остальных inappropriate contexts они игнорируются compiler, а `go vet` сообщает о misplaced directive.

Показать compile-time defaults:

```bash
go list -f '{{.DefaultGODEBUG}}' my/main/package
```

## History compatibility settings

Ниже перечислены compatibility settings, зафиксированные в source Go 1.27.1.

### Go 1.27

Удалены settings, срок compatibility которых закончился:

- `gotypesalias`;
- `tlsunsafeekm`;
- `tlsrsakex`;
- `tls3des`;
- `tls10server`;
- `x509keypairleaf`;
- `asynctimerchan`.

Добавлены/изменены:

- `htmlmetacontenturlescape` / secure meta-content URL escaping behavior; secure default был backported в supported releases;
- `tracebacklabels=1` становится default: runtime tracebacks включают goroutine labels; opt-out сохраняется, поскольку labels могут содержать sensitive data;
- `x509sslcertoverrideplatform=1`: на Windows/Darwin при `SSL_CERT_FILE`/`SSL_CERT_DIR` roots загружаются с disk вместо platform store; `=0` возвращает старое behavior; planned removal Go 1.31;
- `fips140ems=0` может отключить enforcement Extended Master Secret в FIPS 140-3 mode; planned removal Go 1.31.

### Go 1.26

- `httpcookiemaxnum=3000`: limit cookies при parsing HTTP headers; `0` отключает limit; введён как DoS protection и backported;
- `urlmaxqueryparams=10000`: limit URL query parameters; `0` отключает;
- `urlstrictcolons=1`: rejects malformed hostnames с illegal colon usage;
- `tlssecpmlkem`: управление дополнительными post-quantum TLS key exchange mechanisms;
- `tracebacklabels`: inclusion labels runtime/pprof в goroutine status/tracebacks;
- `cryptocustomrand`: controls semantics custom `io.Reader` в crypto APIs.

### Go 1.25

- `decoratemappings=1`: Linux runtime annotations anonymous mappings (`[anon: Go: ...]`);
- `embedfollowsymlinks=0`: go command по умолчанию не follows symlinks при `embed`;
- `containermaxprocs=1`: Linux runtime учитывает cgroup CPU limit при default `GOMAXPROCS`;
- `updatemaxprocs=1`: periodic update `GOMAXPROCS` при CPU affinity/cgroup changes;
- `tlssha1=1` может вернуть pre-1.25 SHA-1 TLS 1.2 signatures behavior;
- `x509sha256skid=0` возвращает SHA-1 SubjectKeyId generation;
- `allowmultiplevcs=1` возвращает VCS stamping при multiple VCS detection.

### Go 1.24

- `fips140=off|on|only`: режим Go Cryptographic Module FIPS 140-3;
- `randseednop`: Go 1.24 делает global `math/rand.Seed` no-op по default;
- `multipathtcp`: expanded modes для MPTCP dialers/listeners;
- `x509rsacrt`: controls validation/use CRT parameters в parsed PKCS#1 RSA private keys;
- ряд compatibility/security settings HTTP/TLS/X.509 согласно release history.

`fips140` фиксируется при process startup и не может динамически измениться последующим изменением environment.

### Go 1.23

Ключевые changes:

- `asynctimerchan` управлял новым synchronous behavior timer channels (`time.Timer`/`Ticker`); setting удалён в Go 1.27;
- `x509keypairleaf` контролировал population parsed leaf certificate; удалён в Go 1.27;
- `tls3des` контролировал 3DES cipher availability; удалён в Go 1.27;
- `httpservecontentkeepheaders` возвращает historical header behavior при errors `ServeContent`;
- другие release-specific TLS/X.509/HTTP compatibility switches.

### Go 1.22

Среди settings:

- `tlsmaxrsasize`: limit RSA key size в TLS handshake, secure default был backported;
- `gotypesalias`: transitional behavior type aliases;
- `tlsunsafeekm`, `tlsrsakex`, `tls10server`: TLS compatibility switches, позднее удалённые;
- `x509usepolicies`: controls newer certificate policy representation.

### Go 1.21

- `panicnil`: controls new runtime error semantics для `panic(nil)`;
- html/template JavaScript/template compatibility settings;
- MPTCP behavior via `multipathtcp`;
- другие targeted compatibility switches, многие сохраняются согласно documented lifecycle.

### Go 1.20

- `tarinsecurepath` и `zipinsecurepath`: handling insecure archive paths;
- `installgoroot`: historical use/install precompiled `.a` files under GOROOT;
- другие behavior toggles для compatibility.

### Go 1.19

- `execerrdot`: protects executable lookup от implicit current-directory resolution.

### Go 1.18

- `x509sha1`: временно возвращал SHA-1 X.509 acceptance; удалён в Go 1.24.

### Go 1.10

Build/test cache diagnostics:

- `gocacheverify`;
- `gocachehash`;
- `gocachetest`.

Для них removal не планируется.

### Go 1.6

HTTP/2:

- `http2client`;
- `http2server`;
- `http2debug`.

Сохраняются long-term.

### Go 1.5

- `netdns`: selection/diagnostics Go DNS resolver.

Removal не планируется.

## Runtime/debug settings вне compatibility history

Не все `GODEBUG` keys относятся к compatibility. Runtime и packages определяют diagnostic/debug keys, например:

```bash
GODEBUG=gctrace=1
GODEBUG=schedtrace=1000
GODEBUG=inittrace=1
GODEBUG=cpu.all=off
```

Для полного набора runtime-specific environment variables используйте `runtime` package documentation текущей Go version. Этот document отвечает именно за compatibility-oriented settings и их lifecycle.
