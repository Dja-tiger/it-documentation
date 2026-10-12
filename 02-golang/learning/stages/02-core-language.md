# Stage 2 — Core language и data structures

## Цель

Освоить syntax и value model, необходимые для чтения/написания обычного Go-кода: variables, constants, functions, control flow, pointers, structs, arrays, slices и maps.

## Перед началом

[[01-foundations|Stage 1]].

## Прочитать

1. Повторно использовать relevant части [[../../docs/tutorial/random-greeting|slice tutorial]] и [[../../docs/tutorial/greetings-multiple-people|map tutorial]].
2. [A Tour of Go — Basics](https://go.dev/tour/basics/1).
3. [A Tour of Go — Flow control](https://go.dev/tour/flowcontrol/1).
4. [A Tour of Go — More types](https://go.dev/tour/moretypes/1).
5. Выборочно [[../../docs/effective-go|Effective Go]]: control structures, functions, data, arrays/slices/maps.
6. Specification использовать только как reference: [[../../docs/spec#Variables|Variables]], [[../../docs/spec#Types|Types]], [[../../docs/spec#Comparison|Comparison]].

## Что необходимо понять

- [ ] `var`, `:=`, zero value, constants и basic types.
- [ ] multiple return values.
- [ ] `if`, `for`, `range`, `switch`, `defer` на базовом уровне.
- [ ] pointer и отсутствие pointer arithmetic в normal Go.
- [ ] struct values и field access.
- [ ] array — value, length входит в type.
- [ ] slice — descriptor над backing array; `len`, `cap`, `append`.
- [ ] map lookup и comma-ok; key comparability.
- [ ] string как bytes + UTF-8/runes distinction.

## Что НЕ нужно пока изучать

- unsafe;
- escape analysis;
- memory model concurrency;
- generic constraints в глубину;
- runtime representation slice/map.

## Практика

- [[../practice/02-core-language|Core language / pricing data]].

## Эксперименты

- менять `append`, `len`, `cap` и проверять, когда slices разделяют backing array;
- читать отсутствующий map key с/без comma-ok;
- dereference nil pointer и классифицировать panic;
- передать array и slice в functions и сравнить mutation semantics.

## Проверка себя

1. Почему `append` обязательно возвращает slice?
2. Что копируется при `b := a`, если `a` — array, slice, map, struct?
3. Почему slice нельзя использовать map key, а struct иногда можно?
4. Что вернёт map при отсутствующем key?
5. Чем `len(string)` отличается от количества Unicode characters?

## Практическая проверка

Без документации написать обработчик `[]Price`, который валидирует records, группирует их по `(store_id, plu_id)` и режет accepted records на batches максимум 3000.

## Критерий завершения

Я могу перейти дальше, если способен:

- моделировать pricing entities structs;
- предсказывать slice/map behavior;
- объяснять value/reference-like semantics без фразы «в Go всё pointer»;
- написать streaming-style loop без лишнего глобального state.

## Следующий этап

[[03-methods-interfaces-generics|Stage 3 — Methods, interfaces, generics]].
