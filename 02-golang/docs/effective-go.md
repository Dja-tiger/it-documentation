---
title: "Effective Go"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/effective_go.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Effective Go

> [!warning]
> Этот документ был написан к первому публичному релизу Go в 2009 году и **не обновляется активно**. Он остаётся хорошим руководством по идиомам core language, но не охватывает значимые последующие изменения: generics, modules и многие новые libraries. Для современного поведения сверяйтесь со [[spec|спецификацией]], release notes и другими разделами этой базы.

## Введение

Go — open-source язык, ориентированный на простоту, надёжность и эффективность, особенно при разработке крупного software.

Механический перенос C++/Java design в Go обычно даёт неидиоматичный результат. Хороший Go-код начинается с понимания особенностей самого языка и привычных для Go conventions: naming, formatting, package design, error handling, interfaces и concurrency.

`Effective Go` дополняет language specification, Tour of Go и [[code|How to Write Go Code]].

### Примеры

Source стандартной библиотеки Go следует рассматривать одновременно как implementation и как набор примеров идиоматичного Go. Package docs на pkg.go.dev содержат executable examples, которые полезны как reference по conventions и API design.

## Formatting

Go сознательно минимизирует споры о code style: formatting выполняет инструмент.

Используйте:

```bash
gofmt -w .
```

или на уровне packages:

```bash
go fmt ./...
```

`gofmt` нормализует indentation и vertical alignment, включая comments.

Исходник:

```go
type T struct {
    name string // name of the object
    value int // its value
}
```

после `gofmt`:

```go
type T struct {
    name  string // name of the object
    value int    // its value
}
```

Практические conventions:

- indentation — tabs, как выдаёт `gofmt`;
- жёсткого line-length limit нет; если строка стала плохо читаемой, разбейте выражение и indent continuation;
- в `if`, `for`, `switch` круглые скобки вокруг condition не нужны;
- не пытайтесь «переспорить» formatter ручным spacing.

## Comments

Go поддерживает `/* ... */` и `//`. В обычном коде преобладают line comments.

Comment непосредственно перед top-level declaration является documentation comment. Полные современные правила вынесены в [[comment|Go Doc Comments]].

## Names

Имя в Go имеет semantic effect: identifier exported за пределы package, если начинается с upper-case Unicode letter.

### Package names

Хорошее package name:

- short;
- lower-case;
- обычно одно слово;
- без underscore и unnecessary mixedCaps.

Package directory `encoding/base64` импортируется как:

```go
import "encoding/base64"
```

и package называется `base64`, а не `encoding_base64`.

Используйте package qualifier, чтобы избежать repetition:

- `bufio.Reader`, а не `bufio.BufReader`;
- `ring.New`, а не `ring.NewRing`;
- `once.Do`, а не длинное дублирующее имя.

Не используйте dot-import (`import . "pkg"`) в production code без очень специфичной причины.

### Getters

Go не требует `Get` prefix:

```go
owner := obj.Owner()
obj.SetOwner(user)
```

Getter — `Owner`, setter — `SetOwner`.

### Interface names

Single-method interfaces традиционно получают имя method + `-er`:

- `Reader`;
- `Writer`;
- `Formatter`.

Если method семантически совпадает с известным contract, сохраняйте canonical name/signature. Например string representation — `String() string`, не `ToString()`.

### MixedCaps

Для multiword identifiers используйте `MixedCaps`/`mixedCaps`, а не underscores.

## Semicolons

Grammar использует semicolons, но lexer вставляет их автоматически. После newline semicolon вставляется, если предыдущий token может завершать statement: identifier/literal либо, например:

```text
break continue fallthrough return ++ -- ) }
```

Поэтому opening brace control structure должен находиться на той же строке:

```go
if x > 0 {
    return x
}
```

а не:

```go
if x > 0
{
    return x
}
```

Explicit semicolons практически нужны только в compact forms вроде classic `for init; cond; post`.

