---
title: "Vulnerability Scanning in IDEs"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/vuln/editor.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Vulnerability Scanning в IDE

Editors с `gopls` integration могут анализировать dependencies через Go vulnerability database.

## Два режима

### Imports analysis

Быстрый mode: анализируется set imported packages workspace. Findings показываются diagnostics рядом с `go.mod`.

Плюс: быстро.

Минус: возможен false positive, если package imported, но vulnerable function/symbol не reachable.

`gopls` setting:

```json
{
  "vulncheck": "Imports"
}
```

### Govulncheck analysis

`govulncheck` встроен в `gopls` и выполняет более дорогой reachability analysis. Обычно запускается вручную code action/codelens после import-based finding.

Это более low-noise подтверждение: вызывает ли code vulnerable functions.

Features доступны начиная с documented `gopls` v0.11.0+.

## VS Code

Пример settings из pinned upstream:

```json
{
  "go.diagnostic.vulncheck": "Imports",
  "gopls": {
    "ui.codelenses": {
      "run_govulncheck": true
    }
  }
}
```

Также есть command `Go: Toggle Vulncheck`.

## Vim/NeoVim + coc.nvim

Initialization options language server могут включать:

```json
{
  "codeLens.enable": true,
  "languageserver": {
    "go": {
      "command": "gopls",
      "initializationOptions": {
        "vulncheck": "Imports"
      }
    }
  }
}
```

## Privacy и caveats

- IDE не отправляет private module source/paths в vulnerability database; analysis загружает known vulnerable-module information и сравнивает локально.
- Workspace package set может отличаться от literal `go.mod` из-за `go.work`, `replace`, `exclude`.
- `govulncheck` result может устареть после code/DB updates; diagnostics можно reset, также существует automatic invalidation window.
- Pinned upstream отмечает, что IDE feature пока не показывает vulnerabilities standard library/toolchain тем же способом; UX остаётся отдельной задачей.
