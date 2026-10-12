---
title: "Go Vulnerability Database"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/vuln/database.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Go Vulnerability Database

[[index|Назад к Go Vulnerability Management]]

## Обзор

Go vulnerability database ([https://vuln.go.dev](https://vuln.go.dev)) публикует information о Go vulnerabilities в [Open Source Vulnerability (OSV) schema](https://ossf.github.io/osv-schema/).

Просматривать vulnerabilities в browser можно на [pkg.go.dev/vuln](https://pkg.go.dev/vuln).

> [!warning]
> **Не полагайтесь** на contents Git repository `x/vulndb`. YAML files в этом repository поддерживаются во внутреннем format, который может меняться без warning.

## Contributing

Go team приглашает всех Go package maintainers [добавлять](https://go.dev/s/vulndb-report-new) information о public vulnerabilities в своих projects и [обновлять](https://go.dev/s/vulndb-report-feedback) существующие сведения о vulnerabilities в своих Go packages.

Цель — сделать reporting low-friction. Suggestions можно отправлять через [feedback form](https://go.dev/s/vuln-feedback).

> [!important]
> Не используйте эти forms для reporting vulnerability в Go standard library или sub-repositories. Для Go project следуйте [[../policy|Go Security Policy]].

## API {#api}

Canonical Go vulnerability database [https://vuln.go.dev](https://vuln.go.dev) — HTTP server, отвечающий на GET requests к endpoints ниже.

Endpoints не требуют query parameters или specific headers. Поэтому API может реализовать даже static site или fixed filesystem source, включая `file://` URL.

Каждый endpoint возвращает JSON либо uncompressed (`.json`), либо gzip-compressed (`.json.gz`).

### `/index/db.json[.gz]`

Возвращает metadata database:

```json
{
  "modified": "RFC3339 UTC timestamp ending in Z"
}
```

`modified` — latest time, когда database следует считать modified.

Его **не следует сравнивать с wall clock time**, например для cache invalidation, потому что между modification database и публикацией change может быть delay.

Live example: [vuln.go.dev/index/db.json](https://vuln.go.dev/index/db.json).

### `/index/modules.json[.gz]`

Возвращает list metadata для каждого module database:

```json
[
  {
    "path": "example.com/module",
    "vulns": [
      {
        "id": "GO-YYYY-NNNN",
        "modified": "RFC3339 UTC timestamp ending in Z",
        "fixed": "v1.2.3"
      }
    ]
  }
]
```

Fields:

- `path` — module path;
- `vulns` — vulnerabilities, affect'ящие module;
- `id` — vulnerability ID;
- `modified` — latest modification time vulnerability;
- `fixed` — optional module version в SemVer 2.0.0, содержащая latest fix; если unknown/unavailable, field отсутствует.

Live example: [vuln.go.dev/index/modules.json](https://vuln.go.dev/index/modules.json).

### `/index/vulns.json[.gz]`

Возвращает metadata vulnerabilities:

```json
[
  {
    "id": "GO-YYYY-NNNN",
    "modified": "RFC3339 UTC timestamp ending in Z",
    "aliases": ["CVE-...", "GHSA-..."]
  }
]
```

`aliases` содержит IDs той же vulnerability в других databases.

Live example: [vuln.go.dev/index/vulns.json](https://vuln.go.dev/index/vulns.json).

### `/ID/$id.json[.gz]`

Возвращает individual OSV report vulnerability с ID `$id`.

Live example: [GO-2022-0191.json](https://vuln.go.dev/ID/GO-2022-0191.json).

### Bulk download

Для скачивания всей database доступен ZIP со всеми index и OSV files:

[https://vuln.go.dev/vulndb.zip](https://vuln.go.dev/vulndb.zip)

### Использование в `govulncheck`

По default `govulncheck` использует canonical database `vuln.go.dev`.

Другую database можно задать flag `-db`, принимающим URL с protocol:

- `http://`;
- `https://`;
- `file://`.

Чтобы корректно работать с `govulncheck`, custom database должна реализовывать API, описанный выше.

При HTTP(S) source `govulncheck` использует compressed `.json.gz` endpoints; при file source — `.json`.

### Legacy API

Canonical database содержит дополнительные endpoints legacy API.

Support этих endpoints планируется удалить. Если вам требуется больше времени для migration, [сообщите Go team](https://go.dev/s/govulncheck-feedback).

## Schema

Reports используют [OSV schema](https://ossf.github.io/osv-schema/). Go vulnerability database задаёт следующие semantics fields.

### `id`

Unique identifier vulnerability имеет format:

```text
GO-<YEAR>-<ENTRYID>
```

### `affected`

Field [`affected`](https://ossf.github.io/osv-schema/#affected-fields) — JSON array объектов, описывающих module versions, содержащие vulnerability.

#### `affected[].package`

Field [`affected[].package`](https://ossf.github.io/osv-schema/#affectedpackage-field) идентифицирует affected **module**.

Required fields:

- `ecosystem` — всегда `Go`;
- `name` — Go module path.

Special names:

- `stdlib` — importable packages standard library;
- `toolchain` — команда Go/toolchain.

#### `affected[].ecosystem_specific`

Field [`affected[].ecosystem_specific`](https://ossf.github.io/osv-schema/#affectedecosystem_specific-field) содержит дополнительную information, используемую Go vulnerability detection tools.

Сейчас это object с единственным field `imports`.

##### `affected[].ecosystem_specific.imports`

JSON array packages и symbols, affected vulnerability.

Каждый object может содержать:

- `path` — import path package, содержащего vulnerability;
- `symbols` — array names vulnerable functions/methods;
- `goos` — execution operating systems, где symbols присутствуют, если known;
- `goarch` — architectures, где symbols присутствуют, если known.

Именно symbol-level information позволяет tools вроде `govulncheck` выполнять precise reachability analysis.

### `database_specific`

Custom fields Go vulnerability database.

#### `database_specific.url`

Fully-qualified URL Go vulnerability report, например:

```text
https://pkg.go.dev/vuln/GO-2023-1621
```

#### `database_specific.review_status`

Review status vulnerability report.

Если field отсутствует, report считается `REVIEWED`.

Possible values:

- `UNREVIEWED` — report автоматически generated на основе external source, например CVE/GHSA; data может быть limited и не verified Go team;
- `REVIEWED` — report originated Go team либо generated из external source и был reviewed member Go team; при необходимости добавлена дополнительная data.

Для остальных fields см. [OSV spec](https://ossf.github.io/osv-schema).

## Note по versions

Go tooling пытается автоматически map modules и versions source advisories в canonical Go modules/versions согласно [[../../modules/version-numbers|Go module version numbering]].

Tools вроде `govulncheck` полагаются на canonical versions, чтобы определять, affected ли конкретный Go project vulnerability dependency.

Иногда mapping невозможен — например, project использует собственную versioning scheme.

В таких случаях Go vulnerability database может conservatively пометить **все** Go versions как affected.

Это уменьшает risk false negatives, когда vulnerability не report'ится из-за unrecognized version range, но может создавать false positives: уже fixed version будет ошибочно считаться affected.

Если `govulncheck` report'ит vulnerability ошибочно либо не report'ит её, [предложите edit vulnerability report](https://github.com/golang/vulndb/issues/new?assignees=&labels=Needs+Triage%2CSuggested+Edit&template=suggest_edit.yaml&title=x%2Fvulndb%3A+suggestion+regarding+GO-2024-2965&report=GO-XXXX-YYYY).

## Examples

Все vulnerabilities Go vulnerability database используют OSV schema выше.

Examples:

- **Go standard library vulnerability** — GO-2022-0191:
  - [JSON](https://vuln.go.dev/ID/GO-2022-0191.json)
  - [HTML](https://pkg.go.dev/vuln/GO-2022-0191)
- **Go toolchain vulnerability** — GO-2022-0189:
  - [JSON](https://vuln.go.dev/ID/GO-2022-0189.json)
  - [HTML](https://pkg.go.dev/vuln/GO-2022-0189)
- **Vulnerability в Go module** — GO-2020-0015:
  - [JSON](https://vuln.go.dev/ID/GO-2020-0015.json)
  - [HTML](https://pkg.go.dev/vuln/GO-2020-0015)

## Excluded Reports {#excluded-reports}

Reports собираются из разных sources и curate'ятся Go Security team.

Некоторые CVE/GHSA могут быть сознательно excluded. В таком случае minimal report создаётся в `x/vulndb` под [`data/excluded`](https://github.com/golang/vulndb/tree/master/data/excluded).

Reasons exclusion:

- `NOT_GO_CODE` — vulnerability не находится в Go package, но другой source пометил её advisory Go ecosystem; она не может affect Go packages, например vulnerability в C++ library.
- `NOT_IMPORTABLE` — vulnerability находится в `package main`, `internal/` package, импортируемом только `main`, или другом месте, которое не может быть imported другим module.
- `EFFECTIVELY_PRIVATE` — package technically importable, но не предназначен для external use и маловероятно, что будет imported вне собственного module.
- `DEPENDENT_VULNERABILITY` — vulnerability является subset другой database vulnerability. Например, если package B зависит от vulnerable package A и существуют separate CVEs для A и B, B может быть excluded как полностью superseded report A.
- `NOT_A_VULNERABILITY` — CVE/GHSA назначен, но известной vulnerability, связанной с ним, нет.
- `WITHDRAWN` — vulnerability withdrawn source.

Сейчас excluded reports не выдаются через public [vuln.go.dev](https://vuln.go.dev) API.

Если у вас есть конкретный use case, где API access к excluded information был бы полезен, [сообщите Go team](https://go.dev/s/govulncheck-feedback).