## Control structures

Go имеет `if`, единый `for`, мощный `switch`, type switch и `select`. `while`/`do-while` отсутствуют.

### `if`

```go
if x > 0 {
    return y
}
```

`if` допускает initialization statement:

```go
if err := file.Chmod(0o664); err != nil {
    return err
}
```

Если error branch завершает flow (`return`, `break`, `continue`, `goto`), обычно не нужен `else`:

```go
f, err := os.Open(name)
if err != nil {
    return err
}
codeUsing(f)
```

Так happy path остаётся слева и идёт вниз по странице.

### Redeclaration и `:=`

Short declaration может redeclare уже существующую variable, если:

- declaration находится в том же lexical block;
- хотя бы одна variable слева действительно новая.

Типичный pattern:

```go
f, err := os.Open(name)
// ...
d, err := f.Stat()
```

`err` переиспользуется, `d` новая.

### `for`

Три основные формы:

```go
for init; condition; post {
}
```

```go
for condition {
}
```

```go
for {
}
```

`range` итерирует arrays/slices/strings/maps/channels и другие supported range operands согласно текущей language specification.

Classic idiom:

```go
for key, value := range oldMap {
    newMap[key] = value
}
```

Если index/value не нужен, используйте `_` или единственную variable:

```go
for _, value := range slice {
    use(value)
}
```

### `switch`

Go `switch` не требует constant expressions и не имеет implicit fallthrough.

```go
switch c {
case ' ', '?', '&', '=', '#', '+', '%':
    return true
}
```

Можно писать expression-less switch:

```go
switch {
case t.Hour() < 12:
    return "Good morning"
case t.Hour() < 17:
    return "Good afternoon"
default:
    return "Good evening"
}
```

Если нужен C-like fallthrough, используйте explicit `fallthrough`, но это редкий pattern.

Labelled `break`/`continue` позволяют управлять outer loop:

```go
Loop:
for {
    switch {
    case done:
        break Loop
    }
}
```

### Type switch

```go
switch v := x.(type) {
case bool:
    fmt.Printf("bool %t\n", v)
case int:
    fmt.Printf("int %d\n", v)
default:
    fmt.Printf("unexpected %T\n", v)
}
```

Variable `v` имеет соответствующий concrete type внутри single-type case.

## Functions

### Multiple returns

Go functions могут возвращать несколько values — это базовый idiom для result + error:

```go
func (f *File) Write(b []byte) (n int, err error)
```

Так API не кодирует error через magic sentinel вроде `-1` и может вернуть partial progress вместе с error.

### Named results

```go
func nextInt(b []byte, pos int) (value, nextPos int) {
    // ...
    return
}
```

Named results — обычные local variables, initialized zero values. Bare `return` возвращает текущие values. Используйте это, когда имена действительно документируют API; слишком длинные functions с implicit return часто читаются хуже.

### `defer`

`defer` планирует call непосредственно перед возвратом surrounding function.

```go
f, err := os.Open(name)
if err != nil {
    return err
}
defer f.Close()
```

Преимущества:

- cleanup находится рядом с acquisition;
- cleanup выполняется на всех return paths;
- arguments deferred call вычисляются **в момент `defer`**, а не позднее;
- deferred calls выполняются LIFO.

```go
for i := 0; i < 5; i++ {
    defer fmt.Printf("%d ", i)
}
```

при return печатает:

```text
4 3 2 1 0
```

`defer` function-scoped, не block-scoped. Это важно и для cleanup, и для `panic`/`recover` patterns.

## Data

### `new`

`new(T)` выделяет storage для zero value `T` и возвращает `*T`.

```go
p := new(bytes.Buffer)
```

Полезный Go design principle: делайте zero value type пригодным к использованию без отдельного constructor, если это возможно. `bytes.Buffer` и `sync.Mutex` — canonical examples.

Начиная с Go 1.26 `new` также принимает value expression:

```go
p := new(int64(300))
```

