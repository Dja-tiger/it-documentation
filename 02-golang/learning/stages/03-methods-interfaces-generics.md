# Stage 3 — Methods, interfaces и generics

## Цель

Научиться читать типичный Go API: methods, value/pointer receivers, implicit interface implementation, assertions/type switches и generics/constraints.

## Перед началом

Structs, pointers, functions, maps/slices из [[02-core-language|Stage 2]].

## Прочитать

1. [A Tour of Go — Methods and interfaces](https://go.dev/tour/methods/1).
2. [A Tour of Go — Generics](https://go.dev/tour/generics/1).
3. [[../../docs/tutorial/generics|Generics tutorial]].
4. Выборочно [[../../docs/effective-go|Effective Go]]: methods, interfaces, embedding.
5. Reference: [[../../docs/spec#Method sets|Method sets]], [[../../docs/spec#Type assertions|Type assertions]], [[../../docs/spec#Comparison|comparability]].

> [!important]
> Для Go 1.27 нормативный источник по generic methods — [[../../docs/spec|Specification]]. Старые explanatory тексты могут отставать от текущего языка.

## Что необходимо понять

- [ ] method receiver не является «классом».
- [ ] method set `T` против `*T`.
- [ ] implicit interface implementation.
- [ ] маленькие consumer-side interfaces.
- [ ] type assertion: one-result vs comma-ok.
- [ ] type switch.
- [ ] `any`, `comparable`, type sets, `~T`, union constraints.
- [ ] type inference и ситуации, когда explicit type arguments полезнее.

## Что НЕ нужно пока изучать

- сложные generic libraries ради самих generics;
- reflection/unsafe;
- generic specialization patterns из других языков;
- compiler implementation generics.

## Практика

- [[../practice/03-interfaces-generics|Interfaces & generics]].

## Эксперименты

- изменить receiver `T` ↔ `*T` и проверить interface satisfaction;
- поместить typed nil pointer в interface и сравнить interface с `nil`;
- выполнить failed one-result type assertion и затем безопасный comma-ok;
- сделать constraint слишком широким и увидеть запрещённую operation.

## Проверка себя

1. Почему `*T` может реализовывать interface, который `T` не реализует?
2. Почему interface с typed nil внутри может быть `!= nil`?
3. Что означает «interface implemented implicitly»?
4. Когда generic helper лучше обычной interface/function composition, а когда хуже?
5. Зачем map key generic parameter часто ограничивается `comparable`?

## Практическая проверка

Создать contracts `PriceSource`, `PriceValidator`, `PriceSink`; написать две реализации одного interface и generic `Chunk[T]` без привязки к `Price`. Tests должны доказывать contract.

## Критерий завершения

Я могу перейти дальше, если способен:

- по method declarations определить interface satisfaction;
- спроектировать узкий interface со стороны consumer;
- диагностировать typed-nil trap;
- написать и ограничить простой generic helper без unnecessary abstraction.

## Следующий этап

[[04-errors-and-testing|Stage 4 — Errors and testing]].
