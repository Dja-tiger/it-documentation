---
title: "Спецификация языка Go 1.27"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/go"
upstream_path: "doc/go_spec.html"
upstream_ref: "go1.27.1"
translation_status: "translated"
---

# Спецификация языка Go 1.27

Эта страница следует нормативной спецификации из `golang/go@go1.27.1`. Если tutorial, FAQ или старый guide расходится с этой страницей, приоритет имеет текущая language specification.

## Введение

Go — strongly typed, garbage-collected язык с explicit support concurrency. Programs состоят из packages, чьи свойства позволяют эффективно управлять dependencies.

Syntax компактна и регулярна; implementations должны соблюдать semantics, определённые specification, включая compile-time constraints и runtime panics.

## Нотация

Grammar записывается в EBNF:

```text
Syntax      = { Production } .
Production  = production_name "=" [ Expression ] "." .
Expression  = Alternative { "|" Alternative } .
Alternative = Term { Term } .
Term        = production_name | token [ "…" token ] | Group | Option | Repetition .
Group       = "(" Expression ")" .
Option      = "[" Expression "]" .
Repetition  = "{" Expression "}" .
```

Lower-case production names обычно обозначают lexical tokens; CamelCase — syntactic non-terminals.

`a … b` обозначает range lexical alternatives от `a` до `b`.

## Source code representation

Source — Unicode text, encoded UTF-8. Implementation может ограничивать BOM только началом file и может игнорировать UTF-8 BOM в начале. NUL character недопустим.

Implementation может ограничивать размер source file, literal и numeric constant, но limit должен быть documented.

### Characters

Термины:

```text
newline        = U+000A .
unicode_char   = arbitrary Unicode code point except newline .
unicode_letter = Unicode class Letter or '_' .
unicode_digit  = Unicode class Nd .
```

Underscore `_` считается letter для identifiers.

## Lexical elements

### Comments

Поддерживаются:

```go
// line comment

/* general
   comment */
```

General comment не может содержать nested `/*` и заканчивается первым `*/`.

Comment не может начинаться внутри rune/string literal.

### Tokens и semicolons

Tokens делятся на identifiers, keywords, operators/punctuation и literals.

Semicolon автоматически вставляется после последнего token строки, если это:

- identifier;
- integer/floating/imaginary/rune/string literal;
- `break`, `continue`, `fallthrough`, `return`;
- `++`, `--`, `)`, `]`, `}`.

Semicolon также можно опустить перед `)` или `}`.

### Identifiers

```text
identifier = letter { letter | unicode_digit } .
```

Примеры:

```text
a
_x9
ThisVariableIsExported
αβ
```

Keywords нельзя использовать как identifiers.

### Keywords

```text
break       default      func         interface    select
case        defer        go           map          struct
chan        else         goto         package      switch
const       fallthrough  if           range        type
continue    for          import       return       var
```

### Operators/punctuation

```text
+  &   +=  &=  &&  ==  !=  (  )
-  |   -=  |=  ||  <   <=  [  ]
*  ^   *=  ^=  <-  >   >=  {  }
/  <<  /=  <<= ++  =   :=  ,  ;
%  >>  %=  >>= --  !   ... .  :
&^
&^=
~
```

`~` используется в type terms constraints.

## Integer literals

Decimal, binary, octal и hexadecimal forms:

```go
42
4_2
0600
0_600
0o600
0O600
0xBadFace
0xBad_Face
0b0110
0B_0110
```

Underscore может разделять successive digits и улучшать readability, но не может стоять произвольно.

## Floating-point literals

Decimal и hexadecimal floating literals поддерживают exponent notation.

```go
0.
72.40
072.40
2.71828
1.e+0
6.67428e-11
1E6
.25
.12345E+5
1_5.         // 15.0
0.15e+0_2    // 15.0

0x1p-2       // 0.25
0x2.p10      // 2048.0
0x1.Fp+0     // 1.9375
```

Hexadecimal mantissa требует binary exponent `p`/`P`.

## Imaginary literals

Imaginary literal = numeric literal + `i`:

```go
0i
011i
0.i
2.71828i
1.e+0i
6.67428e-11i
0x1p-2i
```

## Rune literals

Single-quoted rune literal представляет integer Unicode code point либо byte escape.

```go
'a'
'ä'
'本'
'\t'
'\000'
'\x07'
'\u12e4'
'\U00101234'
```

Недопустимы multiple runes, newline, unmatched quote, invalid Unicode scalar/escape.

## String literals

### Raw string

Backticks:

```go
`abc`
`multi
line`
```

