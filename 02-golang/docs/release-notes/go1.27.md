---
title: "Go 1.27 Release Notes"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/go1.27.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Go 1.27 Release Notes

## Введение в Go 1.27 {#introduction}

Go 1.27 вышел в [августе 2026 года](https://go.dev/doc/devel/release#go1.27.0), через шесть месяцев после [Go 1.26](https://go.dev/doc/go1.26).

Большинство изменений относится к implementation toolchain, runtime и libraries.

Как всегда, release сохраняет [Go 1 compatibility promise](https://go.dev/doc/go1compat). Ожидается, что почти все существующие Go programs продолжат compile'иться и выполняться как раньше.

## Изменения языка {#language}

### Generic methods

Go 1.27 теперь поддерживает [generic methods](https://go.dev/issue/77273): [method declaration](https://go.dev/ref/spec#Method_declarations) может объявлять собственные [type parameters](https://go.dev/ref/spec#Type_parameter_declarations).

Это позволяет размещать generic functions в namespace конкретного data type, тогда как раньше такую function приходилось объявлять на уровне всего package.

Например, `math/rand/v2` теперь имеет generic method:

```go
(*Rand) N[Int intType](Int) Int
```

тогда как раньше был только generic function:

```go
N[Int intType](Int) Int
```

Methods interfaces не могут объявлять type parameters, и interface methods не могут быть implemented generic methods.

### Struct literal field selectors

Key в [struct literal](https://go.dev/ref/spec#Composite_literals) теперь может быть любым valid [field selector](https://go.dev/issue/9859) для struct type, а не только top-level field name struct.

### Function type inference

Function type inference [расширен](https://go.dev/issue/77245) и теперь применяется во всех contexts, где generic function [assign](https://go.dev/ref/spec#Assignability)'ится variable matching function type либо converted к такому function type.

## Tools {#tools}

### Response files

Parsing response files вида `@file` теперь поддерживается tools:

- `compile`;
- `link`;
- `asm`;
- `cgo`;
- `cover`;
- `pack`.

Response file содержит whitespace-separated arguments и поддерживает single/double quoted strings, escape sequences и backslash-newline continuation. Format совместим с GCC response files.

### Go command {#go-command}

Команда `go` больше не поддерживает version control system `bzr` и не может напрямую получать modules с `bzr` servers.

#### `GODEBUG`

Начиная с Go 1.27 команда `go` распознаёт удалённые `GODEBUG` settings, например `asynctimerchan`, если они встречаются в `go.mod` (`godebug`) или `.go` source (`//go:debug`).

Setting принимается, если указан final default value, установленный до его удаления. Старое value приводит к failure. Это позволяет существующим programs с explicit default продолжать build/run после удаления switch.

#### `go test`

`go test` теперь по default запускает vet check `stdversion`, который report'ит standard-library symbols, слишком новые для Go version current file, определяемой `go` directive и build tags.

`go test -json` теперь может добавлять к `"Action":"output"` optional field `"OutputType"`. Сейчас values включают `error`, `error-continue`, `frame`.

#### `go doc`

Поддерживается syntax:

```text
package@version
```

например:

```bash
go doc example.com/pkg@v1.2.3
```

Добавлен `-ex` для listing executable examples package/symbol. При передаче example name, например `go doc bytes.ExampleBuffer`, выводится source example вместе с comments.

#### `go fix`

Добавлены modernizers:

- `atomictypes`;
- `embedlit`;
- `slicesbackward`;
- `unsafefuncs`.

Analyzer `fmtappendf` удалён из-за stylistic concerns. Analyzer `waitgroup` переименован в `waitgroupgo`.

#### `go mod tidy`

Для modules с `go 1.27` или newer `go mod tidy` автоматически объединяет duplicate `require` blocks, оставляя максимум два:

1. direct dependencies;
2. indirect dependencies.

Existing comment blocks сохраняются. Если comment block относится к mixed set direct/indirect dependencies, он прикрепляется к новому direct dependency block.

### Gofmt {#gofmt}

Исправлена logic column alignment в `gofmt` и `go/format`. Старый algorithm мог давать слегка разный result на разных CPU architectures. После Go 1.27 возможны minor whitespace diffs в небольшом числе уже formatted files.

### Vet {#vet}

Analyzer `printf` теперь report'ит calls вроде:

```go
fmt.Errorf("...: %w", p)
```

если `%w` operand `p` имеет type `*E`, а сам `E` implements `error`. Такое wrapping обычно latent bug для type assertions и `errors.Is`.

### Trace

`go tool trace -http=:6060` теперь слушает только localhost. Чтобы слушать все addresses, нужно явно указать:

```bash
go tool trace -http=0.0.0.0:6060
```

## Runtime {#runtime}

Tracebacks modules с Go 1.27+ теперь включают `runtime/pprof` goroutine labels в header line. Отключение:

```text
GODEBUG=tracebacklabels=0
```

Opt-out предполагается сохранять indefinitely из-за possible sensitive labels.

`asynctimerchan` permanently removed. Channels package `time` всегда unbuffered/synchronous независимо от `GODEBUG`.

### Faster memory allocation

Compiler генерирует calls size-specialized allocation routines. Для некоторых small allocations `<80 bytes` cost снижается до 30%; ожидаемый overall improvement allocation-heavy applications — около 1%. Binary size растёт примерно на 60 KB.

Temporary opt-out:

```text
GOEXPERIMENT=nosizespecializedmalloc
```

Планируется удалить в Go 1.28.

### Goroutine leak profile {#goroutineleak-profiles}

Profile type `goroutineleak`, experimental в Go 1.26, теперь generally available через `runtime/pprof` и `/debug/pprof/goroutineleak`.

Leaked goroutine — goroutine, blocked на concurrency primitive, который уже невозможно unblock'ить. Runtime использует GC reachability: если primitive unreachable из runnable goroutines и goroutines, которые они могли бы unblock'ить, blocked goroutine считается leaked.

Mechanism не может обнаружить все leaks, особенно если primitive reachable через globals или locals runnable goroutines.

`goroutineleakprofile` GOEXPERIMENT удалён.

## Compiler {#compiler}

Compiler теперь resolves relative filename в `//line`/`/*line*/` directives относительно directory containing source file, как `go/scanner`. Absolute filenames unaffected.

Compiler также генерирует более простые names function literals/closures. Name теперь стабильно независимо от inlining, а multiple instances одной literal могут share compiled code.

Semantics Go code не меняются. Tests, зависящие от symbol names, могут потребовать update. Programs, некорректно сравнивающие function code pointers, могут чаще видеть равные pointers у closures с разными captured data.

## Linker {#linker}

При targeting macOS linker принимает options:

```text
-macos
-macsdk
```

Они задают OS/SDK versions в `LC_BUILD_VERSION`.

Defaults: oldest supported macOS — `13.0.0`; recent SDK — `26.2.0`.

## Standard library {#library}

### Новые packages `encoding/json/v2` и `encoding/json/jsontext` {#jsonv2}

Go 1.27 добавляет `encoding/json/v2` — major revision `encoding/json` — и low-level `encoding/json/jsontext`.

V2 API включает `Marshal`, `MarshalWrite`, `MarshalEncode`, `Unmarshal`, `UnmarshalRead`, `UnmarshalDecode`, принимающие configurable `Options`.

`jsontext.Encoder`/`Decoder` работают с JSON как sequence `Token`/`Value` и поддерживают state machine valid JSON.

V2 default stricter: invalid UTF-8 и duplicate object member names reject'ятся.

Original `encoding/json` теперь internally использует v2 implementation, но сохраняет v1 behavior; exact error texts могут меняться. V1 API останется supported, migration optional. См. [[../jsonv2-migration|migration guide]].

Marshal performance примерно parity с прежней implementation; unmarshal существенно быстрее.

Temporary opt-out:

```text
GOEXPERIMENT=nojsonv2
```

Experiment changes: removed `format`/`unknown` tags, `DiscardUnknownMembers`, `SkipFunc`; `inline` renamed to `embed`; изменены semantics `string`, `MatchCaseInsensitiveNames` и numeric `jsontext.Token` accessors.

### Новый package `crypto/mldsa` {#crypto_mldsa}

Новый `crypto/mldsa` implements ML-DSA (FIPS 204).

`crypto/x509` поддерживает ML-DSA private/public keys и signatures. `crypto/tls` поддерживает ML-DSA signatures в TLS 1.3 через `MLDSA44`, `MLDSA65`, `MLDSA87`.

### Новый package `uuid` {#uuid}

Новый `uuid` package генерирует и parses UUIDs.

### Experimental `simd` {#simd}

`GOEXPERIMENT=simd` включает portable, vector-size-agnostic package `simd`. Он доступен на всех architectures и предоставляет vectors unspecified width, например `Int8s`, `Float32s`, и scalable subset operations.

### Experimental `simd/archsimd` {#archsimd}

Architecture-specific SIMD experiment, начатый в Go 1.26, расширен: revised amd64 API, arm64 Neon 128-bit SIMD и WebAssembly 128-bit SIMD.

Supported widths: 128-bit на wasm/arm64/amd64; 256/512-bit на некоторых amd64 processors. API пока нестабилен и непереносим.

### Minor changes to the library {#minor_library_changes}

#### `bytes`

Новый `CutLast` разрезает `[]byte` вокруг последнего occurrence separator и упрощает common `LastIndex` usages.

#### `compress/flate`

Compression speed improved. Encoded output может byte-for-byte отличаться от Go 1.26 из-за новой encoder implementation. Это также затрагивает output `archive/zip`, `compress/gzip`, `compress/zlib`, `image/png`.

#### `crypto`

Добавлен `Hash` value `MLDSAMu` для External μ ML-DSA signing.

#### `crypto/ecdsa`

`PrivateKey.Sign` проверяет корректность hash length при non-nil `SignerOpts`.

#### `crypto/tls`

- `QUICConfig.ClientHelloInfoConn` задаёт `net.Conn` для `ClientHelloInfo.Conn` во время QUIC server handshake.
- Поддержан `MLKEM1024` key exchange.
- `Config.Rand` deprecated; для deterministic tests используйте `testing/cryptotest.SetGlobalRandom`.
- PQ hybrid exchanges можно explicitly включать через `CurvePreferences` независимо от `tlsmlkem=0`/`tlssecpmlkem=0`.
- `ConnectionState.LocalCertificate` содержит certificate chain, presented peer.
- Permanently removed: `tlsunsafeekm`, `tlsrsakex`, `tls3des`, `tls10server`, `x509keypairleaf`.
- `tlskyber` фактически был удалён ещё в Go 1.24.

#### `crypto/x509`

- `pkix.Name` parsing поддерживает более широкий range `AttributeTypeAndValue.Value`; unknown types сохраняются как `asn1.RawValue`.
- Добавлены `RawSignatureAlgorithm` в `Certificate`, `CertificateRequest`, `RevocationList`.
- `SystemCertPool` учитывает `SSL_CERT_FILE`/`SSL_CERT_DIR` на Windows/Darwin; при их наличии используется native Go verifier. Opt-out: `GODEBUG=x509sslcertoverrideplatform=0`.

#### `crypto/x509/pkix`

`RDNSequence.String`/`Name.String` renders string-typed unknown-OID values как strings, а не всегда DER hex.

#### `database/sql`

Новая `ConvertAssign` предоставляет drivers conversions, используемые `Rows.Scan`.

#### `database/sql/driver`

Новый interface `RowsColumnScanner` позволяет drivers scan directly в caller destinations.

#### `go/constant`

Новая `StringLen` получает length string `Value`, не материализуя его целиком.

#### `go/scanner`

Новый `Scanner.End` возвращает end position token.

#### `go/token`

`File` получил method `String`.

#### `go/types`

Новый `Hasher` implements `maphash.Hasher` для `Type` с equivalence `Identical`; `HasherIgnoreTags` — для `IdenticalIgnoreTags`.

`gotypesalias` permanently removed. `go/types` всегда создаёт `Alias` node для alias declaration.

#### `hash/maphash`

Новый interface `Hasher` задаёт contract hash functions для future hash-based structures; `ComparableHasher` — convenience implementation для comparable types с equality `==`.

#### `math/big`

`Int.Divide` вычисляет quotient/remainder с rounding modes `Trunc`, `Floor`, `Round`, `Ceil`.

#### `math/rand/v2` {#rand}

`Rand` получил generic method `N`, соответствующий top-level generic function `N`.

#### `net`

Read methods `UnixConn` теперь возвращают `io.EOF` напрямую, а не wrapping в `net.OpError`, если underlying read вернул EOF.

#### `net/http`

- `Transport`/`Server` поддерживают TLS ALPN negotiation на user-provided `net.Conn`, реализующем `ConnectionState() tls.ConnectionState`.
- HTTP/2 server принимает client priority signals RFC 9218; `Server.DisableClientPriority` возвращает round-robin behavior.
- HTTP/1 `Response.Body.Close` drains unread body до conservative limit для connection reuse.
- `Server.MaxHeaderValueCount` задаёт maximum header values; default — `DefaultMaxHeaderValueCount`.

#### `net/http/httptest`

Новая `NewTestServer` создаёт server на in-memory fake network для `testing/synctest`.

#### `net/url`

Новые `URL.Clone` и `Values.Clone` создают deep copies.

#### `runtime/secret`

Goroutines, созданные внутри secret mode, сами выполняются в secret mode.

#### `strings`

Новый `CutLast` разрезает string вокруг последнего occurrence separator.

#### `syscall`

На Plan 9 type `Errno` теперь defined и implements `error`, чтобы portable code с `syscall.Errno` build'ился без build constraints. System calls Plan 9 всё равно возвращают `ErrorString`.

#### `testing/synctest`

Новый `Sleep` объединяет `time.Sleep` и `synctest.Wait`.

#### `unicode`

Unicode support обновлён с Unicode 15 до **Unicode 17**.

## Ports {#ports}

### Darwin {#darwin}

Go 1.27 требует **macOS 13 Ventura или newer**. Support previous versions discontinued.

### PowerPC {#ppc64}

Big-endian 64-bit PowerPC Linux (`GOOS=linux GOARCH=ppc64`) теперь использует ELFv2 system ABI.

ELFv2 требует Linux kernel 3.13+; RHEL7 backported support в kernel 3.10.

Теперь supported:

- cgo;
- PIE;
- external linking.

Для них нужен ELFv2-compatible runtime, libc и libraries. Pure-Go programs без cgo всё ещё по default получают static internally-linked binaries. Для static pure-Go build при cgo options:

```bash
CGO_ENABLED=0 go build
```
