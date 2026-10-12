# Stage 13 — Системное чтение Language Specification

## Цель

После практического опыта превратить [[../../docs/spec|Specification Go 1.27]] в рабочий нормативный reference: уметь точно отвечать на language-semantics questions, а не учить Go с нуля по формальному тексту.

## Перед началом

Stages 1–12. Особенно важны methods/interfaces/generics, concurrency и реальный production-shaped code.

## Прочитать

Основной документ один: [[../../docs/spec|Спецификация языка Go 1.27]]. Читать несколькими проходами:

1. lexical elements, constants, variables;
2. types: arrays/slices/structs/pointers/functions/interfaces/maps/channels;
3. type identity, underlying types, method sets;
4. assignability, representability, comparison;
5. declarations, type parameters, functions/methods;
6. expressions: selectors, assertions, calls, instantiation/inference;
7. operators/conversions/evaluation order;
8. statements: `for/range`, `go`, `select`, `defer`, `return`;
9. built-ins;
10. packages, initialization, `main` lifecycle;
11. errors/runtime panics;
12. `unsafe`/layout — обзорно, если нет low-level use case.

## Что необходимо понять

- [ ] spec — нормативный источник, tutorials/FAQ — explanatory sources.
- [ ] named vs underlying type и type identity.
- [ ] method set `T`/`*T` без смешения с automatic addressability calls.
- [ ] assignability ≠ arbitrary implicit conversion.
- [ ] exact comparability rules для arrays/structs/interfaces/maps/slices/functions.
- [ ] generic constraint/type set semantics.
- [ ] type assertion/call/inference contracts.
- [ ] slice/full-slice and indexing semantics.
- [ ] map iteration order unspecified.
- [ ] channel/send/receive/close/select language rules.
- [ ] `defer` evaluation time и reverse execution order.
- [ ] initialization order и отсутствие implicit wait for goroutines при return `main`.
- [ ] version-specific Go 1.27 language changes из текущего spec.

## Что НЕ нужно пока изучать

- запоминать grammar productions;
- `unsafe` tricks без задачи;
- compiler implementation как будто это часть spec;
- исторические semantics старых Go releases, кроме migration need.

## Практика

- [[../practice/14-spec-runtime-labs|Specification/runtime labs]] — сначала блок Specification.

## Эксперименты

Для каждого experiment сначала найти/сформулировать spec rule, затем написать минимальный program:

- comparable/non-comparable composite types;
- `T` vs `*T` method-set interface assignment;
- nil map lookup vs write;
- nil channel operation;
- failed type assertion one-result vs comma-ok;
- full slice expression и resulting capacity;
- `defer` arguments vs deferred body timing;
- map iteration dependence bug;
- `main` returns while goroutine still active.

## Проверка себя

1. Чем type identity отличается от assignability?
2. Почему automatic `&x` при method call не меняет method set `T`?
3. Когда interface equality может panic?
4. Какие operations над nil map безопасны, а какие нет?
5. Как `select` выбирает ready case?
6. Когда evaluates arguments deferred call?
7. Какие guarantees относятся к language spec, а какие к runtime implementation?

## Практическая проверка

Взять 10 nontrivial fragments из собственного `price-*` codebase. До compiler/runtime письменно предсказать compile/result/panic/blocking, сослаться на соответствующий раздел spec, затем проверить. Не считать задание выполненным, если объяснение основано только на «так обычно работает».

## Критерий завершения

Я могу перейти дальше, если способен:

- быстро найти normative rule в spec;
- отличить language guarantee от implementation detail;
- объяснить method sets/assignability/comparability;
- предсказать tricky `range`/`select`/`defer` behavior;
- обнаружить устаревшее explanatory утверждение, сверив его с Go 1.27 spec.

## Следующий этап

[[14-runtime-internals|Stage 14 — Runtime internals]].
