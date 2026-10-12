---
title: "FIPS 140-3 Compliance"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/fips140.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# FIPS 140-3 Compliance

С Go 1.24 binaries могут нативно работать в режиме, упрощающем FIPS 140-3 compliance, а toolchain умеет линковать frozen versions Go Cryptographic Module.

> [!warning]
> Использование validated cryptographic module **не гарантирует**, что application автоматически удовлетворяет всем regulatory requirements. Compliance зависит от полного system/process context.

## Go Cryptographic Module

Это набор standard-library packages под:

```text
crypto/internal/fips140/...
```

Public APIs (`crypto/ecdsa`, `crypto/rand`, `crypto/tls`, и др.) прозрачно используют module implementations для approved algorithms.

## FIPS mode

В режиме FIPS 140-3:

- module выполняет integrity self-check при initialization, сверяя build-time checksum с loaded symbols;
- algorithms выполняют known-answer self-tests по FIPS implementation guidance — при init или first use;
- key generation выполняет pairwise consistency tests; для некоторых key types это может замедлять generation до ~2×;
- `crypto/rand.Reader` использует NIST SP 800-90A DRBG и дополнительно смешивает platform CSPRNG bytes;
- `crypto/tls` не договаривается о protocol/cipher/signature/key-exchange mechanisms, не approved FIPS mode;
- `crypto/rsa.SignPSS` с `PSSSaltLengthAuto` ограничивает salt length длиной hash.

Native mode не поддерживается на OpenBSD, Wasm, AIX и 32-bit Windows.

## `crypto/fips140`

```go
crypto/fips140.Enabled()
```

сообщает, активен ли FIPS mode.

```go
crypto/fips140.Version()
```

возвращает version используемого Go Cryptographic Module.

## `GOFIPS140`

Build-time environment для `go build`, `go install`, `go test`:

| Value | Behavior |
|---|---|
| `off` | Default: текущий module из standard-library tree, FIPS mode default off. |
| `latest` | Текущий module, FIPS mode default on. |
| `v1.0.0`, `v1.26.0` | Выбрать frozen module version и включить FIPS mode default. |
| `inprocess` | Последняя version в CMVP Modules In Process List. |
| `certified` | Последняя version с CMVP validation certificate. |

## `GODEBUG=fips140`

Runtime option нельзя изменить после process startup.

```text
fips140=off
fips140=on
fips140=only
```

`only` — **best-effort testing/assessment mode**, не production compliance mode. Non-compliant algorithms могут error/panic; возможны false positives/negatives. Большинству programs следует выбирать FIPS build через `GOFIPS140`, а не `only`.

## Module versions

### v1.26.0

Frozen в начале 2026 из Go 1.26, доступен Go 1.26+. По pinned upstream status на 2026-04-28 находился Pending Review CMVP и имел CAVP certificate A8028.

Отличия от v1.0.0 включают:

- ML-DSA;
- `testing/cryptotest.SetGlobalRandom`;
- новые AES-GCM compliance APIs;
- CPU-jitter Entropy Source с validation certificates;
- safety/performance improvements.

### v1.0.0

Frozen в начале 2024 из Go 1.24, доступен Go 1.24+, имеет CMVP certificate #5247 и CAVP A6650.

Older module versions поддерживаются до появления validated newer replacement; после этого older frozen module может быть удалён из distribution. При old module некоторые newer standard-library crypto features могут быть unavailable/error.

## Go+BoringCrypto

Старый BoringCrypto-based mechanism пока существует, но планируется replacement native FIPS mode. Он несовместим с native Go FIPS 140-3 mode.
