---
title: "Отмена выполняющихся операций"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/database/cancel-operations.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Отмена выполняющихся операций

Выполняющимися operations можно управлять через [`context.Context`](https://pkg.go.dev/context#Context).

`Context` — стандартное Go value, которое сообщает, была ли представляющая его общая operation отменена и перестала ли она быть нужна.

Если передавать `context.Context` через function calls и services приложения, downstream code может досрочно прекращать работу и возвращать error, когда дальнейшая обработка больше не нужна.

Подробнее о `Context` см. [Go Concurrency Patterns: Context](https://go.dev/blog/context).

Например, cancellation может использоваться для того, чтобы:

- завершить long-running operations, включая database operations, выполнение которых занимает слишком много времени;
- распространить cancellation request из другого слоя приложения — например, когда client закрывает connection.

Многие Go APIs предоставляют methods, принимающие `Context`, что позволяет последовательно распространять cancellation по всему приложению.

### Отмена database operation по timeout {#timeout_cancel}

Через `Context` можно задать timeout или deadline, после которого operation будет отменена.

Для создания derived Context используйте:

- [`context.WithTimeout`](https://pkg.go.dev/context#WithTimeout);
- [`context.WithDeadline`](https://pkg.go.dev/context#WithDeadline).

В следующем примере создаётся `Context` с timeout, который передаётся в [`DB.QueryContext`](https://pkg.go.dev/database/sql#DB.QueryContext):

```go
func QueryWithTimeout(ctx context.Context) {
	// Create a Context with a timeout.
	queryCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	// Pass the timeout Context with a query.
	rows, err := db.QueryContext(queryCtx, "select * from album")
	if err != nil {
		log.Fatal(err)
	}
	defer rows.Close()

	// Handle returned rows.
}
```

Когда один context derived из внешнего context, как `queryCtx` derived из `ctx` в примере, отмена outer context автоматически отменяет и derived context.

Например, в HTTP server method `http.Request.Context` возвращает context, связанный с конкретным request. Этот context отменяется, если HTTP client disconnect'ится или отменяет HTTP request; последнее возможно, например, в HTTP/2.

Если передать HTTP request context в `QueryWithTimeout`, database query завершится досрочно в любом из двух случаев:

1. отменён весь HTTP request;
2. query выполняется дольше пяти секунд.

> [!important]
> Всегда вызывайте через `defer` функцию `cancel`, возвращённую при создании нового `Context` с timeout или deadline.
>
> Это освобождает resources, удерживаемые новым `Context`, когда enclosing function завершается. Вызов также отменяет `queryCtx`, но к моменту выхода из function этот context уже не должен использоваться.
