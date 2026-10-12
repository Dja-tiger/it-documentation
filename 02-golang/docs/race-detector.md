---
title: "Data Race Detector"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/articles/race_detector.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Data Race Detector

## Введение {#Introduction}

Data races — один из самых распространённых и наиболее сложных для отладки типов ошибок в concurrent systems.

Data race возникает, когда две goroutines одновременно обращаются к одной переменной и хотя бы одно из обращений является записью.

Подробности см. в [[memory-model|Модели памяти Go]].

Ниже приведён пример data race, который может приводить к crashes и повреждению памяти:

```go
func main() {
	c := make(chan bool)
	m := make(map[string]string)
	go func() {
		m["1"] = "a" // First conflicting access.
		c <- true
	}()
	m["2"] = "b" // Second conflicting access.
	<-c
	for k, v := range m {
		fmt.Println(k, v)
	}
}
```

## Использование {#Usage}

Для диагностики таких ошибок Go содержит встроенный data race detector.

Чтобы использовать его, добавьте flag `-race` к команде `go`:

```text
$ go test -race mypkg    // to test the package
$ go run -race mysrc.go  // to run the source file
$ go build -race mycmd   // to build the command
$ go install -race mypkg // to install the package
```

## Формат отчёта {#Report_Format}

Когда race detector находит data race в программе, он печатает report.

Report содержит stack traces конфликтующих accesses, а также stacks мест, где были созданы участвующие goroutines.

Пример:

```text
WARNING: DATA RACE
Read by goroutine 185:
  net.(*pollServer).AddFD()
      src/net/fd_unix.go:89 +0x398
  net.(*pollServer).WaitWrite()
      src/net/fd_unix.go:247 +0x45
  net.(*netFD).Write()
      src/net/fd_unix.go:540 +0x4d4
  net.(*conn).Write()
      src/net/net.go:129 +0x101
  net.func·060()
      src/net/timeout_test.go:603 +0xaf

Previous write by goroutine 184:
  net.setWriteDeadline()
      src/net/sockopt_posix.go:135 +0xdf
  net.setDeadline()
      src/net/sockopt_posix.go:144 +0x9c
  net.(*conn).SetDeadline()
      src/net/net.go:161 +0xe3
  net.func·061()
      src/net/timeout_test.go:616 +0x3ed

Goroutine 185 (running) created at:
  net.func·061()
      src/net/timeout_test.go:609 +0x288

Goroutine 184 (running) created at:
  net.TestProlongTimeout()
      src/net/timeout_test.go:618 +0x298
  testing.tRunner()
      src/testing/testing.go:301 +0xe8
```

## Options {#Options}

Environment variable `GORACE` задаёт options race detector.

Формат:

```text
GORACE="option1=val1 option2=val2"
```

Поддерживаются следующие options:

- `log_path` (default `stderr`) — race detector записывает report в file `log_path.pid`. Special names `stdout` и `stderr` направляют reports в standard output и standard error соответственно.
- `exitcode` (default `66`) — exit status, используемый при завершении после detected race.
- `strip_path_prefix` (default `""`) — удаляет этот prefix из всех file paths в report, делая report короче.
- `history_size` (default `1`) — history memory accesses каждой goroutine содержит `32K * 2**history_size elements`. Увеличение значения может устранить ошибку `failed to restore the stack` в reports ценой увеличенного потребления памяти.
- `halt_on_error` (default `0`) — определяет, завершать ли программу после первого report о data race.
- `atexit_sleep_ms` (default `1000`) — число milliseconds, которое main goroutine ждёт перед exit.

Пример:

```text
$ GORACE="log_path=/tmp/race/report strip_path_prefix=/my/go/sources/" go test -race
```

## Исключение tests {#Excluding_Tests}

При сборке с flag `-race` команда `go` определяет дополнительный build tag `race`.

Этот tag можно использовать, чтобы исключить часть code и tests при запуске race detector.

Примеры:

```go
// +build !race

package foo

// The test contains a data race. See issue 123.
func TestFoo(t *testing.T) {
	// ...
}

// The test fails under the race detector due to timeouts.
func TestBar(t *testing.T) {
	// ...
}

// The test takes too long under the race detector.
func TestBaz(t *testing.T) {
	// ...
}
```

## Как использовать {#How_To_Use}

Начните с запуска tests через race detector:

```bash
go test -race
```

Race detector находит только races, которые происходят во время runtime execution, поэтому он не может обнаружить races в code paths, которые не выполнялись.

Если tests имеют неполное coverage, дополнительные races можно найти, запустив binary, собранный с `-race`, под realistic workload.

## Типичные data races {#Typical_Data_Races}

Ниже приведены несколько типичных data races. Все они обнаруживаются race detector.

### Race на loop counter {#Race_on_loop_counter}

```go
func main() {
	var wg sync.WaitGroup
	wg.Add(5)
	var i int
	for i = 0; i < 5; i++ {
		go func() {
			fmt.Println(i) // Not the 'i' you are looking for.
			wg.Done()
		}()
	}
	wg.Wait()
}
```

Variable `i` внутри function literal — та же variable, которую использует loop, поэтому read в goroutine races с increment loop.

Эта программа обычно печатает `55555`, а не `01234`.

Исправить программу можно, создав copy variable:

