# Минимальный маршрут по standard library

Полная API-документация остаётся на [pkg.go.dev/std](https://pkg.go.dev/std). Здесь только момент изучения, назначение и обязательная практика.

| Package | Когда | Зачем | Минимальная практика |
|---|---|---|---|
| `fmt` | Stage 1–2 | форматирование/output | вывести и отформатировать `Price` |
| `strings` | Stage 2 | строковые преобразования | нормализовать `store_id`/`plu_id` |
| `strconv` | Stage 2 | parse/format scalar values | распарсить price/id из CSV |
| `time` | Stage 2, 7, 10 | timestamps, timers, deadlines | deadline и timestamp `PriceUpdate` |
| `os` | Stage 1–2 | args/env/files/process | CLI input и config из environment |
| `io` | Stage 2, 9 | streaming contracts | pipeline через `io.Reader`/`io.Writer` |
| `bufio` | Stage 2 | buffered streaming | прочитать большой CSV без `ReadAll` |
| `errors` | Stage 4 | error identity/wrapping | sentinel/custom error + `Is`/`As` |
| `testing` | Stage 4 | unit/benchmark/fuzz API | table-driven tests и fuzz target |
| `sync` | Stage 6 | synchronization | `WaitGroup`, `Mutex`, ownership comparison |
| `sync/atomic` | Stage 6 | низкоуровневые atomics | безопасный counter после mutex-варианта |
| `context` | Stage 7 | cancellation/deadline propagation | остановить pipeline по timeout |
| `database/sql` | Stage 8 | relational DB access/pool | PostgreSQL repository с `QueryContext` |
| `encoding/json` | Stage 9 | canonical v1 JSON API/reference | прочитать существующий v1 код и сравнить с v2 |
| `encoding/json/v2` | Stage 9 | Go 1.27 JSON tutorial path | streaming decode pricing payload |
| `net/http` | Stage 9 | HTTP client/server | pricing API без обязательного framework |
| `log/slog` | Stage 10 | structured logging | request/job fields + error context |
| `runtime/pprof` | Stage 12 | profiling | CPU/heap profile processor workload |
| `runtime` | Stage 12–14 | runtime metrics/diagnostics | goroutine/runtime metrics observation |

## Правило использования pkg.go.dev

Для каждого package уметь быстро ответить:

- какой type/function решает задачу;
- кто владеет lifecycle ресурса;
- безопасен ли type для concurrent use;
- что означает zero value;
- какие ошибки/edge cases документированы.

Не нужно заучивать список functions. Нужно уметь читать contract API и применять его без нарушения lifecycle/concurrency guarantees.
