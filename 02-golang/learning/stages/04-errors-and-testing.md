# Stage 4 — Errors, testing и fuzzing

## Цель

Сделать error handling и testing обычной частью design: wrapping/identity, table-driven tests, fuzzing и reproducible regression.

## Перед началом

Functions/interfaces из Stages 2–3.

## Прочитать

1. [[../../docs/tutorial/handle-errors|Return and handle errors]].
2. [[../../docs/tutorial/add-a-test|Add a test]].
3. Testing section в [[../../docs/code|How to Write Go Code]].
4. [Package errors](https://pkg.go.dev/errors): `New`, `Is`, `As`, `Join`, wrapping through `%w`.
5. [Package testing](https://pkg.go.dev/testing).
6. [[../../docs/tutorial/fuzz|Fuzz tutorial]].
7. [[../../docs/security/fuzz/index|Go Fuzzing]] после tutorial.

## Что необходимо понять

- [ ] `error` — value/interface, `nil` означает успех.
- [ ] adding context через `fmt.Errorf("...: %w", err)`.
- [ ] `errors.Is` для identity chain; `errors.As` для typed error.
- [ ] когда sentinel/custom error оправдан.
- [ ] test naming, `*testing.T`, subtests, table-driven tests.
- [ ] deterministic tests vs time/network dependencies.
- [ ] fuzz seed corpus и invariants.
- [ ] найденный fuzz input становится regression artifact.

## Что НЕ нужно пока изучать

- mock framework ecosystem;
- huge test architecture;
- fuzzing engine internals;
- coverage percentage как самоцель.

## Практика

- [[../practice/04-errors-testing|Errors & tests]].

## Эксперименты

- заменить `%w` на `%v` и проверить `errors.Is`;
- сломать table case и прочитать failure;
- fuzz parser pricing payload до найденного edge case;
- создать panic path и решить, должен ли это быть error contract.

## Проверка себя

1. Чем error wrapping отличается от string concatenation?
2. Когда `errors.Is` лучше `==`?
3. Что проверяет `errors.As`?
4. Что делает table-driven test удобным для boundary cases?
5. Какой invariant подходит fuzzing лучше exact expected output?

## Практическая проверка

Без копирования написать validator/parser pricing records с typed validation error, wrapping на boundary, table tests и fuzz test на отсутствие panic + сохранение contract.

## Критерий завершения

Я могу перейти дальше, если способен:

- сохранять causal error chain;
- тестировать success/boundary/error paths;
- писать fuzz invariant;
- превращать найденный case в regression test.

## Следующий этап

[[05-modules-packages-toolchain|Stage 5 — Packages, modules, toolchain]].
