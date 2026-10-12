---
title: "Безопасность Go"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/index.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Безопасность Go

Эта страница объединяет официальные ресурсы, которые помогают разработчикам Go повышать безопасность проектов.

См. также [[best-practices|Security Best Practices for Go Developers]].

## Поиск и исправление известных уязвимостей

Go vulnerability tooling стремится давать малошумные и проверяемые результаты: не просто сообщать, что зависимость когда-то содержала CVE, а по возможности определять, достигает ли application уязвимый symbol.

Архитектура vulnerability management описана в [[vuln/index|Go Vulnerability Management]].

### `govulncheck`

`govulncheck` анализирует source/binaries и сопоставляет code с Go Vulnerability Database. Для source analysis он способен учитывать call graph и выделять vulnerabilities, чьи функции/методы действительно вызываются transitively.

Практический tutorial: [[../tutorial/govulncheck|Поиск уязвимостей через govulncheck]].

### IDE

`gopls` и редакторы с Go language-server integration могут показывать vulnerabilities dependencies. Подробнее: [[vuln/editor|Vulnerability Scanning in IDEs]].

### pkg.go.dev

pkg.go.dev показывает предупреждения о vulnerabilities конкретной version package/module и историю affected versions.

### Go Vulnerability Database

Go vulnerability database агрегирует и курирует reports из источников вроде CVE/MITRE, GitHub advisories и direct reports maintainers. Canonical API использует OSV schema.

Подробнее: [[vuln/database|Go Vulnerability Database]].

## Сообщение security bugs в самом Go

Правила private reporting, disclosure и release handling: [[policy|Go Security Policy]].

Классификационные решения по частым категориям reports: [[decisions|Go Security Decisions]].

Общий threat model standard library/toolchain: [[threat-model|Go Threat Model]].

Go выпускает security fixes для поддерживаемых release lines согласно release policy; security announcements публикуются через `golang-announce`.

## Fuzzing

Native fuzzing встроен в Go toolchain с Go 1.18 и поддерживается OSS-Fuzz.

- [[fuzz/index|Go Fuzzing]] — user-facing guide;
- [[fuzz/technical|Техническое устройство fuzzing]];
- [[../tutorial/fuzz|Tutorial]].

## Cryptography

Standard library `crypto/*` и `golang.org/x/crypto` предоставляют cryptographic primitives/protocol implementations. Выбирайте high-level APIs и следуйте package security notes.

## FIPS 140-3

Go 1.24+ поддерживает native mode, упрощающий FIPS 140-3 compliance. Go 1.27 использует versioned Go Cryptographic Module и предоставляет build/runtime controls.

Подробнее: [[fips140|FIPS 140-3 Compliance]].