`p` имеет type `*int64` и указывает на `300`.

### Composite literals и constructors

```go
return &File{fd: fd, name: name}
```

Возвращать pointer на local value безопасно: compiler/runtime обеспечат appropriate lifetime.

Prefer keyed struct literals для exported/long-lived structures, чтобы код не зависел от positional field order.

Zero literal:

```go
&File{}
```

семантически близок к `new(File)`.

### `make`

`make` применяется только к:

- slices;
- maps;
- channels.

Он инициализирует internal runtime data structure и возвращает value самого type, а не pointer.

```go
s := make([]int, 10, 100)
m := make(map[string]int)
c := make(chan int, 16)
```

Коротко:

- `new(T)` → `*T` на zeroed value;
- `make(T, ...)` → initialized `T` для slice/map/channel.

### Arrays

Arrays в Go — **values**. Assignment/pass копирует весь array.

Size входит в type:

```go
[10]int
[20]int
```

— разные types.

В API чаще используют slices, а arrays полезны как fixed-size values/internal storage.

### Slices

Slice — descriptor над underlying array, поэтому копирование slice не копирует элементы.

```go
func Sum(a []int) int {
    total := 0
    for _, v := range a {
        total += v
    }
    return total
}
```

Изменение `a[i]` видно caller'у, если slices разделяют backing array.

Length и capacity:

```go
len(s)
cap(s)
```

Re-slicing не может превышать capacity без соответствующей full-slice/valid bound semantics.

### Two-dimensional slices

Go не имеет отдельного matrix type. Обычно используют:

```go
picture := make([][]uint8, height)
for i := range picture {
    picture[i] = make([]uint8, width)
}
```

или один contiguous allocation + нарезку rows, если нужна locality/меньше allocations.

### Maps

Map keys должны иметь equality operation. Slices/functions/maps не являются map keys.

```go
var timeZone = map[string]int{
    "UTC": 0,
    "EST": -5 * 60 * 60,
}
```

Lookup отсутствующего key возвращает zero value. Для различения missing/zero используйте comma-ok:

```go
seconds, ok := timeZone[tz]
```

Только membership:

```go
_, ok := timeZone[tz]
```

Удаление:

```go
delete(timeZone, "PDT")
```

Удаление отсутствующего key безопасно.

### Printing

`fmt` использует type-aware formatting.

```go
fmt.Printf("%v\n", value)
fmt.Printf("%+v\n", structValue)
fmt.Printf("%#v\n", value)
fmt.Printf("%T\n", value)
fmt.Printf("%q\n", str)
```

- `%v` — default value representation;
- `%+v` — field names для struct;
- `%#v` — Go-syntax-like representation;
- `%T` — dynamic/concrete type;
- `%q` — quoted representation.

Custom default format можно задать:

```go
func (t T) String() string {
    return fmt.Sprintf("%d/%g/%q", t.a, t.b, t.c)
}
```

Не создавайте recursion:

```go
func (m MyString) String() string {
    return fmt.Sprintf("MyString=%s", string(m))
}
```

а не printing `m` в format, который снова вызовет `String()`.

Variadic arguments:

```go
func Println(v ...any) {
    fmt.Println(v...)
}
```

### `append`

Conceptual signature:

```go
func append(slice []T, elements ...T) []T
```

Result обязательно присваивается, потому что backing array может измениться:

```go
s = append(s, x)
s = append(s, other...)
```

## Initialization

### Constants

Constants вычисляются compile-time и могут иметь arbitrary precision до момента materialization в concrete type.

`iota` позволяет строить related constants:

```go
type ByteSize float64

const (
    _           = iota
    KB ByteSize = 1 << (10 * iota)
    MB
    GB
    TB
)
```

Не злоупотребляйте `iota`, если explicit values делают API понятнее.

### Variables

Initialization variables может использовать arbitrary expressions/functions и dependency order package initialization.

