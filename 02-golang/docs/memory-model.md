---
title: "Модель памяти Go"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/go"
upstream_path: "doc/go_mem.html"
upstream_ref: "go1.27.1"
translation_status: "translated"
---

# Модель памяти Go

Версия формального документа: 6 июня 2022 года.

Модель памяти Go определяет условия, при которых read одной переменной в одной goroutine гарантированно наблюдает value, записанное в ту же переменную другой goroutine.

## Главный практический совет

Если несколько goroutines одновременно обращаются к изменяемым данным, доступ необходимо **сериализовать**.

Для этого используйте:

- channel operations;
- `sync.Mutex` / `sync.RWMutex`;
- `sync.Once` и другие primitives из `sync`;
- атомарные операции из `sync/atomic`.

Если для понимания корректности вашей программы приходится опираться на тонкие детали race semantics — design слишком сложен. Не пытайтесь «обыграть» memory model.

## Неформальный обзор

**Data race** — это concurrent доступ двух goroutines к одной memory location, когда хотя бы один access является write, если только все конфликтующие accesses не являются atomic accesses из `sync/atomic`.

Для программ без data races Go гарантирует поведение, эквивалентное некоторому sequentially consistent interleaving goroutines. Это свойство называется **DRF-SC**: Data-Race-Free → Sequential Consistency.

Race остаётся ошибкой. Runtime/tooling вправе обнаружить race, сообщить о ней и завершить program. В отличие от C/C++, Go не объявляет абсолютно любое поведение race-программы полностью unconstrained: для word/sub-word accesses существуют ограничения на наблюдаемые writes. Но на это нельзя опираться как на synchronization mechanism.

## Формальная модель

Memory operation описывается четырьмя характеристиками:

1. kind: ordinary read/write или synchronizing operation;
2. location в program;
3. memory location/variable;
4. value, которое читается или записывается.

Read-like operations включают ordinary/atomic read, mutex lock, channel receive. Write-like — ordinary/atomic write, mutex unlock, channel send/close. CAS является и read-like, и write-like.

### Requirement 1: выполнение одной goroutine

Memory operations одной goroutine должны соответствовать корректному sequential execution этой goroutine с учётом observed values и отношения **sequenced before**, задаваемого control flow и order of evaluation языка.

### Program execution и mapping W

Execution всей программы моделируется как набор goroutine executions плюс mapping `W`, указывающий для каждого read-like operation, из какого write-like operation он читает value.

### Requirement 2: synchronizing operations

Для synchronizing operations mapping `W` должен объясняться некоторым total order этих operations, согласованным с sequencing и read/written values.

Если synchronizing read `r` наблюдает synchronizing write `w`, то `w` **synchronized before** `r`.

### Happens-before

**Happens before** — transitive closure объединения:

- sequenced before;
- synchronized before.

Это центральное отношение для рассуждения о visibility.

### Requirement 3: ordinary read

Для ordinary read `r` location `x`, `W(r)` должен быть write `w`, **visible** для `r`:

1. `w` happens before `r`;
2. между `w` и `r` нет другого write `w'` в `x`, который happens after `w` и happens before `r`.

### Read-write race

Read-like `r` и write-like `w` одной location образуют race, если хотя бы один access non-synchronizing и они не упорядочены happens-before ни в одну сторону.

### Write-write race

Два write-like operations одной location образуют race по тем же условиям.

Если race отсутствует, у read остаётся единственный допустимый previous write в happens-before order, что и даёт DRF-SC guarantee.

## Race-программы: ограничения implementation

Implementation может при detection race сообщить об ошибке и остановить program. Именно так работает race instrumentation.

Reads/writes arrays, structs и complex values могут быть реализованы как отдельные accesses к sub-values в произвольном order.

Для location размером не больше machine word read должен наблюдать value какого-то preceding/concurrent write, удовлетворяющего ограничениям модели. «Out of thin air» values запрещены.

Для multi-word values implementation может выполнять несколько machine-word accesses. Поэтому race на structures, чья корректность зависит от согласованных пар `(pointer,length)` или `(pointer,type)` — slices, strings, interfaces, maps — может привести не просто к stale value, а к inconsistent representation и memory corruption.

## Synchronization

### Initialization

Initialization packages выполняется последовательно в initialization goroutine, хотя `init` может запускать другие goroutines.

Гарантии:

- если package `p` imports `q`, завершение `q.init` happens before начало `p.init`;
- завершение всех `init` functions synchronized before начало `main.main`.

### Создание goroutine

`go` statement synchronized before начало выполнения созданной goroutine.

```go
var a string

func f() {
    print(a)
}

func hello() {
    a = "hello, world"
    go f()
}
```

Вызов `hello` гарантирует, что `f` увидит присваивание `a = "hello, world"`.

### Завершение goroutine

Само завершение goroutine **не** имеет автоматической synchronization guarantee с каким-либо событием другой goroutine.

```go
var a string

func hello() {
    go func() { a = "hello" }()
    print(a)
}
```

Здесь нет synchronization между write и print. Если effects goroutine должны быть видимы, используйте channel/lock/WaitGroup/другой documented primitive.

### Channels

Channel communication — основной language-level synchronization mechanism.

**Rule 1.** Send synchronized before завершение соответствующего receive.

