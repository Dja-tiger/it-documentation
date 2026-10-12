---
title: "Spark — запись"
tags: [apache-iceberg, spark, writes, merge]
source_project: apache/iceberg
source_file: docs/docs/spark-writes.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/spark-writes.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Запись в Spark

Сначала настройте [[spark-configuration|Spark catalogs]]. Часть execution plans доступна только с Iceberg SQL extensions.

Iceberg использует DataSourceV2 API. Поддержка операций:

| Feature | Spark | Примечание |
| --- | --- | --- |
| SQL `insert into` | ✔️ | Требует `spark.sql.storeAssignmentPolicy=ANSI` (default с Spark 3.0) |
| SQL `merge into` | ✔️ | Требует Iceberg Spark extensions |
| SQL `insert overwrite` | ✔️ | Требует assignment policy ANSI |
| SQL `delete from` | ✔️ | Row-level delete требует extensions |
| SQL `update` | ✔️ | Требует extensions |
| DataFrame append | ✔️ | |
| DataFrame overwrite | ✔️ | |
| DataFrame CTAS/RTAS | ✔️ | DSv2 |
| DataFrame merge | ✔️ | DSv2, Spark 4.0+ |

## Запись через SQL

### `insert into`

```sql
insert into prod.db.table values (1, 'a'), (2, 'b');
insert into prod.db.table select ...;
```

#### Snapshot summary

Начиная с Spark 4.2 snapshot summary после `insert into` может содержать `spark.insert.num-inserted-rows` — число вставленных rows. Поле отсутствует, если Spark не сообщил значение.

### `merge into`

`merge into` выражает row-level updates. Iceberg реализует операцию, переписывая data files с изменяемыми rows в overwrite commit.

**`merge into` рекомендуется вместо `insert overwrite`**: Iceberg может заменить только затронутые data files, а semantics dynamic overwrite способны измениться при эволюции partitioning.

Target сопоставляется source через `on`:

```sql
merge into prod.db.target t
using (select ...) s
on t.id = s.id
when ...;
```

Несколько `when matched` разрешены; применяется первое совпавшее условие:

```sql
when matched and s.op = 'delete' then delete
when matched and t.count is null and s.op = 'increment' then update set t.count = 0
when matched and s.op = 'increment' then update set t.count = t.count + 1
```

Unmatched source rows можно вставлять:

```sql
when not matched then insert *
```

С дополнительным условием:

```sql
when not matched and s.event_time > still_valid_threshold then insert (id, count) values (s.id, 1)
```

Одна target row может быть обновлена не более чем одной source row, иначе Spark выдаёт error.

Spark 3.5+ поддерживает `when not matched by source`:

```sql
when not matched by source then update set status = 'invalid'
```

#### Snapshot summary MERGE

Начиная с Spark 4.1 могут записываться:

| Field | Значение |
| --- | --- |
| `spark.merge-into.num-target-rows-copied` | Target rows, скопированные без изменения |
| `spark.merge-into.num-target-rows-deleted` | Удалённые target rows |
| `spark.merge-into.num-target-rows-updated` | Обновлённые target rows |
| `spark.merge-into.num-target-rows-inserted` | Вставленные target rows |
| `spark.merge-into.num-target-rows-matched-updated` | Rows updated `matched` clause |
| `spark.merge-into.num-target-rows-matched-deleted` | Rows deleted `matched` clause |
| `spark.merge-into.num-target-rows-not-matched-by-source-updated` | Rows updated `not matched by source` |
| `spark.merge-into.num-target-rows-not-matched-by-source-deleted` | Rows deleted `not matched by source` |

### `insert overwrite`

Операция атомарно заменяет данные результатом query. Какие partitions заменяются, зависит от Spark partition overwrite mode и partitioning таблицы. `merge into` обычно безопаснее и понятнее.

Default mode Spark — **static**, но для Iceberg рекомендуется **dynamic**:

```text
spark.sql.sources.partitionOverwriteMode=dynamic
```

Пример таблицы:

```sql
create table prod.my_app.logs (
    uuid string not null,
    level string not null,
    ts timestamp not null,
    message string)
using iceberg
partitioned by (level, hours(ts));
```

