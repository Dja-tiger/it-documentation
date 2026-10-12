---
title: "Go Vulnerability Management"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/vuln/index.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Go Vulnerability Management

Go ecosystem собирает, курирует и раздаёт сведения о vulnerabilities так, чтобы developer tools могли определить не только affected module version, но и vulnerable packages/symbols.

## Architecture

1. **Data pipeline** получает public vulnerability information из NVD, GitHub Advisory Database и direct maintainer reports.
2. **Go Vulnerability Database** хранит curated reports в OSV-compatible form. Go Security Team проверяет package/symbol/version metadata.
3. **Integrations** — pkg.go.dev, `govulncheck`, `gopls`/editors — анализируют конкретный project.

`govulncheck` для source code строит call reachability и старается показывать прежде всего vulnerabilities, symbols которых реально достигаются application code.

## Database

Canonical endpoint:

```text
https://vuln.go.dev
```

Browser:

```text
https://pkg.go.dev/vuln
```

Details/API/schema: [[database|Go Vulnerability Database]].

## Detection

CLI:

```bash
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...
```

IDE: [[editor|Vulnerability Scanning in IDEs]].

## Go CNA

Go Security Team является CVE Numbering Authority для defined scope Go ecosystem. Policy: [[cna|Go CNA Policy]].

## Reporting

Vulnerability **самого Go project** → [[../policy|security policy]], private reporting.

Уже public vulnerability third-party importable Go module можно предложить в Go vuln database через official public reporting form.

## FAQ principles

### Почему report может отсутствовать?

Reasons включают:

- issue не в Go code;
- affected package не importable;
- package effectively private/internal application code;
- report полностью covered другой vulnerability;
- assigned advisory не соответствует реальной vulnerability;
- source advisory withdrawn.

### Почему нет severity labels?

Impact зависит от usage context. Parser crash может быть severe для untrusted Internet traffic и практически irrelevant для trusted local file. Поэтому Go делает ставку на precise description + affected symbols + reachability вместо универсального severity label.
