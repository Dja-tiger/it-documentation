---
title: "Go Doc Comments"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/comment.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Go Doc Comments

Содержание:

- [Packages](#package)
- [Commands](#cmd)
- [Types](#type)
- [Funcs](#func)
- [Consts](#const)
- [Vars](#var)
- [Syntax](#syntax)
- [Частые ошибки и ловушки](#mistakes)

**Doc comments** — comments, расположенные непосредственно перед top-level declarations `package`, `const`, `func`, `type` и `var`, без пустой строки между comment и declaration.

Каждое exported name, то есть имя с uppercase первой буквой, должно иметь doc comment.

Packages [`go/doc`](https://pkg.go.dev/go/doc) и [`go/doc/comment`](https://pkg.go.dev/go/doc/comment) позволяют извлекать documentation из Go source code. Эту functionality используют разные tools.

Команда [`go doc`](https://go.dev/cmd/go#hdr-Show_documentation_for_package_or_symbol) ищет и выводит doc comment для заданного package или symbol. Здесь symbol — top-level `const`, `func`, `type` или `var`.

Web server [pkg.go.dev](https://pkg.go.dev/) показывает documentation публичных Go packages, если license позволяет такое использование. Site обслуживает program [`golang.org/x/pkgsite/cmd/pkgsite`](https://pkg.go.dev/golang.org/x/pkgsite/cmd/pkgsite), который также можно запускать локально для просмотра documentation private modules или без internet connection.

Language server [`gopls`](https://pkg.go.dev/golang.org/x/tools/gopls) показывает documentation при редактировании Go source files в IDE.

Остальная часть страницы описывает, как писать Go doc comments.

## Packages {#package}

Каждый package должен иметь package comment, представляющий package. Он сообщает information, относящуюся к package целиком, и обычно задаёт expectations относительно package.

Особенно для больших packages полезно, чтобы package comment давал краткий обзор наиболее важных частей API и при необходимости ссылался на другие doc comments.

Если package простой, comment может быть коротким:

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

Square brackets в `[path/filepath]` создают [documentation link](#links).

Как видно из example, Go doc comments используют complete sentences. Для package comment это означает, что [first sentence](https://pkg.go.dev/go/doc#Package.Synopsis) начинается с `Package <name>`.

В multi-file packages package comment должен находиться только в одном source file. Если package comments есть в нескольких files, они объединяются в один большой comment для всего package.

## Commands {#cmd}

Package comment для command похож на обычный package comment, но описывает поведение program, а не Go symbols в package.

Первая sentence по convention начинается с имени program, capitalized, поскольку это начало предложения.

Ниже сокращённая version package comment для `gofmt`:

```text
/*
Gofmt formats Go programs.
It uses tabs for indentation and blanks for alignment.
Alignment assumes that an editor is using a fixed-width font.

Without an explicit path, it processes the standard input. Given a file,
it operates on that file; given a directory, it operates on all .go files in
that directory, recursively. (Files starting with a period are ignored.)
By default, gofmt prints the reformatted sources to standard output.

Usage:

    gofmt [flags] [path ...]

The flags are:

    -d
        Do not print reformatted sources to standard output.
        If a file's formatting is different than gofmt's, print diffs
        to standard output.
    -w
        Do not print reformatted sources to standard output.
        If a file's formatting is different from gofmt's, overwrite it
        with gofmt's version. If an error occurred during overwriting,
        the original file is restored from an automatic backup.

When gofmt reads from standard input, it accepts either a full Go program
or a program fragment. A program fragment must be a syntactically
valid declaration list, statement list, or expression. When formatting
such a fragment, gofmt preserves leading indentation as well as leading
and trailing spaces, so that individual sections of a Go program can be
formatted by piping them through gofmt.
*/
package main
```

Начало comment написано с использованием [semantic linefeeds](https://rhodesmill.org/brandon/2012/one-sentence-per-line/): каждая новая sentence или длинная phrase находится на отдельной line. Это может упростить чтение diffs по мере изменения code и comments.

Последующие paragraphs в example этой convention не придерживаются и вручную wrapped. Выбирайте вариант, который удобнее для вашего code base.

В любом случае `go doc` и `pkgsite` rewrap text doc comments при output.

Например:

```text
$ go doc gofmt
Gofmt formats Go programs. It uses tabs for indentation and blanks for
alignment. Alignment assumes that an editor is using a fixed-width font.

Without an explicit path, it processes the standard input. Given a file, it
operates on that file; given a directory, it operates on all .go files in that
directory, recursively. (Files starting with a period are ignored.) By default,
gofmt prints the reformatted sources to standard output.

Usage:

    gofmt [flags] [path ...]

The flags are:

    -d
        Do not print reformatted sources to standard output.
        If a file's formatting is different than gofmt's, print diffs
        to standard output.
...
```

Indented lines считаются preformatted text: они не rewrap'ятся и выводятся code font в HTML и Markdown presentations. Детали приведены в разделе [Syntax](#syntax).

## Types {#type}

Doc comment type должен объяснять, что представляет или предоставляет каждый instance этого type.

Если API прост, comment может быть очень коротким:

```go
package zip

// A Reader serves content from a ZIP archive.
type Reader struct {
    ...
}
```

По умолчанию programmers должны предполагать, что type безопасен для использования только одной goroutine одновременно.

Если type предоставляет более сильные guarantees, это нужно указать в doc comment:

```go
package regexp

// Regexp is the representation of a compiled regular expression.
// A Regexp is safe for concurrent use by multiple goroutines,
// except for configuration methods, such as Longest.
type Regexp struct {
    ...
}
```

Go types также должны стремиться к тому, чтобы zero value имела полезное значение. Если это не очевидно, semantics zero value следует документировать:

```go
package bytes

// A Buffer is a variable-sized buffer of bytes with Read and Write methods.
// The zero value for Buffer is an empty buffer ready to use.
type Buffer struct {
    ...
}
```

Для struct с exported fields либо type comment, либо comments отдельных fields должны объяснять смысл каждого exported field.

Пример, где fields объясняет type comment:

```go
package io

// A LimitedReader reads from R but limits the amount of
// data returned to just N bytes. Each call to Read
// updates N to reflect the new amount remaining.
// Read returns EOF when N <= 0.
type LimitedReader struct {
    R   Reader // underlying reader
    N   int64  // max bytes remaining
}
```

А здесь explanations находятся в per-field comments:

```go
package comment

// A Printer is a doc comment printer.
// The fields in the struct can be filled in before calling
// any of the printing methods
// in order to customize the details of the printing process.
type Printer struct {
    // HeadingLevel is the nesting level used for
    // HTML and Markdown headings.
    // If HeadingLevel is zero, it defaults to level 3,
    // meaning to use <h3> and ###.
    HeadingLevel int
    ...
}
```

Как и для packages и funcs, doc comments types начинаются с complete sentence, называющей declared symbol.

Explicit subject часто делает формулировку яснее и облегчает search в web page или command line.

Например:

```text
$ go doc -all regexp | grep pairs
pairs within the input string: result[2*n:2*n+2] identifies the indexes
    FindReaderSubmatchIndex returns a slice holding the index pairs identifying
    FindStringSubmatchIndex returns a slice holding the index pairs identifying
    FindSubmatchIndex returns a slice holding the index pairs identifying the
$
```

## Funcs {#func}

Doc comment function должен объяснять, что function возвращает, либо, если function вызывается ради side effects, что она делает.

Named parameters и results можно упоминать прямо в comment без специального syntax вроде backquotes. Следствие этой convention: names вроде `a`, которые можно принять за обычное слово, обычно избегаются.

Пример:

```go
package strconv

// Quote returns a double-quoted Go string literal representing s.
// The returned string uses Go escape sequences (\t, \n, \xFF, \u0100)
// for control characters and non-printable characters as defined by IsPrint.
func Quote(s string) string {
    ...
}
```

Ещё example:

```go
package os

// Exit causes the current program to exit with the given status code.
// Conventionally, code zero indicates success, non-zero an error.
// The program terminates immediately; deferred functions are not run.
//
// For portability, the status code should be in the range [0, 125].
func Exit(code int) {
    ...
}
```

Для functions, возвращающих boolean, doc comments обычно используют phrase `reports whether`. Phrase `or not` не нужна.

```go
package strings

// HasPrefix reports whether the string s begins with prefix.
func HasPrefix(s, prefix string) bool
```

Если doc comment должен объяснить несколько results, named results могут сделать comment понятнее, даже если names не используются в body function:

```go
package io

// Copy copies from src to dst until either EOF is reached
// on src or an error occurs. It returns the total number of bytes
// written and the first error encountered while copying, if any.
//
// A successful Copy returns err == nil, not err == EOF.
// Because Copy is defined to read from src until EOF, it does
// not treat an EOF from Read as an error to be reported.
func Copy(dst Writer, src Reader) (n int64, err error) {
    ...
}
```

И наоборот: если results не нужно называть в doc comment, обычно names не указывают и в code, как в example `Quote`, чтобы не загромождать presentation.

Все эти правила применяются как к обычным functions, так и к methods.

Для methods использование одинакового receiver name уменьшает ненужные различия при listing всех methods type:

```text
$ go doc bytes.Buffer
package bytes // import "bytes"

type Buffer struct {
    // Has unexported fields.
}
    A Buffer is a variable-sized buffer of bytes with Read and Write methods.
    The zero value for Buffer is an empty buffer ready to use.

func NewBuffer(buf []byte) *Buffer
func NewBufferString(s string) *Buffer
func (b *Buffer) Bytes() []byte
func (b *Buffer) Cap() int
func (b *Buffer) Grow(n int)
func (b *Buffer) Len() int
func (b *Buffer) Next(n int) []byte
func (b *Buffer) Read(p []byte) (n int, err error)
func (b *Buffer) ReadByte() (byte, error)
...
```

Example также показывает, что top-level functions, возвращающие type `T` или pointer `*T`, возможно вместе с дополнительным error result, показываются рядом с type `T` и его methods как предполагаемые constructors `T`.

По умолчанию programmer может предполагать, что top-level function безопасно вызывать из нескольких goroutines; отдельно это писать не требуется.

С другой стороны, использование instance type любым способом, включая вызов method, обычно предполагается ограниченным одной goroutine одновременно.

Если methods, безопасные для concurrent use, не описаны в type comment, их следует документировать в per-method comments:

```go
package sql

// Close returns the connection to the connection pool.
// All operations after a Close will return with ErrConnDone.
// Close is safe to call concurrently with other operations and will
// block until all other operations finish. It may be useful to first
// cancel any used context and then call Close directly after.
func (c *Conn) Close() error {
    ...
}
```

Doc comments functions и methods должны сосредоточиваться на том, что operation возвращает или делает, и описывать то, что необходимо знать caller.

Особенно важно документировать special cases:

```go
package math

// Sqrt returns the square root of x.
//
// Special cases are:
//
//  Sqrt(+Inf) = +Inf
//  Sqrt(±0) = ±0
//  Sqrt(x < 0) = NaN
//  Sqrt(NaN) = NaN
func Sqrt(x float64) float64 {
    ...
}
```

Doc comments не должны объяснять internal details, например algorithm текущей implementation. Для этого лучше использовать comments внутри body function.

Если asymptotic time или space bounds особенно важны callers, их можно указать:

```go
package sort

// Sort sorts data in ascending order as determined by the Less method.
// It makes one call to data.Len to determine n and O(n*log(n)) calls to
// data.Less and data.Swap. The sort is not guaranteed to be stable.
func Sort(data Interface) {
    ...
}
```

Поскольку этот comment не упоминает конкретный sorting algorithm, implementation легче заменить другим algorithm в будущем.

## Consts {#const}

Syntax declarations Go позволяет группировать declarations. В этом случае один doc comment может вводить группу связанных constants, а отдельные constants могут иметь только короткие end-of-line comments.

```go
package scanner // import "text/scanner"

// The result of Scan is one of these tokens or a Unicode character.
const (
    EOF = -(iota + 1)
    Ident
    Int
    Float
    Char
    ...
)
```

Иногда группе вообще не нужен doc comment:

```go
package unicode // import "unicode"

const (
    MaxRune         = '\U0010FFFF' // maximum valid Unicode code point.
    ReplacementChar = '\uFFFD'     // represents invalid code points.
    MaxASCII        = '\u007F'     // maximum ASCII value.
    MaxLatin1       = '\u00FF'     // maximum Latin-1 value.
)
```

Ungrouped constants обычно заслуживают полноценного doc comment, начинающегося с complete sentence:

```go
package unicode

// Version is the Unicode edition from which the tables are derived.
const Version = "13.0.0"
```

Typed constants показываются рядом с declaration их type, поэтому часто у const group нет собственного doc comment и используется type comment:

```go
package syntax

// An Op is a single regular expression operator.
type Op uint8

const (
    OpNoMatch        Op = 1 + iota // matches no strings
    OpEmptyMatch                   // matches empty string
    OpLiteral                      // matches Runes sequence
    OpCharClass                    // matches Runes interpreted as range pair list
    OpAnyCharNotNL                 // matches any character except newline
    ...
)
```

HTML presentation см. в [`regexp/syntax.Op`](https://pkg.go.dev/regexp/syntax#Op).

## Vars {#var}

Conventions для variables совпадают с conventions для constants.

Пример grouped variables:

```go
package fs

// Generic file system errors.
// Errors returned by file systems can be tested against these errors
// using errors.Is.
var (
    ErrInvalid    = errInvalid()    // "invalid argument"
    ErrPermission = errPermission() // "permission denied"
    ErrExist      = errExist()      // "file already exists"
    ErrNotExist   = errNotExist()   // "file does not exist"
    ErrClosed     = errClosed()     // "file already closed"
)
```

Single variable:

```go
package unicode

// Scripts is the set of Unicode script tables.
var Scripts = map[string]*RangeTable{
    "Adlam":                 Adlam,
    "Ahom":                  Ahom,
    "Anatolian_Hieroglyphs": Anatolian_Hieroglyphs,
    "Arabic":                Arabic,
    "Armenian":              Armenian,
    ...
}
```

## Syntax {#syntax}

Go doc comments используют простой syntax, поддерживающий paragraphs, headings, links, lists и preformatted code blocks.

Чтобы comments оставались лёгкими и читаемыми в source files, сложные features вроде font changes или raw HTML не поддерживаются. Если смотреть с точки зрения Markdown, syntax можно считать упрощённым subset Markdown.

Standard formatter [`gofmt`](https://go.dev/cmd/gofmt) приводит doc comments к canonical formatting для этих features.

`gofmt` старается сохранить readability и user control над тем, как comments выглядят в source code, но корректирует presentation, чтобы semantic meaning comment было яснее — аналогично тому, как обычный source `1+2 * 3` переформатируется в `1 + 2*3`.

`gofmt` удаляет leading и trailing blank lines из doc comments. Если все lines comment начинаются одинаковой последовательностью spaces и tabs, этот prefix удаляется.

### Paragraphs {#paragraphs}

Paragraph — span unindented non-blank lines.

Пара consecutive backticks (``) интерпретируется как Unicode left quote `“`, а пара consecutive single quotes (`''`) — как Unicode right quote `”`.

`gofmt` сохраняет line breaks внутри paragraph text и не rewrap'ит text. Это позволяет использовать semantic linefeeds.

Repeated blank lines между paragraphs заменяются одной blank line. Consecutive backticks и single quotes также преобразуются в соответствующие Unicode quotes.

#### Notes {#notes}

Notes — special comments формы:

```text
MARKER(uid): body
```

`MARKER` должен содержать минимум две uppercase letters `[A-Z]` и обозначает type note. `uid` содержит минимум один character и обычно является username человека, который может предоставить дополнительную information. Colon после `uid` optional.

Notes собираются и отображаются в отдельном section на pkg.go.dev.

```go
// TODO(user1): refactor to use standard library context
// BUG(user2): not cleaned up
var ctx context.Context
```

#### Deprecations {#deprecations}

Paragraphs, начинающиеся с `Deprecated: `, считаются deprecation notices.

Некоторые tools предупреждают при использовании deprecated identifiers. [pkg.go.dev](https://pkg.go.dev) по умолчанию скрывает их docs.

После deprecation marker следует information о причине deprecation и, если применимо, recommendation, что использовать вместо него.

Paragraph не обязан быть последним в doc comment.

```go
// Package rc4 implements the RC4 stream cipher.
//
// Deprecated: RC4 is cryptographically broken and should not be used
// except for compatibility with legacy systems.
//
// This package is frozen and no new functionality will be added.
package rc4

// Reset zeros the key data and makes the Cipher unusable.
//
// Deprecated: Reset can't guarantee that the key will be entirely removed from
// the process's memory.
func (c *Cipher) Reset()
```

### Headings {#headings}

Heading — line, начинающаяся с `#`, затем space и heading text.

Чтобы line распознавалась как heading, она должна быть unindented и отделена от соседнего paragraph text blank lines.

```go
// Package strconv implements conversions to and from string representations
// of basic data types.
//
// # Numeric Conversions
//
// The most common numeric conversions are [Atoi] (string to int) and [Itoa] (int to string).
...
package strconv
```

Следующие examples не являются headings:

```go
// #This is not a heading, because there is no space.
//
// # This is not a heading,
// # because it is multiple lines.
//
// # This is not a heading,
// because it is also multiple lines.
//
// The next paragraph is not a heading, because there is no additional text:
//
// #
//
// In the middle of a span of non-blank lines,
// # this is not a heading either.
//
//     # This is not a heading, because it is indented.
```

Syntax `#` для headings появился в Go 1.19.

До Go 1.19 headings определялись implicit по single-line paragraphs, удовлетворявшим определённым conditions, прежде всего отсутствию terminating punctuation.

`gofmt` переформатирует lines, которые старые versions Go считали implicit headings, используя explicit `#` headings.

Если такое преобразование неверно и line не должна была быть heading, проще всего превратить её в обычный paragraph: добавить terminating punctuation, например period или colon, либо разбить line на две.

### Links {#links}

Span unindented non-blank lines определяет link targets, если каждая line имеет форму:

```text
[Text]: URL
```

В другом text того же doc comment `[Text]` становится link на URL.

Пример:

```go
// Package json implements encoding and decoding of JSON as defined in
// [RFC 7159]. The mapping between JSON and Go values is described
// in the documentation for the Marshal and Unmarshal functions.
//
// For an introduction to this package, see the article
// “[JSON and Go].”
//
// [RFC 7159]: https://tools.ietf.org/html/rfc7159
// [JSON and Go]: https://golang.org/doc/articles/json_and_go.html
package json
```

Размещение URLs в отдельном section минимально нарушает flow основного text и примерно соответствует shortcut reference link format Markdown без optional title.

Если соответствующей URL declaration нет, `[Text]` не становится hyperlink, кроме doc links, описанных ниже, а square brackets сохраняются при отображении.

Каждый doc comment рассматривается отдельно: link target definitions одного comment не влияют на другие comments.

Хотя blocks link target definitions могут находиться между обычными paragraphs, `gofmt` переносит все definitions в конец doc comment максимум в два blocks:

1. targets, на которые действительно есть references;
2. targets, которые нигде не используются.

Отдельный block unused targets облегчает поиск typos либо удаление больше не нужных definitions.

Plain text, распознанный как URL, автоматически превращается в link в HTML rendering.

### Doc links {#doclinks}

Doc links имеют формы `[Name1]` или `[Name1.Name2]` для references на exported identifiers текущего package, а также `[pkg]`, `[pkg.Name1]` или `[pkg.Name1.Name2]` для identifiers других packages.

Пример:

```go
package bytes

// ReadFrom reads data from r until EOF and appends it to the buffer, growing
// the buffer as needed. The return value n is the number of bytes read. Any
// error except [io.EOF] encountered during the read is also returned. If the
// buffer becomes too large, ReadFrom will panic with [ErrTooLarge].
func (b *Buffer) ReadFrom(r io.Reader) (n int64, err error) {
    ...
}
```

Bracketed text symbol link может содержать optional leading `*`, что позволяет удобно ссылаться на pointer types, например `[*bytes.Buffer]`.

При references на другие packages `pkg` может быть либо full import path, либо assumed package name существующего import.

Assumed package name — identifier в renamed import либо name, которое предполагает `goimports`. Если это предположение неверно, `goimports` вставляет rename, поэтому правило работает практически для всего Go code.

Например, если текущий package импортирует `encoding/json`, можно писать `[json.Decoder]` вместо `[encoding/json.Decoder]`.

Если разные source files одного package импортируют разные packages с одинаковым name, shorthand ambiguous и использовать его нельзя.

`pkg` считается full import path только если он начинается с domain name — path element с dot — либо является package стандартной библиотеки (`[os]`, `[encoding/json]` и т. п.).

Например, `[os.File]` и `[example.com/sys.File]` являются documentation links, хотя второй может быть broken link. `[os/sys.File]` не является doc link, потому что package `os/sys` отсутствует в standard library.

Чтобы избежать conflicts с maps, generics и array types, doc link должен быть и preceded, и followed одним из: punctuation, spaces, tabs, start/end line.

Например, `map[ast.Expr]TypeAndValue` не содержит doc link.

### Lists {#lists}

List — span indented или blank lines, который иначе был бы code block, где первая indented line начинается с bullet list marker либо numbered list marker.

Bullet list marker — один из `*`, `+`, `-`, `•`, после которого идёт space или tab и text. Каждая line, начинающаяся с bullet marker, создаёт новый list item.

```go
package url

// PublicSuffixList provides the public suffix of a domain. For example:
//   - the public suffix of "example.com" is "com",
//   - the public suffix of "foo1.foo2.foo3.co.uk" is "co.uk", and
//   - the public suffix of "bar.pvt.k12.ma.us" is "pvt.k12.ma.us".
//
// Implementations of PublicSuffixList must be safe for concurrent use by
// multiple goroutines.
//
// An implementation that always returns "" is valid and may be useful for
// testing but it is not secure: it means that the HTTP server for foo.com can
// set a cookie for bar.com.
//
// A public suffix list implementation is in the package
// golang.org/x/net/publicsuffix.
type PublicSuffixList interface {
    ...
}
```

Numbered list marker — decimal number любой длины, затем `.` или `)`, затем space/tab и text. Каждая line с number marker начинает новый item. Numbers сохраняются как есть и не renumber'ятся.

```go
package path

// Clean returns the shortest path name equivalent to path
// by purely lexical processing. It applies the following rules
// iteratively until no further processing can be done:
//
//  1. Replace multiple slashes with a single slash.
//  2. Eliminate each . path name element (the current directory).
//  3. Eliminate each inner .. path name element (the parent directory)
//     along with the non-.. element that precedes it.
//  4. Eliminate .. elements that begin a rooted path:
//     that is, replace "/.." by "/" at the beginning of a path.
//
// The returned path ends in a slash only if it is the root "/".
//
// If the result of this process is an empty string, Clean
// returns the string ".".
//
// See also Rob Pike, “[Lexical File Names in Plan 9].”
//
// [Lexical File Names in Plan 9]: https://9p.io/sys/doc/lexnames.html
func Clean(path string) string {
    ...
}
```

List items содержат только paragraphs, не code blocks и не nested lists. Это устраняет ambiguity вокруг подсчёта spaces и tabs при inconsistent indentation.

`gofmt` преобразует bullet lists к marker `-`, двум spaces перед dash и четырём spaces indentation continuation lines.

Numbered lists форматируются с одним space перед number, period после number и четырьмя spaces indentation для continuation lines.

Blank line между list и предыдущим paragraph сохраняется, но не требуется. Между list и следующим paragraph/heading `gofmt` вставляет blank line.

### Code blocks {#code}

Code block — span indented или blank lines, не начинающийся с bullet/numbered marker. Он отображается как preformatted text (`<pre>` в HTML).

Часто code blocks содержат Go code:

```go
package sort

// Search uses binary search...
//
// As a more whimsical example, this program guesses your number:
//
//  func GuessingGame() {
//      var s string
//      fmt.Printf("Pick an integer from 0 to 100.\n")
//      answer := sort.Search(100, func(i int) bool {
//          fmt.Printf("Is your number <= %d? ", i)
//          fmt.Scanf("%s", &s)
//          return s != "" && s[0] == 'y'
//      })
//      fmt.Printf("Your number is %d.\n", answer)
//  }
func Search(n int, f func(int) bool) int {
    ...
}
```

Но code blocks могут содержать и другой preformatted text, например grammar:

```go
package path

// Match reports whether name matches the shell pattern.
// The pattern syntax is:
//
//  pattern:
//      { term }
//  term:
//      '*'         matches any sequence of non-/ characters
//      '?'         matches any single non-/ character
//      '[' [ '^' ] { character-range } ']'
//                  character class (must be non-empty)
//      c           matches character c (c != '*', '?', '\\', '[')
//      '\\' c      matches character c
//
//  character-range:
//      c           matches character c (c != '\\', '-', ']')
//      '\\' c      matches character c
//      lo '-' hi   matches character c for lo <= c <= hi
//
// Match requires pattern to match all of name, not just a substring.
// The only possible returned error is [ErrBadPattern], when pattern
// is malformed.
func Match(pattern, name string) (matched bool, err error) {
    ...
}
```

`gofmt` indents все lines code block одним tab, заменяя любой другой common indentation non-blank lines. Также он вставляет blank line до и после code block, явно отделяя его от surrounding paragraph text.

### Directives {#directives}

Directive comments вроде `//go:generate` не считаются частью doc comment и не попадают в rendered documentation.

`gofmt` переносит directive comments в конец doc comment после blank line.

```go
package regexp

// An Op is a single regular expression operator.
//
//go:generate stringer -type Op -trimprefix Op
type Op uint8
```

Directive comment — line, matching regular expression:

```text
//(line |extern |export |[a-z0-9]+:[a-z0-9])
```

Tools могут определять собственные directive comments формы:

```text
//toolname:directive arguments
```

Tool directives соответствуют regular expression:

```text
//([a-z0-9]+):([a-z0-9]\PZ*)($|\pZ+)(.*)
```

Первая group — tool name, вторая — directive name. Optional arguments отделяются от directive name одним или несколькими Unicode whitespace characters.

Каждый tool может задавать собственный argument syntax, но common convention — последовательность space-separated arguments, где argument может быть bare word либо double-quoted/backtick-quoted Go string.

Tool name `go` зарезервирован Go toolchain.

Function [`go/ast.ParseDirective`](https://pkg.go.dev/go/ast#ParseDirective) и связанные types разбирают tool directive syntax.

## Частые ошибки и ловушки {#mistakes}

Правило, согласно которому любой span indented или blank lines в doc comment отображается как code block, существует с первых версий Go.

Историческое отсутствие поддержки doc comments в `gofmt` привело к множеству comments, где indentation использовалась без намерения создать code block.

Например, следующая unindented list всегда интерпретировалась `godoc` как three-line paragraph, после которого идёт one-line code block:

```go
package http

// cancelTimerBody is an io.ReadCloser that wraps rc with two features:
// 1) On Read error or close, the stop func is called.
// 2) On Read failure, if reqDidTimeout is true, the error is wrapped and
//    marked as net.Error that hit its timeout.
type cancelTimerBody struct {
    ...
}
```

`go doc` отображал это так:

```text
cancelTimerBody is an io.ReadCloser that wraps rc with two features:
1) On Read error or close, the stop func is called. 2) On Read failure,
if reqDidTimeout is true, the error is wrapped and

    marked as net.Error that hit its timeout.
```

Похожая проблема с command: comment ниже является one-line paragraph, за которым идёт one-line code block:

```go
package smtp

// localhostCert is a PEM-encoded TLS cert generated from src/crypto/tls:
//
// go run generate_cert.go --rsa-bits 1024 --host 127.0.0.1,::1,example.com \
//     --ca --start-date "Jan 1 00:00:00 1970" --duration=1000000h
var localhostCert = []byte(`...`)
```

`go doc` отображал:

```text
localhostCert is a PEM-encoded TLS cert generated from src/crypto/tls:

go run generate_cert.go --rsa-bits 1024 --host 127.0.0.1,::1,example.com \

    --ca --start-date "Jan 1 00:00:00 1970" --duration=1000000h
```

Ещё example: comment ниже является two-line paragraph, где вторая line — `{`, затем идёт six-line indented code block и one-line paragraph `}`:

```go
// On the wire, the JSON will look something like this:
// {
//  "kind":"MyAPIObject",
//  "apiVersion":"v1",
//  "myPlugin": {
//      "kind":"PluginA",
//      "aOption":"foo",
//  },
// }
```

`go doc` отображал его так:

```text
On the wire, the JSON will look something like this: {

    "kind":"MyAPIObject",
    "apiVersion":"v1",
    "myPlugin": {
        "kind":"PluginA",
        "aOption":"foo",
    },

}
```

Ещё одна common mistake — unindented Go function definition или block statement, аналогично окружённые `{` и `}`.

Появление reformatting doc comments в `gofmt` Go 1.19 сделало такие ошибки заметнее, добавляя blank lines вокруг code blocks.

Анализ 2022 года показал, что draft Go 1.19 `gofmt` вообще изменял только около 3% doc comments в публичных Go modules.

Если рассматривать только изменённые comments:

- примерно 87% reformatting сохраняли structure, которую человек естественно видел в исходном comment;
- примерно 6% ошибочно трактовали unindented lists, multiline shell commands и brace-delimited code blocks.

На основе анализа Go 1.19 `gofmt` применяет несколько heuristics, объединяющих unindented lines с соседними indented list/code blocks.

После этих adjustments examples выше форматируются так:

```go
// cancelTimerBody is an io.ReadCloser that wraps rc with two features:
//  1. On Read error or close, the stop func is called.
//  2. On Read failure, if reqDidTimeout is true, the error is wrapped and
//     marked as net.Error that hit its timeout.
```

```go
// localhostCert is a PEM-encoded TLS cert generated from src/crypto/tls:
//
//  go run generate_cert.go --rsa-bits 1024 --host 127.0.0.1,::1,example.com \
//      --ca --start-date "Jan 1 00:00:00 1970" --duration=1000000h
```

```go
// On the wire, the JSON will look something like this:
//
//  {
//      "kind":"MyAPIObject",
//      "apiVersion":"v1",
//      "myPlugin": {
//          "kind":"PluginA",
//          "aOption":"foo",
//      },
//  }
```

Такое reformatting делает meaning яснее и одновременно позволяет comments корректно render'иться в более старых versions Go.

Если heuristic принимает неправильное решение, его можно override, вставив blank line и явно отделив paragraph text от non-paragraph text.

Даже с этими heuristics некоторые существующие comments требуют manual correction.

Самая распространённая ошибка — indentation wrapped line обычного unindented text:

```go
// TODO Revisit this design. It may make sense to walk those nodes
//      only once.

// According to the document:
// "The alignment factor (in bytes) that is used to align the raw data of sections in
//  the image file. The value should be a power of 2 between 512 and 64 K, inclusive."
```

В обоих examples последняя line indented и поэтому становится code block. Исправление — убрать indentation.

Другая common mistake — не indent'ить wrapped line элемента list или code block:

```go
// Uses of this error model include:
//
//   - Partial errors. If a service needs to return partial errors to the
// client,
//     it may embed the `Status` in the normal response to indicate the
// partial
//     errors.
//
//   - Workflow errors. A typical workflow has multiple steps. Each step
// may
//     have a `Status` message for error reporting.
```

Исправление — indent wrapped lines.

Go doc comments не поддерживают nested lists, поэтому `gofmt` преобразует:

```go
// Here is a list:
//
//  - Item 1.
//    * Subitem 1.
//    * Subitem 2.
//  - Item 2.
//  - Item 3.
```

в:

```go
// Here is a list:
//
//  - Item 1.
//  - Subitem 1.
//  - Subitem 2.
//  - Item 2.
//  - Item 3.
```

Обычно лучший вариант — переписать text так, чтобы nested lists не требовались: это часто улучшает documentation.

Ещё один возможный workaround — смешивать list markers, поскольку bullet markers не создают list items внутри numbered list и наоборот:

```go
// Here is a list:
//
//  1. Item 1.
//
//     - Subitem 1.
//
//     - Subitem 2.
//
//  2. Item 2.
//
//  3. Item 3.
```