```go
var c = make(chan int, 10)
var a string

func f() {
    a = "hello, world"
    c <- 0
}

func main() {
    go f()
    <-c
    print(a)
}
```

Гарантированно печатает `hello, world`.

**Rule 2.** `close(c)` synchronized before receive, который возвращает zero value из-за закрытого channel.

**Rule 3.** Для unbuffered channel receive synchronized before завершение corresponding send.

```go
var c = make(chan int)
var a string

func f() {
    a = "hello, world"
    <-c
}

func main() {
    go f()
    c <- 0
    print(a)
}
```

Также гарантированно видит write `a`. Если заменить channel на buffered capacity 1, такой guarantee из этой последовательности исчезает.

**Rule 4.** Для channel capacity `C`, `k`-й receive synchronized before завершение `(k+C)`-го send.

Именно это позволяет использовать buffered channel как counting semaphore:

```go
var limit = make(chan int, 3)

func main() {
    for _, w := range work {
        go func(w func()) {
            limit <- 1
            w()
            <-limit
        }(w)
    }
    select {}
}
```

Максимум три `w()` одновременно находятся между acquire/release channel token.

### Locks

Для `sync.Mutex` или `sync.RWMutex` `l`, если unlock call `n` происходит раньше lock call `m` (`n < m`), то `n`-й `Unlock` synchronized before возврат `m`-го `Lock`.

```go
var l sync.Mutex
var a string

func f() {
    a = "hello, world"
    l.Unlock()
}

func main() {
    l.Lock()
    go f()
    l.Lock()
    print(a)
}
```

Write `a` видим после второго `Lock`.

Для `RWMutex` documented ordering связывает `Unlock` → последующий `RLock`, а matching `RUnlock` → следующий `Lock`.

Successful `TryLock` / `TryRLock` имеет synchronization effect обычного `Lock` / `RLock`. Failed call **не создаёт** synchronization edge.

### `sync.Once`

Для `once.Do(f)` завершение единственного реального вызова `f()` synchronized before возврат **любого** `once.Do(f)`.

```go
var a string
var once sync.Once

func setup() {
    a = "hello, world"
}

func doprint() {
    once.Do(setup)
    print(a)
}
```

После `Do` caller гарантированно наблюдает initialized state.

### Atomics

Operations из `sync/atomic` являются atomic synchronization operations. Если effect atomic `A` наблюдается atomic `B`, `A` synchronized before `B`.

Все atomic operations в program ведут себя так, как будто они выполнялись в некотором sequentially consistent order. Это соответствует semantics C++ sequentially consistent atomics и Java `volatile`.

### Finalizers

`runtime.SetFinalizer(x, f)` synchronized before finalizer call `f(x)`.

### Другие primitives

`sync.Cond`, `sync.Map`, `sync.Pool`, `sync.WaitGroup` и другие synchronization abstractions имеют собственные guarantees в package documentation. Любой package, предлагающий synchronization abstraction, должен документировать её memory-ordering contract.

## Неправильная synchronization

### Наблюдение одного write не означает observation предыдущих writes

```go
var a, b int

func f() {
    a = 1
    b = 2
}

func g() {
    print(b)
    print(a)
}
```

Без synchronization допустим outcome `2` затем `0`.

### Broken double-checked locking

```go
var a string
var done bool

func setup() {
    a = "hello, world"
    done = true
}

func doprint() {
    if !done {
        once.Do(setup)
    }
    print(a)
}
```

Observation `done == true` само по себе не гарантирует visibility write `a`.

### Busy wait по ordinary variable

```go
var a string
var done bool

func setup() {
    a = "hello, world"
    done = true
}

func main() {
    go setup()
    for !done {
    }
    print(a)
}
```

Нет guarantee, что loop вообще увидит `done = true`; даже если увидит, visibility `a` не гарантирована.

### Publication pointer без synchronization

```go
type T struct {
    msg string
}

var g *T

func setup() {
    t := new(T)
    t.msg = "hello, world"
    g = t
}
```

Observation `g != nil` без synchronization не гарантирует observation fully initialized `g.msg`.

Во всех таких случаях решение одно: **explicit synchronization**.

## Ограничения compiler optimizations

Memory model ограничивает не только programmers, но и compiler.

Compiler не должен:

- вводить writes, отсутствующие в source execution;
- превращать один read в reads, наблюдающие разные concurrent values;
- превращать один write в несколько externally observable writes;
- перемещать accesses через потенциально non-returning/synchronizing calls без доказательства безопасности;
- предполагать, что loops обязательно terminate;
- reload'ить local value из shared memory так, что checked value и later-used value могут различаться;
- использовать shared destination как временное storage, создавая дополнительные observable intermediate values.

Пример недопустимой transformation:

```go
*p = 1
if cond {
    *p = 2
}
```

нельзя просто переписать как:

```go
*p = 2
if !cond {
    *p = 1
}
```

потому что concurrent reader получил бы возможность наблюдать `2` в execution, где original program при `cond == false` этого не допускал.

Другой пример:

```go
*p = i + *p/2
```

нельзя раскладывать в externally visible:

```go
*p /= 2
*p += i
```

если intermediate write может стать видим racing goroutine.

## Вывод

Data-race-free Go programs имеют sequentially consistent semantics. Корректный concurrent design должен создавать явные synchronization edges через documented primitives. Race-detector и memory model — инструменты проверки/понимания, но не замена synchronization.
