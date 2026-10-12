---
title: "Go Fuzzing"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/fuzz/index.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Go Fuzzing

Go поддерживает fuzzing в standard toolchain начиная с Go 1.18. Native Go fuzz tests [поддерживаются OSS-Fuzz](https://google.github.io/oss-fuzz/getting-started/new-project-guide/go-lang/#native-go-fuzzing-support).

**Попробуйте [[../../tutorial/fuzz|tutorial по fuzzing в Go]].**

## Обзор

Fuzzing — вид automated testing, который непрерывно изменяет inputs program для поиска bugs.

Go fuzzing использует coverage guidance, чтобы интеллектуально проходить code under test и находить failures, сообщая их user.

Поскольку fuzzing способен достигать edge cases, которые люди часто пропускают, он особенно полезен для поиска security exploits и vulnerabilities.

## Написание fuzz tests

### Требования

Fuzz tests должны соблюдать следующие правила:

- fuzz test — function с name вида `FuzzXxx`, принимающая только `*testing.F` и не возвращающая values;
- fuzz tests должны находиться в `*_test.go` files;
- [fuzz target](#glos-fuzz-target) должен быть method call [`(*testing.F).Fuzz`](https://pkg.go.dev/testing#F.Fuzz), принимающий `*testing.T` первым parameter, затем fuzzing arguments, и ничего не возвращающий;
- в одном fuzz test должен быть ровно один fuzz target;
- все [seed corpus](#glos-seed-corpus) entries должны иметь types, полностью совпадающие с [fuzzing arguments](#glos-fuzzing-arguments), в том же order — это относится и к [`(*testing.F).Add`](https://pkg.go.dev/testing#F.Add), и к corpus files в `testdata/fuzz`;
- fuzzing arguments могут иметь только следующие types:
  - `string`, `[]byte`;
  - `int`, `int8`, `int16`, `int32`/`rune`, `int64`;
  - `uint`, `uint8`/`byte`, `uint16`, `uint32`, `uint64`;
  - `float32`, `float64`;
  - `bool`.

### Рекомендации {#suggestions}

- Fuzz targets должны быть быстрыми и deterministic, чтобы fuzzing engine эффективно работал, а failures и coverage можно было легко воспроизводить.
- Fuzz target запускается parallel на нескольких workers и в nondeterministic order, поэтому state fuzz target не должен переживать окончание одного call, а behavior не должен зависеть от global state.

## Запуск fuzz tests

Fuzz test можно запускать в двух modes:

1. как unit test — обычным `go test`;
2. с fuzzing — `go test -fuzz=FuzzTestName`.

По default fuzz tests ведут себя похоже на unit tests: каждый seed corpus entry запускается на fuzz target, failures report'ятся, после чего test завершается.

Чтобы включить fuzzing, передайте `go test` flag `-fuzz` с regular expression, matching ровно один fuzz test.

По default до начала fuzzing выполняются все остальные tests package. Это гарантирует, что fuzzing не будет report'ить problems, которые уже ловит обычный existing test.

Продолжительность fuzzing определяет user. Если failures не находятся, execution может продолжаться indefinitely.

**Note:** fuzzing следует запускать на platform с support coverage instrumentation — сейчас AMD64 и ARM64 — чтобы corpus мог осмысленно расти по мере execution и fuzzing покрывал всё больше code.

### Command line output

Во время active fuzzing [fuzzing engine](#glos-fuzzing-engine) генерирует новые inputs и запускает их на fuzz target.

По default он продолжает работу, пока не найдёт [failing input](#glos-failing-input) либо user не остановит process, например `Ctrl+C`.

Typical output:

```text
~ go test -fuzz FuzzFoo
fuzz: elapsed: 0s, gathering baseline coverage: 0/192 completed
fuzz: elapsed: 0s, gathering baseline coverage: 192/192 completed, now fuzzing with 8 workers
fuzz: elapsed: 3s, execs: 325017 (108336/sec), new interesting: 11 (total: 202)
fuzz: elapsed: 6s, execs: 680218 (118402/sec), new interesting: 12 (total: 203)
fuzz: elapsed: 9s, execs: 1039901 (119895/sec), new interesting: 19 (total: 210)
fuzz: elapsed: 12s, execs: 1386684 (115594/sec), new interesting: 21 (total: 212)
PASS
ok      foo 12.692s
```

До fuzzing собирается **baseline coverage**.

Для этого engine выполняет и [seed corpus](#glos-seed-corpus), и [generated corpus](#glos-generated-corpus), чтобы убедиться в отсутствии errors и определить coverage, которое уже предоставляет существующий corpus.

Следующие lines описывают active execution:

- `elapsed` — время с начала process;
- `execs` — total number inputs, выполненных на fuzz target, и average execs/sec с прошлого log line;
- `new interesting` — число новых «interesting» inputs, добавленных в generated corpus в этом run, а также total corpus size.

Input считается **interesting**, если расширяет code coverage дальше, чем existing generated corpus.

Обычно число new interesting inputs быстро растёт в начале, затем постепенно уменьшается, периодически давая всплески при нахождении новых branches/code paths.

### Failing input

Failure во время fuzzing может произойти, если:

- code или test panic'нул;
- fuzz target вызвал `t.Fail`, напрямую или через `t.Error`/`t.Fatal`;
- произошёл non-recoverable error, например `os.Exit` или stack overflow;
- fuzz target слишком долго выполнялся. Текущий timeout одного execution — 1 second. Причиной может быть deadlock, infinite loop или intentional slow behavior.

При error fuzzing engine пытается минимизировать input до smallest possible и наиболее human-readable value, который всё ещё reproduces failure.

После minimization error логируется, а output заканчивается примерно так:

```text
    Failing input written to testdata/fuzz/FuzzFoo/a878c3134fe0404d44eb1e662e5d8d4a24beb05c3d68354903670ff65513ff49
    To re-run:
    go test -run=FuzzFoo/a878c3134fe0404d44eb1e662e5d8d4a24beb05c3d68354903670ff65513ff49
FAIL
exit status 1
FAIL    foo 0.839s
```

Fuzzing engine записывает failing input в seed corpus соответствующего test. После этого input автоматически запускается обычным `go test` и после fix становится regression test.

Дальше developer должен:

1. диагностировать problem;
2. исправить bug;
3. проверить fix повторным `go test`;
4. отправить patch вместе с новым testdata file как regression test.

### Custom settings {#custom-settings}

Default settings подходят большинству случаев:

```text
$ go test -fuzz={FuzzTestName}
```

Дополнительные flags документированы в [`cmd/go`](https://pkg.go.dev/cmd/go).

Основные:

- `-fuzztime` — total time или number iterations fuzz target; default — indefinitely;
- `-fuzzminimizetime` — time/iterations каждого minimization attempt; default 60 sec; `-fuzzminimizetime 0` полностью отключает minimization;
- `-parallel` — number fuzzing processes, default `$GOMAXPROCS`; flag `-cpu` во время fuzzing сейчас не влияет.

## Corpus file format

Corpus files имеют специальный format, одинаковый для seed и generated corpus.

Example:

```text
go test fuzz v1
[]byte("hello\\xbd\\xb2=\\xbc ⌘")
int64(572293)
```

Первая line указывает encoding version. Future formats сейчас не запланированы, но design допускает versioning.

Последующие lines — values corpus entry; их при желании можно непосредственно скопировать в Go code.

В example сначала `[]byte`, затем `int64`. Types и order должны точно соответствовать fuzzing arguments:

```go
f.Fuzz(func(*testing.T, []byte, int64) {})
```

Проще всего задавать собственный seed corpus через `(*testing.F).Add`:

```go
f.Add([]byte("hello\\xbd\\xb2=\\xbc ⌘"), int64(572293))
```

Для больших binary files, которые удобнее хранить отдельными corpus entries в `testdata/fuzz/{FuzzTestName}`, используйте [`file2fuzz`](https://pkg.go.dev/golang.org/x/tools/cmd/file2fuzz):

```text
$ go install golang.org/x/tools/cmd/file2fuzz@latest
$ file2fuzz -h
```

## Resources

### Tutorials

- [[../../tutorial/fuzz|Full tutorial по fuzzing в Go]]
- [Короткий introductory blog post](https://go.dev/blog/fuzz-beta)

### Documentation

- [`testing` package fuzzing docs](https://pkg.go.dev/testing#hdr-Fuzzing) описывают `testing.F`.
- [`cmd/go`](https://pkg.go.dev/cmd/go) описывает flags fuzzing.

### Technical details

- [Design draft](https://go.dev/s/draft-fuzzing-design)
- [Proposal #44551](https://go.dev/issue/44551)

## Glossary {#glossary}

<a id="glos-corpus-entry"></a>
**corpus entry:** input в corpus, используемый при fuzzing. Это может быть specially-formatted file или call `(*testing.F).Add`.

<a id="glos-coverage-guidance"></a>
**coverage guidance:** fuzzing method, использующий расширение code coverage для определения corpus entries, которые стоит сохранять для future use.

<a id="glos-failing-input"></a>
**failing input:** corpus entry, вызывающий error или panic при запуске на [fuzz target](#glos-fuzz-target).

<a id="glos-fuzz-target"></a>
**fuzz target:** function fuzz test, выполняемая для corpus entries и generated values. Она передаётся в `(*testing.F).Fuzz`.

<a id="glos-fuzz-test"></a>
**fuzz test:** function в test file формы `func FuzzXxx(*testing.F)`, которую можно использовать для fuzzing.

<a id="glos-fuzzing"></a>
**fuzzing:** automated testing, непрерывно изменяющий inputs program для поиска issues, включая bugs и [vulnerabilities](#glos-vulnerability).

<a id="glos-fuzzing-arguments"></a>
**fuzzing arguments:** types, передаваемые fuzz target и mutating'ся [mutator](#glos-mutator).

<a id="glos-fuzzing-engine"></a>
**fuzzing engine:** tool, управляющий fuzzing: corpus, mutator, обнаружением new coverage и reporting failures.

<a id="glos-generated-corpus"></a>
**generated corpus:** corpus, который fuzzing engine поддерживает во время fuzzing для tracking progress. Он хранится в `$GOCACHE/fuzz`; entries используются только active fuzzing.

<a id="glos-mutator"></a>
**mutator:** tool, случайным образом изменяющий corpus entries перед передачей fuzz target.

<a id="glos-package"></a>
**package:** collection source files в одном directory, которые compile'ятся вместе. См. [[../../spec#Packages|Packages в Go Language Specification]].

<a id="glos-seed-corpus"></a>
**seed corpus:** user-provided corpus fuzz test, направляющий fuzzing engine. Он состоит из entries из `f.Add` и files `testdata/fuzz/{FuzzTestName}`. Эти entries запускаются обычным `go test` независимо от того, включён fuzzing или нет.

<a id="glos-test-file"></a>
**test file:** file формата `xxx_test.go`, который может содержать tests, benchmarks, examples и fuzz tests.

<a id="glos-vulnerability"></a>
**vulnerability:** security-sensitive weakness в code, которую может exploit attacker.

## Feedback

Если возникла problem или есть предложение feature, [создайте issue](https://go.dev/issue/new?&labels=fuzz).

Для discussion и general feedback также доступен [#fuzzing channel](https://gophers.slack.com/archives/CH5KV1AKE) в Gophers Slack.
