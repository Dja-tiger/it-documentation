---
title: "Управление connections"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/database/manage-connections.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Управление connections

Для подавляющего большинства программ defaults connection pool `sql.DB` менять не требуется. Однако некоторым приложениям необходим tuning параметров pool или явная работа с отдельными connections. Эта страница описывает оба варианта.

Database handle [`sql.DB`](https://pkg.go.dev/database/sql#DB) безопасен для concurrent use несколькими goroutines — в терминологии других языков это часто называется thread-safe.

Некоторые database access libraries строятся вокруг connection, которую можно использовать только для одной operation одновременно. Чтобы совместить такую модель с concurrency Go, каждый `sql.DB` управляет pool активных connections к underlying database и при необходимости создаёт новые для parallel operations.

Для большинства задач встроенного connection pool достаточно. При вызове `sql.DB.Query` или `sql.DB.Exec` implementation получает свободную connection из pool либо при необходимости создаёт новую. После завершения operation connection возвращается в pool. Это обеспечивает высокий уровень parallelism для database access.

### Настройка параметров connection pool {#connection_pool_properties}

Можно задавать свойства, определяющие, как пакет `sql` управляет connection pool. Для оценки эффекта этих настроек используйте [`DB.Stats`](https://pkg.go.dev/database/sql#DB.Stats).

#### Максимальное число открытых connections {#max_open_connections}

[`DB.SetMaxOpenConns`](https://pkg.go.dev/database/sql#DB.SetMaxOpenConns) ограничивает количество одновременно открытых connections.

После достижения limit новые database operations будут ждать завершения существующей operation, после чего `sql.DB` сможет предоставить connection.

По умолчанию, если все существующие connections заняты и требуется ещё одна, `sql.DB` создаёт новую connection.

> [!warning]
> После установки limit использование database начинает напоминать захват lock или semaphore. Поэтому приложение может попасть в deadlock, ожидая новую database connection.

#### Максимальное число idle connections {#max_idle_connections}

[`DB.SetMaxIdleConns`](https://pkg.go.dev/database/sql#DB.SetMaxIdleConns) меняет maximum number idle connections, которые `sql.DB` сохраняет в pool.

После завершения SQL operation connection обычно не закрывается немедленно: приложению вскоре может понадобиться следующая operation, и сохранение открытой connection позволяет избежать нового connection establishment.

По умолчанию `sql.DB` сохраняет до двух idle connections. В приложениях с высоким parallelism увеличение этого limit может уменьшить частые reconnects.

#### Максимальное время простоя connection {#max_idle_time}

[`DB.SetConnMaxIdleTime`](https://pkg.go.dev/database/sql#DB.SetConnMaxIdleTime) задаёт maximum duration, в течение которого connection может оставаться idle перед закрытием.

По умолчанию добавленная в pool idle connection остаётся там до следующего использования.

Если `DB.SetMaxIdleConns` увеличивается для обслуживания bursts параллельной активности, `DB.SetConnMaxIdleTime` можно использовать совместно с ним, чтобы позднее освободить избыточные connections, когда system снова простаивает.

#### Максимальный lifetime connection {#max_connection_lifetime}

[`DB.SetConnMaxLifetime`](https://pkg.go.dev/database/sql#DB.SetConnMaxLifetime) задаёт maximum duration, в течение которого connection может оставаться открытой до принудительного закрытия.

По умолчанию connection может использоваться и переиспользоваться неопределённо долго с учётом остальных pool limits.

В некоторых системах — например, при использовании load-balanced database servers — полезно гарантировать, что приложение периодически reconnect'ится и не использует одну physical connection слишком долго.

### Использование выделенных connections {#dedicated_connections}

Пакет `database/sql` предоставляет отдельный механизм для случаев, когда database придаёт implicit semantics последовательности operations, выполненных на **одной и той же connection**.

Самый распространённый пример — transactions. Обычно они начинаются `begin`, завершаются `commit` или `rollback`, а все commands между ними относятся к одной transaction. Для этого случая следует использовать встроенную transaction support пакета `sql`; см. [[execute-transactions|Выполнение транзакций]].

Для других случаев, где последовательность независимых operations должна выполняться на одной physical connection, используйте dedicated connection.

[`DB.Conn`](https://pkg.go.dev/database/sql#DB.Conn) получает выделенную connection — [`sql.Conn`](https://pkg.go.dev/database/sql#Conn).

`sql.Conn` предоставляет methods:

- `BeginTx`;
- `ExecContext`;
- `PingContext`;
- `PrepareContext`;
- `QueryContext`;
- `QueryRowContext`.

Они ведут себя аналогично соответствующим methods `DB`, но всегда используют именно эту dedicated connection.

После завершения работы выделенную connection необходимо вернуть/освободить через:

```go
conn.Close()
```
