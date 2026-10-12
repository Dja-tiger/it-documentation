---
title: "Миграция на encoding/json/v2"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/jsonv2-migration.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Миграция на `encoding/json/v2`

Package [`encoding/json/v2`](https://pkg.go.dev/encoding/json/v2), представленный в Go 1.27, является major revision original package [`encoding/json`](https://pkg.go.dev/encoding/json).

Этот guide объясняет, почему может быть полезно перейти с v1 на v2 и как сделать migration безопасно.

## Зачем мигрировать?

Сначала главное: **вы не обязаны мигрировать**.

Package `encoding/json` не исчезнет. Он покрывается Go 1 compatibility promise, поэтому packages, использующие `encoding/json`, продолжат работать indefinitely.

Кроме того, `encoding/json` и `encoding/json/v2` совместимы друг с другом.

Например, если type реализует custom marshaling через [`encoding/json/v2.MarshalerTo`](https://pkg.go.dev/encoding/json/v2#MarshalerTo), caller, который marshal'ит этот type через [`encoding/json.Marshal`](https://pkg.go.dev/encoding/json#Marshal), всё равно использует custom marshaler.

Аналогично новые `json` struct tags, появившиеся в Go 1.27 вместе с `encoding/json/v2`, поддерживаются и `encoding/json`.

Хотя migration не обязательна, причин использовать v2 несколько.

Во-первых, новый API проще использовать.

Например, записать JSON в [`io.Writer`](https://pkg.go.dev/io#Writer) можно напрямую через [`encoding/json/v2.MarshalWrite`](https://pkg.go.dev/encoding/json/v2#MarshalWrite), вместо обязательного использования [`encoding/json.Encoder`](https://pkg.go.dev/encoding/json#Encoder).

[`encoding/json/v2.Marshalers`](https://pkg.go.dev/encoding/json/v2#Marshalers) позволяет переопределять marshal behavior конкретных types, даже если эти types вам не принадлежат.

[`encoding/json/v2.MatchCaseInsensitiveNames`](https://pkg.go.dev/encoding/json/v2#MatchCaseInsensitiveNames) позволяет явно управлять case sensitivity при сопоставлении JSON object member names с Go struct fields.

Но главная причина мигрировать — v2 выбирает более строгие и interoperable defaults, чем v1.

Полный список differences находится в documentation [`encoding/json`](https://pkg.go.dev/encoding/json#hdr-Migrating_to_v2), а основные различия таковы:

- В v1 invalid UTF-8 bytes внутри string silently заменяются Unicode replacement character. В v2 invalid UTF-8 приводит к error.
- В v1 JSON object с duplicate names разрешён. В v2 duplicate names приводят к error.
- В v1 nil Go slice или map marshal'ятся как JSON `null`. В v2 nil slice marshal'ится как empty JSON array, а nil map — как empty JSON object.
- В v1 runtime errors никогда не report'ятся для Go struct types с некоторыми structural errors, например malformed field tag. В v2 invalid Go type для JSON serialization приводит к runtime error.

Эти changes делают `encoding/json/v2` более interoperable с остальным JSON ecosystem, менее surprising и менее error-prone.

Но changes не backward compatible. Некоторые applications зависят от v1 behavior, поэтому migration должна сопровождаться careful testing.

## API changes vs behavior changes

Для простого marshal/unmarshal Go APIs в основном language-level compatible, поэтому API migration тривиальна.

Например:

```go
b, err := json.Marshal(v)
```

продолжит компилироваться, если просто заменить:

```go
import "encoding/json"
```

на:

```go
import "encoding/json/v2"
```

Сложная часть migration — не API differences, а behavior changes.

Рассмотрим program:

```go
package main

import (
	"encoding/json"
	"fmt"
)

type Pet struct {
	Name      string
	Nicknames []string
}

func main() {
	pets := []Pet{
		{Name: "Oliver", Nicknames: []string{"Ollie", "Olliepop"}},
		{Name: "Remi"},
	}
	b, err := json.Marshal(pets)
	if err != nil {
		panic(err)
	}
	fmt.Println(string(b))
}
```

В v1 output:

```json
[{"Name":"Oliver","Nicknames":["Ollie","Olliepop"]},{"Name":"Remi","Nicknames":null}]
```

Если trivial migration выполнить только заменой import на `encoding/json/v2`, program продолжит компилироваться, но output станет:

```json
[{"Name":"Oliver","Nicknames":["Ollie","Olliepop"]},{"Name":"Remi","Nicknames":[]}]
```

`Nicknames` для Remi изменился с `null` на `[]`.

Для новой program empty array, вероятно, лучше. Но в существующей application downstream consumers могут зависеть от `null`, и тогда seemingly harmless migration ломает contract.

## Options

Все места, где behavior v2 отличается от v1, покрываются [`Options`](https://pkg.go.dev/encoding/json/v2#Options), позволяющими запросить v1 behavior при использовании v2 API.

Чтобы использовать v2 API со всеми v1 behaviors, примените [`DefaultOptionsV1`](https://pkg.go.dev/encoding/json#DefaultOptionsV1):

```go
package main

import (
	jsonv1 "encoding/json"
	"encoding/json/v2"
	"fmt"
)

type Pet struct {
	Name      string
	Nicknames []string
}

func main() {
	pets := []Pet{
		{Name: "Oliver", Nicknames: []string{"Ollie", "Olliepop"}},
		{Name: "Remi"},
	}
	b, err := json.Marshal(pets, jsonv1.DefaultOptionsV1())
	if err != nil {
		panic(err)
	}
	fmt.Println(string(b))
}
```

Output снова содержит `null`:

```json
[{"Name":"Oliver","Nicknames":["Ollie","Olliepop"]},{"Name":"Remi","Nicknames":null}]
```

Documentation `DefaultOptionsV1` содержит полный set options для v1 compatibility.

Later options override earlier options, поэтому можно начать с полного v1 behavior и включать v2 changes по одному.

## Migration

В зависимости от application и tolerance к risk существуют разные стратегии:

- высокая tolerance к risk — [all-at-once](#all-at-once);
- низкая tolerance к risk или troubleshooting — [option-by-option](#option-by-option);
- production server applications — [`jsonsplit`](#jsonsplit).

### All-at-once {#all-at-once}

Если application простая либо последствия migration errors малы, elaborate migration process может быть не нужен.

Можно просто:

1. заменить calls на `encoding/json/v2`;
2. запустить tests;
3. исправить discovered incompatibilities;
4. commit change.

Если compatibility problem очевидна из change/error message, включите соответствующий [v1 compatibility option](https://pkg.go.dev/encoding/json#DefaultOptionsV1).

Если причина неясна, используйте approaches ниже.

All-at-once также полезен как быстрый первый pass: unit tests могут сразу показать obvious issues, после чего оставшиеся differences можно исследовать более аккуратно.

### Option-by-option {#option-by-option}

Для complex application или low risk tolerance лучше мигрировать постепенно.

Как сказано выше, `Marshal`/`Unmarshal` с `DefaultOptionsV1` ведут себя идентично `encoding/json`.

Первый безопасный step — заменить все calls на `encoding/json/v2`, передавая `DefaultOptionsV1`.

Это действительно safe migration layer; сам package `encoding/json` реализует `Marshal` и `Unmarshal` через v2 с compatibility options.

Additional options override earlier options. Поэтому individual v1 behavior можно отключать отдельно.

Например:

```go
json.Marshal(
	v,
	jsonv1.DefaultOptionsV1(),
	json.FormatNilSliceAsNull(false),
)
```

ведёт себя как v1, **кроме** encoding nil slices: они будут output'иться как empty arrays.

Так можно:

- включать v2 behavior по одному option;
- объединять related options в groups;
- использовать options как bisect mechanism при troubleshooting breaking difference.

### `jsonsplit` {#jsonsplit}

Package [`github.com/go-json-experiment/jsonsplit`](https://pkg.go.dev/github.com/go-json-experiment/jsonsplit) помогает мигрировать production applications, report'я differences между v1 и v2 без немедленного изменения production behavior.

`jsonsplit` предоставляет wrapper functions `Marshal` и `Unmarshal`, которые по default ведут себя как `encoding/json`, но runtime configuration позволяет вызывать:

- только v1;
- только v2;
- оба одновременно.

При mode [`CallBothButReturnV1`](https://pkg.go.dev/github.com/go-json-experiment/jsonsplit#CallMode) `jsonsplit.Marshal` marshal'ит input дважды: через v1 и v2.

Differences report'ятся, но caller получает v1 result.

Это позволяет production service обнаруживать incompatibilities без change external behavior.

Если включить [`AutoDetectOptions`](https://pkg.go.dev/github.com/go-json-experiment/jsonsplit#Codec), `jsonsplit` дополнительно пытается определить, какие конкретно options вызвали difference.

У этого approach есть cost:

- dual v1/v2 marshaling приблизительно удваивает marshal cost;
- `AutoDetectOptions` выполняет ещё больше marshals, чтобы сузить set relevant options.

Чтобы уменьшить overhead, можно анализировать только random subset calls через [`SetMarshalCallRatio`](https://pkg.go.dev/github.com/go-json-experiment/jsonsplit#Codec.SetMarshalCallRatio).

Пример применения `jsonsplit` к исходной program:

```go
package main

import (
	"fmt"

	"github.com/go-json-experiment/jsonsplit"
)

func init() {
	// Вызываем и v1, и v2, чтобы обнаруживать differences,
	// но продолжаем возвращать v1 output.
	jsonsplit.GlobalCodec.SetMarshalCallMode(jsonsplit.CallBothButReturnV1)

	// При difference автоматически определяем options,
	// которые её вызывают.
	jsonsplit.GlobalCodec.AutoDetectOptions = true

	// Log каждую найденную difference.
	jsonsplit.GlobalCodec.ReportDifference = func(d jsonsplit.Difference) {
		fmt.Printf("detected jsonv1-to-jsonv2 difference: %v\n", d)
	}
}

type Pet struct {
	Name      string
	Nicknames []string
}

func main() {
	pets := []Pet{
		{Name: "Oliver", Nicknames: []string{"Ollie", "Olliepop"}},
		{Name: "Remi"},
	}
	b, err := jsonsplit.Marshal(pets)
	if err != nil {
		panic(err)
	}
	fmt.Println(string(b))
}
```

Program report'ит difference и определяет, что она связана с `FormatNilSliceAsNull`:

```text
detected jsonv1-to-jsonv2 difference: {"Caller":"main.main+5","Func":"Marshal","GoType":"[]main.Pet","JSONValueV1":[{"Name":"Oliver","Nicknames":["Ollie","Olliepop"]},{"Name":"Remi","Nicknames":null}],"JSONValueV2":[{"Name":"Oliver","Nicknames":["Ollie","Olliepop"]},{"Name":"Remi","Nicknames":[]}],"Options":["jsonv2.FormatNilSliceAsNull"]}
[{"Name":"Oliver","Nicknames":["Ollie","Olliepop"]},{"Name":"Remi","Nicknames":null}]
```

Production migration с `jsonsplit` может выглядеть так.

#### 1. Перейти на `jsonsplit`

Замените callsites, задайте:

- `CallBothButReturnV1`;
- optional `AutoDetectOptions`;
- integration preferred monitoring в `ReportDifference`, например logs или metrics.

#### 2. Наблюдать production differences

Собирайте reports из реального production traffic.

#### 3. Устранить differences

Там, где `jsonsplit` report'ит difference, настройте options или types так, чтобы outputs совпадали.

В исходном example можно передать:

```go
json.FormatNilSliceAsNull(true)
```

В других случаях v2 может обнаружить реальную problem, которую лучше исправить.

Например, struct field tag `string`, применённый к invalid type вроде struct, игнорируется v1, но v2 report'ит error.

Можно suppress'ить error через [`ReportErrorsWithLegacySemantics`](https://pkg.go.dev/encoding/json#ReportErrorsWithLegacySemantics), но разумнее удалить бессмысленный `string` tag.

Difference output не обязательно означает downstream breakage. Она означает, что **breakage возможно**.

На этом step options используются, чтобы завершить большую часть migration без остановки для detailed analysis каждого subtle difference. После перехода на v2 такие sites следует revisit и решить, можно ли принять новый behavior.

#### 4. Переключиться на v2

Когда production перестанет report'ить новые differences, переключите codec на:

- [`OnlyCallV2`](https://pkg.go.dev/github.com/go-json-experiment/jsonsplit#CallMode);
- либо [`CallBothButReturnV2`](https://pkg.go.dev/github.com/go-json-experiment/jsonsplit#CallMode), если хотите продолжать checking differences.

#### 5. Cleanup

После безопасного rollout v2 замените `jsonsplit` на `encoding/json/v2` напрямую.

Затем revisit compatibility options, оставленные на step 3, и постепенно переходите на v2 behavior там, где это безопасно.

Дополнительные details: [`jsonsplit` migration documentation](https://pkg.go.dev/github.com/go-json-experiment/jsonsplit#hdr-Example_usage_and_migration).