Backslashes не имеют special meaning. Carriage returns внутри raw literal удаляются из resulting value.

### Interpreted string

Double quotes:

```go
"Hello, world!\n"
"日本語"
"\u65e5本\U00008a9e"
```

Используются те же escapes, что rune literals, плюс escaped quote/backslash.

String является immutable sequence bytes и может содержать arbitrary bytes, не обязательно valid UTF-8.

# Constants

Constants могут быть boolean, rune, integer, floating-point, complex или string.

Они создаются literals, constant expressions, `const` declarations и некоторыми built-ins.

Predeclared constants:

```text
true false iota
```

Untyped constants имеют **kind**, но ещё не concrete machine type. Это позволяет arbitrary precision compile-time arithmetic в пределах implementation requirements.

Default types:

| Constant kind | Default type |
|---|---|
| boolean | `bool` |
| rune | `rune` (`int32`) |
| integer | `int` |
| floating-point | `float64` |
| complex | `complex128` |
| string | `string` |

### Representability

Constant `x` representable type `T`, если value может быть represented соответствующим value `T` без нарушения rules.

Для type parameter representability должна выполняться для каждого type из type set.

# Variables

Variable — storage location с associated type/value. Zero value используется при отсутствии explicit initialization.

Variable создаётся:

- declarations;
- function parameters/results;
- `new`;
- composite literals/addressing;
- short declarations;
- implicit iteration variables и другими language constructs.

Zero values:

- boolean → `false`;
- numeric → `0`;
- string → `""`;
- pointer/function/interface/slice/channel/map → `nil`;
- array/struct → recursively zeroed elements/fields.

# Types

Type определяет set values и supported operations.

Type может быть denoted type name либо type literal.

```text
Type      = TypeName [ TypeArgs ] | TypeLit | "(" Type ")" .
TypeName  = identifier | QualifiedIdent .
TypeLit   = ArrayType | StructType | PointerType | FunctionType |
            InterfaceType | SliceType | MapType | ChannelType .
```

## Boolean types

Predeclared `bool`; values `true`/`false`.

## Numeric types

### Integers

```text
uint8       0..255
uint16      0..65535
uint32      0..4294967295
uint64      0..2^64-1
int8        -128..127
int16       -32768..32767
int32       -2^31..2^31-1
int64       -2^63..2^63-1
```

Aliases:

```text
byte = uint8
rune = int32
```

`uint`, `int`, `uintptr` implementation-specific size, но `uint`/`int` одинакового size, минимум 32 bits.

### Floating point

```text
float32
float64
```

IEEE 754 binary formats.

### Complex

```text
complex64  // float32 real+imag
complex128 // float64 real+imag
```

## String type

`string` — immutable byte sequence. Length = bytes. Index returns byte, not rune. Address of string byte cannot be taken.

Range по string декодирует UTF-8 и выдаёт byte index + rune; invalid encoding yields `U+FFFD` width 1.

## Array types

```text
ArrayType = "[" ArrayLength "]" ElementType .
```

Length — part of type and non-negative constant representable `int`.

```go
[32]byte
[2*N]struct{ x, y int32 }
```

Arrays are values: assignment copies elements.

## Slice types

```text
SliceType = "[" "]" ElementType .
```

Slice — descriptor contiguous segment underlying array. Zero value `nil`; length/capacity dynamic.

```go
make([]T, length, capacity)
```

Slices may share underlying array.

## Struct types

```text
StructType    = "struct" "{" { FieldDecl ";" } "}" .
FieldDecl     = (IdentifierList Type | EmbeddedField) [ Tag ] .
EmbeddedField = [ "*" ] TypeName [ TypeArgs ] .
Tag           = string_lit .
```

Field names unique среди non-blank direct fields. Export status field определяется capitalization name.

Embedded field может promote fields/methods.

Struct tags участвуют в reflection/package protocols, но игнорируются для некоторых type identity/conversion rules.

### Promoted methods

Если `S` contains embedded `T`, method sets `S`/`*S` получают promoted methods according to receiver rules. Если embedded `*T`, соответствующие methods входят в method sets в соответствии со spec.

## Pointer types

```text
PointerType = "*" BaseType .
```

`*T` points to variable type `T`; zero value `nil`.

```go
var p *Point
```

## Function types

```text
FunctionType = "func" Signature .
Signature    = Parameters [ Result ] .
Result       = Parameters | Type .
```

Function types identical при identical parameter/result types, одинаковой variadic property; names параметров/results не влияют.

Variadic final parameter:

```go
func(prefix string, values ...int)
```

inside function `values` имеет `[]int`.

## Interface types

Interface определяет **type set**.

Value interface может хранить concrete value type, который implements interface.

### Basic interfaces

Только method elements/embedded basic interfaces:

```go
type Reader interface {
    Read(p []byte) (n int, err error)
}
```

Type `T` implements interface, если method set `T` включает required methods (с rules type sets для general interfaces).

### Embedded interfaces

```go
type ReadWriter interface {
    Reader
    Writer
}
```

Type set — intersection constraints.

### General interfaces / type elements

Interfaces, используемые как constraints, могут включать type terms:

```go
type Signed interface {
    ~int | ~int8 | ~int16 | ~int32 | ~int64
}
```

`~T` означает types с underlying type `T`.

Union terms должны удовлетворять restrictions specification; type sets unioned/intersected согласно elements.

Interfaces с non-method type elements обычно могут использоваться только как constraints, а не ordinary variable types.

### `comparable`

Predeclared constraint `comparable` описывает strictly comparable non-interface types. Начиная с Go 1.20 comparable ordinary interface type arguments могут **satisfy** comparable constraint по специальному exception, даже если сами не implement strictly-comparable type set.

## Map types

```text
MapType = "map" "[" KeyType "]" ElementType .
```

Key type должен support `==`/`!=`; функции/maps/slices не подходят keys.

Zero map `nil`; lookup разрешён, insert в nil map panics.

Comma-ok:

```go
v, ok := m[key]
```

Missing key returns zero element + `false`.

## Channel types

```text
ChannelType = ( "chan" | "chan" "<-" | "<-" "chan" ) ElementType .
```

```go
chan T
chan<- T
<-chan T
```

`make(chan T, capacity)` создаёт channel. Capacity 0 = unbuffered synchronization. Nil channel never ready; send/receive block forever.

## Named types

Named type — defined type либо instantiated defined generic type; predeclared types также named.

## Type identity

Named types всегда distinct, кроме aliases. Unnamed types identical при structural conditions spec:

- arrays same length/element;
- slices same element;
- structs same field sequence/names/types/tags/embedding/export package;
- pointers same base;
- functions same params/results/variadic;
- interfaces define same type set;
- maps same key/element;
- channels same element/direction rules.

## Underlying types

Каждый type имеет underlying type. Для defined type — underlying RHS recursively; для literals — сам literal; для type parameter underlying type определяется constraint rules.

```go
type T1 string
// underlying: string
```

## Method sets

Method set определяет methods, callable through interface satisfaction.

В общих чертах:

- defined type `T`: methods receiver `T`;
- `*T`: methods receiver `T` и `*T`;
- interface: methods type set/interface;
- embedding promotes methods по rules struct embedding.

Call syntax иногда автоматически берёт address/dereference addressable values, но это **не меняет method set** для interface implementation.

# Type declarations

## Alias declarations

```go
type byte = uint8
type NodeList = []*Node
```

Alias обозначает тот же type, не новый defined type.

Generic alias support подчиняется текущим rules type parameters/instantiation.

## Type definitions

```go
type MyString string
type Pair[A, B any] struct {
    A A
    B B
}
```

Defined type distinct от underlying/source types.

При generic definition требуется type parameters list; instantiation создаёт named instantiated type.

# Properties of types and values

## Assignability

Value `x` type `V` assignable variable type `T`, если выполняется одно из spec conditions, включая:

- `V` и `T` identical;
- identical underlying types, и хотя бы один не named type (с type-parameter rules);
- compatible channel assignment;
- `nil` assignable pointer/function/slice/map/channel/interface;
- `x` interface-implementing value assignable interface `T`;
- untyped constant representable `T`;
- type-parameter conditions для всех types в type set.

Assignment не выполняет arbitrary implicit conversions.

## Representability

Untyped constants могут implicit convert, только если value representable target.

## Comparison

Comparable:

- booleans;
- integers/floats/complex;
- strings;
- pointers;
- channels;
- interfaces (runtime dynamic values должны быть comparable для safe equality);
- arrays of comparable elements;
- structs of comparable fields.

Not comparable:

- slices;
- maps;
- functions (кроме comparison с `nil`).

`NaN` obeys IEEE properties, поэтому equality не reflexive для floating values containing NaN.

Strictly comparable используется generics constraint reasoning.

# Blocks и scope

Universe block содержит predeclared identifiers.

Далее:

- package block;
- file block imports;
- function body blocks;
- explicit/implicit blocks control structures.

Scope identifier зависит от declaration kind.