#### Dynamic overwrite

Заменяются partitions, в которые попали rows результата `select`:

```sql
insert overwrite prod.my_app.logs
select uuid, first(level), first(ts), first(message)
from prod.my_app.logs
where cast(ts as date) = '2020-07-01'
group by uuid;
```

Так как result ограничен 1 июля, будут заменены только hourly partitions этого дня.

#### Static overwrite

В static mode `partition` clause превращается в delete filter. Если clause отсутствует, заменяются все partitions. Поэтому предыдущий пример в static mode удалит все существующие rows, а запишет только 1 июля.

```sql
insert overwrite prod.my_app.logs
partition (level = 'INFO')
select uuid, first(level), first(ts), first(message)
from prod.my_app.logs
where level = 'INFO'
group by uuid;
```

Static mode не способен адресовать hidden hourly partitions, потому что `partition` clause видит только table columns.

### `delete from`

```sql
delete from prod.db.table
where ts >= '2020-05-01 00:00:00' and ts < '2020-06-01 00:00:00';

delete from prod.db.all_events
where session_time < (select min(session_time) from prod.db.good_events);

delete from prod.db.orders as t1
where exists (select oid from prod.db.returned_orders where t1.oid = oid);
```

Если filter полностью покрывает partitions, Iceberg выполняет metadata-only delete. Если совпадают отдельные rows, переписываются только затронутые data files.

Spark 4.2+ snapshot summary может содержать `spark.delete.num-deleted-rows` и `spark.delete.num-copied-rows` (последнее — rows, переписанные COW; в MOR `0`).

### `update`

```sql
update prod.db.table
set c1 = 'update_c1', c2 = 'update_c2'
where ts >= '2020-05-01 00:00:00' and ts < '2020-06-01 00:00:00';

update prod.db.all_events
set session_time = 0, ignored = true
where session_time < (select min(session_time) from prod.db.good_events);

update prod.db.orders as t1
set order_status = 'returned'
where exists (select oid from prod.db.returned_orders where t1.oid = oid);
```

Для более сложных row-level updates по incoming data используйте `merge into`.

Spark 4.2+ может записывать `spark.update.num-updated-rows` и `spark.update.num-copied-rows`.

## Запись в branches

