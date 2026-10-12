---
title: "FIPS 140-3 Compliance"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/fips140.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# FIPS 140-3 Compliance

Начиная с Go 1.24 Go binaries могут нативно работать в mode, упрощающем FIPS 140-3 compliance. Кроме того, toolchain умеет build'ить программы с frozen versions cryptography packages, составляющих Go Cryptographic Module.

## FIPS 140-3

NIST FIPS 140-3 — U.S. Government compliance regime для cryptographic applications. Среди прочего он требует использования approved algorithms и [CMVP](https://csrc.nist.gov/projects/cryptographic-module-validation-program)-validated cryptographic modules, протестированных в target operating environments.

Mechanisms, описанные на этой странице, помогают Go applications выполнять соответствующие compliance requirements.

Applications, которым FIPS 140-3 compliance не требуется, могут безопасно игнорировать эти mechanisms и не должны включать FIPS 140-3 mode.

> [!note]
> Само по себе использование FIPS 140-3 compliant и validated cryptographic module может быть недостаточно для выполнения всех regulatory requirements. Go team не может гарантировать или консультировать, удовлетворяет ли provided FIPS 140-3 mode конкретным требованиям конкретного user. Необходимо самостоятельно определить, соответствует ли использование module вашим требованиям.

## Go Cryptographic Module

Go Cryptographic Module — набор standard library Go packages под:

```text
crypto/internal/fips140/...
```

которые реализуют FIPS 140-3 approved algorithms.

Public API packages, например `crypto/ecdsa` и `crypto/rand`, прозрачно используют Go Cryptographic Module для implementation FIPS 140-3 algorithms.

## FIPS 140-3 mode

При работе в FIPS 140-3 mode:

- Go Cryptographic Module автоматически выполняет integrity self-check во время `init`, сравнивая checksum object file module, вычисленную при build, с symbols, загруженными в memory.
- Все algorithms выполняют known-answer self-tests согласно соответствующему FIPS 140-3 Implementation Guidance либо при `init`, либо при first use.
- Для generated cryptographic keys выполняются pairwise consistency tests. Для некоторых key types это может давать slowdown до 2×, что особенно важно для ephemeral keys.
- [`crypto/rand.Reader`](https://pkg.go.dev/crypto/rand#Reader) реализован поверх NIST SP 800-90A DRBG. Чтобы сохранить тот же security level, что и у programs вне FIPS mode, при каждом `Read` дополнительно читаются random bytes из platform CSPRNG и смешиваются с output как uncredited additional data.
- [`crypto/tls`](https://pkg.go.dev/crypto/tls) игнорирует и не negotiates protocol versions, cipher suites, signature algorithms и key-exchange mechanisms, не approved FIPS 140-3. Это эквивалентно legacy opt-in mechanism `crypto/tls/fipsonly` в Go+BoringCrypto.
- [`crypto/rsa.SignPSS`](https://pkg.go.dev/crypto/rsa#SignPSS) с [`PSSSaltLengthAuto`](https://pkg.go.dev/crypto/rsa#PSSSaltLengthAuto) ограничивает salt length длиной hash.

FIPS 140-3 mode не поддерживается на:

- OpenBSD;
- Wasm;
- AIX;
- 32-bit Windows.

## Package `crypto/fips140`

Function [`crypto/fips140.Enabled`](https://pkg.go.dev/crypto/fips140#Enabled) сообщает, активен ли FIPS 140-3 mode.

Function [`crypto/fips140.Version`](https://pkg.go.dev/crypto/fips140#Version) возвращает version используемого Go Cryptographic Module.

## Environment variable `GOFIPS140`

Environment variable `GOFIPS140` можно использовать с:

- `go build`;
- `go install`;
- `go test`.

Она выбирает version Go Cryptographic Module, которая будет linked в executable, и может включать FIPS 140-3 mode по default.

Поддерживаемые values:

- `off` — default; используется `crypto/internal/fips140/...` из текущего standard library tree.
- `latest` — как `off`, но FIPS 140-3 mode включён по default.
- `v1.0.0` или `v1.26.0` — выбирают соответствующую конкретную version Go Cryptographic Module и включают FIPS 140-3 mode по default.
- `inprocess` — эквивалент latest version, которая достигла [CMVP Modules In Process List](https://csrc.nist.gov/Projects/cryptographic-module-validation-program/modules-in-process/modules-in-process-list).
- `certified` — эквивалент latest version, получившей [CMVP validation certificate](https://csrc.nist.gov/projects/cryptographic-module-validation-program/validated-modules/search?SearchMode=Basic&ModuleName=Go+Cryptographic+Module&CertificateStatus=Active&ValidationYear=0).

## `fips140` option `GODEBUG`

Runtime option `fips140` в [[../godebug|GODEBUG]] управляет работой Go Cryptographic Module в FIPS 140-3 mode.

После program startup изменить его нельзя.

По default:

```text
fips140=off
```

если только при build не был установлен `GOFIPS140`.

При:

```text
fips140=on
```

FIPS 140-3 mode включается. Это можно сделать даже если `GOFIPS140` не был установлен при build.

При:

```text
fips140=only
```

cryptographic algorithms, не compliant FIPS 140-3, возвращают error или panic.

Это **best-effort mode только для testing, assessment и debugging**.

Он:

- не предназначен для production;
- не требуется Security Policy;
- намеренно вводит crashes и потенциально unhandled errors;
- может иметь false positives и false negatives.

Большинству programs не следует задавать этот option напрямую. Вместо этого используйте `GOFIPS140` при build.

## Module versions, validations и compatibility

Google имеет contractual relationship с [Geomys](https://geomys.org/) для проведения как минимум yearly CMVP validations Go Cryptographic Module.

В момент validation Go Cryptographic Module freeze'ится и создаётся новая module version для submission.

Validations выполняются на широком наборе Operating Environments и охватывают многие популярные combinations operating systems и hardware platforms.

Older Go Cryptographic Module versions остаются supported и available до тех пор, пока более новая version не получит CMVP validation certificate.

После получения certificate более новой version older versions удаляются.

Некоторые features standard library могут стать недоступны и возвращать errors, если используется Go Cryptographic Module, frozen из более старой Go version.

### Go Cryptographic Module v1.26.0

Go Cryptographic Module v1.26.0 был frozen в начале 2026 года из Go 1.26.

Он доступен в Go 1.26+.

По состоянию на 2026-04-28 он имел status **Pending Review** в CMVP Modules In Process List и был покрыт [CAVP Certificate A8028](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/details?validation=40638).

#### Изменения относительно v1.0.0

- Реализован ML-DSA.
- Поддерживается [`testing/cryptotest.SetGlobalRandom`](https://pkg.go.dev/testing/cryptotest#SetGlobalRandom).
- Добавлены новые AES-GCM compliance APIs для использования в `crypto/hpke` и future exposed APIs.
- Go Cryptographic Module теперь использует CPU jitter Entropy Source с [ESV Certificate #E318](https://csrc.nist.gov/projects/cryptographic-module-validation-program/entropy-validations/certificate/318) и [CAVP Certificate A7715](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/details?product=20498). Platform CSPRNG по-прежнему используется как uncredited additional data source для всех random bytes.
- Различные safety и performance improvements.

### Go Cryptographic Module v1.0.0

Go Cryptographic Module v1.0.0 был frozen в начале 2024 года из Go 1.24.

Он доступен в Go 1.24+.

Он покрыт:

- [CMVP Certificate #5247](https://csrc.nist.gov/projects/cryptographic-module-validation-program/certificate/5247);
- [CAVP Certificate A6650](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/details?product=19371).

## Go+BoringCrypto

Предыдущий unsupported mechanism использования BoringCrypto module для некоторых FIPS 140-3 approved algorithms пока остаётся доступным, но должен быть удалён и заменён mechanism, описанным на этой странице, в future release.

Go+BoringCrypto несовместим с native FIPS 140-3 mode.