Exported identifier:

1. начинается Unicode uppercase letter;
2. объявлен package block либо field/method name.

# Declarations

## Constant declarations

```go
const Pi = 3.141592653589793
const zero = 0.0

const (
    Sunday = iota
    Monday
    Tuesday
)
```

Empty expression list внутри group повторяет previous non-empty ConstSpec вместе с type, если был.

`iota` — untyped integer ordinal ConstSpec начиная с 0 в каждом constant declaration group.

## Type parameter declarations

```text
TypeParameters = "[" TypeParamList [ "," ] "]" .
TypeParamList   = TypeParamDecl { "," TypeParamDecl } .
TypeParamDecl   = IdentifierList TypeConstraint .
```

Примеры:

```go
[P any]
[S ~[]E, E any]
[K comparable, V any]
```

Каждый type parameter — distinct named placeholder type.

Constraint — interface/type element.

Convenient omission `interface{}` разрешён в parameter list:

```go
[T ~int]
[T int | string]
```

Если parsing single parameter ambiguous (`[P *C]`), используйте explicit interface или trailing comma.

### Constraint satisfaction

Type argument должен satisfy constraint: обычно implement interface/type set. `comparable` имеет специальное Go 1.20 exception для comparable interface arguments.

## Variable declarations

```go
var i int
var x, y = 1, "two"
var p *T
```

Без initializer → zero value. Без explicit type → type соответствующего initialization value; untyped constants получают default type.

`nil` нельзя использовать единственным initializer variable без explicit type.

## Short variable declarations

```go
i := 0
x, y := f()
```

Redeclaration разрешена в same block, если redeclared variable same type и хотя бы одна non-blank variable слева новая.

```go
field1, offset := nextField(str, 0)
field2, offset := nextField(str, offset)
```

Short declaration только внутри functions.

## Function declarations

```text
FunctionDecl = "func" FunctionName [ TypeParameters ] Signature [ FunctionBody ] .
```

Generic function:

```go
func min[T ~int | ~float64](x, y T) T {
    if x < y {
        return x
    }
    return y
}
```

Generic function должен быть instantiated до использования как callable/function value, если inference не выполняет instantiation contextually.

Body может отсутствовать у non-generic declaration implemented externally (например assembly).

## Method declarations

```text
MethodDecl = "func" Receiver MethodName [ TypeParameters ] Signature [ FunctionBody ] .
```

Receiver — один non-variadic parameter; base type defined в том же package, не pointer/interface base definition.

```go
func (p *Point) Scale(factor float64) {
    p.x *= factor
    p.y *= factor
}
```

Для generic receiver type receiver заново объявляет соответствующие receiver type parameter names:

```go
type Pair[A, B any] struct {
    a A
    b B
}

func (p Pair[A, B]) Swap() Pair[B, A] {
    return Pair[B, A]{p.b, p.a}
}
```

### Go 1.27: generic methods

Go 1.27 разрешает **собственные type parameters method**, дополнительно к receiver type parameters:

```go
type List[E any] []E

func (l List[E]) Apply[F any](f func(E) F) List[F] {
    r := make(List[F], len(l))
    for i, x := range l {
        r[i] = f(x)
    }
    return r
}
```

Method name обозначает generic method и должен быть instantiated явно или через supported inference context перед call/value use.

Это изменение `[Go 1.27]`; старые FAQ/статьи, утверждающие, что methods не имеют собственных type parameters, устарели относительно этой specification.

# Expressions

## Operands

Operand может быть literal, identifier, qualified identifier, instantiated generic function/type-related operand либо parenthesized expression.

Blank identifier нельзя использовать как ordinary value operand.

## Qualified identifiers

```go
math.Sin
```

Package должен быть imported; selected identifier exported.

## Composite literals

Создают values structs/arrays/slices/maps:

```go
Point{1, 2}
[]int{1, 2, 3}
map[string]int{"a": 1}
```

### Struct literals

Unkeyed literal требует fields по declaration order и обычно запрещён для struct с unexported fields из другого package.

Keyed literal может опускать unspecified fields → zero.

### Go 1.27: promoted fields как keys

В Go 1.27 keyed struct literal key может обозначать valid selector promoted field, если:

- traversed embedded fields не pointer types;
- key не обозначает promoted field внутри embedded struct, который одновременно задан другим overlapping key;
- duplicate/overlapping selections запрещены.

Пример conceptually:

```go
type Object struct{ name, color string }
type Point3D struct {
    Object
    x, y, z float64
}
```