```go
func main() {
	var wg sync.WaitGroup
	wg.Add(5)
	var i int
	for i = 0; i < 5; i++ {
		go func(j int) {
			fmt.Println(j) // Good. Read local copy of the loop counter.
			wg.Done()
		}(i)
	}
	wg.Wait()
}
```

### Случайно разделяемая variable {#Accidentally_shared_variable}

```go
// ParallelWrite writes data to file1 and file2, returns the errors.
func ParallelWrite(data []byte) chan error {
	res := make(chan error, 2)
	f1, err := os.Create("file1")
	if err != nil {
		res <- err
	} else {
		go func() {
			// This err is shared with the main goroutine,
			// so the write races with the write below.
			_, err = f1.Write(data)
			res <- err
			f1.Close()
		}()
	}
	f2, err := os.Create("file2") // The second conflicting write to err.
	if err != nil {
		res <- err
	} else {
		go func() {
			_, err = f2.Write(data)
			res <- err
			f2.Close()
		}()
	}
	return res
}
```

Исправление — объявить новые variables внутри goroutines; обратите внимание на использование `:=`:

```go
			...
			_, err := f1.Write(data)
			...
			_, err := f2.Write(data)
			...
```

### Незащищённая global variable {#Unprotected_global_variable}

Если следующий code вызывается из нескольких goroutines, возникает race на map `service`.

Concurrent reads и writes одной и той же map небезопасны:

```go
var service map[string]net.Addr

func RegisterService(name string, addr net.Addr) {
	service[name] = addr
}

func LookupService(name string) net.Addr {
	return service[name]
}
```

Чтобы сделать code безопасным, защитите accesses mutex:

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

### Незащищённая primitive variable {#Primitive_unprotected_variable}

Data races могут возникать и на variables primitive types (`bool`, `int`, `int64` и т. д.).

Пример:

```go
type Watchdog struct{ last int64 }

func (w *Watchdog) KeepAlive() {
	w.last = time.Now().UnixNano() // First conflicting access.
}

func (w *Watchdog) Start() {
	go func() {
		for {
			time.Sleep(time.Second)
			// Second conflicting access.
			if w.last < time.Now().Add(-10*time.Second).UnixNano() {
				fmt.Println("No keepalives for 10 seconds. Dying.")
				os.Exit(1)
			}
		}
	}()
}
```

Даже такие на первый взгляд «безобидные» data races могут приводить к трудно диагностируемым проблемам из-за:

- non-atomicity memory accesses;
- взаимодействия с compiler optimizations;
- reordering при обращении к processor memory.

Обычное исправление — использовать channel или mutex.

Чтобы сохранить lock-free behavior, можно использовать package `sync/atomic`:

```go
type Watchdog struct{ last int64 }

func (w *Watchdog) KeepAlive() {
	atomic.StoreInt64(&w.last, time.Now().UnixNano())
}

func (w *Watchdog) Start() {
	go func() {
		for {
			time.Sleep(time.Second)
			if atomic.LoadInt64(&w.last) < time.Now().Add(-10*time.Second).UnixNano() {
				fmt.Println("No keepalives for 10 seconds. Dying.")
				os.Exit(1)
			}
		}
	}()
}
```

### Несинхронизированные send и close {#Unsynchronized_send_and_close_operations}

Как показывает следующий пример, unsynchronized send и close operations на одном channel тоже могут быть race condition:

```go
c := make(chan struct{}) // or buffered channel

// The race detector cannot derive the happens before relation
// for the following send and close operations. These two operations
// are unsynchronized and happen concurrently.
go func() { c <- struct{}{} }()
close(c)
```

Согласно модели памяти Go, send в channel happens before завершение соответствующего receive из этого channel.

Чтобы синхронизировать send и close, используйте receive operation, гарантирующую завершение send до close:

```go
c := make(chan struct{}) // or buffered channel

go func() { c <- struct{}{} }()
<-c
close(c)
```

## Требования {#Requirements}

Race detector требует включённый `cgo`, а на non-Darwin systems — установленный C compiler.

Race detector поддерживает:

- `linux/amd64`;
- `linux/ppc64le`;
- `linux/arm64`;
- `linux/s390x`;
- `linux/loong64`;
- `freebsd/amd64`;
- `netbsd/amd64`;
- `darwin/amd64`;
- `darwin/arm64`;
- `windows/amd64`.

На Windows runtime race detector чувствителен к версии установленного C compiler. Начиная с Go 1.21 сборка программы с `-race` требует C compiler, содержащего runtime libraries `mingw-w64` версии 8 или новее.

Проверить C compiler можно, вызвав его с arguments:

```text
--print-file-name libsynchronization.a
```

Новый совместимый C compiler напечатает полный path этой library, тогда как старые compilers просто повторят argument.

## Runtime overhead {#Runtime_Overheads}

Стоимость race detection зависит от программы, но для типичной программы:

- memory usage может увеличиться в **5–10 раз**;
- execution time может увеличиться в **2–20 раз**.

Race detector в настоящее время выделяет дополнительные 8 bytes на каждый statement `defer` и `recover`.

Эти дополнительные allocations не освобождаются до завершения goroutine.

Это означает, что если long-running goroutine периодически выполняет `defer` и `recover`, memory usage программы может расти без ограничений.

Эти memory allocations не отображаются в output `runtime.ReadMemStats` или `runtime/pprof`.
