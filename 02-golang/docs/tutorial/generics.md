---
title: "Tutorial: начало работы с generics"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/generics.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Начало работы с generics

Этот tutorial знакомит с основами generics в Go. Generics позволяют объявлять и использовать functions или types, написанные для работы с любым type из заданного набора types, предоставляемых calling code.

Сначала вы объявите две простые non-generic functions, а затем выразите ту же logic в одной generic function.

Последовательность:

1. создать folder для code;
2. добавить non-generic functions;
3. добавить generic function для нескольких types;
4. убрать явные type arguments при вызове generic function;
5. объявить type constraint.

> [!note]
> Другие tutorials см. на [go.dev/doc/tutorial](https://go.dev/doc/tutorial/).

## Предварительные требования

- **Go.** Рекомендуется актуальная версия Go. Инструкции см. в [[../install|Установка Go]].
- **Редактор.** Подойдёт любой text editor.
- **Terminal.** Подойдёт terminal Linux/macOS или PowerShell/`cmd` в Windows.

## Создайте folder для code {#create_folder}

1. Откройте command prompt и перейдите в home directory.

Linux/macOS:

```text
$ cd
```

Windows:

```text
C:\> cd %HOMEPATH%
```

Далее в tutorial prompt показывается как `$`; команды также работают в Windows.

2. Создайте directory `generics`:

```bash
mkdir generics
cd generics
```

3. Создайте module:

```text
$ go mod init example/generics
go: creating new go.mod: module example/generics
```

> [!note]
> В production используйте module path, соответствующий реальному location проекта. Подробнее см. [[../modules/managing-dependencies|Управление dependencies]].

Далее добавьте код для работы с maps.

## Добавьте non-generic functions {#non_generic_functions}

На этом шаге создаются две functions, каждая из которых суммирует values map и возвращает total.

Две functions нужны потому, что используются разные map types: одна хранит `int64`, другая — `float64`.

#### Напишите код

1. Создайте `main.go` в directory `generics`.
2. Добавьте package declaration:

```go
package main
```

Standalone program, в отличие от library, находится в package `main`.

3. Добавьте две functions:

```go
// SumInts adds together the values of m.
func SumInts(m map[string]int64) int64 {
	var s int64
	for _, v := range m {
		s += v
	}
	return s
}

// SumFloats adds together the values of m.
func SumFloats(m map[string]float64) float64 {
	var s float64
	for _, v := range m {
		s += v
	}
	return s
}
```

Здесь:

- `SumFloats` принимает `map[string]float64`;
- `SumInts` принимает `map[string]int64`;
- обе functions проходят по map и суммируют values.

4. Добавьте `main`, инициализирующий maps и вызывающий functions:

```go
func main() {
	// Initialize a map for the integer values
	ints := map[string]int64{
		"first":  34,
		"second": 12,
	}

	// Initialize a map for the float values
	floats := map[string]float64{
		"first":  35.98,
		"second": 26.99,
	}

	fmt.Printf("Non-Generic Sums: %v and %v\n",
		SumInts(ints),
		SumFloats(floats))
}
```

Код:

- создаёт `map` с `int64` values и `map` с `float64` values, по две entry в каждом;
- вызывает соответствующую function для каждого map;
- печатает totals.

5. Добавьте import:

```go
package main

import "fmt"
```

6. Сохраните `main.go`.

#### Запустите код

```text
$ go run .
Non-Generic Sums: 46 and 62.97
```

С generics вместо двух functions можно написать одну.

## Добавьте generic function для нескольких types {#add_generic_function}

Теперь добавьте одну generic function, принимающую map с integer или float values и тем самым заменяющую предыдущие две functions.

Function должна описать, какие types она поддерживает, а calling code — при необходимости указать, с каким конкретным type выполняется call.

Для этого function объявляет **type parameters** в дополнение к обычным function parameters. Type parameters делают function generic. При call можно передавать **type arguments** и обычные function arguments.

У каждого type parameter есть **type constraint** — своего рода meta-type, задающий допустимые type arguments.

Хотя constraint обычно представляет набор types, во время compilation type parameter в конкретной instantiation представляет ровно один type — тот, который calling code передал как type argument. Если type argument не удовлетворяет constraint, code не compile'ится.

Type parameter должен поддерживать все operations, которые generic code выполняет над ним. Например, если function пытается выполнять string-specific operations над type parameter, constraint которого включает numeric types, code не скомпилируется.

Здесь constraint разрешит integer или float types.

#### Напишите код

1. Добавьте generic function:

```go
// SumIntsOrFloats sums the values of map m. It supports both int64 and float64
// as types for map values.
func SumIntsOrFloats[K comparable, V int64 | float64](m map[K]V) V {
	var s V
	for _, v := range m {
		s += v
	}
	return s
}
```

Здесь:

- `SumIntsOrFloats` имеет два type parameters в square brackets: `K` и `V`;
- argument `m` имеет type `map[K]V`, а return value — type `V`;
- constraint `K comparable` использует predeclared constraint `comparable`, допускающий types, values которых можно сравнивать через `==` и `!=`. Map keys в Go обязаны быть comparable, поэтому без этого constraint `map[K]V` был бы недопустим;
- constraint `V int64 | float64` — union двух types. Operator `|` означает, что допустим любой из этих types;
- compiler проверяет, что concrete type arguments вызывающего кода удовлетворяют constraints.

2. В `main.go` добавьте calls с явными type arguments:

```go
fmt.Printf("Generic Sums: %v and %v\n",
	SumIntsOrFloats[string, int64](ints),
	SumIntsOrFloats[string, float64](floats))
```

Type arguments указаны в square brackets и подставляются вместо type parameters generic function.

#### Запустите код

```text
$ go run .
Non-Generic Sums: 46 and 62.97
Generic Sums: 46 and 62.97
```

При каждом call compiler подставляет concrete types вместо type parameters.

Во многих случаях type arguments можно не указывать явно: compiler способен вывести их из ordinary function arguments.

## Уберите type arguments при вызове generic function {#remove_type_arguments}

Если compiler может вывести types из function arguments, явные type arguments можно опустить.

Это возможно не всегда. Например, при call generic function без ordinary arguments type arguments могут потребоваться явно.

Добавьте:

```go
fmt.Printf("Generic Sums, type parameters inferred: %v and %v\n",
	SumIntsOrFloats(ints),
	SumIntsOrFloats(floats))
```

Здесь generic function вызывается без type arguments.

Output:

```text
$ go run .
Non-Generic Sums: 46 and 62.97
Generic Sums: 46 and 62.97
Generic Sums, type parameters inferred: 46 and 62.97
```

Далее вынесите union integers/floats в reusable type constraint.

## Объявите type constraint {#declare_type_constraint}

На последнем шаге constraint, написанный непосредственно в generic function, переносится в отдельный interface, чтобы его можно было переиспользовать.

Type constraint объявляется как interface. Constraint допускает любой type, удовлетворяющий этому interface. Например, если constraint interface содержит три methods, type argument generic function должен предоставлять все три.

Constraint interfaces также могут перечислять конкретные types.

#### Напишите код

1. Сразу после imports и перед `main` объявите constraint:

```go
type Number interface {
	int64 | float64
}
```

Здесь:

- `Number` — interface type, используемый как type constraint;
- внутри interface объявлен union `int64 | float64`;
- union вынесен из function declaration, поэтому constraint можно использовать повторно.

2. Добавьте generic function `SumNumbers`:

```go
// SumNumbers sums the values of map m. It supports both integers
// and floats as map values.
func SumNumbers[K comparable, V Number](m map[K]V) V {
	var s V
	for _, v := range m {
		s += v
	}
	return s
}
```

Logic та же, что у предыдущей generic function, но type parameter `V` теперь использует named constraint `Number`.

3. В `main.go` добавьте:

```go
fmt.Printf("Generic Sums with Constraint: %v and %v\n",
	SumNumbers(ints),
	SumNumbers(floats))
```

Type arguments снова опущены, поскольку compiler выводит их из arguments.

#### Запустите код

```text
$ go run .
Non-Generic Sums: 46 and 62.97
Generic Sums: 46 and 62.97
Generic Sums, type parameters inferred: 46 and 62.97
Generic Sums with Constraint: 46 and 62.97
```

## Заключение {#conclusion}

Теперь вы познакомились с базовыми generics Go.

Рекомендуемые следующие материалы:

- [Tour of Go](https://go.dev/tour/) — пошаговое введение в fundamentals Go;
- [[../effective-go|Effective Go]] — idioms и best practices;
- [[../code|Как писать Go-код]].

## Полный код {#completed_code}

Program можно запустить в [Go Playground](https://go.dev/play/p/apNmfVwogK0).

```go
package main

import "fmt"

type Number interface {
	int64 | float64
}

func main() {
	// Initialize a map for the integer values
	ints := map[string]int64{
		"first":  34,
		"second": 12,
	}

	// Initialize a map for the float values
	floats := map[string]float64{
		"first":  35.98,
		"second": 26.99,
	}

	fmt.Printf("Non-Generic Sums: %v and %v\n",
		SumInts(ints),
		SumFloats(floats))

	fmt.Printf("Generic Sums: %v and %v\n",
		SumIntsOrFloats[string, int64](ints),
		SumIntsOrFloats[string, float64](floats))

	fmt.Printf("Generic Sums, type parameters inferred: %v and %v\n",
		SumIntsOrFloats(ints),
		SumIntsOrFloats(floats))

	fmt.Printf("Generic Sums with Constraint: %v and %v\n",
		SumNumbers(ints),
		SumNumbers(floats))
}

// SumInts adds together the values of m.
func SumInts(m map[string]int64) int64 {
	var s int64
	for _, v := range m {
		s += v
	}
	return s
}

// SumFloats adds together the values of m.
func SumFloats(m map[string]float64) float64 {
	var s float64
	for _, v := range m {
		s += v
	}
	return s
}

// SumIntsOrFloats sums the values of map m. It supports both floats and integers
// as map values.
func SumIntsOrFloats[K comparable, V int64 | float64](m map[K]V) V {
	var s V
	for _, v := range m {
		s += v
	}
	return s
}

// SumNumbers sums the values of map m. It supports both integers
// and floats as map values.
func SumNumbers[K comparable, V Number](m map[K]V) V {
	var s V
	for _, v := range m {
		s += v
	}
	return s
}
```
