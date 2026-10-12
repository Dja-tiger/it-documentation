---
title: "Editor plugins и IDE для Go"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/editors.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Editor plugins и IDE для Go

Go не требует конкретной IDE. Большинство современных editors используют официальный language server **`gopls`**, который реализует Language Server Protocol (LSP) и предоставляет semantic functionality независимо от конкретного UI.

## Официальные/наиболее распространённые интеграции

### Visual Studio Code

Для VS Code используется официальное расширение Go. Оно интегрируется с `gopls` и предоставляет:

- code completion;
- diagnostics;
- go-to-definition/references;
- rename/refactoring;
- formatting/import organization;
- testing/debugging;
- vulnerability diagnostics;
- module/workspace tooling.

### GoLand / IntelliJ IDEA

JetBrains GoLand — полноценная Go IDE. IntelliJ IDEA также поддерживает Go через соответствующий plugin/product configuration.

### Vim / Neovim

Можно использовать LSP clients с `gopls`; ecosystem также включает vim-go и другие plugins.

### Emacs

Go development поддерживается через LSP/Eglot/lsp-mode и Go-specific modes.

### Другие editors

Любой editor с LSP client может использовать `gopls`. Это предпочтительный путь для semantic features, потому что language intelligence живёт в одном maintained Go tool, а не дублируется в каждом editor plugin.

## `gopls`

Установка:

```bash
go install golang.org/x/tools/gopls@latest
```

`gopls` понимает:

- modules/workspaces;
- build tags;
- generated code;
- types/generics;
- imports;
- tests;
- diagnostics from analyzers;
- vulnerability analysis в поддерживаемых editors.

Для editor-specific setup используйте актуальную документацию самого editor/plugin и [`gopls` documentation](https://go.dev/gopls/).

## Форматирование

Независимо от IDE canonical formatter Go остаётся `gofmt`/`go fmt`:

```bash
gofmt -w file.go
go fmt ./...
```

Editors обычно запускают formatter автоматически при save. Imports часто организуются через `goimports`/`gopls`.

## Практический baseline

Для профессиональной Go-разработки разумный минимальный набор:

```text
Go toolchain
+ gopls
+ gofmt/goimports
+ go test
+ go vet
+ delve
+ govulncheck
```

Editor является UI над этим toolchain и не должен становиться единственным источником build/test truth.
