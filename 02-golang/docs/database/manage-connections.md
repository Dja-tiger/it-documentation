---
title: "Управление database connections"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/database/manage-connections.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Управление connections

Для большинства программ defaults `sql.DB` connection pool не требуют изменения. Tuning нужен при известных database limits, высокой concurrency, load balancer behavior или специфических connection-local требованиях.

`sql.DB` concurrency-safe и рассчитан на совместное использование несколькими goroutines.

При `Query`/`Exec` pool:

1. берёт свободное connection;
2. либо создаёт новое;
3. выполняет operation;
4. возвращает connection в pool.

## Pool statistics

Для наблюдения используйте:

```go
stats := db.Stats()
```

Полезны `OpenConnections`, `InUse`, `Idle`, `WaitCount`, `WaitDuration`, counters closed connections.

## Max open connections

```go
db.SetMaxOpenConns(n)
```

Ограничивает число одновременно открытых connections. После достижения limit новые operations ждут освобождения connection.

> [!warning]
> Ограниченный pool начинает вести себя как semaphore. Неправильная архитектура может создать deadlock, особенно если operation удерживает connection и одновременно ждёт другую operation, которой также нужен connection.

## Max idle connections

```go
db.SetMaxIdleConns(n)
```

Управляет количеством idle connections, которые pool сохраняет открытыми.

Высокое значение уменьшает reconnect overhead при bursty parallel traffic, но увеличивает число постоянно открытых server connections.

Default historically поддерживает небольшой idle pool (официальный guide указывает два idle connections).

## Max idle time

```go
db.SetConnMaxIdleTime(d)
```

Закрывает connections, простаивающие дольше заданного duration. Полезно, если `SetMaxIdleConns` поднят для bursts, но после снижения нагрузки лишние connections нужно постепенно освобождать.

## Max connection lifetime

```go
db.SetConnMaxLifetime(d)
```

Ограничивает общую lifetime connection независимо от активности.

Полезно при:

- load-balanced database endpoints;
- server-side connection TTL;
- topology rotation;
- необходимости периодически перераспределять long-lived connections.

## Dedicated connections

Если несколько последовательных operations обязаны выполняться на одном physical connection, получите `*sql.Conn`:

```go
conn, err := db.Conn(ctx)
if err != nil {
    return err
}
defer conn.Close()
```

`sql.Conn` предоставляет:

- `BeginTx`;
- `ExecContext`;
- `PingContext`;
- `PrepareContext`;
- `QueryContext`;
- `QueryRowContext`.

Для обычных transactions используйте `sql.Tx`. Dedicated `Conn` нужен для иных connection-local semantics, например session state, temp objects или DB-specific operations.
