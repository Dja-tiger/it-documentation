---
title: "Начало работы с generics"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/generics.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Начало работы с generics

Generics позволяют объявлять functions и types, которые работают не с одним конкретным type, а с множеством допустимых types, определённых constraints.

В tutorial одна и та же логика суммирования сначала реализуется двумя обычными functions, затем объединяется в generic function.

## Подготовка module

```bash
mkdir generics
cd generics
go mod init example/generics
```

## Без generics

Два разных map value types требуют двух функций:

```go
func SumInts(m map[string]int64) int64 {
    var s int64
    for _, v := range m {
        s += v
    }
    return s
}

func SumFloats(m map[string]float64) float64 {
    var s float64
    for _, v := range m {
        s += v
    }
    return s
}
```

Пример данных:

```go
ints := map[string]int64{
    "first":  34,
    "second": 12,
}

floats := map[string]float64{
    "first":  35.98,
    "second": 26.99,
}
```

## Generic function

Обе реализации можно выразить через type parameters:

```go
func SumIntsOrFloats[K comparable, V int64 | float64](m map[K]V) V {
    var s V
    for _, v := range m {
        s += v
    }
    return s
}
```

В declaration:

- `K` — type parameter key;
- constraint `comparable` обязателен, потому что keys map должны поддерживать `==`/`!=`;
- `V` ограничен union `int64 | float64`;
- argument имеет type `map[K]V`;
- result имеет type `V`.

Explicit type arguments:

```go
SumIntsOrFloats[string, int64](ints)
SumIntsOrFloats[string, float64](floats)
```

Compiler подставляет concrete types вместо type parameters и проверяет constraints на compile time.

## Type inference

Когда type arguments можно вывести из function arguments, их не нужно указывать:

```go
SumIntsOrFloats(ints)
SumIntsOrFloats(floats)
```

Inference не всегда возможен. Если generic function не получает values, из которых compiler может вывести нужный type, explicit type arguments могут оставаться необходимыми.

## Reusable type constraint

Constraint можно вынести в interface:

```go
type Number interface {
    int64 | float64
}
```

И использовать повторно:

```go
func SumNumbers[K comparable, V Number](m map[K]V) V {
    var s V
    for _, v := range m {
        s += v
    }
    return s
}
```

Constraint interface задаёт type set — множество types, допустимых для type argument.

## Полный пример

```go
package main

import "fmt"

type Number interface {
    int64 | float64
}

func SumInts(m map[string]int64) int64 {
    var s int64
    for _, v := range m {
        s += v
    }
    return s
}

func SumFloats(m map[string]float64) float64 {
    var s float64
    for _, v := range m {
        s += v
    }
    return s
}

func SumIntsOrFloats[K comparable, V int64 | float64](m map[K]V) V {
    var s V
    for _, v := range m {
        s += v
    }
    return s
}

func SumNumbers[K comparable, V Number](m map[K]V) V {
    var s V
    for _, v := range m {
        s += v
    }
    return s
}

func main() {
    ints := map[string]int64{
        "first":  34,
        "second": 12,
    }

    floats := map[string]float64{
        "first":  35.98,
        "second": 26.99,
    }

    fmt.Printf("Non-Generic Sums: %v and %v\n", SumInts(ints), SumFloats(floats))
    fmt.Printf(
        "Generic Sums: %v and %v\n",
        SumIntsOrFloats[string, int64](ints),
        SumIntsOrFloats[string, float64](floats),
    )
    fmt.Printf(
        "Generic Sums, inferred: %v and %v\n",
        SumIntsOrFloats(ints),
        SumIntsOrFloats(floats),
    )
    fmt.Printf(
        "Generic Sums with Constraint: %v and %v\n",
        SumNumbers(ints),
        SumNumbers(floats),
    )
}
```

Основной принцип: generic implementation должна быть корректна для **каждого** type, разрешённого constraint. Operations, не поддерживаемые всем type set, compiler не разрешит.
