---
title: "Go, backward compatibility и GODEBUG"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/go"
upstream_path: "doc/godebug.md"
upstream_ref: "go1.27.1"
translation_status: "reviewed"
---

# Go, backward compatibility и `GODEBUG`

## Введение {#intro}

Акцент Go на backward compatibility — одна из ключевых сильных сторон языка. Однако бывают ситуации, когда полную compatibility сохранить невозможно.

Если code зависит от buggy behavior, включая insecure behavior, исправление bug сломает такой code. Новые features могут иметь похожие последствия: например, включение HTTP/2 в HTTP client сломало программы, подключавшиеся к servers с некорректными HTTP/2 implementations.

Подобные изменения неизбежны и [разрешены правилами совместимости Go 1](https://go.dev/doc/go1compat).

Тем не менее Go предоставляет механизм `GODEBUG`, уменьшающий влияние таких изменений на developers, которые компилируют старый code новыми toolchains.

`GODEBUG` setting — это pair `key=value`, управляющая execution определённых частей Go program.

Environment variable `GODEBUG` может содержать comma-separated list таких settings. Например:

```text
GODEBUG=http2client=0,http2server=0
```

В таком environment Go program по умолчанию отключит HTTP/2 и в HTTP client, и в HTTP server.

Unknown settings в environment variable `GODEBUG` игнорируются. Кроме того, default `GODEBUG` конкретной program можно задавать при build; это описано ниже.

Перед внесением изменения, разрешённого Go 1 compatibility rules, но способного сломать существующие programs, Go team сначала проектирует change так, чтобы продолжило работать как можно больше существующих programs.

Для оставшихся случаев обычно вводится новый `GODEBUG` setting, позволяющий отдельным programs opt back in в старое behavior. Setting может не добавляться, если это технически infeasible, но такие случаи должны быть крайне редкими.

Compatibility settings `GODEBUG` поддерживаются минимум два года, то есть четыре Go releases. Некоторые, например `http2client` и `http2server`, могут поддерживаться значительно дольше или даже indefinitely.

Когда возможно, каждому `GODEBUG` setting соответствует counter в [`runtime/metrics`](https://pkg.go.dev/runtime/metrics) с name:

```text
/godebug/non-default-behavior/<name>:events
```

Counter показывает, сколько раз behavior конкретной program изменилось из-за non-default value setting.

Например, при `GODEBUG=http2client=0` metric `/godebug/non-default-behavior/http2client:events` считает HTTP transports, настроенные program без HTTP/2 support.

## Default значения `GODEBUG` {#default}

Если setting отсутствует в environment variable, его value выводится из трёх sources:

1. defaults Go toolchain, которым program была собрана;
2. эти defaults корректируются под Go version, указанную в `go.mod`;
3. затем переопределяются explicit `//go:debug` lines в program.

Раздел [GODEBUG History](#history) содержит точные defaults для каждой Go toolchain version.

Например, Go 1.21 ввёл setting `panicnil`, управляющий допустимостью `panic(nil)`. Его default — `panicnil=0`, поэтому `panic(nil)` становится run-time error. `panicnil=1` возвращает behavior Go 1.20 и более ранних versions.

Когда новый toolchain компилирует work module или workspace, объявляющий более старую Go version, toolchain изменяет defaults так, чтобы как можно точнее соответствовать этой старой version.

Например, если Go 1.21 toolchain компилирует program, а `go.mod` work module или `go.work` workspace содержит `go 1.20`, program получает default `panicnil=1`, соответствующий Go 1.20, а не Go 1.21.

Исключение: `GODEBUG` settings, введённые security releases, применяют новое behavior ко всем versions.

Поскольку mechanism version-sensitive defaults появился только в Go 1.21, programs, указывающие Go versions старше Go 1.20, настраиваются под Go 1.20, а не под фактическую более старую version.

Начиная с Go 1.23 defaults можно переопределять в `go.mod` work module или `go.work` workspace через одну или несколько `godebug` lines:

```text
godebug (
    default=go1.21
    panicnil=1
    asynctimerchan=0
)
```

Special key `default` задаёт Go version, от которой берутся unspecified settings. Это позволяет настраивать `GODEBUG` defaults отдельно от Go language version module.

В example program запрашивает Go 1.21 semantics, затем старое pre-Go 1.21 behavior `panic(nil)` и новое Go 1.23 behavior `asynctimerchan=0`.

Для `godebug` directives учитывается только `go.mod` work module. Directives required dependency modules игнорируются.

Unknown setting в `godebug` — error. Toolchains старше Go 1.23 отвергают все `godebug` lines, поскольку вообще не понимают directive `godebug`.

При использовании workspace `godebug` directives из `go.mod` игнорируются, а settings читаются из `go.work`.

Defaults, заданные `go` и `godebug` lines, применяются ко всем main packages, которые строятся.

Для более fine-grained control начиная с Go 1.21 source files main package могут содержать `//go:debug` directives в начале file, перед `package` statement:

```go
//go:debug default=go1.21
//go:debug panicnil=1
//go:debug asynctimerchan=0

package main
```

Начиная с Go 1.21 `//go:debug` с unknown setting делает program invalid. Более одной `//go:debug` line для одного setting также invalid.

Старые toolchains полностью игнорируют `//go:debug` directives.

Посмотреть defaults, которые будут compiled в main package, можно командой:

```text
go list -f '{{.DefaultGODEBUG}}' my/main/package
```

Выводятся только отличия от base defaults текущего Go toolchain.

При testing package `//go:debug` lines из `*_test.go` считаются directives для test main package.

В любом другом context `//go:debug` lines игнорируются toolchain; `go vet` сообщает о misplaced directives.

## История `GODEBUG` {#history}

Этот раздел описывает `GODEBUG` settings, которые добавлялись и удалялись в major Go releases по причинам compatibility.

Packages или programs могут определять дополнительные settings для internal debugging. См. также [runtime environment variables](https://pkg.go.dev/runtime#hdr-Environment_Variables) и [build/test caching документацию команды go](https://go.dev/cmd/go#hdr-Build_and_test_caching).

### Go 1.27

Go 1.27 удалил следующие compatibility settings, как было запланировано в соответствующих предыдущих releases:

- `gotypesalias`;
- `tlsunsafeekm`;
- `tlsrsakex`;
- `tls3des`;
- `tls10server`;
- `x509keypairleaf`;
- `asynctimerchan`.

Go 1.27 добавил новый setting `htmlmetacontenturlescape`, управляющий escaping URLs в `url=` portion attribute `content` HTML `meta` tags в `html/template`.

Default включает escaping URLs. Setting `htmlmetacontentescape=0`, как указано в upstream document, отключает это behavior. Для предотвращения content injection attacks этот setting и secure default были backported в Go 1.25.8 и Go 1.26.1.

Go 1.27 изменил default `tracebacklabels`, добавленного в Go 1.26, на `1`.

Этот opt-out предполагается поддерживать indefinitely, поскольку goroutine labels могут содержать sensitive information, которую не следует раскрывать в tracebacks.

Go 1.27 добавил `x509sslcertoverrideplatform`, управляющий тем, будет ли `crypto/x509` загружать roots с disk в Windows и Darwin, когда установлены `SSL_CERT_FILE` или `SSL_CERT_DIR`.

- default `x509sslcertoverrideplatform=1` — roots загружаются с disk при наличии этих environment variables;
- `x509sslcertoverrideplatform=0` — platform certificate store используется вместо environment variables.

Setting планируется удалить в Go 1.31.

Go 1.27 добавил `fips140ems`; при value `0` он отключает enforcement Extended Master Secret в FIPS 140-3 mode. Default behavior не изменился.

Setting был backported в Go 1.26.6 и Go 1.25.13 и планируется к удалению в Go 1.31.

### Go 1.26

Go 1.26 добавил `httpcookiemaxnum`, управляющий maximum number cookies, которые `net/http` принимает при parsing HTTP headers.

Если cookie count превышает limit, parsing завершается раньше. Default:

```text
httpcookiemaxnum=3000
```

`httpcookiemaxnum=0` отключает limit. Для защиты от denial-of-service attacks setting и default были backported в Go 1.25.2 и Go 1.24.8.

Go 1.26 добавил `urlmaxqueryparams`, задающий maximum number query parameters, принимаемых `net/url` при parsing URL-encoded query string.

Default:

```text
urlmaxqueryparams=10000
```

`urlmaxqueryparams=0` отключает limit. Для защиты от DoS setting и default были backported в Go 1.25.6 и Go 1.24.12.

Go 1.26 добавил `urlstrictcolons`, управляющий тем, разрешает ли `net/url.Parse` malformed hostnames с colons вне bracketed IPv6 address.

Default `urlstrictcolons=1` отвергает URLs вроде:

```text
http://localhost:1:2
http://::1/
```

Colons разрешены в bracketed IPv6 address, например:

```text
http://[::1]/
```

Go 1.26 включил два дополнительных post-quantum key exchange mechanisms:

- `SecP256r1MLKEM768`;
- `SecP384r1MLKEM1024`.

Default можно вернуть назад через [`tlssecpmlkem`](https://pkg.go.dev/crypto/tls#Config.CurvePreferences).

Go 1.26 добавил `tracebacklabels`, управляющий включением goroutine labels, заданных через `runtime/pprof`.

`tracebacklabels=1` включает key/value pairs в goroutine status header runtime tracebacks и `debug=2` runtime/pprof stack dumps. Format может измениться в будущем.

Go 1.26 добавил `cryptocustomrand`, управляющий тем, игнорируют ли большинство `crypto/...` APIs parameter random `io.Reader`.

Для Go 1.26 default:

```text
cryptocustomrand=0
```

При этом random parameters игнорируются. `cryptocustomrand=1` возвращает pre-Go 1.26 behavior.

### Go 1.25

Go 1.25 добавил `decoratemappings`, управляющий тем, annotates ли Go runtime anonymous memory mappings OS information об их назначении.

В Linux annotations появляются в `/proc/self/maps` и `/proc/self/smaps` как:

```text
[anon: Go: ...]
```

Default Go 1.25:

```text
decoratemappings=1
```

`decoratemappings=0` возвращает pre-Go 1.25 behavior. Setting применяется только в Linux и фиксируется при program startup; изменение environment `GODEBUG` после старта program его не меняет.

Go 1.25 добавил `embedfollowsymlinks`, управляющий тем, следует ли команда Go по symlinks на regular files при embedding files.

- `embedfollowsymlinks=0` — default, symlinks не follow'ятся;
- `embedfollowsymlinks=1` — follow symlinks разрешён.

Go 1.25 добавил `containermaxprocs`, управляющий тем, учитывает ли Go runtime cgroup CPU limits при выборе default `GOMAXPROCS`.

- `containermaxprocs=1` — default, учитываются cgroup limits, total logical CPU count и CPU affinity;
- `containermaxprocs=0` — cgroup limits не учитываются.

Setting применяется только в Linux.

Go 1.25 добавил `updatemaxprocs`, управляющий periodic update `GOMAXPROCS` при изменении CPU affinity или cgroup limits.

- `updatemaxprocs=1` — default, periodic updates включены;
- `updatemaxprocs=0` — updates отключены.

Go 1.25 отключил SHA-1 signature algorithms в TLS 1.2 согласно RFC 9155. `tlssha1=1` возвращает старый default.

Go 1.25 начал использовать SHA-256 для заполнения отсутствующего `SubjectKeyId` в `crypto/x509.CreateCertificate`. `x509sha256skid=0` возвращает SHA-1 behavior.

Go 1.25 исправил semantics contention reports runtime-internal locks и удалил `runtimecontentionstacks`.

Начиная с Go 1.25 RC 2 build information stamping отключается, если обнаружено несколько VCS, из-за риска VCS injection attacks. Change и setting были backported в Go 1.24.5 и Go 1.23.11. Старое behavior можно вернуть через:

```text
allowmultiplevcs=1
```

### Go 1.24

Go 1.24 добавил setting `fips140`, управляющий режимом Go Cryptographic Module FIPS 140-3.

Допустимые values:

- `off` — special FIPS 140-3 support выключена; default;
- `on` — Go Cryptographic Module работает в FIPS 140-3 mode;
- `only` — как `on`, но algorithms, не approved FIPS 140-3, возвращают error или panic.

Подробнее: [[security/fips140|FIPS 140-3 Compliance]].

`fips140` фиксируется при program startup и не меняется последующим изменением `GODEBUG` environment.

Go 1.24 сделал global [`math/rand.Seed`](https://pkg.go.dev/math/rand#Seed) no-op. Behavior контролируется `randseednop`.

Default Go 1.24:

```text
randseednop=1
```

`randseednop=0` возвращает pre-Go 1.24 behavior.

Go 1.24 добавил новые values `multipathtcp`:

- `0` — disable MPTCP на dialers и listeners по default;
- `1` — enable MPTCP на dialers и listeners;
- `2` — enable MPTCP только на listeners;
- `3` — enable MPTCP только на dialers.

Default Go 1.24 — `multipathtcp="2"`, то есть MPTCP включён по default на listeners. `multipathtcp="0"` возвращает pre-Go 1.24 behavior.

Go 1.24 изменил `go test -json`: build errors теперь выводятся как JSON вместо text.

Новые JSON events отличаются новыми `Action` values, но могут ломать CI systems, которые не готовы к таким events.

Behavior управляется `gotestjsonbuildtext`. `gotestjsonbuildtext=1` возвращает Go 1.23 behavior. Setting будет удалён в future release, не раньше Go 1.28.

Go 1.24 изменил `crypto/rsa`: RSA keys должны иметь minimum 1024 bits.

`rsa1024min=0` возвращает Go 1.23 behavior.

Go 1.24 добавил mechanism platform-specific Data Independent Timing (DIT) modes в package `crypto/subtle`.

Для всей program mode можно включить через:

```text
dataindependenttiming=1
```

Default Go 1.24 — `dataindependenttiming=0`, что сохраняет Go 1.23 behavior.

При включении DIT:

- mode включается при call из Go в C;
- при call C → Go DIT включается на время Go code и отключается перед return в C, если изначально был выключен.

На данный момент setting влияет только на arm64; на остальных platforms это no-op.

Go 1.24 удалил `x509sha1`. `crypto/x509` больше не поддерживает verification signatures certificates с SHA-1 based signature algorithms.

Go 1.24 изменил default `x509usepolicies` с `0` на `1`.

При marshalling certificates policies теперь по default берутся из `Certificate.Policies`, а не `Certificate.PolicyIdentifiers`.

Go 1.24 по default включил post-quantum key exchange mechanism `X25519MLKEM768`. Default можно вернуть через `tlsmlkem`.

Это может быть полезно с buggy TLS servers, которые неправильно обрабатывают большие records и timeout'ятся во время handshake.

Go 1.24 также удалил `X25519Kyber768Draft00` и setting Go 1.23 `tlskyber`.

Go 1.24 изменил `ParsePKCS1PrivateKey`: function теперь использует и validates CRT parameters encoded private key.

`x509rsacrt=0` возвращает Go 1.23 behavior.

### Go 1.23

Go 1.23 сделал channels, создаваемые package `time`, unbuffered (synchronous), что значительно упрощает корректное использование results methods `Timer.Stop` и `Timer.Reset`.

Setting `asynctimerchan` отключал это изменение. Runtime metrics для него нет. Setting удалён в Go 1.27.

Go 1.23 изменил mode bits, возвращаемые `os.Lstat` и `os.Stat` для Windows reparse points. Behavior управляется `winsymlink`.

При `winsymlink=1`:

- mount points больше не имеют `os.ModeSymlink`;
- reparse points, которые не являются symlinks, Unix sockets или dedup files, всегда получают `os.ModeIrregular`.

В результате `filepath.EvalSymlinks` больше не evaluates mount points, что устраняет ряд inconsistencies и bugs.

При старом `winsymlink=0` mount points считаются symlinks, а другие reparse points с non-default `os.ModeType` bits могут не иметь `ModeIrregular`.

Go 1.23 изменил `os.Readlink` и `filepath.EvalSymlinks`, чтобы они не пытались normalize volumes до drive letters, поскольку это не всегда возможно.

Behavior контролируется `winreadlinkvolume`:

- Go 1.23 default — `winreadlinkvolume=1`;
- предыдущие versions — `winreadlinkvolume=0`.

Go 1.23 по default включил experimental post-quantum key exchange `X25519Kyber768Draft00`.

Default можно было вернуть через `tlskyber`, например для buggy TLS servers, которые timeout'ятся при больших records.

Go 1.23 изменил `crypto/x509.ParseCertificate`, отвергая negative serial numbers. Change можно было вернуть через `x509negativeserial`.

Go 1.23 снова включил support ECMAScript 6 template literals в `html/template` по default. `jstmpllitinterp` перестал иметь эффект.

Go 1.23 изменил default TLS cipher suites clients/servers, удалив 3DES suites. `tls3des` возвращал прежний default; setting удалён в Go 1.27.

Go 1.23 изменил `tls.X509KeyPair` и `tls.LoadX509KeyPair`: field `Leaf` возвращаемого `tls.Certificate` теперь заполняется.

Behavior управлялся `x509keypairleaf`:

- Go 1.23 default — `x509keypairleaf=1`;
- предыдущие versions — `x509keypairleaf=0`.

Setting удалён в Go 1.27.

Go 1.23 изменил `net/http.ServeContent`, `ServeFile` и `ServeFS`: при serving error удаляются headers `Cache-Control`, `Content-Encoding`, `Etag` и `Last-Modified`.

`httpservecontentkeepheaders=1` возвращает pre-Go 1.23 behavior.

### Go 1.22

Go 1.22 добавил configurable limit максимального RSA key size для TLS handshakes через `tlsmaxrsasize`.

Default:

```text
tlsmaxrsasize=8192
```

Для предотвращения denial-of-service attacks setting и default были backported в Go 1.19.13, 1.20.8 и 1.21.1.

Go 1.22 сделал error request/response `net/http` client/server с пустым `Content-Length` header. Behavior контролируется `httplaxcontentlength`.

Go 1.22 изменил `ServeMux`, добавив extended patterns и unescaping patterns/request paths по segments. Behavior управляется `httpmuxgo121`.

Go 1.22 добавил type `Alias` в `go/types` для explicit representation type aliases.

Setting `gotypesalias` управлял тем, создаёт ли type checker `Alias` types:

- Go 1.22 default — `gotypesalias=0`;
- в Go 1.23 default стал `gotypesalias=1`.

Setting удалён в Go 1.27.

Go 1.22 повысил default minimum TLS version clients и servers до TLS 1.2. `tls10server` возвращал TLS 1.0; setting удалён в Go 1.27.

Go 1.22 удалил из default TLS cipher suites suites с RSA key exchange. `tlsrsakex` возвращал прежний default; setting удалён в Go 1.27.

Go 1.22 отключил `ConnectionState.ExportKeyingMaterial`, когда connection поддерживает ни TLS 1.3, ни Extended Master Secret. `tlsunsafeekm` мог re-enable это behavior; setting удалён в Go 1.27.

Go 1.22 изменил interaction runtime с transparent huge pages в Linux. Common default Linux kernel configuration может создавать значительный memory overhead, и Go 1.22 перестал обходить этот default.

Чтобы workaround issue без изменения kernel settings, THP для Go memory можно отключить через `disablethp`.

Change был backported в Go 1.21.1, но setting доступен только начиная с Go 1.21.6.

Setting может быть удалён в future release. Users, на которых влияет problem, должны настроить Linux согласно рекомендациям [[gc-guide|GC guide]] либо использовать distribution, отключающий transparent huge pages.

Go 1.22 добавил contention runtime-internal locks в `mutex` profile. Contention таких locks всегда отображается как `runtime._LostContendedRuntimeLock`.

Полные stack traces runtime locks можно было включить `runtimecontentionstacks`; они имеют non-standard semantics. В Go 1.25 этот setting был удалён после исправления semantics contention reports.

Go 1.22 добавил field `Policies` в `crypto/x509.Certificate`, поддерживающий certificate policy OIDs с components больше 31 bits.

По default field используется при parsing, но не при marshalling. Для marshalling больших OIDs вместо старого `PolicyIdentifiers` можно включить `x509usepolicies`.

### Go 1.21

Go 1.21 сделал `panic` с nil interface value run-time error. Behavior управляется `panicnil`.

Go 1.21 сделал error actions `html/template` внутри ECMAScript 6 template literal. Behavior контролируется `jstmpllitinterp` и был backported в Go 1.19.8+ и Go 1.20.3+.

Go 1.21 ввёл limits maximum number MIME headers и multipart forms через `multipartmaxheaders` и `multipartmaxparts`. Behavior также был backported в Go 1.19.8+ и Go 1.20.3+.

Go 1.21 добавил Multipath TCP support, но он использовался только если application явно его запросила. Behavior контролируется `multipathtcp`.

Удалять эти settings не планируется.

### Go 1.20

Go 1.20 добавил support rejection insecure paths в tar и zip archives через `tarinsecurepath` и `zipinsecurepath`.

Defaults:

```text
tarinsecurepath=1
zipinsecurepath=1
```

Они сохраняют behavior старых Go versions. Future version может изменить defaults на `0`.

Go 1.20 добавил automatic seeding global random number generator `math/rand`, контролируемый `randautoseed`.

Go 1.20 добавил concept fallback roots для certificate verification, управляемый `x509usefallbackroots`.

Go 1.20 удалил preinstalled `.a` files standard library из Go distribution. Теперь installations build и cache standard library так же, как packages других modules.

`installgoroot` возвращает installation и использование preinstalled `.a` files.

Удалять эти settings не планируется.

### Go 1.19

Go 1.19 сделал error path lookup, который resolves binary из current directory. Behavior управляется `execerrdot`. Удалять setting не планируется.

Go 1.19 начал отправлять EDNS0 additional headers в DNS requests. Это может ломать DNS servers некоторых routers, например CenturyLink Zyxel C3000Z.

Behavior меняется через `netedns0`. Setting доступен в Go 1.21.12, Go 1.22.5, Go 1.23 и later. Удалять его не планируется.

### Go 1.18

Go 1.18 удалил SHA-1 support для большинства X.509 certificates. Behavior контролировался `x509sha1`. Setting был удалён в Go 1.24.

### Go 1.10

Go 1.10 изменил build caching и добавил test caching, вместе с settings:

- `gocacheverify`;
- `gocachehash`;
- `gocachetest`.

Удалять их не планируется.

### Go 1.6

Go 1.6 добавил transparent HTTP/2 support через:

- `http2client`;
- `http2server`;
- `http2debug`.

Удалять эти settings не планируется.

### Go 1.5

Go 1.5 добавил pure Go DNS resolver, управляемый `netdns`.

Удалять этот setting не планируется.
