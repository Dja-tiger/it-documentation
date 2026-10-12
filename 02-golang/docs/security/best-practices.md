---
title: "Security Best Practices for Go Developers"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/best-practices.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Security Best Practices for Go Developers

## Регулярно сканируйте source и binaries

Используйте `govulncheck`, backed by Go vulnerability database:

```bash
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...
```

Tool можно включать в CI/CD. Для machine-readable integration доступен JSON output. Официальный GitHub Action также поддерживает automated checks.

Для editor-based scanning см. [[vuln/editor|IDE integration]].

## Обновляйте Go и dependencies

Новый patch release Go содержит bug/security fixes. Для production используйте поддерживаемую release line и актуальный patch.

Dependencies также следует обновлять, но не механически: новая version может содержать breaking behavior, regression или malicious supply-chain change. Любой upgrade проходит review, tests и желательно automated security/compatibility checks.

## Fuzzing

Coverage-guided fuzzing помогает находить edge cases, которые трудно перечислить вручную: parser crashes, resource exhaustion, injection-like inputs, malformed encodings и другие security-sensitive failures.

```bash
go test -fuzz=FuzzName
```

Подробнее: [[fuzz/index|Go Fuzzing]].

## Race detector

Data races делают behavior непредсказуемым и могут стать security boundary failure.

```bash
go test -race ./...
```

Detector динамический: он видит только executed code paths. Поэтому важны integration/load tests. Полный reference: [[../race-detector|Data Race Detector]].

## `go vet`

```bash
go vet ./...
```

`vet` ищет suspicious constructs, которые компилируются, но часто являются ошибками: некорректные format calls, misuse synchronization/copylocks и другие analyzer-specific patterns.

`go vet` не заменяет tests, static analyzers или security review, но должен быть частью обычного CI pipeline.

## Следите за security releases

Подпишитесь на low-volume `golang-announce`. Security-related announcements получают соответствующую маркировку; Go team также pre-announces часть PRIVATE-track fixes перед planned release.
