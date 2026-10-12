---
title: "Предотвращение SQL injection"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/database/sql-injection.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Предотвращение SQL injection

Риск SQL injection можно устранить, передавая SQL parameter values отдельными arguments functions пакета `sql`.

Многие functions `database/sql` принимают отдельно:

- SQL statement;
- values для parameters этого statement.

Другие functions принимают prepared statement и parameter values.

В следующем корректном примере `?` является placeholder для parameter `id`, а само значение передаётся отдельным function argument:

```go
// Correct format for executing an SQL statement with parameters.
rows, err := db.Query("select * from user where id = ?", id)
```

Functions пакета `sql`, выполняющие database operations, формируют prepared statement из переданных arguments. Во время выполнения пакет отправляет SQL statement и parameter отдельно, а не объединяет их в одну SQL string.

> [!note]
> Parameter placeholders зависят от DBMS и driver. Например, [pq driver](https://pkg.go.dev/github.com/lib/pq) для Postgres принимает placeholder вида `$1` вместо `?`.

Может возникнуть желание собрать SQL statement через `fmt`, подставив parameter непосредственно в string:

```go
// SECURITY RISK!
rows, err := db.Query(fmt.Sprintf("select * from user where id = %s", id))
```

Это **небезопасно**.

В таком случае Go сначала формирует полный SQL statement, заменяя `%s` значением parameter, и только затем отправляет готовую строку DBMS.

Так возникает [SQL injection](https://en.wikipedia.org/wiki/SQL_injection): caller может передать вместо ожидаемого `id` произвольный SQL fragment, который непредсказуемо изменит semantics итогового statement и может привести к опасным последствиям.

Например, специально сформированное значение `%s` может превратить statement в:

```sql
select * from user where id = 1 or 1=1;
```

Такой statement способен вернуть все user records из database.
