---
title: "Go Threat Model"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/threat-model.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Go Threat Model

## Обзор

Этот документ определяет общий threat model для Go toolchain и standard library.

Если documentation конкретного package не определяет собственный threat model, следует считать, что ко всем packages standard library применяется model, описанный здесь.

### Threat Model

#### Build Safety

Сборка Go code считается безопасной и не должна иметь side effects, например unexpected execution.

#### Runtime Execution

Execution malicious code в общем случае не считается relevant security issue.

Предполагается, что user, знакомый с Go, понимает, что именно он запускает.

#### Memory Safety

Предполагается, что при отсутствии использования package `unsafe` memory safety гарантируется runtime.

#### Trust Boundaries

APIs, от которых разумно ожидается приём arbitrary user-provided input, должны быть hardened против panics и arbitrary resource consumption.

Передача garbage в API, приводящая к unexpected output, не считается security issue.

#### Environment Control

Предполагается, что local system безопасна.

Attacks, требующие уже compromised OS, не считаются relevant. В частности, threat model не включает attacker control над:

- filesystem;
- environment variables, включая `PATH`;
- memory access или control.

### Packages с собственным threat model

Для следующих packages используются их package-specific security models:

- [`encoding/json`](https://pkg.go.dev/encoding/json#hdr-Security_Considerations)
- [`encoding/json/v2`](https://pkg.go.dev/encoding/json/v2#hdr-Security_Considerations)
- [`encoding/json/jsontext`](https://pkg.go.dev/encoding/json/jsontext#hdr-Security_Considerations)
- [`encoding/gob`](https://pkg.go.dev/encoding/gob#hdr-Security)
- [`html/template`](https://pkg.go.dev/html/template#hdr-Security_Model)
- [`image`](https://pkg.go.dev/image#hdr-Security_Considerations)
- [`debug/pe`](https://pkg.go.dev/debug/pe#hdr-Security)
- [`debug/macho`](https://pkg.go.dev/debug/macho#hdr-Security)
- [`debug/dwarf`](https://pkg.go.dev/debug/dwarf#hdr-Security)
- [`debug/plan9obj`](https://pkg.go.dev/debug/plan9obj#hdr-Security)
- [`debug/elf`](https://pkg.go.dev/debug/elf#hdr-Security)