Current Go 1.27 spec расширяет selector semantics keyed fields; при overlapping direct embedded initialization conflict literal invalid.

### Arrays/slices/maps

Array/slice keys — integer indexes; omitted index = previous + 1.

```go
[10]float32{-1, 4: -0.1, -0.1, 9: -1}
[]Point{{0, 1}, {1, 2}}
```

Map literal требует key для каждого element.

Nested literal element type можно elide, если identical expected element/key type.

## Function literals

```go
f := func(x, y int) int { return x + y }
```

Closures capture surrounding variables by reference to variables (shared storage semantics), не snapshot values автоматически.

Function literals **не могут объявлять type parameters**.

## Selectors

```go
x.f
```

Selector ищет field/method shallowest depth. Если на minimal depth более одного candidate — ambiguous/invalid.

Для pointer to struct field selector действует implicit dereference. Nil pointer field access panics.

Nil interface method call/value evaluation panics.

## Method expressions

```go
T.M
(*T).M
```

Method expression превращает method в function с explicit receiver первым argument.

```go
t.Mv(7)
T.Mv(t, 7)
```

## Method values

```go
f := t.M
```

Receiver expression `t` evaluation/save происходит при создании method value; subsequent calls используют saved receiver.

## Index expressions

`a[x]` применяется array/*array/slice/string/map и type parameters с соответствующими core types.

Out-of-range array/slice/string runtime index panics. Map missing key returns zero element.

## Slice expressions

Simple:

```go
a[low:high]
```

Full:

```go
a[low:high:max]
```

Full form контролирует resulting capacity `max-low`.

Strings можно slice by bytes, producing substring bytes; boundary не обязана быть rune boundary.

## Type assertions

```go
x.(T)
```

`x` interface; assertion требует dynamic type implements target condition.

Safe two-result:

```go
v, ok := x.(T)
```

One-result failed assertion panics.

## Calls

```go
f(a1, a2)
x.M(args)
```

Arguments assignable parameters. Method call допускает implicit `&x` для addressable value, если `(&x)` method set содержит method.

Multi-valued expression может supply arguments при allowed shape.

Variadic call:

```go
Greeting("hello", "A", "B")
Greeting("hello", names...)
```

При `slice...` existing slice передаётся без создания нового variadic backing slice.

## Instantiation

Generic type/function/method instantiated подстановкой type arguments и последующей проверкой constraints.

```go
min[int]
List[string]
list.Apply[string]
```

Для generic **type** все type arguments explicit.

Для generic function/method arguments могут быть partially/completely inferred в поддерживаемых contexts: calls, assignments к known function type, function arguments/results.

Partial type argument list задаёт prefix; omitted suffix inferred.

## Type inference

Inference решает equations между argument/parameter types и constraints.

Два этапа в общем виде:

1. unify typed operands/constraints;
2. для ещё unresolved type parameters использовать kinds/default types untyped constants.

Если не все bound type parameters определены однозначно или constraints не satisfied, inference fails compile-time.

# Operators

Precedence:

```text
*  /  %  <<  >>  &  &^   highest binary level
+  -  |  ^
== != < <= > >=
&&
||                         lowest
```

Unary:

```text
+ - ! ^ * & <-
```

Multiplication operators bind strongest; comparisons same level.

## Arithmetic

Integer:

```text
+ - * / % << >> & | ^ &^
```

Division integers truncates toward zero. Division by zero panics for non-constant runtime divisor; constant zero invalid compile-time.

Signed overflow defined by two's-complement-like deterministic representation rules: operations may overflow but compiler cannot assume overflow never occurs.

Unsigned arithmetic modulo `2^n`.

Floating operations follow IEEE properties subject spec implementation precision rules.

## String concatenation

```go
s := "hello" + " " + "world"
```

## Comparison

```text
== != < <= > >=
```

Ordered operators для integers/floats/strings/type parameters appropriate sets.

Strings compare lexically by bytes.

Pointers equal если same variable/address or both nil with special zero-size caveat implementation; channels equal same channel/both nil; interfaces compare dynamic types/values and panic if dynamic values not comparable.

## Logical

```text
&& || !
```

`&&`/`||` short-circuit left-to-right.

## Address operators

```go
&p
*x
```

`&x` requires addressable operand, кроме allowed composite literal exception. Dereferencing nil pointer panics.

## Receive

```go
v := <-ch
v, ok := <-ch
```

Nil channel receive blocks forever. Closed drained channel returns zero immediately, `ok=false`.

# Conversions

Explicit:

```go
T(x)
```

Constants должны быть representable target.

Non-constant conversions разрешены по spec cases, включая:

- assignable values;
- identical underlying types при named/type-parameter restrictions;
- compatible unnamed pointer underlying bases;
- numeric conversions;
- string ↔ `[]byte`/`[]rune`;
- integer → string;
- slice → array / pointer-to-array при identical element type и runtime length check;
- type parameter set-wise convertible cases.

Numeric conversion overflow не сообщает error; integer truncation defined. Float→integer discards fractional part toward zero; unrepresentable floating conversions implementation-dependent where specified.

String conversions:

```go
string([]byte{...})
[]byte("hello")
[]rune("日本語")
string([]rune{...})
```

Integer → string produces rune encoding, invalid Unicode values replaced `U+FFFD` according to conversion rules.

Go language не имеет general pointer↔integer conversion; specialized unsafe operations — package `unsafe`.

# Constant expressions

Constant expression вычисляется compile-time и содержит только constants/constant-capable operations/functions.

Untyped expression получает kind according operands; representability проверяется при conversion/assignment.

Compile-time arithmetic требует exactness, кроме explicitly rounded conversion to typed float/complex.

# Order of evaluation

Package initialization dependencies имеют отдельные rules. В expression/function call обычные function/method/channel communication operations evaluated lexical left-to-right order where spec defines order.

Однако order некоторых subexpressions, не связанных dependency/specified sequencing, может быть unspecified. Не пишите code, correctness которого зависит от order map iteration или unspecified operand interactions.

# Statements

## Terminating statements

Spec определяет statements, которые гарантированно terminate block: `return`, `goto` under conditions, panic call, infinite for without reachable break, exhaustive terminating switch/select conditions и др. Это используется compile-time missing-return checks.

## Empty / labeled

```go
Label:
    statement
```

Label scope = body containing function; labels distinct from ordinary identifiers.

## Expression statements

Function/method calls и receive operations могут быть statements. Некоторые built-ins ограничены: например `append` result нельзя просто discard как arbitrary call where grammar/semantics forbids.

## Send

```go
ch <- value
```

Channel must permit send; send to nil blocks forever; send on closed channel panics.

## Inc/dec

```go
x++
x--
```

Statements, не expressions.

## Assignment

```go
x = y
a, b = b, a
x += y
```

Multi-assignment сначала evaluates left operands addresses/indexing and right expressions в specified order, затем performs assignments left-to-right.

Assignment copies value stored in variable; references внутри slice/map/interface/etc. остаются references, underlying data не deep-copied.

## `if`

```go
if init; condition {
} else {
}
```

Condition boolean; optional simple statement has scope across condition/branches per block rules.

## `switch`

### Expression switch

Cases evaluated left-to-right/top-to-bottom; first equal match executes. No implicit fallthrough.

```go
switch x := f(); {
case x < 0:
    return -x
default:
    return x
}
```

Empty switch expression = `true`.

`fallthrough` only final non-empty statement non-final expression case.

### Type switch

```go
switch v := x.(type) {
case nil:
case int:
case string:
default:
}
```

Guard operand interface, not type parameter. Single-type case variable gets that type; multi-type/default gets guard expression interface type.

Generic type/type parameter может appear case; после instantiation duplicates выбираются first matching case.

No `fallthrough`.

## `for`

Три forms:

```go
for condition {}
for init; condition; post {}
for {}
```

Начиная с Go 1.22 each iteration classic `for` имеет separate iteration variables, созданные/initialized according to spec; это устраняет historical closure-capture behavior для modern language version.

### `range`

`range` поддерживает operands:

- array / pointer to array;
- slice;
- string;
- map;
- channel;
- integer values (Go 1.22+);
- iterator functions supported current spec (Go 1.23+ range-over-function forms).

Количество iteration values зависит operand.

#### Arrays/slices

```go
for i, v := range a {}
```

index 0..len-1; value copy element.

#### String

index = byte offset UTF-8 rune; value = rune. Invalid encoding → `U+FFFD`, advances one byte.

#### Map

Iteration order **not specified** and can differ each iteration. Entries inserted/deleted during iteration имеют spec-defined inclusion uncertainty/omission rules; не полагайтесь на order.

#### Channel

```go
for v := range ch {}
```

receives until channel closed/drained. Nil channel range blocks forever.

#### Integer

```go
for i := range n {}
```

итерации от 0 до `n-1`; if `n <= 0` no iterations, type rules зависят declared iteration variable/type context.

#### Function iterator

Current Go поддерживает range over functions определённых signatures (yield callbacks). Loop body управляет continuation через generated `yield` function; `break`/return stop iteration. Iterator implementation обязана уважать boolean result yield и не продолжать yield после false.

## `go`

```go
go f(args)
```

Function value/arguments evaluated в calling goroutine, actual call starts independent goroutine. Result values discard; built-in call restrictions apply.

## `select`

```go
select {
case v := <-ch:
case out <- x:
default:
}
```

Execution:

1. channel operands и send RHS evaluated once in source order;
2. если one/more communications can proceed, один выбирается pseudo-random uniformly among ready cases;
3. если none ready и default есть — default;
4. если none ready и no default — block;
5. execute selected communication и statements.

`select {}` blocks forever.

## `return`

Return завершает function и возвращает result values. Named results могут быть returned bare.

Bare return запрещён/ambiguous, если result identifier shadowed в scope, где compiler не может однозначно выполнить semantics.

## `break` / `continue`

`break` завершает innermost `for`, `switch`, `select`; label может target enclosing one.

`continue` начинает next iteration enclosing `for`; label должен обозначать enclosing `for`.

## `goto`

`goto Label` остаётся внутри same function и не может перепрыгнуть так, чтобы новые variables внезапно вошли scope без initialization, либо прыгнуть извне внутрь nested block.

## `fallthrough`

Только expression switch, final statement non-last case; не выполняет следующую case condition, просто переходит к statements следующего clause.

## `defer`

```go
defer f(args)
```

Function value и args evaluated сразу при execution `defer`; call выполняется при возврате surrounding function/panic unwinding.

Deferred calls выполняются reverse order. Они выполняются после установки result parameters `return`, но до actual return caller.

Deferred function может read/modify named results.

Nil deferred function value panics в момент invocation, не в момент `defer`.

# Built-in functions

Built-ins predeclared, но не являются ordinary first-class function values.

## `append`

```go
s = append(s, elems...)
```

Если capacity недостаточна, allocates new underlying array; иначе reuses current. Special case:

```go
bytes = append(bytes, "text"...)
```

## `copy`

```go
n := copy(dst, src)
n := copy(dstBytes, "string")
```

Copies `min(len(src), len(dst))`, overlaps allowed.

## `clear`

Go 1.21+:

```go
clear(m) // delete all map entries
clear(s) // zero all slice elements up to len
```

Nil no-op. Type parameters allowed when type set suitable maps/slices.

## `close`

```go
close(ch)
```

Marks no more sends. Closing nil/already closed channel panics. Send closed panics. Receive drains buffered values then yields zero immediately.

## `complex`, `real`, `imag`

Construct/extract complex values; typed/untyped rules follow operand types. Type-parameter operands not permitted where spec says.

## `delete`

```go
delete(m, key)
```

No-op для missing key/nil map; key assignable map key type.

## `len`, `cap`

`len` applies strings, arrays/*arrays, slices, maps, channels and supported type parameters.

`cap` applies arrays/*arrays, slices, channels and supported type parameters.

Некоторые `len/cap` calls compile-time constants для arrays/string constants when operand has no channel receive/non-constant function calls and size fixed according spec.

## Allocation: `new`

Modern Go supports:

```go
p := new(T)
```

→ pointer to zero `T`.

Начиная с Go 1.26 `new` также может принимать value expression:

```go
p := new(int64(300))
```

→ pointer to newly allocated variable initialized provided value. Exact typing follows current built-in specification.

## `make`

```go
make([]T, len, cap)
make(map[K]V, hint)
make(chan T, cap)
```

Initializes slice/map/channel runtime value. `make` returns `T`, not `*T`.

Invalid negative/too-large runtime sizes panic; constants validated compile-time.

## `min` / `max`

Predeclared Go 1.21+:

```go
min(x, y, ...)
max(x, y, ...)
```

Arguments ordered types or untyped constants with rules spec. Для floating NaN/signed-zero behavior следует exact built-in rules current spec; не используйте их как total-order NaN sanitizer.

## `panic` / `recover`

`panic(v)` starts panicking sequence current goroutine, runs deferred calls while unwinding.

`recover()` stops panicking only when called **directly** by deferred function during panic of same goroutine according exact spec conditions; otherwise returns nil.

`panic(nil)` modern runtime behavior governed language/runtime compatibility settings; see [[godebug|GODEBUG]].

## `print` / `println`

Implementation-specific bootstrapping/debug functions; output format not specified. Не используйте application logging API вместо `fmt`/`log`.

# Packages

Source file:

```go
package math
```

Package name not necessarily final path component but conventionally совпадает.

## Imports

```go
import "lib/math"
import m "lib/math"
import . "lib/math"
import _ "lib/math"
```

- default local package name = declared package name;
- explicit alias changes qualifier;
- dot-import imports exported identifiers directly into file block;
- blank import imports only side effects initialization.

Import declaration scope file-local. Import cycles запрещены.

# Program initialization и execution

## Package initialization

Package-level variables initialize dependency order.

Variable `x` depends on `y`, если initializer/body referenced function/method transitively references `y` under spec rules.

Earliest declaration-ready variable initializes first; multi-value declaration group initializes together.

После variables вызываются все:

```go
func init() {}
```

в source presentation order. `init` нельзя reference/call explicitly как normal identifier.

Package initialization sequential inside single initialization goroutine. `init` может launch goroutines, но next `init` вызывается только после return previous.

## Program initialization

Imported packages initialize before importer, each package once. Complete dependency graph has no import cycle.

## `main`

Executable содержит unimported package:

```go
package main

func main() {}
```

`main` no args/results.

Execution:

1. initialize program packages;
2. call `main.main`;
3. когда `main` returns — process exits, не ожидая остальные goroutines автоматически.

# Errors

Predeclared:

```go
type error interface {
    Error() string
}
```

Convention: `nil` error = no error.

# Run-time panics

Invalid runtime operations (out-of-bounds, nil dereference, send closed channel и т. п.) trigger panic equivalent semantics с implementation-defined `runtime.Error` implementing `error`.

Specific runtime error values не стандартизированы language spec.

# System considerations

## Package `unsafe`

`unsafe` позволяет operations вне type-system safety и portability. Любой такой code требует manual review.

Ключевые APIs current spec:

```go
type Pointer *ArbitraryType

func Alignof(variable ArbitraryType) uintptr
func Offsetof(selector ArbitraryType) uintptr
func Sizeof(variable ArbitraryType) uintptr
func Add(ptr Pointer, len IntegerType) Pointer
func Slice(ptr *ArbitraryType, len IntegerType) []ArbitraryType
func SliceData(slice []ArbitraryType) *ArbitraryType
func String(ptr *byte, len IntegerType) string
func StringData(str string) *byte
```

### `unsafe.Pointer`

Поддерживает restricted conversions между arbitrary pointer types и `uintptr` patterns. Не является license на arbitrary pointer arithmetic; valid patterns documented package `unsafe`.

GC не обязан рассматривать naked `uintptr` как pointer root. Сохранение address как integer через GC/safepoint может нарушить liveness.

### `Sizeof`, `Alignof`, `Offsetof`

Возвращают implementation layout properties. Для constant-size operands calls являются constant expressions `uintptr`.

`Offsetof(s.f)` требует selector reachability без forbidden pointer traversals.

### `unsafe.Add`

```go
unsafe.Add(ptr, n)
```

Equivalent conceptual pointer-byte offset с restricted valid-pointer rules.

### `unsafe.Slice`

Создаёт slice на memory starting `ptr`, length/cap `len`; invalid nil/nonzero/negative combinations panic.

### `SliceData`, `StringData`

Expose pointers underlying slice/string с documented nil/empty special cases. Lifetime/read-only rules must be respected; modifying string bytes через unsafe violates string immutability assumptions and может corrupt program.

# Size and alignment guarantees

Implementation определяет concrete sizes для many types в рамках minimum guarantees. Для arrays/structs size включает element/field alignment/padding.

For struct fields:

- non-zero-size field alignment учитывается;
- zero-size final field может потребовать padding, чтобы pointer на it не совпал с address immediately after struct storage;
- exact layout architecture/compiler-specific, используйте `unsafe.Sizeof/Alignof/Offsetof` только для low-level code.

Do not use in-memory struct representation as portable wire/storage format.

# Version-specific changes, значимые для Go 1.27

Эта baseline specification содержит накопленные language changes. Особо важно для Go 1.27:

1. **Generic methods**: method declaration может иметь собственные type parameters после method name.
2. **Keyed promoted struct fields**: keys struct literals могут использовать selector promoted fields с новыми overlap/pointer-path restrictions.
3. Все более ранние modern features остаются частью языка: type parameters (1.18), comparable exception (1.20), `clear`/`min`/`max` (1.21), per-iteration loop variables + integer range (1.22), range-over-function iterators (1.23), current alias/toolchain-related language evolution, `new(value)` (1.26).

Для migration code между language versions учитывайте `go` directive: compiler применяет language semantics, соответствующие declared module Go version там, где это предусмотрено compatibility model.
