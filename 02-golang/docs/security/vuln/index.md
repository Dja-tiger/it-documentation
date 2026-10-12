---
title: "Go Vulnerability Management"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/vuln/index.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Go Vulnerability Management

[[../index|Назад к Go Security]]

## Обзор

Go помогает developers обнаруживать, оценивать и устранять errors или weaknesses, которые могут быть exploited attackers.

Внутри ecosystem Go team поддерживает pipeline, который curates vulnerability reports и сохраняет их в Go vulnerability database.

Различные libraries и tools могут читать и анализировать эти reports, чтобы определять, как конкретный user project может быть затронут.

Эта functionality интегрирована в [pkg.go.dev](https://pkg.go.dev) и command-line tool `govulncheck`.

Project активно развивается. Feedback приветствуется; способы участия перечислены [ниже](#feedback).

> [!note]
> Чтобы сообщить vulnerability в самом Go project, используйте [[../policy|Go Security Policy]].

## Architecture

Upstream page содержит architecture diagram Go Vulnerability Management: `/security/vuln/architecture.png`.

Vulnerability management Go состоит из следующих high-level components:

1. **Data pipeline** собирает vulnerability information из разных sources, включая:
   - [National Vulnerability Database (NVD)](https://nvd.nist.gov/);
   - [GitHub Advisory Database](https://github.com/advisories);
   - [direct reports Go package maintainers](https://go.dev/s/vulndb-report-new).
2. **Vulnerability database** заполняется reports, сформированными из pipeline data. Все database reports review'ятся и curate'ятся Go Security team. Reports имеют [Open Source Vulnerability (OSV) format](https://ossf.github.io/osv-schema/) и доступны через [[database#api|API]].
3. **Integrations** с [pkg.go.dev](https://pkg.go.dev) и `govulncheck` помогают developers находить vulnerabilities в своих projects. [`govulncheck`](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck) анализирует codebase и показывает vulnerabilities, которые действительно affect project, на основе того, какие functions application transitively вызывают vulnerable functions. Это даёт low-noise и надёжный способ поиска known vulnerabilities.

## Resources

### Go Vulnerability Database

[Go vulnerability database](https://vuln.go.dev) содержит information из множества существующих sources, а также direct reports package maintainers Go security team.

Каждый database entry review'ится, чтобы убедиться, что:

- vulnerability description;
- package/symbol information;
- version details

указаны точно.

Подробнее: [[database|Go Vulnerability Database]].

Browser database: [pkg.go.dev/vuln](https://pkg.go.dev/vuln).

Package maintainers приглашаются [добавлять](#feedback) information о public vulnerabilities собственных projects и [предлагать improvements](https://go.dev/s/vuln-feedback), уменьшающие friction.

### Vulnerability Detection for Go

Go vulnerability detection стремится предоставлять low-noise и reliable способ узнавать о known vulnerabilities, которые могут affect project.

Vulnerability checking интегрирована в Go tools/services, включая:

- [`govulncheck`](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck);
- [pkg.go.dev](https://pkg.go.dev);
- [[editor|major editors]], например VS Code с Go extension.

Чтобы начать использовать `govulncheck`, запустите из project:

```text
$ go install golang.org/x/vuln/cmd/govulncheck@latest
$ govulncheck ./...
```

Для vulnerability detection в editor см. [[editor|editor integration]].

### Go CNA

Go security team является [CVE Numbering Authority](https://www.cve.org/ProgramOrganization/CNAs).

Подробнее: [[cna|Go CNA]].

## Feedback {#feedback}

Go team предлагает участвовать следующими способами:

- [добавлять новые](https://go.dev/s/vulndb-report-new) и [обновлять существующие](https://go.dev/s/vulndb-report-feedback) сведения о public vulnerabilities в Go packages, которые вы maintain'ите;
- [пройти survey](https://go.dev/s/govulncheck-feedback) и поделиться опытом `govulncheck`;
- [отправить feedback](https://go.dev/s/vuln-feedback) по issues и feature requests.

## FAQ

### Как сообщить vulnerability в Go project?

Все security bugs Go project отправляйте на [security@golang.org](mailto:security@golang.org).

Подробнее о process: [[../policy|Go Security Policy]].

### Как добавить public vulnerability в Go vulnerability database?

Чтобы запросить добавление public vulnerability, [заполните форму](https://go.dev/s/vulndb-report-new).

Vulnerability считается public, если:

- она уже публично disclosed;
- либо находится в package, который вы maintain'ите, и вы готовы её disclose.

Форма предназначена только для public vulnerabilities в **importable Go packages**, которые не maintained Go Team — то есть за пределами standard library, Go toolchain и `golang.org` modules.

Эту же форму можно использовать для request нового CVE ID. Подробнее см. [[cna|Go CVE Numbering Authority]].

### Как предложить edit существующей vulnerability?

Для edit существующего report в Go vulnerability database [заполните эту форму](https://go.dev/s/vulndb-report-feedback).

### Как сообщить issue или feedback о govulncheck?

Используйте [Go issue tracker](https://go.dev/s/vuln-feedback).

### Vulnerability есть в другой database. Почему её нет в Go vulnerability database?

Reports могут быть excluded по разным причинам, например:

- vulnerability не находится в Go package;
- vulnerability находится в installable command, а не importable package;
- vulnerability полностью subsumed другой vulnerability, уже представленной в database.

Подробнее о причинах exclusion: [[database#excluded-reports|Excluded Reports]].

Если вы считаете, что report исключён из `vuln.go.dev` ошибочно, [сообщите Go team](https://go.dev/s/vulndb-report-feedback).

### Почему Go vulnerability database не использует severity labels?

Большинство vulnerability reporting formats используют labels `LOW`, `MEDIUM`, `CRITICAL`, чтобы описывать impact и помогать developers prioritizing issues.

Go намеренно не использует такие labels по нескольким причинам.

Impact vulnerability редко universal, поэтому severity indicator может вводить в заблуждение.

Например, crash parser может быть critical issue, если parser обрабатывает user-supplied input и его можно использовать для DoS. Но если тот же parser работает только с local configuration files, даже severity `low` может быть преувеличением.

Severity labels также неизбежно subjective. Это относится даже к CVE program и scoring systems, которые разбивают vulnerability на attack vector, complexity, exploitability и другие factors: оценка этих factors всё равно содержит subjective judgment.

Go team считает хорошие vulnerability descriptions полезнее severity indicators.

Хорошее description объясняет:

- что именно представляет собой issue;
- как её trigger'ить;
- что consumers должны учитывать, оценивая impact для собственного software.

Feedback по этой теме можно отправить через [issue form](https://go.dev/s/vuln-feedback).
