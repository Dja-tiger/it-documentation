---
title: "Go Doc Comments"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/comment.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Go Doc Comments

**Doc comment** — comment, расположенный непосредственно перед top-level declaration `package`, `const`, `func`, `type` или `var` без пустой строки между comment и declaration.

Каждый exported identifier (начинающийся с uppercase) должен иметь doc comment.

Документацию извлекают `go/doc` и `go/doc/comment`. Её используют:

- `go doc`;
- [pkg.go.dev](https://pkg.go.dev/);
- local `pkgsite`;
- language server `gopls` и IDE integrations.

## Packages

Каждый package должен иметь package comment, объясняющий назначение package в целом и, для крупных APIs, дающий обзор ключевых частей.

```go
// Package path implements utility routines for manipulating slash-separated
// paths.
//
// The path package should only be used for paths separated by forward
// slashes, such as the paths in URLs. This package does not deal with
// Windows paths with drive letters or backslashes; to manipulate
// operating system paths, use the [path/filepath] package.
package path
```

Первая sentence обычно начинается с `Package <name> ...`.

В multi-file package package comment должен находиться в одном source file. Если package comments присутствуют в нескольких files, tooling объединит их.

## Commands

Для command (`package main`) package comment описывает поведение executable, а не API symbols. Первая sentence обычно начинается с имени программы.

Для command docs нормально включать:

- purpose;
- usage syntax;
- flags;
- input/output behavior;
- examples.

Indented lines считаются preformatted text и не rewrap'ятся.

Semantic linefeeds — одна sentence/long phrase на source line — допустимы и часто облегчают diffs. Renderer всё равно rewrap'ит prose для presentation.

## Types

Type doc comment должен объяснять, что представляет или предоставляет instance type.

```go
// A Reader serves content from a ZIP archive.
type Reader struct {
    // ...
}
```

### Concurrency guarantees

По умолчанию user не должен предполагать, что instance type безопасен для concurrent use несколькими goroutines. Если type thread-safe/concurrency-safe, это нужно явно документировать:

```go
// Regexp is the representation of a compiled regular expression.
// A Regexp is safe for concurrent use by multiple goroutines,
// except for configuration methods, such as Longest.
type Regexp struct {
    // ...
}
```

### Zero value

Idiomatic Go types стремятся иметь useful zero value. Если semantics не очевидна, её документируют:

```go
// A Buffer is a variable-sized buffer of bytes with Read and Write methods.
// The zero value for Buffer is an empty buffer ready to use.
type Buffer struct {
    // ...
}
```

### Exported fields

Каждый exported field должен быть объяснён либо общим type comment, либо field comments.

```go
type LimitedReader struct {
    R Reader // underlying reader
    N int64  // max bytes remaining
}
```

Полные sentences, называющие documented symbol, улучшают searchability и readability generated docs.

## Functions и methods

Function doc comment объясняет, что function возвращает или делает. Parameter/result names можно использовать непосредственно, без backticks.

```go
// Quote returns a double-quoted Go string literal representing s.
// The returned string uses Go escape sequences (\t, \n, \xFF, \u0100)
// for control characters and non-printable characters as defined by IsPrint.
func Quote(s string) string {
    // ...
}
```

Boolean-returning functions conventionally описываются как `reports whether ...`.

Если multiple results обсуждаются в docs, named results могут повысить ясность:

```go
// Copy copies from src to dst until either EOF is reached
// on src or an error occurs. It returns the total number of bytes
// written and the first error encountered while copying, if any.
func Copy(dst Writer, src Reader) (n int64, err error) {
    // ...
}
```

Для methods полезно использовать consistent receiver name across methods type.

Top-level functions по умолчанию считаются безопасными для concurrent calls, если нет shared mutable state/иного documented restriction; обычно это отдельно не пишется. Для methods concurrency guarantee относится к instance и должна быть documented, если она сильнее обычной single-goroutine assumption.

Документируйте contract и caller-visible special cases, а не internal algorithm implementation. Если complexity (`O(n log n)`, memory bound) важна callers, её можно включить.

## Constants

Related constants можно документировать одной group comment:

```go
// The result of Scan is one of these tokens or a Unicode character.
const (
    EOF = -(iota + 1)
    Ident
    Int
    Float
    Char
)
```

Иногда self-explanatory group достаточно line comments. Ungrouped exported constant обычно заслуживает complete doc sentence:

```go
// Version is the Unicode edition from which the tables are derived.
const Version = "13.0.0"
```

Typed constants отображаются рядом с type и часто полагаются на type documentation.

## Variables

Для vars применяются те же conventions, что для constants. Related exported vars можно объединять common comment; standalone exported variable обычно получает отдельную complete sentence.

## Syntax doc comments

Go doc comments поддерживают lightweight syntax:

- paragraphs;
- headings;
- links;
- lists;
- preformatted code blocks.

Raw HTML, font formatting и сложный Markdown намеренно не поддерживаются.

`gofmt` canonicalizes formatting doc comments, сохраняя source readability.

### Paragraphs

Paragraph — последовательность non-indented non-blank lines. Blank line отделяет paragraphs.

`gofmt`:

- удаляет leading/trailing blank lines;
- при общем indentation prefix снимает его;
- сохраняет source line breaks внутри paragraph;
- нормализует repeated blank lines.

Двойные backticks интерпретируются как left quote, двойные single quotes — как right quote.

### Notes

Special notes имеют форму:

```text
MARKER(uid): body
```

`MARKER` — минимум две uppercase Latin letters, `uid` — identifier автора/контакта.

```go
// TODO(user1): refactor to use standard library context
// BUG(user2): not cleaned up
```

pkg.go.dev собирает такие notes в отдельный section.

### Deprecations

Paragraph, начинающийся с exact prefix:

```text
Deprecated: ...
```

распознаётся tools как deprecation notice.

```go
// Deprecated: RC4 is cryptographically broken and should not be used
// except for compatibility with legacy systems.
```

Хороший notice объясняет причину и replacement, если он существует.

### Headings

Heading — unindented line:

```text
# Heading text
```

Она должна быть отделена blank lines и содержать `#` + space + text.

```go
// # Numeric Conversions
```

Syntax `#` headings появился в Go 1.19; `gofmt` умеет переводить старые implicit headings в explicit form.

### Links

Reference target:

```go
// [RFC 7159]: https://tools.ietf.org/html/rfc7159
```

Использование:

```go
// Package json implements encoding and decoding of JSON as defined in
// [RFC 7159].
```

Tooling переносит link definitions в конец comment, отделяя used и unused targets. Plain URLs автоматически link'ятся в HTML rendering.

### Doc links

Ссылки на exported Go identifiers:

- `[Name]`;
- `[Type.Method]`;
- `[pkg]`;
- `[pkg.Name]`;
- `[pkg.Type.Method]`.

Пример:

```go
// ReadFrom reads data from r until EOF. Any error except [io.EOF]
// encountered during the read is returned. If the buffer becomes too
// large, ReadFrom will panic with [ErrTooLarge].
```

Pointer type можно обозначить как `[*bytes.Buffer]`.

Для external package допустим full import path или assumed package name. Например `[json.Decoder]` может ссылаться на `encoding/json.Decoder`, если import name unambiguous.

Чтобы не конфликтовать с map/generic/array syntax, doc link должен быть окружён punctuation/whitespace или boundary line.

### Lists

Bullet markers:

```text
* + - •
```

Numbered marker — decimal number + `.` или `)`.

`gofmt` canonicalizes bullets к `-` и canonical indentation; numbered list сохраняет numbers и нормализует indentation.

Nested lists **не поддерживаются** как отдельная semantic structure. Лучше переписать docs либо использовать clear separated paragraphs.

### Code blocks

Indented non-list block — preformatted code block.

```go
// Example:
//
//	func Hello() {
//		fmt.Println("hello")
//	}
```

`gofmt` приводит common indentation code block к одному tab и добавляет blank lines вокруг него.

Code block может содержать не только Go, но и grammar, shell commands, structured examples.

### Directives

Directives вроде `//go:generate` не считаются prose doc comment и не отображаются как documentation body. `gofmt` перемещает directive lines в конец comment после blank line.

```go
// An Op is a single regular expression operator.
//
//go:generate stringer -type Op -trimprefix Op
type Op uint8
```

Go toolchain резервирует prefix `//go:`. Сторонние tools могут использовать `//toolname:directive ...`. Parser syntax доступен через `go/ast.ParseDirective`.

## Частые ошибки

### Accidentally indented continuation

Indented prose line может неожиданно стать code block. Например wrapped TODO/comment следует выровнять как prose, если code block не планировался.

### Unindented continuation code/list item

Обратная ошибка: continuation list/code line не indent'ирована и становится paragraph text. `gofmt` Go 1.19+ исправляет часть исторических patterns эвристически, но clear source formatting предпочтительнее.

### Brace-delimited examples без indentation

JSON/function examples следует явно оформлять indented code block, иначе `{`/`}` могут стать отдельными prose paragraphs.

### Nested lists

Doc-comment syntax не поддерживает nested lists. Лучше restructure text. Если hierarchy действительно нужна, можно разделить material headings/paragraphs или осторожно использовать разные marker types, но простая structure обычно лучше.

### `gofmt` как validator intent

Go 1.19+ reformatting делает ambiguous/mistaken formatting заметнее. Если heuristic трактует boundary неправильно, добавьте explicit blank line между prose и list/code block.
