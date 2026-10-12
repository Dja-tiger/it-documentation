---
title: "Миграция на encoding/json/v2"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/jsonv2-migration.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Миграция на `encoding/json/v2`

Go 1.25 представил экспериментальные `encoding/json/v2` и `encoding/json/jsontext`; в Go 1.27 API продолжает развиваться. `json/v2` исправляет ряд historical behaviors v1, которые нельзя безопасно поменять в старом package из-за Go 1 compatibility promise.

Для использования v2 в соответствующих Go versions может требоваться experiment/build configuration, описанная release docs. Всегда проверяйте текущий release status перед production migration.

## Зачем v2

Legacy `encoding/json` имеет behavior, которое с современным security/API-design взглядом неудобно:

- case-insensitive field matching по default;
- inconsistent nil slice/map encoding;
- duplicate JSON object names могут приниматься;
- invalid UTF-8 historically заменялся вместо строгого rejection;
- custom marshal/unmarshal interfaces работают через intermediate `[]byte`, что затрудняет streaming;
- option model ограничен.

V2 меняет defaults и предоставляет explicit options для compatibility.

## Основные packages

```go
import "encoding/json/v2"
import "encoding/json/jsontext"
```

`json/v2` отвечает за semantic conversion Go values ↔ JSON values.

`jsontext` предоставляет syntactic streaming/token-level encoder/decoder.

## API mapping

Legacy:

```go
json.Marshal(v)
json.Unmarshal(data, &v)
json.NewEncoder(w)
json.NewDecoder(r)
```

V2 добавляет option-oriented forms и streaming helpers. В tutorial/reference используются, например:

```go
json.Marshal(v, opts...)
json.Unmarshal(data, &v, opts...)
json.MarshalWrite(w, v, opts...)
json.UnmarshalRead(r, &v, opts...)
```

Low-level stream semantic integration:

```go
json.MarshalEncode(enc, v, opts...)
json.UnmarshalDecode(dec, &v, opts...)
```

## Case-sensitive struct field matching

V1 исторически мог сопоставить JSON field с struct field без учёта регистра. V2 default строже и ожидает exact semantic match согласно tag/name rules.

Если migration временно требует legacy matching, используйте соответствующую compatibility option (`MatchCaseInsensitiveNames` в API текущей версии).

Рекомендация: исправить JSON schema/tags так, чтобы exact field names совпадали, а compatibility option использовать как transitional bridge.

## Duplicate object member names

Duplicate JSON names потенциально dangerous: разные parsers могут выбирать first/last value, что создаёт security ambiguity.

V2 по default reject'ит duplicates. Legacy behavior можно временно разрешить option'ом `jsontext.AllowDuplicateNames(true)` там, где это действительно требуется.

Лучше очистить producer/schema и оставить strict default.

## Invalid UTF-8

V2 более строго относится к invalid UTF-8. Legacy replacement behavior можно включить compatibility option'ом `jsontext.AllowInvalidUTF8(true)`.

Для external/untrusted JSON strict rejection обычно безопаснее.

## Nil slices/maps

Legacy v1 часто marshal'ит nil slice/map как JSON `null`; v2 выбирает semantics, направленные на более предсказуемые collection encodings и предоставляет options для legacy behavior.

При migration проверьте API contracts, где clients различают:

```json
null
```

и:

```json
[]
{}
```

Это может быть breaking change wire format даже если Go types не поменялись.

## `omitempty` и `omitzero`

V2 уточняет semantics omission.

`omitempty` ориентирован на JSON-level empty representation и может отличаться от historical Go-value intuition.

Для Go zero-value semantics существует `omitzero`:

```go
type Event struct {
    Created time.Time `json:"created,omitzero"`
}
```

При migration fields, где исторически ожидалось «omit when Go zero», стоит проверить и при необходимости использовать `omitzero`.

## Map key ordering

V1 deterministic encoding map keys часто relied on sorting. V2 стремится к streaming/performance behavior и deterministic output управляется option'ами.

Если JSON bytes участвуют в:

- golden files;
- signatures/hashes;
- cache keys;
- reproducible snapshots;

явно включите deterministic serialization и не полагайтесь на accidental ordering.

## Byte arrays и binary

Проверьте encoding `[N]byte`, `[]byte` и named byte types: v2 изменяет/уточняет special binary representation и предоставляет compatibility options для legacy arrays/bytes behavior.

Не assume, что arbitrary slice/array of uint8 всегда имеет identical JSON representation между v1/v2 — добавьте compatibility tests.

## Method invocation semantics

V2 лучше поддерживает methods через pointers/interfaces и более последовательные rules custom marshal/unmarshal. Это может открыть ранее невызывавшийся `MarshalJSON`/`UnmarshalJSON` method в edge cases.

Migration tests должны включать:

- nil pointers;
- embedded fields;
- interface dynamic values;
- pointer-receiver marshalers;
- map values;
- slice elements.

## Custom marshalers v2

Legacy interfaces:

```go
type Marshaler interface {
    MarshalJSON() ([]byte, error)
}

type Unmarshaler interface {
    UnmarshalJSON([]byte) error
}
```

V2 streaming interfaces:

```go
type MarshalerTo interface {
    MarshalJSONTo(*jsontext.Encoder) error
}

type UnmarshalerFrom interface {
    UnmarshalJSONFrom(*jsontext.Decoder) error
}
```

Они позволяют работать непосредственно с JSON stream/token encoder/decoder без обязательного intermediate full `[]byte`.

Для compatibility можно поддерживать оба поколения methods во время staged migration.

## Options как migration layer

V2 специально предоставляет options, которыми можно приблизить behavior к v1 и затем постепенно убрать compatibility flags.

Типичный staged strategy:

1. Перейти на v2 API с options, максимально повторяющими текущий v1 wire behavior.
2. Сравнить golden/contract tests.
3. По одному отключать legacy options.
4. На каждом шаге проверять downstream clients и security assumptions.

Не мигрируйте большой public API «одной заменой import path» без wire-level tests.

## Что тестировать

Минимальный migration matrix:

- exact/case-mismatched field names;
- unknown fields;
- duplicate names;
- invalid UTF-8;
- nil vs empty slices/maps;
- zero values + `omitempty`/`omitzero`;
- map order/deterministic bytes;
- `[]byte` и `[N]byte`;
- custom marshaler/unmarshaler;
- embedded/promoted fields;
- numbers/overflow;
- streaming concatenated values;
- malformed JSON;
- security-sensitive schema validation.

## Security consequence

Самое важное migration direction v2 — более строгие и однозначные defaults. Для untrusted JSON не включайте legacy permissive options автоматически «чтобы tests прошли». Сначала определите, какой producer/client зависит от permissive behavior и можно ли исправить его.

## Связанный tutorial

Практические examples API v2: [[tutorial/json|Работа с JSON]].
