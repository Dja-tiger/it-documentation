---
title: "Data Race Detector"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/articles/race_detector.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Data Race Detector

Data race возникает, когда две goroutines concurrent обращаются к одной variable и хотя бы один access — write, без необходимой synchronization.

Пример race на map:

```go
func main() {
    c := make(chan bool)
    m := make(map[string]string)

    go func() {
        m["1"] = "a" // first conflicting access
        c <- true
    }()

    m["2"] = "b" // second conflicting access
    <-c

    for k, v := range m {
        fmt.Println(k, v)
    }
}
```

Concurrent map write/read/write без synchronization unsafe.

## Использование

Race detector встроен в Go toolchain. Добавьте `-race`:

```bash
go test -race mypkg
go run -race mysrc.go
go build -race mycmd
go install -race mypkg
```

Detector находит **только races, реально произошедшие во время instrumented execution**. Поэтому высокая test coverage и realistic load важны.

## Report format

Report содержит:

- stack текущего conflicting access;
- stack previous conflicting access;
- stacks creation goroutines, участвующих в conflict.

Именно creation stacks часто позволяют понять, кто запустил goroutine и какой lifecycle привёл к race.

## `GORACE` options

Format:

```text
GORACE="option1=val1 option2=val2"
```

| Option | Default | Назначение |
|---|---:|---|
| `log_path` | `stderr` | Путь base report file `log_path.pid`; special `stdout`/`stderr`. |
| `exitcode` | `66` | Exit status после detected race. |
| `strip_path_prefix` | `""` | Удаляет prefix из file paths report. |
| `history_size` | `1` | Per-goroutine memory-access history: `32K * 2**history_size` elements. Увеличение помогает при `failed to restore the stack`, но требует памяти. |
| `halt_on_error` | `0` | Завершать program после первого race report. |
| `atexit_sleep_ms` | `1000` | Sleep main goroutine перед exit. |

Пример:

```bash
GORACE="log_path=/tmp/race/report strip_path_prefix=/my/go/sources/" \
    go test -race
```

## Build constraint `race`

При `-race` Go определяет build tag `race`. Его можно использовать для исключения tests/code, которые:

- intentionally содержат race;
- timeout'ятся под detector overhead;
- становятся неприемлемо медленными.

Modern build constraint:

```go
//go:build !race

package foo
```

Не используйте exclusion как способ скрыть реальные races.

## Как использовать detector эффективно

Начните с:

```bash
go test -race ./...
```

Если coverage недостаточна, соберите production-like binary:

```bash
go build -race ./cmd/service
```

и прогоните realistic workload/integration tests. Detector не является static analyzer: unexecuted path не проверяется.

## Типичные races

### Shared loop counter

```go
func main() {
    var wg sync.WaitGroup
    wg.Add(5)

    var i int
    for i = 0; i < 5; i++ {
        go func() {
            fmt.Println(i)
            wg.Done()
        }()
    }

    wg.Wait()
}
```

Read `i` в goroutine races с loop increment.

Исправление — передать copy:

```go
go func(j int) {
    fmt.Println(j)
    wg.Done()
}(i)
```

> [!note]
> Modern Go loop-variable semantics уменьшили целый класс closure mistakes для range/loop variables в соответствующих language versions, но общий принцип shared mutable variable остаётся.

### Accidentally shared error variable

Плохо:

```go
_, err = f1.Write(data)
```

из нескольких goroutines, если `err` — shared outer variable.

Создайте local variable:

```go
_, err := f1.Write(data)
```

### Unprotected global map

Unsafe:

```go
var service map[string]net.Addr

func RegisterService(name string, addr net.Addr) {
    service[name] = addr
}

func LookupService(name string) net.Addr {
    return service[name]
}
```

Protect accesses:

```go
var (
    service   map[string]net.Addr
    serviceMu sync.Mutex
)

func RegisterService(name string, addr net.Addr) {
    serviceMu.Lock()
    defer serviceMu.Unlock()
    service[name] = addr
}

func LookupService(name string) net.Addr {
    serviceMu.Lock()
    defer serviceMu.Unlock()
    return service[name]
}
```

Read-heavy case может использовать `RWMutex`; другие designs — ownership через goroutine/channel или specialized concurrency-safe structure.

### Primitive variable тоже может race

```go
type Watchdog struct{ last int64 }

func (w *Watchdog) KeepAlive() {
    w.last = time.Now().UnixNano()
}
```

Одновременный read другой goroutine race'ит с write, даже если type — простой `int64`.

Lock-free variant:

```go
func (w *Watchdog) KeepAlive() {
    atomic.StoreInt64(&w.last, time.Now().UnixNano())
}

func (w *Watchdog) expired() bool {
    return atomic.LoadInt64(&w.last) <
        time.Now().Add(-10*time.Second).UnixNano()
}
```

Atomics нужно использовать в соответствии с memory model, а не как случайную «оптимизацию вместо mutex».

### Concurrent send и `close`

Unsafe:

```go
c := make(chan struct{})

go func() { c <- struct{}{} }()
close(c)
```

Send и close не упорядочены.

Synchronize completion send:

```go
c := make(chan struct{})

go func() { c <- struct{}{} }()
<-c
close(c)
```

Send happens before corresponding receive completes; receive создаёт ordering перед close.

## Requirements

Race detector требует `cgo` и, кроме Darwin, установленный C compiler.

Официально документированные supported targets включают:

- `linux/amd64`, `linux/ppc64le`, `linux/arm64`, `linux/s390x`, `linux/loong64`;
- `freebsd/amd64`;
- `netbsd/amd64`;
- `darwin/amd64`, `darwin/arm64`;
- `windows/amd64`.

На Windows современный detector требует C compiler с достаточно новой `mingw-w64` runtime; проверить наличие нужной library можно compiler option `--print-file-name libsynchronization.a`.

## Runtime overhead

Typical overhead существенно выше обычного binary:

- memory: примерно **5–10×**;
- execution time: примерно **2–20×**.

Detector также выделяет дополнительную memory на `defer`/`recover`; для long-lived goroutine с постоянно создаваемыми deferred calls эта instrumentation memory может накапливаться до завершения goroutine и не отражаться в `runtime.ReadMemStats`/`runtime/pprof`.

Поэтому `-race` — обязательный test/debug инструмент, но обычно не режим постоянной production эксплуатации.