```go
var (
    home   = os.Getenv("HOME")
    user   = os.Getenv("USER")
    gopath = os.Getenv("GOPATH")
)
```

### `init`

Каждый source file может иметь:

```go
func init() {
    // initialization
}
```

`init` выполняется после package-level variable initialization и до использования package. Multiple `init` допустимы, но сложная implicit initialization ухудшает reasoning; предпочитайте explicit setup там, где это practical.

## Methods

Methods можно объявлять для named non-pointer/non-interface type, определённого в том же package (современные точные ограничения см. [[spec|spec]]).

```go
type ByteSlice []byte

func (p *ByteSlice) Write(data []byte) (int, error) {
    *p = append(*p, data...)
    return len(data), nil
}
```

### Pointer vs value receiver

Используйте pointer receiver, если:

- method должен изменять receiver;
- receiver large;
- type содержит mutex/non-copyable state;
- consistency method set требует pointer semantics.

Value receiver подходит для small immutable/value-like types.

Compiler автоматически берёт address addressable value при method call, если method требует pointer receiver:

```go
b.Write(data)
```

может означать `(&b).Write(data)`.

## Interfaces и types

Interface определяет behavior через method set; type не объявляет `implements` явно.

```go
type Reader interface {
    Read(p []byte) (n int, err error)
}
```

Любой type с matching method set implements `Reader`.

Это позволяет определять small interfaces рядом с потребителем, а concrete types остаются независимыми от interface hierarchy.

### Conversions и assertions

Type assertion:

```go
str, ok := value.(string)
```

без `ok` failed assertion panics.

Type conversion — compile-time/runtime language conversion между compatible/convertible types:

```go
x := IntSlice(sequence)
```

Не путайте conversion concrete types с assertion из interface dynamic value.

### Interface generality

Go APIs часто принимают минимально необходимый interface (`io.Reader`, `io.Writer`) вместо concrete implementation. Это делает functions reusable для files, buffers, network connections и custom implementations.

### Methods on arbitrary defined types

Methods можно использовать как adapters. Canonical example:

```go
type HandlerFunc func(http.ResponseWriter, *http.Request)

func (f HandlerFunc) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    f(w, r)
}
```

Обычная function получает method и тем самым satisfies `http.Handler`.

## Blank identifier `_`

`_` принимает value любого type и discard'ит его.

### Multiple assignment

```go
_, err := os.Stat(path)
```

Но не discard'ьте errors автоматически:

```go
fi, _ := os.Stat(path) // плохой pattern, если error важен
```

### Unused values/imports во время разработки

Compiler запрещает unused local variables/imports. `_` может временно помочь, но production source лучше очищать. `goimports`/`gopls` автоматически управляют imports.

### Import for side effect

```go
import _ "net/http/pprof"
```

Это explicit signal: package нужен только ради initialization side effects.

### Compile-time interface checks

```go
var _ json.Marshaler = (*RawMessage)(nil)
```

Используйте такой pattern, когда satisfaction interface не проверяется elsewhere static conversion и важно зафиксировать contract compile-time. Не добавляйте механически ко всем types.

## Embedding

Go embedding — не subclassing.

Interface composition:

```go
type ReadWriter interface {
    io.Reader
    io.Writer
}
```

Struct embedding:

```go
type ReadWriter struct {
    *Reader
    *Writer
}
```

Methods embedded field promoted outer type, но receiver method остаётся embedded value, а не outer struct.

Embedding также может делегировать utility methods:

```go
type Job struct {
    Command string
    *log.Logger
}
```

Name conflicts разрешаются по shallowest level; ambiguity на одном level требует explicit qualification.

Embedding implementation detail не следует использовать как замену ясной composition API, если promoted methods случайно расширяют public surface.

## Concurrency

### Share by communicating

Go slogan:

> Не общайтесь, разделяя memory; разделяйте memory, общаясь.

Это не означает запрет mutex. Это рекомендация строить ownership так, чтобы shared mutable state по возможности принадлежал одной goroutine, а coordination шла через channels.

