# Practice 14 — Specification и runtime labs

## Часть A. Specification prediction drills

Для каждого fragment сначала записать prediction и ссылку на раздел [[../../docs/spec|Specification]], затем запускать compiler/runtime.

### 1. Comparability matrix

Составить таблицу `comparable?` для:

- `[3]int`;
- `[]int`;
- `struct{ ID string; N int }`;
- `struct{ Values []int }`;
- `map[string]int`;
- `func()`;
- interface values с comparable и non-comparable dynamic values.

Проверить equality/map-key possibilities и interface equality panic scenario.

### 2. Method-set matrix

Для methods с receivers `T` и `*T` предсказать assignments `T`/`*T` в interfaces и calls через addressable/non-addressable values.

### 3. Nil matrix

Предсказать behavior:

- read nil map;
- write nil map;
- receive nil channel;
- send nil channel;
- close nil channel;
- dereference nil pointer;
- typed nil inside interface.

Для blocking cases запускать только с external/test timeout.

### 4. Slice capacity

Использовать `a[low:high:max]`, `append`, aliases. Предсказать `len`, `cap` и mutation visibility.

### 5. `defer`

Проверить separately:

- когда evaluates arguments;
- reverse order;
- named result modification;
- nil deferred function behavior.

### 6. Map/range/select

Написать bug, который случайно зависит от map iteration order, затем исправить design. Для `select` иметь несколько ready cases и доказать, что code не зависит от deterministic priority.

## Часть B. Runtime diagnostics labs

### 7. Happens-before

Создать intentional race shared variable. Затем исправить дважды:

1. через mutex;
2. через channel ownership/communication.

Для обоих нарисовать happens-before edge и подтвердить `go test -race`.

### 8. Allocation profile → escape analysis

Создать representative processor benchmark. Снять heap/allocation profile. Только выбранный hotspot исследовать:

```bash
go build -gcflags=-m=3 ./...
```

Записать, какой value escapes и почему это важно/неважно для workload.

### 9. Scheduler/trace

Под load создать:

- CPU-bound workers;
- blocked workers;
- mutex contention.

Собрать runtime trace и сравнить observed states. Затем использовать controlled `GODEBUG=schedtrace=1000` run.

### 10. GC trade-off lab

На synthetic allocation workload сравнить несколько controlled runs с разным `GOGC` и отдельно realistic `GOMEMLIMIT`.

### Acceptance criteria

Не искать «лучшее число». Report должен показать trade-off CPU / allocation rate / live heap / peak memory и объяснить, почему microbenchmark не задаёт production setting.

## Общая проверка

```bash
gofmt -w .
go test ./...
go test -race ./...
go vet ./...
go test -bench=. -benchmem ./...
```

Все intentional panics/deadlocks/races должны жить в isolated tests/examples и не ломать обычный test suite.
