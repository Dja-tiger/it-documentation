---
title: "Vulnerability Scanning in IDEs"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/vuln/editor.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Vulnerability Scanning in IDEs

[[../index|Назад к Go Security]]

Editors, интегрированные с [Go language server](https://pkg.go.dev/golang.org/x/tools/cmd/gopls), например [VS Code с Go extension](https://marketplace.visualstudio.com/items?itemName=golang.go), могут обнаруживать vulnerabilities в dependencies.

Существуют два mode vulnerability detection. Оба используют [Go vulnerability database](https://vuln.go.dev) и дополняют друг друга.

- **Imports-based analysis.** Editor сканирует set packages, imported workspace, и показывает findings как diagnostics в `go.mod`. Mode быстрый, но может давать false positives, если code импортирует package с vulnerable symbol, но vulnerable function не reachable. Включается setting [`"vulncheck": "Imports"`](https://github.com/golang/tools/blob/master/gopls/doc/settings.md#vulncheck-enum) в `gopls`.
- **Govulncheck analysis.** Основан на CLI tool [`govulncheck`](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck), встроенном в `gopls`. Даёт low-noise и надёжное подтверждение того, вызывает ли code vulnerable functions. Поскольку analysis может быть expensive, он запускается вручную через code action **Run govulncheck to verify**, связанный с diagnostic imports-based analysis, либо через code lens [`"codelenses.run_govulncheck"`](https://github.com/golang/tools/blob/master/gopls/doc/settings.md#run-govulncheck) на `go.mod`.

Upstream page содержит demo `vscode.gif` и video для command **Go: Toggle Vulncheck**.

Features доступны в `gopls` v0.11.0 или newer. Feedback: [go.dev/s/vsc-vulncheck-feedback](https://go.dev/s/vsc-vulncheck-feedback).

## Editor-specific instructions

### VS Code

[Go extension](https://marketplace.visualstudio.com/items?itemName=golang.go) предоставляет integration с `gopls`.

Для vulnerability scanning нужны settings:

```json
"go.diagnostic.vulncheck": "Imports", // enable the imports-based analysis by default.
"gopls": {
  "ui.codelenses": {
    "run_govulncheck": true  // "Run govulncheck" code lens on go.mod file.
  }
}
```

Command [Go Toggle Vulncheck](https://github.com/golang/vscode-go/wiki/Commands#go-toggle-vulncheck) включает/выключает imports-based analysis для current workspace.

### Vim/NeoVim

При использовании [coc.nvim](https://www.vim.org/scripts/script.php?script_id=5779) imports-based analysis включается так:

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

## Notes and caveats

- Extension не сканирует private packages и не отправляет information о private modules. Analysis выполняется локально: загружается list известных vulnerable modules из Go vulnerability database, после чего вычисляется intersection с local project.
- Imports-based analysis использует list packages в workspace modules. Он может отличаться от literal contents `go.mod`, если используются `go.work`, module `replace` или `exclude`.
- Result govulncheck analysis может устареть после changes code или обновления Go vulnerability database. Для manual invalidation используйте codelens **Reset go.mod diagnostics** сверху `go.mod`; иначе result автоматически invalidated через один hour.
- Features сейчас не report'ят vulnerabilities standard library или toolchain. UX для таких findings и рекомендации users всё ещё исследуются.