### Goroutines

```go
go list.Sort()
```

`go` запускает function call как independent goroutine в том же address space. Stacks goroutines динамически управляются runtime и обычно значительно дешевле OS threads.

Не путайте concurrency с parallelism: scheduler может выполнять множество goroutines на меньшем/равном/большем наборе OS threads/CPUs.

### Channels

```go
c := make(chan int)
c <- value
value := <-c
```

Unbuffered send/receive synchronizes participants. Buffered channels decouple operations до capacity и полезны для queues/semaphores.

```go
sem := make(chan struct{}, maxConcurrent)
```

### Channels of channels

Channel является first-class value и может передаваться через другой channel. Это позволяет request включать reply channel и строить multiplexed services без shared reply maps.

```go
type Request struct {
    args        []int
    f           func([]int) int
    resultChan  chan int
}
```

Worker получает request, computes result и отправляет ответ в `resultChan`.

### Parallelization

Если iterations independent, work можно распределять по goroutines, но обязательно корректно capture loop value и дождаться completion.

Modern code обычно использует `sync.WaitGroup`, `errgroup`/structured cancellation patterns вместо ad-hoc counting channels, хотя каналы остаются valid primitive.

### Buffered-channel pool

Buffered channel может быть bounded freelist:

```go
select {
case b = <-freeList:
default:
    b = new(Buffer)
}
```

Возврат:

```go
select {
case freeList <- b:
default:
    // pool full: GC освободит object
}
```

Сегодня для общего temporary object pooling часто уместен `sync.Pool`, но channel pattern полезен, когда нужны explicit capacity/ownership semantics.

## Errors

По convention обычные failures возвращаются как `error`:

```go
type error interface {
    Error() string
}
```

Хороший error содержит context:

```go
type PathError struct {
    Op   string
    Path string
    Err  error
}
```

Error strings должны помогать понять origin/operation. Modern Go также использует wrapping (`%w`, `errors.Is`, `errors.As`), которого original 2009 Effective Go не охватывал.

### `panic`

`panic` предназначен для действительно unrecoverable/internal invariant failures, а не как обычная замена return error.

```go
if impossible {
    panic("invariant violated")
}
```

Library APIs по возможности должны возвращать errors, а не заставлять callers ловить panic.

### `recover`

`recover` работает только при вызове из deferred function в panicking goroutine.

```go
defer func() {
    if v := recover(); v != nil {
        log.Printf("request failed: %v", v)
    }
}()
```

Нормальный pattern — использовать panic/recover **внутри package boundary**, если это делает internal parser/algorithm проще, а наружу преобразовать known panic type в normal `error`. Не скрывайте unexpected runtime panics.

## Web server example

Original Effective Go завершает guide небольшим HTTP server и демонстрирует центральную силу interfaces: `http.Handler` может реализовать struct, integer-like type, channel или function adapter.

Canonical adapter:

```go
type HandlerFunc func(ResponseWriter, *Request)

func (f HandlerFunc) ServeHTTP(w ResponseWriter, req *Request) {
    f(w, req)
}
```

Именно поэтому обычная function подходящей signature может быть превращена в HTTP handler.

Современный `net/http` и `html/template` сохраняют тот же fundamental design: маленькие interfaces + adapters + composable types.

## Что из документа считать современным

По-прежнему фундаментальны:

- `gofmt`;
- package/naming idioms;
- explicit errors;
- useful zero values;
- slices/maps/interfaces;
- small interfaces;
- composition/embedding;
- goroutines/channels;
- `defer`;
- `panic/recover` как ограниченный internal mechanism.

Документ не покрывает или покрывает исторически:

- modules/workspaces;
- generics;
- modern `errors.Is`/`errors.As`/wrapping;
- current loop-variable semantics;
- current `encoding/json/v2`;
- current toolchain directives/security/runtime features.

Для этих тем используйте современные страницы этой базы.
