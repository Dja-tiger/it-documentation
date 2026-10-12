---
title: "Отмена database operations"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/database/cancel-operations.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Отмена выполняющихся операций

`context.Context` позволяет сообщить глубоко вложенным operations, что результат больше не нужен и работу следует прекратить.

Это полезно для:

- long-running database queries;
- request timeout;
- client disconnect;
- propagation cancellation через service layers.

## Timeout

```go
func QueryWithTimeout(ctx context.Context) {
    queryCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()

    rows, err := db.QueryContext(queryCtx, "select * from album")
    if err != nil {
        log.Printf("query failed: %v", err)
        return
    }
    defer rows.Close()

    // handle rows
}
```

Derived context автоматически отменяется, когда отменён parent context.

Для HTTP server `http.Request.Context()` отменяется, когда request отменён или client connection закрывается. Если от него вывести query context с дополнительным 5-second timeout, DB operation остановится при первом из событий:

- HTTP request canceled;
- client disconnected;
- query timeout exceeded.

> [!important]
> Всегда вызывайте returned `cancel` function, обычно через `defer cancel()`. Это освобождает timer/context resources даже если operation завершилась раньше deadline.
