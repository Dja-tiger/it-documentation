---
title: "Модель памяти Go"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/go"
upstream_path: "doc/go_mem.html"
upstream_ref: "go1.27.1"
translation_status: "reviewed"
---

# Модель памяти Go

Версия документа: **6 июня 2022 года**.

## Введение {#introduction}

Модель памяти Go определяет условия, при которых чтение переменной в одной goroutine гарантированно наблюдает значения, созданные записями в ту же переменную в другой goroutine.

### Совет {#advice}

Programs, изменяющие данные, к которым одновременно обращаются несколько goroutines, должны сериализовать такой доступ.

Для сериализации защищайте данные channel operations или другими synchronization primitives, например из packages [`sync`](https://pkg.go.dev/sync/) и [`sync/atomic`](https://pkg.go.dev/sync/atomic/).

Если вам необходимо прочитать оставшуюся часть этого документа, чтобы понять поведение собственной program, вы слишком усложнили design.

**Не пытайтесь быть слишком умным.**

### Неформальный обзор {#overview}

Go подходит к memory model так же, как к остальному языку: semantics должны быть простыми, понятными и полезными. Этот раздел даёт общий обзор, которого должно хватить большинству programmers. Формальная модель приведена ниже.

**Data race** — запись в memory location, выполняющаяся concurrent с другим чтением или записью той же location, если только все involved accesses не являются atomic accesses из package `sync/atomic`.

Programmers настоятельно рекомендуется использовать proper synchronization и избегать data races.

В отсутствие data races Go programs ведут себя так, как если бы все goroutines multiplex'ились на одном processor. Это свойство часто называется **DRF-SC**: data-race-free programs выполняются sequentially consistently.

Хотя Go code должен быть race-free, существуют ограничения на то, что implementation может делать при наличии race. Implementation всегда может обнаружить race, сообщить о ней и завершить program. В противном случае каждое чтение memory location размером не более machine word должно наблюдать значение, которое действительно было записано в эту location — возможно concurrent goroutine — и ещё не было overwritten.

Эти ограничения делают Go ближе к Java/JavaScript, где большинство races имеет ограниченный набор outcomes, и дальше от C/C++, где поведение program с race полностью undefined и compiler может делать произвольные вещи.

Цель Go — сделать ошибочные programs более надёжными и проще debug'ить, одновременно сохраняя принцип: races являются errors, и tools могут их диагностировать.

## Memory Model {#model}

Формальное определение следует подходу Hans-J. Boehm и Sarita V. Adve из статьи [Foundations of the C++ Concurrency Memory Model](https://dl.acm.org/doi/10.1145/1375581.1375591), PLDI 2008. Определение race-free programs и guarantee sequential consistency эквивалентны изложенным в этой работе.

Memory model задаёт требования к executions program. Program execution состоит из executions goroutines, а они — из memory operations.

**Memory operation** моделируется четырьмя характеристиками:

1. kind — ordinary data read, ordinary data write или **synchronizing operation**, например atomic access, mutex operation или channel operation;
2. location operation в program;
3. memory location / variable, к которой выполняется access;
4. values, которые operation читает или записывает.

Некоторые operations являются **read-like**: ordinary read, atomic read, mutex lock, channel receive.

Другие являются **write-like**: ordinary write, atomic write, mutex unlock, channel send, channel close.

Некоторые — например atomic compare-and-swap — одновременно read-like и write-like.

**Goroutine execution** моделируется как set memory operations, выполняемых одной goroutine.

### Requirement 1

Memory operations каждой goroutine должны соответствовать корректному sequential execution этой goroutine с учётом прочитанных и записанных values.

Execution должно быть согласовано с relation **sequenced before** — partial ordering requirements, задаваемыми [[spec|Go language specification]] для control flow constructs и [порядка evaluation expressions](https://go.dev/ref/spec#Order_of_evaluation).

**Go program execution** моделируется как set goroutine executions вместе с mapping **W**, которое для каждой read-like operation указывает write-like operation, значение которой она читает. Разные executions одной program могут иметь разные W.

### Requirement 2

Для конкретного program execution mapping W, ограниченное synchronizing operations, должно быть объяснимо некоторым implicit **total order** всех synchronizing operations, согласованным с sequencing и values, читаемыми/записываемыми этими operations.

Relation **synchronized before** — partial order synchronizing memory operations, derived from W.

Если synchronizing read-like operation *r* наблюдает synchronizing write-like operation *w*, то есть:

```text
W(r) = w
```

то *w* synchronized before *r*.

Неформально synchronized-before — subset implicit total order из предыдущего requirement, содержащий только information, непосредственно наблюдаемую W.

Relation **happens before** определяется как transitive closure union relations:

- sequenced before;
- synchronized before.

### Requirement 3

Для ordinary non-synchronizing read *r* memory location *x*, W(r) должна быть записью *w*, **visible** для *r*.

Visible означает выполнение обоих условий:

1. *w* happens before *r*;
2. *w* не happens before никакой другой записи *w′* в *x*, которая сама happens before *r*.

### Data races

**Read-write data race** на location *x* состоит из read-like operation *r* и write-like operation *w* на *x*, где хотя бы одна operation non-synchronizing, а operations unordered relation happens-before:

- *r* не happens before *w*;
- *w* не happens before *r*.

**Write-write data race** состоит из двух write-like operations *w* и *w′* на одной location *x*, где хотя бы одна non-synchronizing, и они также unordered by happens-before.

Если на location *x* нет read-write или write-write races, у любого read *r* этой location существует только одна возможная W(r): единственная запись *w*, непосредственно предшествующая *r* в happens-before order.

Более общо можно показать: любая Go program, являющаяся data-race-free — то есть не имеющая executions с read-write или write-write races — может иметь только outcomes, объяснимые некоторым sequentially consistent interleaving goroutine executions.

Это и есть **DRF-SC**.

Цель formal definition — предоставить race-free programs тот же DRF-SC guarantee, который существует в C, C++, Java, JavaScript, Rust и Swift.

Некоторые language operations Go — например goroutine creation и memory allocation — действуют как synchronization operations. Их влияние на synchronized-before описано ниже. Packages, предоставляющие собственные synchronization abstractions, отвечают за документирование аналогичных guarantees.

## Ограничения implementation для programs с data races {#restrictions}

Предыдущий раздел формально описал race-free execution. Здесь неформально указаны semantics, которые implementations обязаны предоставлять programs, содержащим races.

Implementation может при обнаружении race сообщить о ней и остановить program. Именно это делают implementations с ThreadSanitizer, доступные через:

```bash
go build -race
```

Чтение array, struct или complex number может быть реализовано как отдельные reads каждого sub-value — array element, struct field, real/imaginary component — в любом порядке.

Аналогично write array, struct или complex number может быть набором writes отдельных sub-values в любом порядке.

Read *r* location *x*, содержащей value размером не больше machine word, должна наблюдать некоторую write *w*, для которой:

- *r* не happens before *w*;
- не существует write *w′*, такой что *w* happens before *w′* и *w′* happens before *r*.

Иначе говоря, read должна наблюдать value, записанное preceding или concurrent write.

Наблюдение acausal и **out-of-thin-air** writes запрещено.

Для locations больше machine word implementations рекомендуется предоставлять те же semantics, но это не обязательно. Ради performance implementation может рассматривать larger operation как set machine-word operations в unspecified order.

Следствие: races на multiword structures могут давать inconsistent values, не соответствующие ни одной single write. Если value зависит от согласованности internal pairs вроде `(pointer, length)` или `(pointer, type)` — как interfaces, maps, slices и strings в большинстве Go implementations — race может привести к произвольной memory corruption.

Примеры неправильной synchronization приведены в [[#Неправильная synchronization]]. Ограничения compiler optimizations — в [[#Неправильная compilation]].

## Synchronization {#synchronization}

### Initialization {#init}

Program initialization выполняется в одной goroutine, хотя эта goroutine может создать другие goroutines, которые будут выполняться concurrently.

> **Rule.** Если package `p` импортирует package `q`, завершение `init` functions package `q` happens before начало любой `init` function package `p`.

> **Rule.** Завершение всех `init` functions synchronized before начало `main.main`.

### Создание goroutine {#go}

> **Rule.** `go` statement, запускающий новую goroutine, synchronized before начало execution этой goroutine.

Пример:

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

Call `hello` гарантированно когда-нибудь напечатает:

```text
hello, world
```

возможно уже после return `hello`.

### Завершение goroutine {#goexit}

Exit goroutine **не гарантированно** synchronized before какое-либо последующее event program.

```go
var a string

func hello() {
	go func() { a = "hello" }()
	print(a)
}
```

Assignment `a` не followed by synchronization event и поэтому не гарантированно будет observed другой goroutine. Aggressive compiler даже может удалить весь `go` statement.

Если effect goroutine должен быть observed другой goroutine, установите ordering через explicit synchronization — lock или channel communication.

### Channel communication {#chan}

Channel communication — основной synchronization mechanism между goroutines. Каждый send на конкретный channel соответствует receive с этого channel, обычно в другой goroutine.

> **Rule.** Send на channel synchronized before завершение corresponding receive с этого channel.

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

Program гарантированно печатает `"hello, world"`: write `a` sequenced before send `c`, send synchronized before completion corresponding receive, а receive sequenced before `print`.

> **Rule.** Closing channel synchronized before receive, возвращающий zero value из-за того, что channel closed.

Если в предыдущем example заменить:

```go
c <- 0
```

на:

```go
close(c)
```

гарантия останется той же.

> **Rule.** Receive из unbuffered channel synchronized before завершение corresponding send в этот channel.

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

Эта program также гарантированно печатает `"hello, world"`.

Если сделать channel buffered:

```go
c = make(chan int, 1)
```

гарантия исчезает: program может напечатать empty string, crash или проявить другое behavior.

> **Rule.** *k*-й receive из channel capacity *C* synchronized before завершение (*k* + *C*)-го send в этот channel.

Это generalization buffered channels позволяет моделировать counting semaphore:

- число items channel = число active uses;
- capacity = maximum simultaneous uses;
- send = acquire semaphore;
- receive = release semaphore.

Пример ограничивает concurrent work максимум тремя goroutines:

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
	select{}
}
```

### Locks {#locks}

Package `sync` предоставляет `sync.Mutex` и `sync.RWMutex`.

> **Rule.** Для любого `sync.Mutex` или `sync.RWMutex` `l` и *n* < *m*, call *n* `l.Unlock()` synchronized before return call *m* `l.Lock()`.

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

Program гарантированно печатает `"hello, world"`.

Первый `l.Unlock()` в `f` synchronized before return второго `l.Lock()` в `main`, который sequenced before `print`.

> **Rule.** Для любого call `l.RLock` на `sync.RWMutex` существует *n*, такое что *n*-й `l.Unlock` synchronized before return из `l.RLock`, а matching `l.RUnlock` synchronized before return из call *n*+1 `l.Lock`.

> **Rule.** Successful `l.TryLock` или `l.TryRLock` equivalent `l.Lock`/`l.RLock`. Unsuccessful call не имеет никакого synchronizing effect.

С точки зрения memory model `TryLock`/`TryRLock` может рассматриваться как способный вернуть `false` даже когда mutex unlocked.

### `Once` {#once}

`sync.Once` обеспечивает safe one-time initialization при нескольких goroutines.

Несколько goroutines могут выполнить:

```go
once.Do(f)
```

но только одна выполнит `f`; остальные calls block до return `f`.

> **Rule.** Completion единственного `f()` из `once.Do(f)` synchronized before return любого call `once.Do(f)`.

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

func twoprint() {
	go doprint()
	go doprint()
}
```

Call `twoprint` вызывает `setup` ровно один раз; `setup` завершится до обоих `print`, поэтому `"hello, world"` будет напечатано дважды.

### Atomic values {#atomic}

APIs package [`sync/atomic`](https://pkg.go.dev/sync/atomic/) являются atomic operations, используемыми для synchronization goroutines.

> **Rule.** Если effect atomic operation *A* observed atomic operation *B*, то *A* synchronized before *B*.

Все atomic operations program ведут себя так, как если бы выполнялись в некотором **sequentially consistent order**.

Эти semantics соответствуют sequentially consistent atomics C++ и `volatile` variables Java.

### Finalizers {#finalizer}

`runtime.SetFinalizer(x, f)` добавляет finalizer для object `x`.

> **Rule.** Call `SetFinalizer(x, f)` synchronized before finalization call `f(x)`.

### Дополнительные mechanisms {#more}

Package `sync` также предоставляет synchronization abstractions:

- `sync.Cond`;
- `sync.Map`;
- `sync.Pool`;
- `sync.WaitGroup`.

Documentation каждого type определяет его memory synchronization guarantees.

Другие packages, предоставляющие synchronization abstractions, также должны документировать свои guarantees.

## Неправильная synchronization {#badsync}

Programs с races являются incorrect и могут иметь non-sequentially-consistent executions.

Read *r* может наблюдать value любой write *w*, выполняемой concurrently с *r*. Даже если это произошло, из него **не следует**, что reads после *r* увидят writes, предшествовавшие *w*.

Пример:

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

func main() {
	go f()
	g()
}
```

`g` может напечатать:

```text
2
0
```

Это делает несколько common idioms invalid.

### Double-checked locking

Неправильный вариант:

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

func twoprint() {
	go doprint()
	go doprint()
}
```

Наблюдение write `done=true` не гарантирует observation write `a`. Program может incorrect напечатать empty string.

### Busy waiting

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

Наблюдение `done=true` снова не гарантирует observation write `a`; program может напечатать empty string.

Более того, write `done` вообще не гарантированно когда-либо будет observed `main`, потому что между goroutines нет synchronization. Loop не обязан завершиться.

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

func main() {
	go setup()
	for g == nil {
	}
	print(g.msg)
}
```

Даже если `main` увидит `g != nil`, нет гарантии, что он увидит initialized `g.msg`.

Во всех этих examples решение одно: **explicit synchronization**.

## Неправильная compilation {#badcompiler}

Memory model ограничивает compiler optimizations так же, как ограничивает programs.

Optimization, valid для single-threaded program, не обязательно valid для Go concurrency.

Compiler не должен:

- вводить writes, отсутствующие в original program;
- позволять одному read наблюдать несколько values;
- позволять одной write записывать несколько values.

Все examples ниже предполагают, что `*p` и `*q` указывают memory locations, доступные нескольким goroutines.

### Нельзя выносить write из conditional

Original:

```go
*p = 1
if cond {
	*p = 2
}
```

Compiler не может переписать его в:

```go
*p = 2
if !cond {
	*p = 1
}
```

Если `cond == false` и другая goroutine читает `*p`, в original она может увидеть prior value или `1`; в rewritten она может увидеть `2`, чего original execution не позволял.

### Нельзя предполагать, что loop завершится

```go
n := 0
for e := list; e != nil; e = e.next {
	n++
}
i := *p
*q = 1
```

Compiler в общем случае не может переместить accesses `*p`/`*q` перед loop.

Если `list` cyclic, original никогда не обращается к `*p`/`*q`, а rewritten program обращалась бы.

Перенос `*p` мог бы быть допустим, если compiler докажет, что access не panic; перенос `*q` дополнительно требует доказать, что никакая другая goroutine не обращается к `*q`.

### Нельзя предполагать, что called function возвращается или не synchronizes

```go
f()
i := *p
*q = 1
```

Compiler не может произвольно перенести accesses перед `f()` без точного знания поведения `f`.

Если `f` не возвращается, original не обращается к `*p`/`*q`. Если `f` содержит synchronization, original может устанавливать happens-before edges, которых не будет у rewritten program.

### Один read не может наблюдать несколько values

```go
i := *p
if i < 0 || i >= len(funcs) {
	panic("invalid function index")
}
... complex code ...
// compiler must NOT reload i = *p here
funcs[i]()
```

Compiler не должен discard local `i`, а затем reload его из shared `*p`: value `*p` могла измениться concurrent goroutine. Вместо этого compiler может spill `i` в stack.

### Одна write не может записывать несколько values

Original:

```go
*p = i + *p/2
```

Compiler не может использовать `*p` как temporary storage, переписав:

```go
*p /= 2
*p += i
```

Если `i` и `*p` изначально равны 2, original пишет только 3, поэтому racing reader видит 2 или 3. Rewritten program временно пишет 1 и позволяет racing reader увидеть value, невозможное в original.

Такие optimizations разрешены C/C++ compilers. Go compiler с shared C/C++ backend должен явно отключать optimizations, invalid для Go.

### Когда added read допустим

Prohibition на introduction data races не применяется, если compiler может доказать, что race не влияет на correct execution target platform.

Например, на практически всех CPUs допустимо преобразовать:

```go
n := 0
for i := 0; i < m; i++ {
	n += *shared
}
```

в:

```go
n := 0
local := *shared
for i := 0; i < m; i++ {
	n += local
}
```

если доказано, что read `*shared` не fault'ит. Дополнительный read не влияет на существующие concurrent reads/writes.

Но такое преобразование было бы invalid для source-to-source translator, поскольку изменяет observable source-level memory accesses.

## Заключение {#conclusion}

Go programmers, пишущие data-race-free programs, могут рассчитывать на sequentially consistent execution так же, как в большинстве современных programming languages.

Для programs с races и programmers, и compilers должны помнить главный совет этого документа:

**не пытайтесь быть слишком умным.**
