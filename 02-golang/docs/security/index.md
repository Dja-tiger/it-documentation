---
title: "Безопасность"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/index.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Безопасность

Эта страница содержит resources, помогающие Go developers повышать безопасность своих projects.

См. также: [[best-practices|Security Best Practices for Go Developers]].

## Поиск и исправление известных уязвимостей

Go vulnerability detection стремится предоставлять developers малошумные и надёжные tools, позволяющие узнать об известных vulnerabilities, которые могут затрагивать их projects.

Для общего понимания начните со [[vuln/index|summary и FAQ по архитектуре vulnerability management Go]]. Для практической работы используйте tools ниже.

### Проверка code через govulncheck

Developers могут использовать `govulncheck`, чтобы определить, влияют ли известные vulnerabilities на их code, и расставить priorities с учётом того, какие vulnerable functions и methods реально вызываются.

- [Документация govulncheck](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck)
- [[../tutorial/govulncheck|Tutorial: начало работы с govulncheck]]

### Обнаружение vulnerabilities из editor

VS Code Go extension проверяет third-party dependencies и показывает relevant vulnerabilities.

- [[vuln/editor|User documentation]]
- [Скачать VS Code Go](https://marketplace.visualstudio.com/items?itemName=golang.go)
- [Tutorial: Get started with VS Code Go](https://go.dev/doc/tutorial/govulncheck-ide)

### Поиск Go modules для использования

[pkg.go.dev](https://pkg.go.dev/) — website для поиска, оценки и изучения Go packages и modules.

При просмотре packages на pkg.go.dev сверху страницы показывается [banner](https://pkg.go.dev/golang.org/x/text@v0.3.7/language), если выбранная version содержит known vulnerabilities.

Кроме того, на странице version history можно увидеть [vulnerabilities, затрагивающие каждую version package](https://pkg.go.dev/golang.org/x/text@v0.3.7/language?tab=versions).

### Просмотр vulnerability database

Go vulnerability database получает data непосредственно от Go package maintainers, а также из внешних sources, включая [MITRE](https://www.cve.org/) и [GitHub](https://github.com/). Reports проходят curation Go Security team.

- [Reports в Go vulnerability database](https://pkg.go.dev/vuln/)
- [[vuln/database|Документация Go Vulnerability Database]]
- [Добавить public vulnerability в database](https://go.dev/s/vulndb-report-new)

## Сообщение security bugs в Go project

### [[policy|Security Policy]]

Security Policy содержит instructions по [reporting vulnerability в Go project](https://go.dev/security/policy#reporting-a-security-bug).

Там же описан process Go security team по tracking issues и их public disclosure.

[Release history](https://go.dev/doc/devel/release) содержит сведения о прошлых security fixes. Согласно [release policy](https://go.dev/doc/devel/release#policy), security fixes выпускаются для двух последних major Go releases.

- [[decisions|Classification decisions about commonly-reported vulnerabilities]]

## Проверка неожиданных inputs через fuzzing

Native fuzzing Go — вид automated testing, который непрерывно изменяет inputs program, чтобы находить bugs.

Go поддерживает fuzzing в standard toolchain начиная с Go 1.18. Native Go fuzz tests [поддерживаются OSS-Fuzz](https://google.github.io/oss-fuzz/getting-started/new-project-guide/go-lang/#native-go-fuzzing-support).

- [[fuzz/index|Основы fuzzing]]
- [[../tutorial/fuzz|Tutorial: начало работы с fuzzing]]

## Защита services с cryptography libraries Go

Cryptography libraries Go предназначены для помощи developers в создании secure applications.

См. documentation для [crypto packages](https://pkg.go.dev/crypto) и [`golang.org/x/crypto`](https://pkg.go.dev/golang.org/x/crypto/).

## FIPS 140-3 compliant cryptography

Cryptography libraries Go можно использовать в FIPS 140-3 compliant mode для regulated environments.

Подробнее см. [[fips140|FIPS 140-3 Compliance]].