Branch должен существовать заранее; write operation branch автоматически не создаёт. См. [[spark-ddl#Branching и Tagging DDL]]. При записи validation использует current table schema.

### SQL

Branch указывается идентификатором `branch_<name>`. В WAP можно использовать `spark.wap.branch`, но одновременно branch identifier и WAP branch задавать нельзя.

```sql
insert into prod.db.table.branch_audit values (1, 'a'), (2, 'b');

merge into prod.db.table.branch_audit t
using (select ...) s
on t.id = s.id
when ...;

update prod.db.table.branch_audit as t1
set val = 'c';

delete from prod.db.table.branch_audit where id = 2;

set spark.wap.branch = audit-branch;
insert into prod.db.table values (3, 'c');
```

### DataFrames

```scala
val data: DataFrame = ...
data.writeTo("prod.db.table.branch_audit").append()
```

```scala
val data: DataFrame = ...
data.writeTo("prod.db.table.branch_audit").overwritePartitions()
```

## Запись через DataFrames

`DataFrameWriterV2` рекомендуется, потому что:

- поддерживает CTAS, RTAS, overwrite by filter;
- всегда сопоставляет columns по имени;
- поддерживает hidden partition expressions в `partitionedBy`;
- overwrite semantics явно задаются dynamic mode или filter;
- операции соответствуют SQL:
  - `df.writeTo(t).create()` → CTAS;
  - `replace()` → RTAS;
  - `append()` → `insert into`;
  - `overwritePartitions()` → dynamic `insert overwrite`.

V1 `write` поддерживается, но не рекомендуется.

> [!danger]
> При V1 API используйте `saveAsTable` или `insertInto`, чтобы таблица загружалась через catalog. `format("iceberg")` создаёт isolated table reference, которая не будет автоматически refresh таблицы, уже используемые queries.

### Append

```scala
val data: DataFrame = ...
data.writeTo("prod.db.table").append()
```

### Overwrite

Dynamic:

```scala
val data: DataFrame = ...
data.writeTo("prod.db.table").overwritePartitions()
```

Explicit filter:

```scala
data.writeTo("prod.db.table").overwrite($"level" === "INFO")
```

### Создание таблиц

```scala
val data: DataFrame = ...
data.writeTo("prod.db.table").create()
```

При `SparkSessionCatalog`:

```scala
val data: DataFrame = ...
data.writeTo("db.table").using("iceberg").create()
```

Конфигурация create/replace:

```scala
data.writeTo("prod.db.table")
    .tableProperty("write.format.default", "orc")
    .partitionedBy($"level", days($"ts"))
    .createOrReplace()
```

Location:

```scala
data.writeTo("prod.db.table")
    .tableProperty("location", "/path/to/location")
    .createOrReplace()
```

### Merge через DataFrame

Spark 4.0+:

```scala
val source: DataFrame = ...
source.mergeInto("target", $"source.id" === $"target.id")
    .whenMatched($"target.id" === 1)
    .updateAll()
    .whenMatched($"target.id" === 2)
    .delete()
    .whenNotMatched()
    .insertAll()
    .whenNotMatchedBySource($"target.id" === 3)
    .update(Map("status" -> lit("invalid")))
    .merge()
```

### Schema merge

Iceberg может автоматически разрешать schema mismatch:

- source содержит новую колонку → она добавляется target table, а существующим rows назначается `null`;
- target содержит колонку, которой нет в source → при insert записывается `null`, при update existing value не меняется.

Table должна разрешать изменение schema:

```sql
alter table prod.db.sample set tblproperties (
  'write.spark.accept-any-schema'='true'
);
```

Writer должен включить `mergeSchema`:

```scala
data.writeTo("prod.db.sample").option("mergeSchema","true").append()
```

## Режимы распределения при записи

Default Spark writers Iceberg требуют, чтобы data внутри каждого Spark task были clustered по partition values. Начиная с Iceberg 1.2.0 default `write.distribution-mode=hash` просит Spark заранее распределять данные. До Spark 3.5 CTAS/RTAS не учитывают distribution mode.

Пример:

```sql
create table prod.db.sample (
    id bigint,
    data string,
    category string,
    ts timestamp)
using iceberg
partitioned by (days(ts), category);
```

При `hash` данные автоматически распределяются по `days(ts), category`, поэтому вручную sort не нужен:

```sql
insert into prod.db.sample
select id, data, category, ts from another_table;
```

Режимы:

- **`none`** — legacy default. Spark автоматически не выполняет shuffle/sort; данные нужно вручную sort по partition values внутри task или глобально. Global sort минимизирует число files. Альтернатива — fanout writer, но он держит все file handles открытыми до конца task.
- **`hash`** — текущий default. Spark выполняет hash exchange по partition value. AQE может дополнительно split/coalesce tasks.
- **`range`** — двухстадийный, дороже `hash`: сначала sample по partition/sort columns, затем range exchange. Каждый task получает эксклюзивный диапазон, данные clustered по partition и globally sorted. Может улучшить reads по sorted columns. Используется default, если у таблицы задан sort order.

## Управление размером файлов

Spark не может записать файл больше Spark task; один file не пересекает Iceberg partition boundary. Поэтому Iceberg roll over при `write.target-file-size-bytes` сработает только если task достаточно большой.

Размер файла на disk обычно значительно меньше Spark task, поскольку disk representation columnar/compressed, а Spark shuffle data — row-based и с другим compression ratio. Например, 100 MB task может создать существенно меньший file; если task пишет несколько Iceberg partitions, files будут ещё меньше.

Контролировать распределение данных по tasks можно через [[#Режимы распределения при записи|distribution mode]] или manual repartition.

При distribution mode != `none` Adaptive Query Execution управляет coalescing/splitting tasks, пытаясь приблизиться к `spark.sql.adaptive.advisoryPartitionSizeInBytes`. Это **shuffle input size**, а не target disk file size, поэтому обычно advisory value должен быть больше `write.target-file-size-bytes`. Точное соотношение зависит от данных и compression.
