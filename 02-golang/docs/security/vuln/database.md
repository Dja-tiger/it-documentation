---
title: "Go Vulnerability Database"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/vuln/database.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Go Vulnerability Database

Canonical database:

```text
https://vuln.go.dev
```

Reports выдаются в OSV schema. Browsing: `https://pkg.go.dev/vuln`.

> [!warning]
> Не используйте internal YAML из `golang/vulndb` Git repository как public stable API. Это внутренний format, который может меняться без warning.

## Contributing

Maintainers third-party Go packages могут отправлять public vulnerability reports/исправления через official forms. Vulnerabilities standard library/toolchain/golang.org repositories отправляются **не через public form**, а согласно [[../policy|Go Security Policy]].

## HTTP API

Endpoints принимают GET без обязательных query params/headers и доступны как `.json` или `.json.gz`. Благодаря этому compatible mirror может быть даже static/file-backed.

### `/index/db.json[.gz]`

Metadata всей DB:

```json
{
  "modified": "RFC3339 UTC timestamp"
}
```

`modified` — database logical modification time, а не wall-clock freshness guarantee; между mutation и publication возможна задержка.

### `/index/modules.json[.gz]`

Для каждого module:

```json
[
  {
    "path": "example.com/module",
    "vulns": [
      {
        "id": "GO-YYYY-NNNN",
        "modified": "...",
        "fixed": "v1.2.3"
      }
    ]
  }
]
```

`fixed` optional, если latest fixed version известна.

### `/index/vulns.json[.gz]`

Index vulnerabilities:

```json
[
  {
    "id": "GO-YYYY-NNNN",
    "modified": "...",
    "aliases": ["CVE-...", "GHSA-..."]
  }
]
```

### `/ID/$id.json[.gz]`

Individual OSV report vulnerability.

### Bulk download

```text
https://vuln.go.dev/vulndb.zip
```

содержит indexes + OSV files.

## `govulncheck -db`

Default database — `vuln.go.dev`.

Custom DB:

```bash
govulncheck -db=https://internal-vulndb.example ./...
```

`-db` поддерживает `http://`, `https://`, `file://`. HTTP(S) client использует compressed `.json.gz`, file source — `.json`.

Custom DB должна реализовать API выше.

Legacy endpoints canonical DB существуют временно и planned for removal.

## OSV schema: Go-specific semantics

### `id`

```text
GO-<YEAR>-<ENTRYID>
```

### `affected[].package`

```json
{
  "ecosystem": "Go",
  "name": "module/path"
}
```

Special module names:

- `stdlib` — importable standard-library package;
- `toolchain` — Go command/toolchain.

### `affected[].ecosystem_specific.imports`

Go-specific affected package/symbol information:

```json
{
  "path": "package/import/path",
  "symbols": ["Function", "Type.Method"],
  "goos": ["linux"],
  "goarch": ["amd64"]
}
```

`goos`/`goarch` присутствуют, если platform scope известен.

Именно symbol-level metadata позволяет `govulncheck` делать reachability analysis.

### `database_specific.url`

Canonical HTML report URL, например:

```text
https://pkg.go.dev/vuln/GO-2023-1621
```

### `database_specific.review_status`

- `UNREVIEWED` — auto-generated external-source report, не проверен Go team;
- `REVIEWED` — создан/проверен Go team.

Если field отсутствует, report трактуется как `REVIEWED` по documented convention.

## Versions

Pipeline пытается сопоставить external advisory versions с canonical Go module semver.

Если mapping не удаётся, DB может консервативно считать affected **все** versions: это снижает false-negative risk, но может дать false positive для уже fixed version.

Ошибку mapping/report можно предложить исправить через vulnerability feedback workflow.

## Excluded reports

Некоторые external CVE/GHSA сознательно исключаются:

| Reason | Значение |
|---|---|
| `NOT_GO_CODE` | Issue не находится в Go package. |
| `NOT_IMPORTABLE` | Только `main`, private internal code или другое место, которое нельзя импортировать external module. |
| `EFFECTIVELY_PRIVATE` | Technically importable, но package не предназначен/практически не используется внешними modules. |
| `DEPENDENT_VULNERABILITY` | Полностью покрывается другой vulnerability report. |
| `NOT_A_VULNERABILITY` | Advisory существует, но реальной vulnerability не подтверждено. |
| `WITHDRAWN` | Source withdrew vulnerability. |

Excluded reports пока не выдаются через public `vuln.go.dev` API в pinned upstream.
