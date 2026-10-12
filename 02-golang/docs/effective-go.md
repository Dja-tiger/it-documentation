---
title: "Effective Go"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/effective_go.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Effective Go

> **Примечание.** Этот документ был написан к выпуску Go в 2009 году и активно не обновляется. Хотя он остаётся хорошим руководством по использованию ядра языка, он не охватывает значительные изменения языка — generics, — экосистемы — modules, — и библиотек, добавленных позднее. Контекст см. в [issue 28782](https://go.dev/issue/28782). Полный список изменений приведён в [release notes](https://go.dev/doc/devel/release).

## Введение {#introduction}

Go — open-source язык программирования, ориентированный на простоту, надёжность и эффективность и специально спроектированный так, чтобы упрощать создание software в большом масштабе. Хотя Go заимствует идеи из существующих языков, у него есть необычные свойства, из-за которых эффективные Go-программы по своему характеру отличаются от программ, написанных на родственных языках. Прямолинейный перевод C++- или Java-программы на Go вряд ли даст удовлетворительный результат: Java-программы пишутся на Java, а не на Go. Если же рассматривать задачу с точки зрения Go, можно получить успешную, но заметно отличающуюся программу.

Иными словами, чтобы хорошо писать на Go, важно понимать свойства и idioms языка. Не менее важно знать сложившиеся conventions программирования на Go — именование, форматирование, построение программ и так далее, — чтобы ваш код был легко понятен другим Go-программистам.

Этот документ содержит рекомендации по написанию ясного, idiomatic Go-кода. Он дополняет [language specification](spec.md), [Tour of Go](https://go.dev/tour/) и [How to Write Go Code](code.md), которые следует прочитать прежде.

### Примеры {#examples}

[Исходники Go packages](https://go.dev/src/) предназначены не только для роли core library, но и как примеры использования языка. Кроме того, многие packages содержат рабочие самодостаточные executable examples, которые можно запускать прямо на сайте [go.dev](https://go.dev/), например [этот](https://go.dev/pkg/strings/#example-Map) — при необходимости нажмите «Example», чтобы раскрыть его.

Если у вас возникает вопрос о подходе к задаче или возможной реализации чего-либо, documentation, code и examples в library могут дать ответы, идеи и необходимый контекст.

## Форматирование {#formatting}

Вопросы форматирования вызывают больше всего споров и при этом имеют наименьшее значение. Люди способны привыкнуть к разным styles, но лучше, если им не приходится этого делать; кроме того, теме уделяется меньше времени, когда все придерживаются одного style. Проблема в том, как прийти к такой утопии без длинного prescriptive style guide.

В Go используется необычный подход: большая часть вопросов форматирования отдаётся машине. Программа `gofmt` — также доступная как `go fmt`, работающая на уровне package, а не отдельного source file, — читает Go-программу и выдаёт source в standard style indentation и vertical alignment, сохраняя и при необходимости переформатируя comments. Если вы не знаете, как оформить новую layout-ситуацию, запустите `gofmt`; если результат кажется неправильным, перестройте программу — либо заведите bug на `gofmt`, — а не пытайтесь обходить formatter.

Например, нет смысла вручную выравнивать comments полей structure. `gofmt` сделает это за вас. Для declaration:

```go
type T struct {
    name string // name of the object
    value int // its value
}
```

`gofmt` выровняет columns:

```go
type T struct {
    name    string // name of the object
    value   int    // its value
}
```

Весь Go-код standard packages отформатирован `gofmt`.

Некоторые детали форматирования всё же остаются. Кратко:

**Отступы.** Для indentation используются tabs, и `gofmt` по умолчанию выводит именно их. Используйте spaces только при необходимости.

**Длина строки.** В Go нет ограничения длины строки. Не беспокойтесь о выходе за пределы перфокарты. Если строка кажется слишком длинной, перенесите её и сделайте дополнительный tab indentation.

**Скобки.** Go требует меньше parentheses, чем C и Java: control structures (`if`, `for`, `switch`) не содержат parentheses в своём syntax. Кроме того, hierarchy precedence operators короче и понятнее, поэтому

```go
x<<8 + y<<16
```

означает именно то, что подсказывает spacing, в отличие от некоторых других языков.

## Комментарии {#commentary}

Go предоставляет C-style block comments `/* */` и C++-style line comments `//`. Нормой являются line comments; block comments встречаются в основном как package comments, но бывают полезны внутри expression или для отключения больших фрагментов кода.

Comments, расположенные непосредственно перед top-level declarations без пустой строки между ними, считаются документацией соответствующего declaration. Эти doc comments являются основной документацией Go package или command. Подробнее см. [Go Doc Comments](comment.md).

## Имена {#names}

Имена в Go столь же важны, как и в любом другом языке. Более того, у них есть semantic effect: visibility имени за пределами package определяется тем, является ли первый символ uppercase. Поэтому conventions именования в Go заслуживают отдельного внимания.

### Имена packages {#package-names}

При import package его имя становится accessor к содержимому. После

```go
import "bytes"
```

импортирующий package может обращаться к `bytes.Buffer`. Полезно, когда все пользователи package могут использовать одно и то же имя для обращения к его содержимому, поэтому package name должно быть хорошим: коротким, лаконичным и выразительным. По convention packages получают lowercase single-word names; underscores или mixedCaps не нужны.

Лучше ошибиться в сторону краткости: каждый пользователь package будет постоянно печатать это имя. И не беспокойтесь заранее о collisions. Package name — лишь default name import; оно не обязано быть уникальным во всём source code, а в редком случае collision импортирующий package может выбрать другое local name. В любом случае путаница редка, поскольку filename/path в import точно определяет используемый package.

Ещё одна convention: package name является base name его source directory. Package в `src/encoding/base64` импортируется как `"encoding/base64"`, но называется `base64`, а не `encoding_base64` и не `encodingBase64`.

Код, импортирующий package, будет использовать package name для обращения к его содержимому, поэтому exported names внутри package могут учитывать это и избегать повторения. Не используйте notation `import .`, которая может упростить tests, запускаемые вне тестируемого package, но в остальных случаях её следует избегать.

Например, type buffered reader в package `bufio` называется `Reader`, а не `BufReader`, поскольку пользователи видят его как `bufio.Reader` — ясное и краткое имя. Кроме того, поскольку imported entities всегда адресуются через package name, `bufio.Reader` не конфликтует с `io.Reader`.

Аналогично function для создания нового `ring.Ring` — то есть constructor в терминологии Go — обычно могла бы называться `NewRing`, но поскольку `Ring` — единственный type, экспортируемый package, а сам package называется `ring`, function называется просто `New`; clients видят её как `ring.New`. Используйте структуру package, чтобы выбирать хорошие имена.

Ещё один короткий пример — `once.Do`: `once.Do(setup)` читается хорошо и не станет лучше как `once.DoOrWaitUntilDone(setup)`. Длинные имена автоматически не повышают читаемость. Хороший doc comment часто полезнее сверхдлинного имени.

### Getters {#Getters}

Go не предоставляет автоматической поддержки getters и setters. Нет ничего плохого в том, чтобы реализовать их самостоятельно, и часто это уместно, но добавлять `Get` в имя getter неidiomatic и не требуется. Если есть field `owner` — lowercase, unexported, — getter должен называться `Owner` — uppercase, exported, — а не `GetOwner`. Использование uppercase names для export позволяет отличить field от method. Setter, если он нужен, скорее всего, будет называться `SetOwner`.

Оба имени хорошо читаются:

```go
owner := obj.Owner()
if owner != user {
    obj.SetOwner(user)
}
```

### Имена interfaces {#interface-names}

По convention one-method interfaces называют именем method плюс suffix `-er` или похожим изменением, образующим имя действующего лица: `Reader`, `Writer`, `Formatter`, `CloseNotifier` и так далее.

Таких имён много, и полезно соблюдать их вместе с function names, которые они фиксируют. `Read`, `Write`, `Close`, `Flush`, `String` и подобные имеют канонические signatures и meanings. Чтобы избежать путаницы, не называйте свой method одним из этих имён, если он не имеет той же signature и того же смысла. И наоборот: если ваш type реализует method с тем же meaning, что и method известного type, используйте то же имя и signature; method преобразования в string называйте `String`, а не `ToString`.

### MixedCaps {#mixed-caps}

Наконец, convention Go — использовать `MixedCaps` или `mixedCaps`, а не underscores, для multiword names.

## Semicolons {#semicolons}

Как и C, formal grammar Go использует semicolons для завершения statements, но, в отличие от C, эти semicolons обычно отсутствуют в source. Вместо этого lexer автоматически вставляет semicolons во время scanning по простому правилу, поэтому input text почти свободен от них.

Правило таково. Если последний token перед newline является identifier — включая такие слова, как `int` и `float64`, — basic literal, например numeric или string constant, либо одним из tokens

```text
break continue fallthrough return ++ -- ) }
```

lexer всегда вставляет после token semicolon. Кратко правило можно сформулировать так: «если newline идёт после token, который способен завершить statement, вставить semicolon».

Semicolon также можно опустить непосредственно перед closing brace, поэтому statement вроде

```go
go func() { for { dst <- <-src } }()
```

не требует semicolons. В idiomatic Go semicolons встречаются только, например, в clauses цикла `for`, где разделяют initializer, condition и continuation. Они также нужны для разделения нескольких statements в одной строке, если вы всё же пишете код таким образом.

Следствие rules вставки semicolons: opening brace control structure (`if`, `for`, `switch` или `select`) нельзя переносить на следующую строку. Иначе перед brace будет вставлен semicolon, что может привести к нежелательному результату. Пишите:

```go
if i < f() {
    g()
}
```

а не:

```go
if i < f()  // wrong!
{           // wrong!
    g()
}
```

## Control structures {#control-structures}

Control structures Go родственны C, но отличаются в важных деталях. Нет loops `do` или `while`, есть только немного более общий `for`; `switch` гибче; `if` и `switch` принимают optional initialization statement наподобие `for`; statements `break` и `continue` могут принимать optional label, указывающий, что именно прервать или продолжить; кроме того, существуют новые control structures, включая type switch и multiway communications multiplexer `select`. Syntax тоже немного отличается: parentheses отсутствуют, а bodies всегда должны быть заключены в braces.

### If {#if}

Простой `if` в Go выглядит так:

```go
if x > 0 {
    return y
}
```

Обязательные braces побуждают писать даже простые `if` statements в несколько строк. Это хороший style в любом случае, особенно если body содержит control statement вроде `return` или `break`.

Поскольку `if` и `switch` принимают initialization statement, его часто используют для задания local variable:

```go
if err := file.Chmod(0664); err != nil {
    log.Print(err)
    return err
}
```

В Go libraries вы увидите, что когда `if` statement не переходит в следующий statement — то есть body заканчивается `break`, `continue`, `goto` или `return`, — лишний `else` опускается. {#else}

```go
f, err := os.Open(name)
if err != nil {
    return err
}
codeUsing(f)
```

Это пример типичной ситуации, где код должен последовательно защищаться от нескольких error conditions. Код хорошо читается, если успешный control flow идёт вниз по странице, а error cases исключаются по мере появления. Поскольку error cases обычно завершаются `return`, resulting code не требует `else` statements.

```go
f, err := os.Open(name)
if err != nil {
    return err
}
d, err := f.Stat()
if err != nil {
    f.Close()
    return err
}
codeUsing(f, d)
```

### Повторное объявление и присваивание {#redeclaration}

Небольшое отступление: последний пример предыдущего раздела демонстрирует деталь работы short declaration `:=`. Declaration, вызывающее `os.Open`, выглядит так:

```go
f, err := os.Open(name)
```

Этот statement объявляет две variables: `f` и `err`. Несколькими строками ниже вызов `f.Stat` выглядит так:

```go
d, err := f.Stat()
```

на первый взгляд будто объявляя `d` и `err`. Однако `err` встречается в обоих statements. Такое дублирование допустимо: `err` объявляется первым statement, а во втором только *пере-присваивается*. Поэтому вызов `f.Stat` использует существующую variable `err`, объявленную выше, и лишь записывает в неё новое value.

В declaration `:=` variable `v` может встречаться, даже если уже объявлена, при соблюдении условий:

- это declaration находится в том же scope, что и существующее declaration `v` — если `v` уже объявлена во внешнем scope, будет создана новая variable §;
- соответствующее value в initialization assignable к `v`;
- declaration создаёт как минимум ещё одну новую variable.

Это необычное свойство — чистый прагматизм, позволяющий, например, легко использовать одно value `err` в длинной `if-else` chain. Такой код встречается часто.

§ Стоит отметить, что в Go scope function parameters и return values совпадает со scope function body, даже несмотря на то, что лексически они находятся за пределами braces body.

### For {#for}

Цикл `for` Go похож на C `for`, но не идентичен ему. Он объединяет `for` и `while`; `do-while` отсутствует. Есть три формы, и только одна содержит semicolons:

```go
// Like a C for
for init; condition; post { }

// Like a C while
for condition { }

// Like a C for(;;)
for { }
```

Short declarations позволяют объявлять index variable прямо в loop:

```go
sum := 0
for i := 0; i < 10; i++ {
    sum += i
}
```

При iteration по array, slice, string или map либо при чтении из channel loop может управляться clause `range`:

```go
for key, value := range oldMap {
    newMap[key] = value
}
```

Если нужен только первый item range — key или index, — второй можно опустить:

```go
for key := range m {
    if key.expired() {
        delete(m, key)
    }
}
```

Если нужен только второй item — value, — используйте *blank identifier* `_`, чтобы отбросить первый:

```go
sum := 0
for _, value := range array {
    sum += value
}
```

У blank identifier много применений; они описаны [далее](#blank).

Для strings `range` выполняет дополнительную работу: разбивает input на отдельные Unicode code points, parsing UTF-8. Ошибочная encoding потребляет один byte и выдаёт replacement rune U+FFFD. Термин `rune` — также built-in type — в Go означает один Unicode code point. Подробнее см. [language specification](spec.md#Rune_literals).

Loop:

```go
for pos, char := range "日本\x80語" { // \x80 is an illegal UTF-8 encoding
    fmt.Printf("character %#U starts at byte position %d\n", char, pos)
}
```

печатает:

```text
character U+65E5 '日' starts at byte position 0
character U+672C '本' starts at byte position 3
character U+FFFD '�' starts at byte position 6
character U+8A9E '語' starts at byte position 7
```

Наконец, в Go нет comma operator, а `++` и `--` являются statements, а не expressions. Поэтому, если в `for` нужно изменять несколько variables, используйте parallel assignment, хотя это исключает `++` и `--`:

```go
// Reverse a
for i, j := 0, len(a)-1; i < j; i, j = i+1, j-1 {
    a[i], a[j] = a[j], a[i]
}
```

### Switch {#switch}

`switch` Go более общий, чем C. Expressions не обязаны быть constants и даже integers; cases вычисляются сверху вниз до первого match; если у `switch` нет expression, он переключается по `true`. Поэтому цепочку `if`-`else if`-`else` можно — и idiomatic — писать как `switch`.

```go
func unhex(c byte) byte {
    switch {
    case '0' <= c && c <= '9':
        return c - '0'
    case 'a' <= c && c <= 'f':
        return c - 'a' + 10
    case 'A' <= c && c <= 'F':
        return c - 'A' + 10
    }
    return 0
}
```

Automatic fallthrough отсутствует, но несколько cases можно перечислять через commas:

```go
func shouldEscape(c byte) bool {
    switch c {
    case ' ', '?', '&', '=', '#', '+', '%':
        return true
    }
    return false
}
```

Хотя в Go `break` statements встречаются реже, чем в некоторых других C-like языках, ими можно завершить `switch` раньше. Иногда, однако, нужно выйти из окружающего loop, а не из `switch`. В Go это делается label на loop и `break` к этому label. Следующий пример показывает оба варианта:

```go
Loop:
    for n := 0; n < len(src); n += size {
        switch {
        case src[n] < sizeOne:
            if validateOnly {
                break
            }
            size = 1
            update(src[n])

        case src[n] < sizeTwo:
            if n+1 >= len(src) {
                err = errShortInput
                break Loop
            }
            if validateOnly {
                break
            }
            size = 2
            update(src[n] + src[n+1]<<shift)
        }
    }
```

Разумеется, `continue` также принимает optional label, но применяется только к loops.

В завершение раздела — comparison routine для byte slices, использующая два `switch` statements:

```go
// Compare returns an integer comparing the two byte slices,
// lexicographically.
// The result will be 0 if a == b, -1 if a < b, and +1 if a > b
func Compare(a, b []byte) int {
    for i := 0; i < len(a) && i < len(b); i++ {
        switch {
        case a[i] > b[i]:
            return 1
        case a[i] < b[i]:
            return -1
        }
    }
    switch {
    case len(a) > len(b):
        return 1
    case len(a) < len(b):
        return -1
    }
    return 0
}
```

### Type switch {#type_switch}

`switch` также можно использовать для определения dynamic type interface variable. Такой *type switch* использует syntax type assertion с keyword `type` внутри parentheses. Если `switch` объявляет variable в expression, в каждом clause эта variable имеет соответствующий type. В таких случаях idiomatic также повторно использовать то же имя, фактически объявляя в каждом case новую variable с тем же именем, но другим type.

```go
var t interface{}
t = functionOfSomeType()
switch t := t.(type) {
default:
    fmt.Printf("unexpected type %T\n", t)     // %T prints whatever type t has
case bool:
    fmt.Printf("boolean %t\n", t)             // t has type bool
case int:
    fmt.Printf("integer %d\n", t)             // t has type int
case *bool:
    fmt.Printf("pointer to boolean %t\n", *t) // t has type *bool
case *int:
    fmt.Printf("pointer to integer %d\n", *t) // t has type *int
}
```

## Functions {#functions}

### Несколько возвращаемых значений {#multiple-returns}

Одна из необычных возможностей Go — functions и methods могут возвращать несколько values. Это позволяет избавиться от пары неуклюжих idioms C: in-band error returns вроде `-1` для `EOF` и изменения argument, переданного by address.

В C write error сигнализируется negative count, а error code прячется в volatile location. В Go `Write` может вернуть и count, *и* error: «да, вы записали некоторое количество bytes, но не все, потому что устройство заполнилось». Signature method `Write` для files из package `os`:

```go
func (file *File) Write(b []byte) (n int, err error)
```

Как говорит documentation, он возвращает число записанных bytes и non-nil `error`, когда `n != len(b)`. Это распространённый style; дополнительные примеры см. в разделе об error handling.

Похожий подход устраняет необходимость передавать pointer на return value для имитации reference parameter. Вот простая function, извлекающая число из позиции byte slice и возвращающая число вместе со следующей позицией:

```go
func nextInt(b []byte, i int) (int, int) {
    for ; i < len(b) && !isDigit(b[i]); i++ {
    }
    x := 0
    for ; i < len(b) && isDigit(b[i]); i++ {
        x = x*10 + int(b[i]) - '0'
    }
    return x, i
}
```

Её можно использовать для scanning чисел во входном slice `b`:

```go
for i := 0; i < len(b); {
    x, i = nextInt(b, i)
    fmt.Println(x)
}
```

### Именованные result parameters {#named-results}

Return, или result, parameters Go function можно именовать и использовать как обычные variables — так же, как incoming parameters. Если они именованы, при входе в function они инициализируются zero values своих types; если function выполняет `return` без arguments, возвращаются текущие values result parameters.

Имена не обязательны, но способны сделать код короче и яснее: они служат документацией. Если дать имена results `nextInt`, сразу ясно, какой из возвращаемых `int` что означает:

```go
func nextInt(b []byte, pos int) (value, nextPos int) {
```

Поскольку named results инициализируются и связаны с bare return, они могут одновременно упрощать и прояснять код. Вот version `io.ReadFull`, хорошо использующая эту возможность:

```go
func ReadFull(r Reader, buf []byte) (n int, err error) {
    for len(buf) > 0 && err == nil {
        var nr int
        nr, err = r.Read(buf)
        n += nr
        buf = buf[nr:]
    }
    return
}
```

### Defer {#defer}

Statement `defer` в Go планирует function call — *deferred function* — на выполнение непосредственно перед return function, внутри которой выполнен `defer`. Это необычный, но эффективный способ обрабатывать ситуации, где resources должны освобождаться независимо от пути return. Канонические examples — unlocking mutex или closing file.

```go
// Contents returns the file's contents as a string.
func Contents(filename string) (string, error) {
    f, err := os.Open(filename)
    if err != nil {
        return "", err
    }
    defer f.Close()  // f.Close will run when we're finished.

    var result []byte
    buf := make([]byte, 100)
    for {
        n, err := f.Read(buf[0:])
        result = append(result, buf[0:n]...) // append is discussed later.
        if err != nil {
            if err == io.EOF {
                break
            }
            return "", err  // f will be closed if we return here.
        }
    }
    return string(result), nil // f will be closed if we return here.
}
```

Deferred call function вроде `Close` даёт два преимущества. Во-первых, гарантирует, что вы не забудете закрыть file — это легко сделать после последующего редактирования function и добавления нового return path. Во-вторых, `close` оказывается рядом с `open`, что гораздо яснее, чем размещать его в конце function.

Arguments deferred function — включая receiver, если function является method — вычисляются в момент выполнения `defer`, а не в момент выполнения самого отложенного *call*. Помимо устранения опасений по поводу изменения variables во время выполнения function, это означает, что один deferred call site может отложить несколько function executions. Глупый пример:

```go
for i := 0; i < 5; i++ {
    defer fmt.Printf("%d ", i)
}
```

Deferred functions выполняются в LIFO order, поэтому при return function этот код напечатает `4 3 2 1 0`. Более правдоподобный пример — простой tracing function execution. Можно написать пару routines:

```go
func trace(s string)   { fmt.Println("entering:", s) }
func untrace(s string) { fmt.Println("leaving:", s) }

// Use them like this:
func a() {
    trace("a")
    defer untrace("a")
    // do something....
}
```

Можно сделать лучше, используя тот факт, что arguments deferred functions вычисляются при выполнении `defer`. Tracing routine может подготовить argument для untracing routine:

```go
func trace(s string) string {
    fmt.Println("entering:", s)
    return s
}

func un(s string) {
    fmt.Println("leaving:", s)
}

func a() {
    defer un(trace("a"))
    fmt.Println("in a")
}

func b() {
    defer un(trace("b"))
    fmt.Println("in b")
    a()
}

func main() {
    b()
}
```

выводит:

```text
entering: b
in b
entering: a
in a
leaving: a
leaving: b
```

Для программистов, привыкших к block-level resource management в других языках, `defer` может казаться необычным, но его наиболее интересные и мощные применения возникают именно потому, что он function-based, а не block-based. В разделе о `panic` и `recover` будет ещё один пример.

## Данные {#data}

### Выделение памяти с `new` {#allocation_new}

В Go есть два allocation primitives — built-in functions `new` и `make`. Они делают разные вещи и применяются к разным types, что может сбивать с толку, но правила просты.

Сначала `new`. Это built-in function, выделяющая memory, однако, в отличие от одноимённых constructs некоторых других языков, она не *инициализирует* memory, а только *обнуляет* её. `new(T)` выделяет zeroed storage для новой variable типа `T` и возвращает её address — value типа `*T`. В терминологии Go она возвращает pointer на newly allocated zero value типа `T`.

Начиная с Go 1.26, `new` также принимает value expression как argument, задающее initial value variable. Например, `new(int64(300))` выделяет новую variable типа `int64`, инициализированную значением 300, и возвращает её address.

Поскольку memory, возвращаемая `new`, zeroed, при design data structures полезно добиваться, чтобы zero value каждого type можно было использовать без дополнительной initialization. Тогда пользователь data structure может создать её через `new` и сразу начать работу.

Например, documentation `bytes.Buffer` говорит: «zero value для `Buffer` — пустой buffer, готовый к использованию». Аналогично `sync.Mutex` не имеет explicit constructor или method `Init`. Вместо этого zero value `sync.Mutex` определяется как unlocked mutex.

Свойство «zero value пригодно к использованию» работает transitively. Рассмотрим declaration:

```go
type SyncedBuffer struct {
    lock    sync.Mutex
    buffer  bytes.Buffer
}
```

Values типа `SyncedBuffer` также готовы к использованию сразу после allocation или обычного declaration. В следующем fragment и `p`, и `v` корректны без дополнительной подготовки:

```go
p := new(SyncedBuffer)  // type *SyncedBuffer
var v SyncedBuffer      // type  SyncedBuffer
```

### Constructors и composite literals {#composite_literals}

Иногда zero value недостаточно и нужен initializing constructor, как в примере, производном от package `os`:

```go
func NewFile(fd int, name string) *File {
    if fd < 0 {
        return nil
    }
    f := new(File)
    f.fd = fd
    f.name = name
    f.dirinfo = nil
    f.nepipe = 0
    return f
}
```

Здесь много boilerplate. Его можно упростить с помощью *composite literal* — expression, создающего новый instance при каждом evaluation:

```go
func NewFile(fd int, name string) *File {
    if fd < 0 {
        return nil
    }
    f := File{fd, name, nil, 0}
    return &f
}
```

В отличие от C, в Go совершенно нормально возвращать address local variable: storage, связанное с variable, продолжает существовать после return function. Более того, взятие address composite literal выделяет fresh instance при каждом evaluation, поэтому последние две строки можно объединить:

```go
return &File{fd, name, nil, 0}
```

Fields composite literal располагаются по порядку и при positional form должны быть указаны все. Однако если явно пометить elements парами *field*`:`*value*, initializers могут идти в любом порядке, а отсутствующие fields останутся равны соответствующим zero values. Поэтому можно написать:

```go
return &File{fd: fd, name: name}
```

В предельном случае composite literal без fields создаёт zero value данного type. Expressions `new(File)` и `&File{}` эквивалентны.

Composite literals также можно создавать для arrays, slices и maps; field labels в зависимости от type становятся indices или map keys. В следующих examples initialization работает независимо от конкретных values `Enone`, `Eio` и `Einval`, если они различны:

```go
a := [...]string   {Enone: "no error", Eio: "Eio", Einval: "invalid argument"}
s := []string      {Enone: "no error", Eio: "Eio", Einval: "invalid argument"}
m := map[int]string{Enone: "no error", Eio: "Eio", Einval: "invalid argument"}
```

### Выделение памяти с `make` {#allocation_make}

Вернёмся к allocation. Built-in function `make(T, args)` служит другой цели, чем `new(T)`. Она создаёт только slices, maps и channels и возвращает *initialized*, а не просто *zeroed*, value типа `T`, а не `*T`.

Различие связано с тем, что эти три types внутренне представляют references на data structures, которые необходимо инициализировать до использования. Slice, например, является descriptor из трёх элементов: pointer на data внутри array, length и capacity; пока они не инициализированы, slice равен `nil`.

Для slices, maps и channels `make` инициализирует внутреннюю data structure и подготавливает value к использованию. Например:

```go
make([]int, 10, 100)
```

выделяет array из 100 `int`, затем создаёт slice structure длиной 10 и capacity 100, указывающую на первые 10 elements array. При создании slice capacity можно опустить; подробнее см. раздел о slices.

В отличие от этого `new([]int)` возвращает pointer на newly allocated zeroed slice structure, то есть pointer на `nil` slice value.

Следующие examples показывают различие `new` и `make`:

```go
var p *[]int = new([]int)       // allocates slice structure; *p == nil; rarely useful
var v  []int = make([]int, 100) // the slice v now refers to a new array of 100 ints

// Unnecessarily complex:
var p *[]int = new([]int)
*p = make([]int, 100, 100)

// Idiomatic:
v := make([]int, 100)
```

Помните: `make` применяется только к maps, slices и channels и не возвращает pointer. Чтобы получить explicit pointer, используйте `new` либо явно возьмите address variable.

### Arrays {#arrays}

Arrays полезны при точном планировании layout memory и иногда позволяют избежать allocation, но прежде всего они являются building block для slices — темы следующего раздела. Для основы несколько слов об arrays.

Между поведением arrays в Go и C есть важные различия. В Go:

- arrays являются values; assignment одного array другому копирует все elements;
- если передать array в function, function получит *copy* array, а не pointer на него;
- size array является частью его type; types `[10]int` и `[20]int` различны.

Value semantics может быть полезна, но также дорога. Если требуется C-like behavior и efficiency, можно передать pointer на array:

```go
func Sum(a *[3]float64) (sum float64) {
    for _, v := range *a {
        sum += v
    }
    return
}

array := [...]float64{7.0, 8.5, 9.1}
x := Sum(&array)  // Note the explicit address-of operator
```

Но даже такой style неidiomatic для Go. Используйте slices.

### Slices {#slices}

Slices оборачивают arrays, предоставляя более общий, мощный и удобный interface к sequences data. За исключением объектов с явно фиксированной dimension, например transformation matrices, большая часть array programming в Go выполняется через slices, а не простые arrays.

Slices содержат references на underlying array; если присвоить один slice другому, оба будут ссылаться на один array. Если function принимает slice argument, изменения elements slice будут видны caller — аналогично передаче pointer на underlying array. Поэтому function `Read` может принимать slice вместо pointer и count; length slice задаёт верхний предел объёма data, который можно прочитать.

Signature method `Read` type `File` package `os`:

```go
func (f *File) Read(buf []byte) (n int, err error)
```

Method возвращает число прочитанных bytes и error value, если оно есть. Чтобы читать в первые 32 bytes более крупного buffer `buf`, выполните slicing buffer:

```go
n, err := f.Read(buf[0:32])
```

Такой slicing распространён и эффективен. Если пока не учитывать efficiency, первые 32 bytes buffer прочитала бы и следующая version:

```go
var n int
var err error
for i := 0; i < 32; i++ {
    nbytes, e := f.Read(buf[i:i+1])  // Read one byte.
    n += nbytes
    if nbytes == 0 || e != nil {
        err = e
        break
    }
}
```

Length slice можно изменять, пока он остаётся в пределах underlying array: просто присвойте slice от самого себя. *Capacity* slice, доступная через built-in function `cap`, сообщает maximum length, до которого slice может расшириться.

Вот function для append data к slice. Если data превышает capacity, slice reallocates. Resulting slice возвращается. Function использует тот факт, что `len` и `cap` допустимы для `nil` slice и возвращают 0:

```go
func Append(slice, data []byte) []byte {
    l := len(slice)
    if l + len(data) > cap(slice) {  // reallocate
        // Allocate double what's needed, for future growth.
        newSlice := make([]byte, (l+len(data))*2)
        // The copy function is predeclared and works for any slice type.
        copy(newSlice, slice)
        slice = newSlice
    }
    slice = slice[0:l+len(data)]
    copy(slice[l:], data)
    return slice
}
```

После этого slice необходимо вернуть, потому что, хотя `Append` может изменять elements `slice`, сам slice — runtime data structure с pointer, length и capacity — передаётся by value.

Идея append к slice настолько полезна, что реализована built-in function `append`. Но для понимания её design нужна ещё некоторая информация, поэтому вернёмся к ней позднее.

### Двумерные slices {#two_dimensional_slices}

Arrays и slices Go одномерны. Чтобы создать equivalent 2D array или slice, нужно определить array-of-arrays или slice-of-slices:

```go
type Transform [3][3]float64  // A 3x3 array, really an array of arrays.
type LinesOfText [][]byte     // A slice of byte slices.
```

Поскольку slices имеют variable length, каждый inner slice может иметь собственную длину. Это типичная ситуация, как в `LinesOfText`: каждая строка имеет независимую length.

```go
text := LinesOfText{
    []byte("Now is the time"),
    []byte("for all good gophers"),
    []byte("to bring some fun to the party."),
}
```

Иногда требуется выделить 2D slice, например при обработке scan lines pixels. Есть два способа. Первый — независимо выделить каждый slice. Второй — выделить один общий array и направить individual slices в его regions. Выбор зависит от application. Если slices могут расти или уменьшаться, их следует выделять независимо, чтобы не перезаписать следующую строку; если нет, эффективнее может быть single allocation.

Первый вариант — по одной строке:

```go
// Allocate the top-level slice.
picture := make([][]uint8, YSize) // One row per unit of y.
// Loop over the rows, allocating the slice for each row.
for i := range picture {
    picture[i] = make([]uint8, XSize)
}
```

Второй — одна allocation, нарезанная на строки:

```go
// Allocate the top-level slice, the same as before.
picture := make([][]uint8, YSize) // One row per unit of y.
// Allocate one large slice to hold all the pixels.
pixels := make([]uint8, XSize*YSize) // Has type []uint8 even though picture is [][]uint8.
// Loop over the rows, slicing each row from the front of the remaining pixels slice.
for i := range picture {
    picture[i], pixels = pixels[:XSize], pixels[XSize:]
}
```

### Maps {#maps}

Maps — удобная и мощная built-in data structure, связывающая values одного type — *key* — с values другого — *element* или *value*. Key может иметь любой type, для которого определён equality operator: integers, floating-point и complex numbers, strings, pointers, interfaces — если dynamic type поддерживает equality, — structs и arrays. Slices нельзя использовать как map keys, поскольку equality для них не определена.

Как и slices, maps хранят references на underlying data structure. Если передать map в function, изменяющую contents map, caller увидит изменения.

Maps можно создавать обычным syntax composite literals с key-value pairs, разделёнными colon, поэтому их легко строить при initialization:

```go
var timeZone = map[string]int{
    "UTC":  0*60*60,
    "EST": -5*60*60,
    "CST": -6*60*60,
    "MST": -7*60*60,
    "PST": -8*60*60,
}
```

Assignment и получение map values синтаксически выглядят так же, как для arrays и slices, за исключением того, что index не обязан быть integer:

```go
offset := timeZone["EST"]
```

Попытка получить map value по key, отсутствующему в map, возвращает zero value типа map elements. Например, для map integers lookup несуществующего key вернёт `0`. Set можно реализовать как map с value type `bool`: присваивайте entry `true`, чтобы добавить value в set, а проверяйте обычным indexing:

```go
attended := map[string]bool{
    "Ann": true,
    "Joe": true,
    ...
}

if attended[person] { // will be false if person is not in the map
    fmt.Println(person, "was at the meeting")
}
```

Иногда нужно отличать отсутствующий entry от zero value. Есть ли entry для `"UTC"`, или 0 получился потому, что key вообще отсутствует? Это можно различить одной из форм multiple assignment:

```go
var seconds int
var ok bool
seconds, ok = timeZone[tz]
```

По очевидным причинам это называется idiom «comma ok». Если `tz` присутствует, `seconds` получает правильное value, а `ok` — true; если нет, `seconds` получает zero, а `ok` — false.

Function, объединяющая это с понятным error report:

```go
func offset(tz string) int {
    if seconds, ok := timeZone[tz]; ok {
        return seconds
    }
    log.Println("unknown time zone:", tz)
    return 0
}
```

Чтобы проверить наличие key в map, не интересуясь самим value, вместо обычной variable value используйте [blank identifier](#blank) `_`:

```go
_, present := timeZone[tz]
```

Для удаления map entry используется built-in function `delete`, arguments которой — map и удаляемый key. Это безопасно даже если key уже отсутствует:

```go
delete(timeZone, "PDT")  // Now on Standard Time
```

### Printing {#printing}

Formatted printing в Go использует style, похожий на family `printf` C, но богаче и более общий. Functions находятся в package `fmt` и имеют capitalized names: `fmt.Printf`, `fmt.Fprintf`, `fmt.Sprintf` и так далее. String functions — `Sprintf` и другие — возвращают string, а не заполняют предоставленный buffer.

Format string указывать необязательно. Для `Printf`, `Fprintf` и `Sprintf` существуют соответствующие pairs functions, например `Print` и `Println`. Они не принимают format string, а генерируют default format для каждого argument. Versions `Println` также вставляют space между arguments и добавляют newline; versions `Print` добавляют spaces только когда ни один из соседних operands не является string.

В следующем примере каждая строка даёт одинаковый output:

```go
fmt.Printf("Hello %d\n", 23)
fmt.Fprint(os.Stdout, "Hello ", 23, "\n")
fmt.Println("Hello", 23)
fmt.Println(fmt.Sprint("Hello ", 23))
```

Formatted print functions `fmt.Fprint` и аналогичные принимают первым argument любой object, реализующий interface `io.Writer`; знакомые instances — `os.Stdout` и `os.Stderr`.

Здесь начинаются отличия от C. Во-первых, numeric formats вроде `%d` не требуют flags signedness или size; printing routines определяют эти свойства по type argument.

```go
var x uint64 = 1<<64 - 1
fmt.Printf("%d %x; %d %x\n", x, x, int64(x), int64(x))
```

печатает:

```text
18446744073709551615 ffffffffffffffff; -1 -1
```

Если нужен просто default conversion, например decimal для integers, можно использовать catchall format `%v` — «value»; результат точно такой же, как у `Print` и `Println`. Более того, этот format способен печатать *любое* value: arrays, slices, structs и maps.

Для map `timeZone` из предыдущего раздела:

```go
fmt.Printf("%v\n", timeZone)  // or just fmt.Println(timeZone)
```

получится:

```text
map[CST:-21600 EST:-18000 MST:-25200 PST:-28800 UTC:0]
```

Для maps `Printf` и связанные functions сортируют output lexicographically по key.

При printing struct modified format `%+v` сопровождает fields structure их именами, а alternate format `%#v` печатает любое value в полном Go syntax:

```go
type T struct {
    a int
    b float64
    c string
}
t := &T{ 7, -2.35, "abc\tdef" }
fmt.Printf("%v\n", t)
fmt.Printf("%+v\n", t)
fmt.Printf("%#v\n", t)
fmt.Printf("%#v\n", timeZone)
```

печатает:

```text
&{7 -2.35 abc   def}
&{a:7 b:-2.35 c:abc     def}
&main.T{a:7, b:-2.35, c:"abc\tdef"}
map[string]int{"CST":-21600, "EST":-18000, "MST":-25200, "PST":-28800, "UTC":0}
```

Обратите внимание на ampersands. Quoted string format также доступен через `%q` для values типа `string` или `[]byte`. Alternate format `%#q` при возможности использует backquotes. Format `%q` применим также к integers и runes, создавая single-quoted rune constant. `%x` работает со strings, byte arrays и byte slices так же, как с integers, создавая длинную hexadecimal string, а с space во format (`% x`) вставляет spaces между bytes.

Ещё один удобный format — `%T`, печатающий *type* value:

```go
fmt.Printf("%T\n", timeZone)
```

печатает:

```text
map[string]int
```

Если требуется контролировать default format custom type, достаточно определить для него method с signature `String() string`. Для простого type `T` это может выглядеть так:

```go
func (t *T) String() string {
    return fmt.Sprintf("%d/%g/%q", t.a, t.b, t.c)
}
fmt.Printf("%v\n", t)
```

чтобы печатать:

```text
7/-2.35/"abc\tdef"
```

Если нужно печатать также *values* типа `T`, а не только pointers на `T`, receiver `String` должен быть value type; здесь использован pointer, потому что это эффективнее и idiomatic для struct types. Подробнее см. [pointers vs. value receivers](#pointers_vs_values).

Наш method `String` может вызывать `Sprintf`, потому что print routines полностью reentrant и могут оборачиваться таким образом. Но есть важная деталь: не создавайте `String` method, вызывающий `Sprintf` так, что тот бесконечно рекурсивно войдёт обратно в `String`.

Это произойдёт, если `Sprintf` попытается печатать receiver непосредственно как string, что снова вызовет method. Такая ошибка распространена и легко допускается:

```go
type MyString string

func (m MyString) String() string {
    return fmt.Sprintf("MyString=%s", m) // Error: will recur forever.
}
```

Исправить её тоже легко: преобразуйте argument к basic string type, у которого этого method нет:

```go
type MyString string
func (m MyString) String() string {
    return fmt.Sprintf("MyString=%s", string(m)) // OK: note conversion.
}
```

В [разделе об initialization](#initialization) будет показана ещё одна technique, избегающая такой recursion.

Ещё один printing technique — передавать arguments одной print routine непосредственно другой. Signature `Printf` использует type `...interface{}` для последнего argument, указывая, что после format может идти произвольное число parameters любых types:

```go
func Printf(format string, v ...interface{}) (n int, err error) {
```

Внутри `Printf` variable `v` ведёт себя как `[]interface{}`, но при передаче в другую variadic function может использоваться как обычный список arguments. Вот implementation `log.Println`, использованной выше; она передаёт arguments напрямую в `fmt.Sprintln` для actual formatting:

```go
// Println prints to the standard logger in the manner of fmt.Println.
func Println(v ...interface{}) {
    std.Output(2, fmt.Sprintln(v...))  // Output takes parameters (int, string)
}
```

`...` после `v` во вложенном call `Sprintln` говорит compiler трактовать `v` как список arguments; без этого `v` передавался бы как один slice argument.

Printing содержит ещё больше возможностей, чем описано здесь. Подробности см. в documentation package `fmt`.

Кстати, parameter `...` может иметь конкретный type, например `...int` для function min, выбирающей minimum из списка integers:

```go
func Min(a ...int) int {
    min := int(^uint(0) >> 1)  // largest int
    for _, i := range a {
        if i < min {
            min = i
        }
    }
    return min
}
```

### Append {#append}

Теперь есть недостающая часть для объяснения design built-in function `append`. Signature `append` отличается от нашей custom function `Append` выше. Схематически она выглядит так:

```text
func append(slice []T, elements ...T) []T
```

где `T` — placeholder для любого конкретного type. Нельзя написать обычную Go function, где type `T` определяется caller. Поэтому `append` является built-in: ему нужна поддержка compiler.

`append` добавляет elements в конец slice и возвращает result. Result необходимо возвращать, потому что, как и в нашей `Append`, underlying array может измениться. Простой пример:

```go
x := []int{1,2,3}
x = append(x, 4, 5, 6)
fmt.Println(x)
```

печатает `[1 2 3 4 5 6]`. Таким образом, `append` немного похож на `Printf`, собирая произвольное количество arguments.

А что, если нужно сделать то же, что наша `Append`, — append целого slice к slice? Просто используйте `...` в call site, как выше для `Output`. Этот fragment выводит то же самое:

```go
x := []int{1,2,3}
y := []int{4,5,6}
x = append(x, y...)
fmt.Println(x)
```

Без `...` код не скомпилируется из-за несовпадения types: `y` не имеет type `int`.

## Initialization {#initialization}

Хотя внешне initialization в Go не сильно отличается от C или C++, в Go она мощнее. Сложные structures можно строить во время initialization, а вопросы ordering между initialized objects — даже из разных packages — обрабатываются корректно.

### Constants {#constants}

Constants в Go действительно constant. Они создаются compile time, даже если объявлены local в functions, и могут быть только numbers, characters — runes, — strings или booleans. Из-за compile-time restriction expressions, задающие constants, должны быть constant expressions, вычисляемыми compiler. Например, `1<<3` — constant expression, а `math.Sin(math.Pi/4)` — нет, потому что call `math.Sin` должен выполняться runtime.

В Go enumerated constants создаются через enumerator `iota`. Поскольку `iota` может быть частью expression, а expressions могут неявно повторяться, легко строить сложные sets values:

```go
// Copyright 2009 The Go Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package main

import "fmt"

type ByteSize float64

const (
	_           = iota // ignore first value by assigning to blank identifier
	KB ByteSize = 1 << (10 * iota)
	MB
	GB
	TB
	PB
	EB
	ZB
	YB
)
```

Возможность прикрепить method вроде `String` к любому user-defined type позволяет arbitrary values автоматически форматировать себя при printing. Хотя чаще это применяется к structs, technique полезна и для scalar types, например floating-point type `ByteSize`:

```go
func (b ByteSize) String() string {
	switch {
	case b >= YB:
		return fmt.Sprintf("%.2fYB", b/YB)
	case b >= ZB:
		return fmt.Sprintf("%.2fZB", b/ZB)
	case b >= EB:
		return fmt.Sprintf("%.2fEB", b/EB)
	case b >= PB:
		return fmt.Sprintf("%.2fPB", b/PB)
	case b >= TB:
		return fmt.Sprintf("%.2fTB", b/TB)
	case b >= GB:
		return fmt.Sprintf("%.2fGB", b/GB)
	case b >= MB:
		return fmt.Sprintf("%.2fMB", b/MB)
	case b >= KB:
		return fmt.Sprintf("%.2fKB", b/KB)
	}
	return fmt.Sprintf("%.2fB", b)
}
```

Expression `YB` печатается как `1.00YB`, а `ByteSize(1e13)` — как `9.09TB`.

Использование `Sprintf` для implementation `ByteSize.String` безопасно и не приводит к бесконечной recursion не из-за conversion, а потому что `Sprintf` вызывается с `%f`, который не является string format: `Sprintf` вызывает method `String` только когда ему нужна string, а `%f` требует floating-point value.

### Variables {#variables}

Variables можно инициализировать так же, как constants, но initializer может быть general expression, вычисляемым runtime:

```go
var (
    home   = os.Getenv("HOME")
    user   = os.Getenv("USER")
    gopath = os.Getenv("GOPATH")
)
```

### Function `init` {#init}

Наконец, каждый source file может определить собственную niladic function `init` для настройки требуемого state. На самом деле в одном file может быть несколько `init` functions.

И «наконец» здесь буквально означает последнее: `init` вызывается после того, как все variable declarations package вычислили свои initializers, а они вычисляются только после initialization всех imported packages.

Помимо initialization, которую нельзя выразить declarations, распространённое применение `init` — проверка или восстановление корректности program state перед началом реального execution.

```go
func init() {
    if user == "" {
        log.Fatal("$USER not set")
    }
    if home == "" {
        home = "/home/" + user
    }
    if gopath == "" {
        gopath = home + "/go"
    }
    // gopath may be overridden by --gopath flag on command line.
    flag.StringVar(&gopath, "gopath", gopath, "override default GOPATH")
}
```

## Methods {#methods}

### Pointers против values {#pointers_vs_values}

Как мы видели на `ByteSize`, methods можно определять для любого named type, кроме pointer или interface; receiver не обязан быть struct.

В разделе о slices выше была написана function `Append`. Её можно определить как method slices. Для этого сначала объявим named type, к которому можно привязать method, затем сделаем receiver method value этого type:

```go
type ByteSlice []byte

func (slice ByteSlice) Append(data []byte) []byte {
    // Body exactly the same as the Append function defined above.
}
```

По-прежнему приходится возвращать updated slice. Эту неуклюжесть можно устранить, изменив method так, чтобы receiver был *pointer* на `ByteSlice`; тогда method сможет перезаписать slice caller:

```go
func (p *ByteSlice) Append(data []byte) {
    slice := *p
    // Body as above, without the return.
    *p = slice
}
```

Можно сделать ещё лучше. Если изменить function так, чтобы она выглядела как standard method `Write`:

```go
func (p *ByteSlice) Write(data []byte) (n int, err error) {
    slice := *p
    // Again as above.
    *p = slice
    return len(data), nil
}
```

тогда type `*ByteSlice` удовлетворяет standard interface `io.Writer`, что удобно. Например, в него можно печатать:

```go
var b ByteSlice
fmt.Fprintf(&b, "This hour has %d days\n", 7)
```

Мы передаём address `ByteSlice`, потому что только `*ByteSlice` удовлетворяет `io.Writer`. Правило pointers vs. values для receivers таково: value methods можно вызывать и на pointers, и на values, а pointer methods — только на pointers.

Причина в том, что pointer methods могут изменять receiver. Их вызов на value заставил бы method получить copy value, поэтому изменения были бы потеряны. Язык запрещает эту ошибку.

Есть удобное исключение. Если value addressable, язык обрабатывает типичный случай вызова pointer method на value, автоматически вставляя address operator. В примере variable `b` addressable, поэтому можно вызвать `b.Write`; compiler перепишет это как `(&b).Write`.

К слову, идея `Write` на byte slice лежит в основе implementation `bytes.Buffer`.

## Interfaces и другие types {#interfaces_and_types}

### Interfaces {#interfaces}

Interfaces в Go позволяют задавать behavior object: если нечто умеет делать *это*, его можно использовать *здесь*. Несколько простых examples уже встречались: custom printers можно реализовать method `String`, а `Fprintf` может выдавать output во всё, что имеет method `Write`.

Interfaces с одним или двумя methods распространены в Go и обычно получают name, производное от method, например `io.Writer` для объекта, реализующего `Write`.

Type может реализовывать несколько interfaces. Например, collection может сортироваться routines package `sort`, если реализует `sort.Interface`, содержащий `Len()`, `Less(i, j int) bool` и `Swap(i, j int)`, и одновременно иметь custom formatter. В следующем искусственном example `Sequence` удовлетворяет обоим:

```go
// Copyright 2009 The Go Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package main

import (
	"fmt"
	"sort"
)

func main() {
	seq := Sequence{6, 2, -1, 44, 16}
	sort.Sort(seq)
	fmt.Println(seq)
}

type Sequence []int

// Methods required by sort.Interface.
func (s Sequence) Len() int {
	return len(s)
}
func (s Sequence) Less(i, j int) bool {
	return s[i] < s[j]
}
func (s Sequence) Swap(i, j int) {
	s[i], s[j] = s[j], s[i]
}

// Copy returns a copy of the Sequence.
func (s Sequence) Copy() Sequence {
	copy := make(Sequence, 0, len(s))
	return append(copy, s...)
}

// Method for printing - sorts the elements before printing.
func (s Sequence) String() string {
	s = s.Copy() // Make a copy; don't overwrite argument.
	sort.Sort(s)
	str := "["
	for i, elem := range s { // Loop is O(N²); will fix that in next example.
		if i > 0 {
			str += " "
		}
		str += fmt.Sprint(elem)
	}
	return str + "]"
}
```

### Conversions {#conversions}

Method `String` type `Sequence` заново выполняет работу, которую `Sprint` уже умеет делать для slices. Кроме того, его complexity O(N²), что плохо. Можно переиспользовать готовую работу — и ускорить код — если перед `Sprint` преобразовать `Sequence` в обычный `[]int`:

```go
func (s Sequence) String() string {
    s = s.Copy()
    sort.Sort(s)
    return fmt.Sprint([]int(s))
}
```

Этот method — ещё один пример technique безопасного вызова `Sprintf` из `String`. Поскольку два types — `Sequence` и `[]int` — одинаковы, если игнорировать type name, conversion между ними допустим. Оно не создаёт новое value, а лишь временно заставляет существующее value рассматриваться как другой type. Есть и другие legal conversions, например integer → floating point, которые создают новое value.

Idiomatic для Go — преобразовывать type expression, чтобы получить доступ к другому set methods. Например, можно использовать существующий type `sort.IntSlice`, сократив весь example до:

```go
type Sequence []int

// Method for printing - sorts the elements before printing
func (s Sequence) String() string {
    s = s.Copy()
    sort.IntSlice(s).Sort()
    return fmt.Sprint([]int(s))
}
```

Теперь вместо того, чтобы `Sequence` реализовывал несколько interfaces — sorting и printing, — используется возможность одного data item преобразовываться в несколько types (`Sequence`, `sort.IntSlice`, `[]int`), каждый из которых выполняет часть задачи. На практике это более необычно, но может быть эффективно.

### Interface conversions и type assertions {#interface_conversions}

[Type switches](#type_switch) являются формой conversion: они принимают interface и в каждом case в некотором смысле преобразуют его в type этого case.

Вот упрощённая version того, как code под `fmt.Printf` превращает value в string через type switch. Если value уже string, нужен фактический string внутри interface; если у него есть method `String`, нужен result method:

```go
type Stringer interface {
    String() string
}

var value interface{} // Value provided by caller.
switch str := value.(type) {
case string:
    return str
case Stringer:
    return str.String()
}
```

Первый case находит concrete value; второй преобразует interface в другой interface. Смешивать types таким образом совершенно нормально.

А если нас интересует только один type? Если известно, что value содержит `string`, и его просто нужно извлечь? Type switch с одним case сработал бы, но можно использовать *type assertion*. Type assertion принимает interface value и извлекает из него value явно указанного type. Syntax заимствован у clause, открывающего type switch, но вместо keyword `type` указывается concrete type:

```text
value.(typeName)
```

Result — новое value со static type `typeName`. Этот type должен быть либо concrete type внутри interface, либо вторым interface type, к которому value можно преобразовать.

Чтобы извлечь известный `string`:

```go
str := value.(string)
```

Но если value на самом деле не содержит string, program завершится runtime error. Для безопасной проверки используйте idiom «comma, ok»:

```go
str, ok := value.(string)
if ok {
    fmt.Printf("string value is: %q\n", str)
} else {
    fmt.Printf("value is not a string\n")
}
```

Если type assertion неудачен, `str` всё равно существует и имеет type string, но получает zero value — empty string.

Для иллюстрации возможностей ниже `if`-`else`, эквивалентный type switch в начале раздела:

```go
if str, ok := value.(string); ok {
    return str
} else if str, ok := value.(Stringer); ok {
    return str.String()
}
```

### Generality {#generality}

Если type существует только ради implementation interface и никогда не будет иметь exported methods помимо interface, нет необходимости экспортировать сам type. Export только interface ясно показывает, что у value нет интересного behavior помимо описанного interface. Это также позволяет не повторять documentation для каждого instance общего method.

В таких случаях constructor должен возвращать interface value, а не implementing type. Например, в hash libraries `crc32.NewIEEE` и `adler32.New` возвращают interface type `hash.Hash32`. Замена CRC-32 algorithm на Adler-32 требует изменить только constructor call; остальной код не затрагивается сменой algorithm.

Похожий подход позволяет отделить streaming cipher algorithms в различных `crypto` packages от block ciphers, которые они объединяют. Interface `Block` в package `crypto/cipher` задаёт behavior block cipher, шифрующего один data block. Затем, по аналогии с package `bufio`, cipher packages, реализующие этот interface, можно использовать для построения streaming ciphers, представленных interface `Stream`, не зная деталей block encryption.

Interfaces `crypto/cipher` выглядят так:

```go
type Block interface {
    BlockSize() int
    Encrypt(dst, src []byte)
    Decrypt(dst, src []byte)
}

type Stream interface {
    XORKeyStream(dst, src []byte)
}
```

Definition counter mode (CTR) stream, превращающего block cipher в streaming cipher, выглядит так; детали block cipher абстрагированы:

```go
// NewCTR returns a Stream that encrypts/decrypts using the given Block in
// counter mode. The length of iv must be the same as the Block's block size.
func NewCTR(block Block, iv []byte) Stream
```

`NewCTR` применим не к одному конкретному encryption algorithm и data source, а к любой implementation `Block` и любому `Stream`. Поскольку constructors возвращают interface values, замена CTR encryption другим mode — локальное изменение. Constructor calls придётся изменить, но surrounding code работает с result только как со `Stream` и разницы не заметит.

### Interfaces и methods {#interface_methods}

Поскольку почти к чему угодно можно привязать methods, почти что угодно может удовлетворять interface. Наглядный example находится в package `http`, определяющем interface `Handler`. Любой object, реализующий `Handler`, может обслуживать HTTP requests:

```go
type Handler interface {
    ServeHTTP(ResponseWriter, *Request)
}
```

`ResponseWriter` сам является interface, предоставляющим methods, необходимые для возврата response client. Среди них standard method `Write`, поэтому `http.ResponseWriter` можно использовать везде, где можно `io.Writer`. `Request` — struct с parsed representation request от client.

Для краткости проигнорируем POST и предположим, что HTTP requests всегда GET; это не влияет на setup handlers. Вот тривиальная implementation handler, считающая число visits page:

```go
// Simple counter server.
type Counter struct {
    n int
}

func (ctr *Counter) ServeHTTP(w http.ResponseWriter, req *http.Request) {
    ctr.n++
    fmt.Fprintf(w, "counter = %d\n", ctr.n)
}
```

В соответствии с нашей темой обратите внимание, что `Fprintf` может печатать в `http.ResponseWriter`. В real server доступ к `ctr.n` пришлось бы защитить от concurrent access. Рекомендации см. в packages `sync` и `atomic`.

Подключение server к node URL tree:

```go
import "net/http"
...
ctr := new(Counter)
http.Handle("/counter", ctr)
```

Но зачем делать `Counter` struct? Достаточно integer. Receiver должен быть pointer, чтобы increment был виден caller:

```go
// Simpler counter server.
type Counter int

func (ctr *Counter) ServeHTTP(w http.ResponseWriter, req *http.Request) {
    *ctr++
    fmt.Fprintf(w, "counter = %d\n", *ctr)
}
```

А если program имеет внутреннее state, которое нужно уведомлять о visit page? Свяжите channel с web page:

```go
// A channel that sends a notification on each visit.
// (Probably want the channel to be buffered.)
type Chan chan *http.Request

func (ch Chan) ServeHTTP(w http.ResponseWriter, req *http.Request) {
    ch <- req
    fmt.Fprint(w, "notification sent")
}
```

Наконец, предположим, что на `/args` нужно показать arguments, с которыми server binary был запущен. Function для printing arguments написать легко:

```go
func ArgServer() {
    fmt.Println(os.Args)
}
```

Как превратить её в HTTP server? Можно было бы сделать `ArgServer` method некоторого type, value которого игнорируется, но есть более чистый способ. Поскольку method можно определить для любого type, кроме pointers и interfaces, method можно определить для function.

Package `http` содержит такой code:

```go
// The HandlerFunc type is an adapter to allow the use of
// ordinary functions as HTTP handlers.  If f is a function
// with the appropriate signature, HandlerFunc(f) is a
// Handler object that calls f.
type HandlerFunc func(ResponseWriter, *Request)

// ServeHTTP calls f(w, req).
func (f HandlerFunc) ServeHTTP(w ResponseWriter, req *Request) {
    f(w, req)
}
```

`HandlerFunc` — type с method `ServeHTTP`, поэтому values этого type могут обслуживать HTTP requests. Посмотрите на implementation: receiver — function `f`, а method вызывает `f`. Это может казаться странным, но не сильно отличается от receiver-channel, method которого отправляет value в channel.

Чтобы превратить `ArgServer` в HTTP server, сначала изменим её signature:

```go
// Argument server.
func ArgServer(w http.ResponseWriter, req *http.Request) {
    fmt.Fprintln(w, os.Args)
}
```

Теперь `ArgServer` имеет ту же signature, что и `HandlerFunc`, поэтому её можно преобразовать к этому type и получить доступ к methods — так же, как `Sequence` преобразовывался в `IntSlice` для доступа к `IntSlice.Sort`.

Setup code краток:

```go
http.Handle("/args", http.HandlerFunc(ArgServer))
```

Когда кто-то посещает `/args`, handler, установленный для этой page, имеет value `ArgServer` и type `HandlerFunc`. HTTP server вызовет method `ServeHTTP` этого type с `ArgServer` как receiver, который, в свою очередь, вызовет `ArgServer` через `f(w, req)` внутри `HandlerFunc.ServeHTTP`. Затем arguments будут отображены.

В этом разделе HTTP server был построен из struct, integer, channel и function — всё потому, что interfaces представляют собой всего лишь sets methods, которые можно определить почти для любого type.

## Blank identifier {#blank}

Мы уже несколько раз упоминали blank identifier — в контексте [`for range`](#for) loops и [maps](#maps). Blank identifier можно присвоить или объявить с любым value любого type; value безвредно отбрасывается. Это немного похоже на запись в Unix file `/dev/null`: write-only value-placeholder для места, где variable синтаксически нужна, но actual value неважно. Его применения не ограничиваются уже рассмотренными.

### Blank identifier в multiple assignment {#blank_assign}

Использование blank identifier в `for range` — частный случай общей ситуации: multiple assignment.

Если assignment требует нескольких values слева, но одно из них program не использует, blank identifier в left-hand side устраняет необходимость создавать dummy variable и ясно показывает, что value отбрасывается. Например, когда function возвращает value и error, но важен только error:

```go
if _, err := os.Stat(path); os.IsNotExist(err) {
    fmt.Printf("%s does not exist\n", path)
}
```

Иногда встречается code, который, наоборот, отбрасывает error value, чтобы игнорировать ошибку; это ужасная практика. Всегда проверяйте error returns: они возвращаются не просто так.

```go
// Bad! This code will crash if path does not exist.
fi, _ := os.Stat(path)
if fi.IsDir() {
    fmt.Printf("%s is a directory\n", path)
}
```

### Неиспользуемые imports и variables {#blank_unused}

Import package или declaration variable без использования является ошибкой. Unused imports раздувают program и замедляют compilation, а initialized, но unused variable — как минимум лишнее вычисление и, возможно, признак более крупной bug.

Во время активной разработки unused imports и variables, однако, возникают часто, и раздражает удалять их только ради compilation, чтобы чуть позже они снова понадобились. Blank identifier даёт workaround.

Следующая недописанная program содержит два unused imports (`fmt`, `io`) и unused variable `fd`, поэтому не компилируется, хотя хотелось бы проверить корректность уже написанного code:

```go
package main

import (
	"fmt"
	"io"
	"log"
	"os"
)

func main() {
	fd, err := os.Open("test.go")
	if err != nil {
		log.Fatal(err)
	}
	// TODO: use fd.
}
```

Чтобы убрать complaints об unused imports, сослитесь через blank identifier на symbol из imported package. Аналогично assignment unused variable `fd` blank identifier убирает unused-variable error. Эта version компилируется:

```go
package main

import (
	"fmt"
	"io"
	"log"
	"os"
)

var _ = fmt.Printf // For debugging; delete when done.
var _ io.Reader    // For debugging; delete when done.

func main() {
	fd, err := os.Open("test.go")
	if err != nil {
		log.Fatal(err)
	}
	// TODO: use fd.
	_ = fd
}
```

По convention global declarations, подавляющие import errors, должны идти сразу после imports и содержать comments — чтобы их легко было найти и чтобы они напоминали позднее очистить код.

### Import ради side effect {#blank_import}

Unused import вроде `fmt` или `io` из предыдущего example в конечном итоге должен быть использован или удалён: blank assignments показывают work in progress. Но иногда полезно импортировать package только ради side effects без explicit use.

Например, во время `init` package [`net/http/pprof`](https://go.dev/pkg/net/http/pprof/) регистрирует HTTP handlers, предоставляющие debugging information. У него есть exported API, но большинству clients нужны только registration handlers и доступ к data через web page.

Чтобы импортировать package только ради side effects, переименуйте package в blank identifier:

```go
import _ "net/http/pprof"
```

Такая форма import ясно показывает, что package импортирован ради side effects, потому что никакого другого use быть не может: в этом file package не имеет имени. Если бы имя было и не использовалось, compiler отклонил бы program.

### Проверки interfaces {#blank_implements}

Как было показано в разделе [interfaces](#interfaces_and_types), type не обязан явно объявлять implementation interface. Он реализует interface просто через implementation его methods. На практике большинство interface conversions статичны и проверяются compile time. Например, передача `*os.File` в function, ожидающую `io.Reader`, не скомпилируется, если `*os.File` не реализует `io.Reader`.

Но некоторые interface checks выполняются runtime. Один из examples — package [`encoding/json`](https://go.dev/pkg/encoding/json/), определяющий interface [`Marshaler`](https://go.dev/pkg/encoding/json/#Marshaler). Когда JSON encoder получает value, реализующее interface, encoder вызывает его marshaling method вместо standard conversion. Проверка выполняется runtime через type assertion:

```go
m, ok := val.(json.Marshaler)
```

Если нужно только выяснить, реализует ли type interface, не используя сам interface — например, как часть error check, — можно blank identifier отбросить asserted value:

```go
if _, ok := val.(json.Marshaler); ok {
    fmt.Printf("value %v of type %T implements json.Marshaler\n", val, val)
}
```

Иногда внутри package, реализующего type, необходимо гарантировать, что он действительно удовлетворяет interface. Если type — например [`json.RawMessage`](https://go.dev/pkg/encoding/json/#RawMessage) — требует custom JSON representation, он должен реализовать `json.Marshaler`, но в коде может не быть static conversions, автоматически заставляющих compiler это проверить. Если type случайно перестанет удовлетворять interface, JSON encoder всё равно будет работать, но custom implementation использовать не станет.

Чтобы гарантировать correctness implementation, в package можно использовать global declaration с blank identifier:

```go
var _ json.Marshaler = (*RawMessage)(nil)
```

В этом declaration assignment, включающий conversion `*RawMessage` к `Marshaler`, требует, чтобы `*RawMessage` реализовывал `Marshaler`; compiler проверит это compile time. Если interface `json.Marshaler` изменится, package перестанет компилироваться и потребует update.

Появление blank identifier в такой construct показывает, что declaration существует только для type checking, а не для создания variable. Однако не делайте это для каждого type, удовлетворяющего interface. По convention такие declarations используют лишь там, где в коде уже нет static conversions — это редкая ситуация.

## Embedding {#embedding}

Go не предоставляет типичную type-driven концепцию subclassing, но позволяет «заимствовать» части implementation через *embedding* types внутри struct или interface.

Interface embedding очень прост. Ранее упоминались interfaces `io.Reader` и `io.Writer`; их definitions:

```go
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}
```

Package `io` экспортирует и другие interfaces, задающие objects, умеющие выполнять несколько таких methods. Например, `io.ReadWriter` содержит и `Read`, и `Write`. Можно перечислить оба methods явно, но проще и выразительнее embed два interfaces в новый:

```go
// ReadWriter is the interface that combines the Reader and Writer interfaces.
type ReadWriter interface {
    Reader
    Writer
}
```

Это означает именно то, что кажется: `ReadWriter` умеет всё, что `Reader`, *и* всё, что `Writer`; это union embedded interfaces. В interfaces можно embed только interfaces.

Та же основная идея применяется к structs, но имеет более далеко идущие consequences. Package `bufio` имеет два struct types — `bufio.Reader` и `bufio.Writer`, — каждый из которых реализует аналогичный interface package `io`. `bufio` также реализует buffered reader/writer, объединяя reader и writer в одну struct через embedding: types перечисляются внутри struct без field names.

```go
// ReadWriter stores pointers to a Reader and a Writer.
// It implements io.ReadWriter.
type ReadWriter struct {
    *Reader  // *bufio.Reader
    *Writer  // *bufio.Writer
}
```

Embedded elements — pointers на structs — должны быть инициализированы valid structs перед использованием. `ReadWriter` можно было бы написать так:

```go
type ReadWriter struct {
    reader *Reader
    writer *Writer
}
```

но тогда для promotion methods fields и удовлетворения `io` interfaces потребовались бы forwarding methods:

```go
func (rw *ReadWriter) Read(p []byte) (n int, err error) {
    return rw.reader.Read(p)
}
```

При direct embedding structs этот bookkeeping исчезает. Methods embedded types предоставляются автоматически, поэтому `bufio.ReadWriter` не только имеет methods `bufio.Reader` и `bufio.Writer`, но и удовлетворяет всем трём interfaces: `io.Reader`, `io.Writer`, `io.ReadWriter`.

Embedding существенно отличается от subclassing. Когда type embed'ится, его methods становятся methods outer type, но receiver при их вызове остаётся inner type, а не outer. В нашем example вызов `Read` у `bufio.ReadWriter` имеет точно такой же effect, как явный forwarding method выше; receiver — field `reader` внутри `ReadWriter`, а не сам `ReadWriter`.

Embedding также может быть просто удобством. Example embedded field вместе с regular named field:

```go
type Job struct {
    Command string
    *log.Logger
}
```

Type `Job` теперь имеет `Print`, `Printf`, `Println` и другие methods `*log.Logger`. Можно было бы дать `Logger` field name, но это не требуется. После initialization можно логировать через `Job`:

```go
job.Println("starting now...")
```

`Logger` — обычный field `Job`, поэтому его можно инициализировать стандартным способом в constructor:

```go
func NewJob(command string, logger *log.Logger) *Job {
    return &Job{command, logger}
}
```

или composite literal:

```go
job := &Job{command, log.New(os.Stderr, "Job: ", log.Ldate)}
```

Если нужно напрямую обратиться к embedded field, type name field без package qualifier служит field name, как в method `Read` нашей struct `ReadWriter`. Для доступа к `*log.Logger` variable `job` используется `job.Logger`, что полезно, например, для refinement methods `Logger`:

```go
func (job *Job) Printf(format string, args ...interface{}) {
    job.Logger.Printf("%q: %s", job.Command, fmt.Sprintf(format, args...))
}
```

Embedding types создаёт проблему name conflicts, но rules просты. Во-первых, field или method `X` скрывает любой другой `X`, находящийся глубже в nesting type. Если `log.Logger` содержал бы field или method `Command`, field `Command` в `Job` доминировал бы над ним.

Во-вторых, если одинаковое имя встречается на одном nesting level, обычно это error. Например, нельзя embed `log.Logger`, если struct `Job` содержит другой field или method `Logger`. Однако если duplicate name вообще не упоминается program за пределами type definition, это допустимо.

Эта оговорка даёт некоторую защиту от изменений types, embed'нутых извне: добавление field, конфликтующего с field другого subtype, не создаёт проблему, пока ни один из конфликтующих fields не используется.

## Concurrency {#concurrency}

### Делитесь через communication {#sharing}

Concurrent programming — огромная тема, и здесь есть место лишь для некоторых Go-specific моментов.

Во многих environments concurrent programming усложняется тонкостями правильного доступа к shared variables. Go поощряет другой подход: shared values передаются через channels и фактически никогда не shared активно разными threads execution. В каждый момент доступ к value имеет только одна goroutine. Data races конструктивно исключаются.

Для закрепления такого мышления используется slogan:

> Не общайтесь, разделяя память; вместо этого разделяйте память, общаясь.

Этот подход можно довести слишком далеко. Например, reference count может быть лучше реализован mutex вокруг integer variable. Но как high-level approach использование channels для контроля доступа упрощает написание ясных, корректных programs.

Один способ понять эту model — представить обычную single-threaded program на одном CPU. Ей synchronization primitives не нужны. Теперь запустим второй такой instance — ему они тоже не нужны. Пусть эти два instance общаются; если сама communication является synchronizer, дополнительные synchronization mechanisms всё ещё не нужны. Unix pipelines, например, идеально соответствуют этой model.

Хотя подход Go к concurrency происходит от Communicating Sequential Processes (CSP) Hoare, его можно также рассматривать как type-safe generalization Unix pipes.

### Goroutines {#goroutines}

Они называются *goroutines*, потому что существующие термины — threads, coroutines, processes и другие — несут неточные connotations. Model goroutine проста: это function, выполняющаяся concurrently с другими goroutines в том же address space. Она lightweight и стоит лишь немного больше, чем allocation stack space. Stacks начинают маленькими, поэтому дёшевы, и растут через allocation — и освобождение — heap storage по необходимости.

Goroutines multiplexed на несколько OS threads, поэтому если одна блокируется, например ожидая I/O, другие продолжают выполняться. Их design скрывает многие сложности создания и управления threads.

Поставьте keyword `go` перед function или method call, чтобы выполнить call в новой goroutine. Когда call завершится, goroutine молча exits. Effect похож на notation `&` Unix shell для запуска command в background.

```go
go list.Sort()  // run list.Sort concurrently; don't wait for it.
```

Function literal удобен в goroutine invocation:

```go
func Announce(message string, delay time.Duration) {
    go func() {
        time.Sleep(delay)
        fmt.Println(message)
    }()  // Note the parentheses - must call the function.
}
```

В Go function literals — closures: implementation гарантирует, что variables, на которые ссылается function, продолжают существовать, пока active.

Эти examples не слишком практичны, потому что functions никак не сигнализируют о завершении. Для этого нужны channels.

### Channels {#channels}

Как и maps, channels выделяются через `make`, а полученное value действует как reference на underlying data structure. Если указан optional integer parameter, он задаёт buffer size channel. Default — zero, то есть unbuffered/synchronous channel.

```go
ci := make(chan int)            // unbuffered channel of integers
cj := make(chan int, 0)         // unbuffered channel of integers
cs := make(chan *os.File, 100)  // buffered channel of pointers to Files
```

Unbuffered channels объединяют communication — exchange value — с synchronization, гарантируя, что два calculations/goroutines находятся в известном состоянии.

Channels поддерживают множество удобных idioms. Начнём с одного. В предыдущем разделе sort запускался в background. Channel позволяет launching goroutine дождаться завершения sort:

```go
c := make(chan int)  // Allocate a channel.
// Start the sort in a goroutine; when it completes, signal on the channel.
go func() {
    list.Sort()
    c <- 1  // Send a signal; value does not matter.
}()
doSomethingForAWhile()
<-c   // Wait for sort to finish; discard sent value.
```

Receivers всегда block, пока нет data для receive. Если channel unbuffered, sender blocks, пока receiver не получил value. Если channel buffered, sender blocks только до копирования value в buffer; если buffer full, это означает ожидание, пока receiver не извлечёт value.

Buffered channel можно использовать как semaphore, например для ограничения throughput. В следующем example incoming requests передаются `handle`, которая отправляет value в channel, обрабатывает request, затем получает value из channel, освобождая «semaphore» для следующего consumer. Capacity buffer ограничивает число simultaneous calls `process`.

```go
var sem = make(chan int, MaxOutstanding)

func handle(r *Request) {
    sem <- 1    // Wait for active queue to drain.
    process(r)  // May take a long time.
    <-sem       // Done; enable next request to run.
}

func Serve(queue chan *Request) {
    for {
        req := <-queue
        go handle(req)  // Don't wait for handle to finish.
    }
}
```

Когда `MaxOutstanding` handlers уже выполняют `process`, новые будут блокироваться при попытке send в заполненный channel buffer, пока один из existing handlers не завершится и не выполнит receive из buffer.

Но у этого design есть проблема: `Serve` создаёт новую goroutine для каждого incoming request, хотя одновременно могут выполняться только `MaxOutstanding`. Если requests приходят слишком быстро, program может потреблять неограниченные resources. Это можно исправить, заставив `Serve` ограничивать создание goroutines:

```go
func Serve(queue chan *Request) {
    for req := range queue {
        sem <- 1
        go func() {
            process(req)
            <-sem
        }()
    }
}
```

Обратите внимание: в версиях Go до 1.22 этот код содержит bug — loop variable shared между всеми goroutines. Подробности см. в [Go wiki](https://go.dev/wiki/LoopvarExperiment).

Другой resource-friendly approach — запустить фиксированное число `handle` goroutines, каждая из которых читает request channel. Число goroutines ограничит simultaneous calls `process`. Эта `Serve` также принимает channel, по которому получает signal exit; после запуска goroutines она blocks на receive из этого channel.

```go
func handle(queue chan *Request) {
    for r := range queue {
        process(r)
    }
}

func Serve(clientRequests chan *Request, quit chan bool) {
    // Start handlers
    for i := 0; i < MaxOutstanding; i++ {
        go handle(clientRequests)
    }
    <-quit  // Wait to be told to exit.
}
```

### Channels of channels {#chan_of_chan}

Одно из важнейших свойств Go: channel — first-class value, который можно выделять и передавать, как любое другое value. Частое применение — safe parallel demultiplexing.

В предыдущем section `handle` был idealized handler request, но type request не определялся. Если этот type включает channel для reply, каждый client может предоставлять собственный path для answer. Схематическое definition `Request`:

```go
type Request struct {
    args        []int
    f           func([]int) int
    resultChan  chan int
}
```

Client предоставляет function и её arguments, а также channel внутри request object для receive answer:

```go
func sum(a []int) (s int) {
    for _, v := range a {
        s += v
    }
    return
}

request := &Request{[]int{3, 4, 5}, sum, make(chan int)}
// Send request
clientRequests <- request
// Wait for response.
fmt.Printf("answer: %d\n", <-request.resultChan)
```

На server side меняется только handler function:

```go
func handle(queue chan *Request) {
    for req := range queue {
        req.resultChan <- req.f(req.args)
    }
}
```

Очевидно, до realistic system ещё далеко, но этот code уже является framework для rate-limited, parallel, non-blocking RPC system — и ни одного mutex.

### Parallelization {#parallel}

Ещё одно применение этих идей — parallelize calculation по нескольким CPU cores. Если computation можно разбить на независимые части, их можно выполнять параллельно, используя channel для signaling завершения каждой части.

Пусть есть дорогая operation над vector items, и result на каждом item независим:

```go
type Vector []float64

// Apply the operation to v[i], v[i+1] ... up to v[n-1].
func (v Vector) DoSome(i, n int, u Vector, c chan int) {
    for ; i < n; i++ {
        v[i] += u.Op(v[i])
    }
    c <- 1    // signal that this piece is done
}
```

Запустим parts независимо в loop, по одной на CPU. Они могут завершаться в любом order — это неважно; после launch всех goroutines достаточно посчитать completion signals, drain'я channel:

```go
const numCPU = 4 // number of CPU cores

func (v Vector) DoAll(u Vector) {
    c := make(chan int, numCPU)  // Buffering optional but sensible.
    for i := 0; i < numCPU; i++ {
        go v.DoSome(i*len(v)/numCPU, (i+1)*len(v)/numCPU, u, c)
    }
    // Drain the channel.
    for i := 0; i < numCPU; i++ {
        <-c    // wait for one task to complete
    }
    // All done.
}
```

Вместо constant `numCPU` можно спросить runtime о подходящем value. Function [`runtime.NumCPU`](https://go.dev/pkg/runtime#NumCPU) возвращает число hardware CPU cores:

```go
var numCPU = runtime.NumCPU()
```

Также существует [`runtime.GOMAXPROCS`](https://go.dev/pkg/runtime#GOMAXPROCS), сообщающая — или устанавливающая — user-specified число cores, которые Go program может использовать одновременно. Default равен `runtime.NumCPU`, но его можно override одноимённой shell environment variable или вызовом function с positive number. Call с zero только запрашивает value. Поэтому, чтобы учитывать user resource request:

```go
var numCPU = runtime.GOMAXPROCS(0)
```

Не путайте concurrency — structuring program как independently executing components — и parallelism — simultaneous execution calculations ради эффективности на нескольких CPU. Хотя concurrency features Go позволяют удобно структурировать некоторые задачи как parallel computations, Go является concurrent language, а не parallel language, и не все parallelization problems соответствуют model Go. Различие обсуждается в [этом докладе](https://go.dev/blog/concurrency-is-not-parallelism).

### Leaky buffer {#leaky_buffer}

Tools concurrent programming могут упрощать выражение даже non-concurrent ideas. Следующий example абстрагирован от RPC package. Client goroutine в loop получает data из некоторого source, возможно network. Чтобы не выделять и освобождать buffers постоянно, она держит free list, представленную buffered channel. Если channel empty, выделяется новый buffer. Готовый message buffer отправляется server через `serverChan`.

```go
var freeList = make(chan *Buffer, 100)
var serverChan = make(chan *Buffer)

func client() {
    for {
        var b *Buffer
        // Grab a buffer if available; allocate if not.
        select {
        case b = <-freeList:
            // Got one; nothing more to do.
        default:
            // None free, so allocate a new one.
            b = new(Buffer)
        }
        load(b)              // Read next message from the net.
        serverChan <- b      // Send to server.
    }
}
```

Server loop получает каждое message, обрабатывает его и возвращает buffer в free list:

```go
func server() {
    for {
        b := <-serverChan    // Wait for work.
        process(b)
        // Reuse buffer if there's room.
        select {
        case freeList <- b:
            // Buffer on free list; nothing more to do.
        default:
            // Free list full, just carry on.
        }
    }
}
```

Client пытается взять buffer из `freeList`; если ничего нет, выделяет новый. Send server в `freeList` помещает `b` обратно, если list не full; иначе buffer просто отбрасывается и позднее reclaimed garbage collector. Clauses `default` в `select` выполняются, когда ни один другой case не ready, поэтому `select` никогда не blocks.

Эта implementation создаёт leaky-bucket free list в нескольких строках, полагаясь на buffered channel и garbage collector для bookkeeping.

## Errors {#errors}

Library routines часто должны возвращать caller некоторый признак error. Как говорилось ранее, multivalue return Go позволяет легко вернуть детальное error description вместе с normal return value. Хороший style — использовать это для подробной error information. Например, `os.Open` при failure возвращает не просто `nil` pointer, но и error value, описывающее причину.

По convention errors имеют type `error`, простой built-in interface:

```go
type error interface {
    Error() string
}
```

Author library может реализовать этот interface более богатой внутренней model, позволяющей не только увидеть error, но и получить context. Как уже упоминалось, вместе с обычным `*os.File` `os.Open` возвращает error value. Если file открыт успешно, error равен `nil`; иначе содержит `os.PathError`:

```go
// PathError records an error and the operation and
// file path that caused it.
type PathError struct {
    Op string    // "open", "unlink", etc.
    Path string  // The associated file.
    Err error    // Returned by the system call.
}

func (e *PathError) Error() string {
    return e.Op + " " + e.Path + ": " + e.Err.Error()
}
```

`PathError.Error` формирует string вроде:

```text
open /etc/passwx: no such file or directory
```

Такая error, включающая problematic filename, operation и operating-system error, полезна даже если напечатана далеко от call, вызвавшего её; она гораздо информативнее простого «no such file or directory».

Когда возможно, error strings должны указывать origin, например prefix с operation или package, породившим error. В package `image`, например, string representation decoding error для неизвестного format — `image: unknown format`.

Callers, которым важны точные details, могут использовать type switch или type assertion для поиска specific errors и извлечения details. Для `PathError` это может включать анализ internal field `Err` для recoverable failures:

```go
for try := 0; try < 2; try++ {
    file, err = os.Create(filename)
    if err == nil {
        return
    }
    if e, ok := err.(*os.PathError); ok && e.Err == syscall.ENOSPC {
        deleteTempFiles()  // Recover some space.
        continue
    }
    return
}
```

Второй `if` — ещё один [type assertion](#interface_conversions). Если он fails, `ok` false, а `e` nil. Если succeeds, `ok` true: error имеет type `*os.PathError`, и `e` тоже, поэтому его можно исследовать подробнее.

### Panic {#panic}

Обычный способ сообщить caller об error — вернуть `error` как дополнительное return value. Канонический method `Read` — известный пример: он возвращает byte count и `error`. Но что делать, если error unrecoverable и program просто не может продолжаться?

Для этого существует built-in function `panic`, фактически создающая runtime error, останавливающую program — с оговоркой следующего раздела. Function принимает один argument arbitrary type, часто string, который будет напечатан при завершении program. Это также способ показать, что произошло нечто невозможное, например выход из infinite loop.

```go
// A toy implementation of cube root using Newton's method.
func CubeRoot(x float64) float64 {
    z := x/3   // Arbitrary initial value
    for i := 0; i < 1e6; i++ {
        prevz := z
        z -= (z*z*z-x) / (3*z*z)
        if veryClose(z, prevz) {
            return z
        }
    }
    // A million iterations has not converged; something is wrong.
    panic(fmt.Sprintf("CubeRoot(%g) did not converge", x))
}
```

Это лишь example; реальные library functions должны избегать `panic`. Если проблему можно скрыть или обойти, почти всегда лучше позволить program продолжить работу, чем завершить её целиком. Возможное исключение — initialization: если library действительно не может настроиться, panic может быть оправдан.

```go
var user = os.Getenv("USER")

func init() {
    if user == "" {
        panic("no value for $USER")
    }
}
```

### Recover {#recover}

Когда вызывается `panic`, включая implicit panic из-за runtime errors вроде index slice out of bounds или failed type assertion, выполнение current function немедленно прекращается и начинается unwinding stack goroutine с запуском всех deferred functions по пути. Если unwinding достигает вершины stack goroutine, program завершается. Но built-in function `recover` позволяет вернуть control goroutine и возобновить normal execution.

Call `recover` останавливает unwinding и возвращает argument, переданный `panic`. Поскольку при unwinding выполняется только code внутри deferred functions, `recover` полезен только внутри deferred functions.

Одно применение `recover` — завершить failing goroutine внутри server, не убивая другие выполняющиеся goroutines:

```go
func server(workChan <-chan *Work) {
    for work := range workChan {
        go safelyDo(work)
    }
}

func safelyDo(work *Work) {
    defer func() {
        if err := recover(); err != nil {
            log.Println("work failed:", err)
        }
    }()
    do(work)
}
```

Если `do(work)` panics, result будет logged, а goroutine корректно завершится, не затрагивая остальные. Ничего больше в deferred closure делать не требуется; `recover` полностью обрабатывает condition.

Поскольку `recover` всегда возвращает `nil`, если не вызван напрямую из deferred function, deferred code может вызывать library routines, которые сами используют `panic` и `recover`, без failure. Например, deferred function в `safelyDo` может вызвать logging function перед `recover`; logging code выполнится независимо от panicking state.

С recovery pattern function `do` — и всё, что она вызывает — может чисто выйти из плохой ситуации через `panic`. Это можно использовать для упрощения error handling в complex software.

Рассмотрим idealized version package `regexp`, сообщающего parsing errors через `panic` с local error type. Definition `Error`, method `Error` и function `Compile`:

```go
// Error is the type of a parse error; it satisfies the error interface.
type Error string
func (e Error) Error() string {
    return string(e)
}

// error is a method of *Regexp that reports parsing errors by
// panicking with an Error.
func (regexp *Regexp) error(err string) {
    panic(Error(err))
}

// Compile returns a parsed representation of the regular expression.
func Compile(str string) (regexp *Regexp, err error) {
    regexp = new(Regexp)
    // doParse will panic if there is a parse error.
    defer func() {
        if e := recover(); e != nil {
            regexp = nil    // Clear return value.
            err = e.(Error) // Will re-panic if not a parse error.
        }
    }()
    return regexp.doParse(str), nil
}
```

Если `doParse` panics, recovery block установит return value в `nil` — deferred functions могут изменять named return values. Затем assignment `err` проверит через assertion local type `Error`, что проблема действительно была parse error. Если нет, type assertion fails, вызывая runtime error, который продолжит stack unwinding так, как будто recovery не вмешивался.

Эта проверка означает, что при неожиданной проблеме — например index out of bounds — код всё равно завершится failure, несмотря на использование `panic`/`recover` для parse errors.

С такой error handling method `error` — поскольку это method type, нормально и естественно, что его name совпадает с built-in type `error` — позволяет легко сообщать parse errors, не заботясь вручную об unwinding parse stack:

```go
if pos == 0 {
    re.error("'*' illegal at start of expression")
}
```

Каким бы полезным ни был pattern, использовать его следует только внутри package. `Parse` превращает internal `panic` calls в `error` values и не раскрывает panics client. Это хорошее правило.

К слову, idiom re-panic выше изменяет panic value, если происходит actual error. Однако crash report покажет и original, и new failures, поэтому root cause останется виден. Обычно простого re-panic достаточно — речь всё равно о crash. Если же нужно показать только original value, можно написать немного дополнительного code, отфильтровать unexpected problems и re-panic с original error. Это оставляется читателю как упражнение.

## Web server {#web_server}

Завершим полной Go program — web server. Фактически это своего рода web re-server. Google предоставляет service по адресу `chart.apis.google.com`, автоматически форматирующий data в charts и graphs. Interactive использовать его неудобно, потому что data нужно помещать в URL как query.

Program ниже даёт более удобный interface к одному виду data: получив короткий text, она обращается к chart server, чтобы создать QR code — matrix boxes, кодирующую text. Image можно считать camera мобильного телефона и интерпретировать, например, как URL, избавляясь от ввода URL с маленькой phone keyboard.

Полная program:

```go
// Copyright 2009 The Go Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package main

import (
	"flag"
	"html/template"
	"log"
	"net/http"
)

var addr = flag.String("addr", ":1718", "http service address") // Q=17, R=18

var templ = template.Must(template.New("qr").Parse(templateStr))

func main() {
	flag.Parse()
	http.Handle("/", http.HandlerFunc(QR))
	err := http.ListenAndServe(*addr, nil)
	if err != nil {
		log.Fatal("ListenAndServe:", err)
	}
}

func QR(w http.ResponseWriter, req *http.Request) {
	templ.Execute(w, req.FormValue("s"))
}

const templateStr = `
<html>
<head>
<title>QR Link Generator</title>
</head>
<body>
{{if .}}
<img src="http://chart.apis.google.com/chart?chs=300x300&cht=qr&choe=UTF-8&chl={{.}}" />
<br>
{{.}}
<br>
<br>
{{end}}
<form action="/" name=f method="GET">
	<input maxLength=1024 size=70 name=s value="" title="Text to QR Encode">
	<input type=submit value="Show QR" name=qr>
</form>
</body>
</html>
`
```

Части до `main` должны быть понятны. Единственный flag задаёт default HTTP port server. Variable template `templ` — место, где начинается интересное: она строит HTML template, который server будет выполнять для отображения page; подробнее через минуту.

Function `main` parses flags и, используя механизм, описанный выше, связывает function `QR` с root path server. Затем вызывается `http.ListenAndServe`, запускающая server; call blocks, пока server работает.

`QR` лишь получает request с form data и выполняет template на data из form value с name `s`.

Package `html/template` мощный; эта program затрагивает только малую часть его возможностей. По сути он на лету переписывает fragment HTML text, подставляя elements, вычисленные из data items, переданных `templ.Execute`, — здесь это form value.

В template text (`templateStr`) fragments, ограниченные double braces, обозначают template actions. Fragment от `{{if .}}` до `{{end}}` выполняется только если value current data item, называемого `.` — dot, — non-empty. То есть при empty string этот fragment template подавляется.

Два fragment `{{.}}` означают вывести data, переданные template — query string — на web page. HTML template package автоматически выполняет подходящий escaping, чтобы text было безопасно отображать.

Остальная часть template string — обычный HTML, показываемый при загрузке page. Если это объяснение слишком краткое, подробности см. в [documentation package `html/template`](https://go.dev/pkg/html/template/).

Итак, перед нами полезный web server в нескольких строках code плюс немного data-driven HTML text. Go достаточно мощен, чтобы делать много всего малым количеством строк.

<!--
TODO
verifying implementation
type Color uint32

// Check that Color implements image.Color and image.Image
var _ image.Color = Black
var _ image.Image = Black
-->
