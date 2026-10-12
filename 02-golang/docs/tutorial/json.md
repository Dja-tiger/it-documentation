---
title: "Tutorial: работа с JSON"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/json.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Работа с JSON

JSON (JavaScript Object Notation) — простой формат обмена данными. Синтаксически он напоминает objects и lists JavaScript. JSON часто используется при взаимодействии с network API services, но применяется и во многих других случаях. На [json.org](http://json.org) приведено краткое и ясное определение стандарта.

С package [`encoding/json/v2`](https://pkg.go.dev/encoding/json/v2) чтение и запись JSON в Go выполняются напрямую. Этот package предоставляет более чистый API и более безопасные defaults, чем старый [`encoding/json`](https://pkg.go.dev/encoding/json).

## Encoding

Для кодирования JSON используется [`Marshal`](https://pkg.go.dev/encoding/json/v2#Marshal):

```go
func Marshal(in any, opts ...Options) (out []byte, err error)
```

Пусть определён Go type:

```go
type Message struct {
	Name string
	Body string
	Time time.Time
}
```

и value:

```go
m := Message{"Alice", "Hello", time.Date(2011, 1, 25, 0, 0, 0, 0, time.UTC)}
```

JSON representation можно получить через `json.Marshal`:

```go
b, err := json.Marshal(m)
```

Если всё успешно, `err == nil`, а `b` — `[]byte` с JSON:

```go
b == []byte(`{"Name":"Alice","Body":"Hello","Time":"2011-01-25T00:00:00Z"}`)
```

Кодируются только data structures, представимые как valid JSON:

- pointers кодируются как values, на которые они указывают, либо как `null`, если pointer равен `nil`;
- JSON objects поддерживают только strings в качестве keys. Поэтому Go map должен иметь key, кодируемый как JSON string, например `map[string]T`, где `T` — поддерживаемый json package Go type;
- channel, complex и function types не могут быть encoded;
- cyclic data structures не поддерживаются;
- полный набор semantics описан в [`Marshal`](https://pkg.go.dev/encoding/json/v2#Marshal).

JSON package обращается только к exported fields struct types — полям, начинающимся с заглавной буквы. Поэтому только exported fields присутствуют в JSON output.

## Decoding

Для decoding используется [`Unmarshal`](https://pkg.go.dev/encoding/json/v2#Unmarshal):

```go
func Unmarshal(in []byte, out any, opts ...Options) (err error)
```

Сначала создайте value, куда будут записаны decoded data:

```go
var m Message
```

Затем передайте `[]byte` JSON и pointer на `m`:

```go
err := json.Unmarshal(b, &m)
```

Если `b` содержит valid JSON, совместимый с `m`, после call `err == nil`, а data из `b` будут записаны в struct примерно так:

```go
m = Message{
	Name: "Alice",
	Body: "Hello",
	Time: time.Date(2011, 1, 25, 0, 0, 0, 0, time.UTC),
}
```

Как `Unmarshal` определяет destination fields?

Для JSON key `"Foo"` он ищет в destination struct, по приоритету:

1. exported field с tag `json:"Foo"` — о struct tags см. [[../spec#Struct types|Go Specification]];
2. exported field с именем `Foo`.

Что происходит, если JSON structure не полностью совпадает с Go type?

```go
b := []byte(`{"Name":"Bob","Food":"Pickle"}`)
var m Message
err := json.Unmarshal(b, &m)
```

`Unmarshal` декодирует только те fields, которые может сопоставить destination type. В этом примере заполнится только `Name`, а `Food` будет проигнорирован.

Это полезно, если из большого JSON blob нужны лишь отдельные fields. По той же причине unexported fields destination struct остаются неизменными.

Но что делать, если JSON structure заранее неизвестна?

## Generic JSON с `any`

Type `any` может содержать value любого Go type. Он является alias для `interface{}` — empty interface с нулём methods.

Любой Go type реализует как минимум ноль methods, поэтому удовлетворяет empty interface.

`any` может служить универсальным container:

```go
var a any
a = "a string"
a = 2011
a = 2.777
```

Type assertion позволяет получить concrete type:

```go
r := a.(float64)
fmt.Println("the circle's area", math.Pi*r*r)
```

Если concrete type неизвестен, можно использовать type switch:

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
    // a isn't one of the types above
}
```

JSON package использует `map[string]any` и `[]any` для arbitrary JSON objects и arrays и может unmarshal'ить любой valid JSON blob в обычный `any`.

Default concrete Go types:

- `bool` для JSON booleans;
- `float64` для JSON numbers;
- `string` для JSON strings;
- `nil` для JSON `null`.

## Decoding arbitrary data

Пусть в `b` находится JSON:

```go
b := []byte(`{"Name":"Wednesday","Age":6,"Parents":["Gomez","Morticia"]}`)
```

Не зная structure заранее, можно decode'ить его в `any`:

```go
var f any
err := json.Unmarshal(b, &f)
```

После этого `f` будет map со string keys и `any` values:

```go
f = map[string]any{
	"Name": "Wednesday",
	"Age":  6,
	"Parents": []any{
		"Gomez",
		"Morticia",
	},
}
```

Получить underlying `map[string]any` можно type assertion:

```go
m := f.(map[string]any)
```

Затем map можно перебрать через `range`, а concrete types values определить через type switch:

```go
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

Так можно обрабатывать заранее неизвестный JSON, сохраняя type safety после определения concrete types.

## Reference Types

Определим Go type для предыдущих data:

```go
type FamilyMember struct {
	Name    string
	Age     int
	Parents []string
}

var m FamilyMember
err := json.Unmarshal(b, &m)
```

Unmarshal в `FamilyMember` работает ожидаемо, но здесь происходит важная вещь.

При `var m FamilyMember` создаётся struct, а `Parents` изначально является `nil` slice. Чтобы заполнить `Parents`, `Unmarshal` самостоятельно allocation'ит новый slice.

Это типичное поведение `Unmarshal` для поддерживаемых reference types: pointers, slices и maps.

Рассмотрим:

```go
type Foo struct {
	Bar *Bar
}
```

Если JSON object содержит field `Bar`, `Unmarshal` allocation'ит новый `Bar` и заполнит его. Если field отсутствует, pointer `Bar` останется `nil`.

Из этого следует полезный pattern. Если application получает несколько типов messages, можно определить receiver structure:

```go
type IncomingMessage struct {
	Cmd *Command
	Msg *Message
}
```

Sender может заполнить `Cmd` и/или `Msg` в top-level JSON object в зависимости от message type.

При decoding в `IncomingMessage` `Unmarshal` allocation'ит только structures, которые реально присутствуют в JSON. Чтобы понять, какие messages обрабатывать, достаточно проверить `Cmd != nil` или `Msg != nil`.

## Streaming Marshal и Unmarshal

Interfaces [`io.Reader`](https://pkg.go.dev/io#Reader) и [`io.Writer`](https://pkg.go.dev/io#Writer) широко используются в Go и предоставляют streaming access к resources вроде HTTP connections, WebSockets и files.

`MarshalWrite` и `UnmarshalRead` позволяют marshal/unmarshal напрямую в/из streams без промежуточного `[]byte`, содержащего весь message:

```go
func MarshalWrite(out io.Writer, in any, opts ...Options) (err error)
func UnmarshalRead(in io.Reader, out any, opts ...Options) (err error)
```

Например, JSON можно сразу записать в stdout:

```go
err := json.MarshalWrite(os.Stdout, m)
```

## Custom Marshal и Unmarshal

Иногда default marshal behavior не подходит конкретному type.

Например, пусть software version представлена так:

```go
type Version struct {
	Major, Minor, Patch int64
}

v := Version{1, 2, 3}
b, err := json.Marshal(v)
```

По struct definition value будет encoded примерно как:

```json
{"Major":1,"Minor":2,"Patch":3}
```

Но для JSON consumers representation `"1.2.3"` может быть удобнее.

Реализовав interface [`MarshalerTo`](https://pkg.go.dev/encoding/json/v2#MarshalerTo), type может предоставить собственное JSON representation. [`UnmarshalerFrom`](https://pkg.go.dev/encoding/json/v2#UnmarshalerFrom) позволяет декодировать custom representation.

```go
type MarshalerTo interface {
	MarshalJSONTo(*jsontext.Encoder) error
}

type UnmarshalerFrom interface {
	UnmarshalJSONFrom(*jsontext.Decoder) error
}
```

Реализуем conversion в string representation:

```go
func (v Version) MarshalJSONTo(enc *jsontext.Encoder) error {
	return json.MarshalEncode(enc, fmt.Sprintf("%d.%d.%d", v.Major, v.Minor, v.Patch))
}
```

Теперь `Version{1, 2, 3}` marshals как:

```json
"1.2.3"
```

Custom unmarshal:

```go
func (v *Version) UnmarshalJSONFrom(dec *jsontext.Decoder) error {
	if k := dec.PeekKind(); k != jsontext.KindString {
		// Value must be a string.
		return &json.SemanticError{JSONKind: k}
	}

	var s string
	if err := json.UnmarshalDecode(dec, &s); err != nil {
		return err
	}

	_, err := fmt.Sscanf(s, "%d.%d.%d", &v.Major, &v.Minor, &v.Patch)
	return err
}
```

Теперь JSON `"1.2.3"` unmarshals как `Version{1, 2, 3}`.

Этот простой пример требует точного format `major.minor.patch`, но более сложный `UnmarshalJSONFrom` мог бы, например, разрешать optional minor и patch versions.

## References

Дополнительная информация:

- [`encoding/json/v2`](https://pkg.go.dev/encoding/json/v2);
- [`encoding/json/jsontext`](https://pkg.go.dev/encoding/json/jsontext).
