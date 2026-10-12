---
title: "Tutorial: работа с JSON"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/json.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Работа с JSON

JSON — распространённый text data-interchange format. В актуальной документации Go 1.27 tutorial использует новый package `encoding/json/v2`, который предоставляет более чистый API и более безопасные defaults по сравнению с legacy `encoding/json`.

## Encoding: `Marshal`

Сигнатура:

```go
func Marshal(in any, opts ...Options) (out []byte, err error)
```

Структура:

```go
type Message struct {
    Name string
    Body string
    Time time.Time
}
```

Value:

```go
m := Message{
    "Alice",
    "Hello",
    time.Date(2011, 1, 25, 0, 0, 0, 0, time.UTC),
}
```

Encoding:

```go
b, err := json.Marshal(m)
```

Результат:

```json
{"Name":"Alice","Body":"Hello","Time":"2011-01-25T00:00:00Z"}
```

### Что можно encode

- pointer encode'ится как pointed value, `nil` pointer → `null`;
- JSON object keys — strings, поэтому Go map key должен быть encodable as JSON string, типично `map[string]T`;
- channels, complex numbers и functions не encode'ятся;
- cyclic data structures не поддерживаются;
- для struct доступны только **exported fields**.

Полная семантика определяется документацией `Marshal`.

## Decoding: `Unmarshal`

```go
func Unmarshal(in []byte, out any, opts ...Options) error
```

Создайте destination value:

```go
var m Message
```

И передайте pointer:

```go
err := json.Unmarshal(b, &m)
```

После успеха fields `m` заполнены decoded values.

### Как JSON keys сопоставляются struct fields

Для key `"Foo"` decoder предпочитает:

1. exported field с tag `json:"Foo"`;
2. exported field с именем `Foo`.

Если JSON содержит неизвестный field, default behavior позволяет его проигнорировать, а известные fields заполнить.

Например:

```go
b := []byte(`{"Name":"Bob","Food":"Pickle"}`)
var m Message
err := json.Unmarshal(b, &m)
```

`Name` будет заполнен, а `Food`, отсутствующий в target type, не попадёт в struct.

## Generic JSON через `any`

`any` — alias `interface{}` и может хранить value любого Go type.

```go
var a any
a = "a string"
a = 2011
a = 2.777
```

Type assertion:

```go
r := a.(float64)
```

Type switch:

```go
switch v := a.(type) {
case int:
    fmt.Println("twice a is", v*2)
case float64:
    fmt.Println("the reciprocal of a is", 1/v)
case string:
    h := len(v) / 2
    fmt.Println("a swapped by halves is", v[h:]+v[:h])
default:
    // unknown type
}
```

Для arbitrary JSON package использует object/array representations на базе:

- `map[string]any`;
- `[]any`.

Default primitive mappings:

- JSON boolean → `bool`;
- JSON number → `float64`;
- JSON string → `string`;
- JSON `null` → `nil`.

## Decoding arbitrary data

```go
b := []byte(`{"Name":"Wednesday","Age":6,"Parents":["Gomez","Morticia"]}`)

var f any
err := json.Unmarshal(b, &f)
```

Logical result:

```go
map[string]any{
    "Name": "Wednesday",
    "Age":  6,
    "Parents": []any{
        "Gomez",
        "Morticia",
    },
}
```

Доступ:

```go
m := f.(map[string]any)

for k, v := range m {
    switch vv := v.(type) {
    case string:
        fmt.Println(k, "is string", vv)
    case float64:
        fmt.Println(k, "is float64", vv)
    case []any:
        fmt.Println(k, "is an array:")
        for i, u := range vv {
            fmt.Println(i, u)
        }
    default:
        fmt.Println(k, "is of a type I don't know how to handle")
    }
}
```

Если schema известна, typed structs обычно предпочтительнее: они дают compile-time types, меньше assertions и яснее contract.

## Reference types

```go
type FamilyMember struct {
    Name    string
    Age     int
    Parents []string
}

var m FamilyMember
err := json.Unmarshal(b, &m)
```

Если `Parents` был `nil`, decoder сам allocate'ит slice при наличии JSON array.

То же применяется к pointers/maps/slices. Например:

```go
type Foo struct {
    Bar *Bar
}
```

Если JSON содержит `Bar`, decoder может allocate'ить pointed `Bar`; если field отсутствует, pointer останется `nil`.

Это даёт pattern optional message variants:

```go
type IncomingMessage struct {
    Cmd *Command
    Msg *Message
}
```

После decode можно определить variant по non-nil pointer.

## Streaming Marshal/Unmarshal

В Go `io.Reader`/`io.Writer` используются для streams — HTTP bodies, files, sockets и др. `json/v2` позволяет обрабатывать stream без промежуточного full-message `[]byte`:

```go
func MarshalWrite(out io.Writer, in any, opts ...Options) error
func UnmarshalRead(in io.Reader, out any, opts ...Options) error
```

Например:

```go
err := json.MarshalWrite(os.Stdout, m)
```

## Custom JSON representation

Иногда default struct representation не подходит API contract.

```go
type Version struct {
    Major int64
    Minor int64
    Patch int64
}
```

Default JSON был бы object:

```json
{"Major":1,"Minor":2,"Patch":3}
```

Но клиенту может быть удобнее string:

```json
"1.2.3"
```

В `json/v2` custom behavior задаётся interfaces `MarshalerTo` и `UnmarshalerFrom`:

```go
type MarshalerTo interface {
    MarshalJSONTo(*jsontext.Encoder) error
}

type UnmarshalerFrom interface {
    UnmarshalJSONFrom(*jsontext.Decoder) error
}
```

Custom marshal:

```go
func (v Version) MarshalJSONTo(enc *jsontext.Encoder) error {
    return json.MarshalEncode(
        enc,
        fmt.Sprintf("%d.%d.%d", v.Major, v.Minor, v.Patch),
    )
}
```

Custom unmarshal:

```go
func (v *Version) UnmarshalJSONFrom(dec *jsontext.Decoder) error {
    if k := dec.PeekKind(); k != jsontext.KindString {
        return &json.SemanticError{JSONKind: k}
    }

    var s string
    if err := json.UnmarshalDecode(dec, &s); err != nil {
        return err
    }

    _, err := fmt.Sscanf(
        s,
        "%d.%d.%d",
        &v.Major,
        &v.Minor,
        &v.Patch,
    )
    return err
}
```

Эта implementation намеренно принимает только exact `major.minor.patch`; более гибкий parser можно реализовать внутри custom unmarshal.
