---
title: "Защита от SQL injection"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/database/sql-injection.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Защита от SQL injection

Передавайте SQL parameter values отдельными arguments методов `database/sql`, а не вставляйте их в SQL string.

Правильно:

```go
rows, err := db.Query("select * from user where id = ?", id)
```

SQL text и parameter value передаются driver/DBMS раздельно.

Placeholder зависит от driver. Например, PostgreSQL driver может использовать:

```go
rows, err := db.Query("select * from users where id = $1", id)
```

## Нельзя собирать query через `fmt.Sprintf`

Небезопасно:

```go
rows, err := db.Query(
    fmt.Sprintf("select * from user where id = %s", id),
)
```

В таком коде untrusted input становится частью SQL syntax. Злоумышленник может передать значение, превращающее statement, например, в:

```sql
select *
from user
where id = 1 or 1 = 1;
```

Вместо data value application фактически принимает произвольный fragment SQL grammar.

> [!important]
> Parameterization защищает **values**, но не предназначена для dynamic identifiers (`table`, `column`, `order by` field). Такие элементы нужно выбирать из allowlist/known mappings, а не принимать как произвольный user input.
