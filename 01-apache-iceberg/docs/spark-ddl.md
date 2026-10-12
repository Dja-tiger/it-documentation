---
title: "Spark DDL"
tags: [apache-iceberg, spark, ddl]
source_project: apache/iceberg
source_file: docs/docs/spark-ddl.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/spark-ddl.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Spark DDL

Чтобы использовать Iceberg в Spark, сначала настройте [[spark-configuration|Spark catalogs]]. Iceberg использует Apache Spark DataSourceV2 API для data source и catalog implementations.

## `create table`

Spark 3 может создавать таблицы в любом Iceberg catalog через `using iceberg`:

```sql
create table prod.db.sample (
    id bigint not null comment 'unique id',
    data string)
using iceberg;
```

Iceberg преобразует Spark column types в соответствующие Iceberg types. Mapping см. в [[spark-getting-started#Spark type → Iceberg type]].

Команды create, включая CTAS/RTAS, поддерживают стандартные Spark clauses:

- `partitioned by (partition-expressions)` — настройка partitioning;
- `location '(fully-qualified-uri)'` — location таблицы;
- `comment 'table documentation'` — описание;
- `tblproperties ('key'='value', ...)` — [[configuration|table properties]].

Default format можно задать через `using`. Это поддерживается только `SparkCatalog`, поскольку built-in catalog Spark обрабатывает `using` иначе.

`create table ... like ...` не поддерживается.

### `partitioned by`

```sql
create table prod.db.sample (
    id bigint,
    data string,
    category string)
using iceberg
partitioned by (category);
```

Поддерживаются transform expressions для [[partitioning|hidden partitions]]:

```sql
create table prod.db.sample (
    id bigint,
    data string,
    category string,
    ts timestamp)
using iceberg
partitioned by (bucket(16, id), days(ts), category);
```

Transforms:

- `year(ts)` — year;
- `month(ts)` — month;
- `day(ts)` или `date(ts)` — date partitioning;
- `hour(ts)` или `date_hour(ts)` — date + hour;
- `bucket(N, col)` — hash modulo N buckets;
- `truncate(L, col)` — усечение до L:
  - strings — первые L символов;
  - integers/longs — bins: `truncate(10, i)` → 0, 10, 20, 30, ...

Legacy syntax `years`, `months`, `days`, `hours` также поддерживается. Эти transforms доступны и как Spark SQL functions в namespace `system`; см. [[spark-queries#Spark SQL functions]].

## `create table ... as select`

CTAS атомарен при `SparkCatalog`; с `SparkSessionCatalog` поддерживается, но **не атомарен**.

```sql
create table prod.db.sample
using iceberg
as select ...;
```

Новая таблица не наследует partition spec и properties source table автоматически. Их необходимо объявить:

```sql
create table prod.db.sample
using iceberg
partitioned by (part)
tblproperties ('key'='value')
as select ...;
```

## `replace table ... as select`

RTAS также атомарен с `SparkCatalog`, но не с `SparkSessionCatalog`. Atomic replacement создаёт новый snapshot с результатом `select`, сохраняя историю таблицы.

```sql
replace table prod.db.sample
using iceberg
as select ...;
```

```sql
replace table prod.db.sample
using iceberg
partitioned by (part)
tblproperties ('key'='value')
as select ...;
```

```sql
create or replace table prod.db.sample
using iceberg
as select ...;
```

Schema и partition spec будут заменены, если изменились. Чтобы заменить данные без изменения schema/partitioning, используйте `insert overwrite`. Новые properties объединяются с существующими: заданные обновляются, остальные сохраняются.

## `drop table`

Поведение изменилось начиная с Iceberg 0.14. До 0.14 `drop table` удалял и catalog entry, и содержимое таблицы. Начиная с 0.14 обычный `drop table` удаляет только регистрацию в catalog; для физического удаления используется `purge`.

```sql
drop table prod.db.sample;
```

```sql
drop table prod.db.sample purge;
```

## `alter table`

Spark 3 поддерживает:

- rename table;
- set/unset properties;
- add/drop/rename columns;
- add/drop/rename nested fields;
- reorder top-level и nested struct fields;
- widening `int`, `float`, `decimal`;
- перевод required column в optional.

Iceberg SQL extensions добавляют partition evolution и write order.

> [!warning] Ограничение Hive Catalog
> Hive Metastore проверяет schema changes **позиционно** через `hive.metastore.disallow.incompatible.col.type.changes` (default `true`). Изменения, сдвигающие positions, могут завершиться ошибкой: `add column ... first/after`, reorder через `alter column`, `drop column` не последней колонки.
>
> Workaround: `hive.metastore.disallow.incompatible.col.type.changes=false`. Для remote HMS — в server `hive-site.xml`; для embedded HMS — `--conf spark.hadoop.hive.metastore.disallow.incompatible.col.type.changes=false`.
>
> Цена workaround: Hive engine может некорректно читать schema из HMS. Iceberg-aware engines (Spark/Flink/Trino и др.) продолжают работать, поскольку читают schema из Iceberg metadata.

### `alter table ... rename to`

```sql
alter table prod.db.sample rename to prod.db.new_name;
```

### `alter table ... set tblproperties`

```sql
alter table prod.db.sample set tblproperties (
    'read.split.target-size'='268435456'
);
```

Удаление property:

```sql
alter table prod.db.sample unset tblproperties ('read.split.target-size');
```

Table comment:

```sql
alter table prod.db.sample set tblproperties (
    'comment' = 'A table comment.'
);
```

### `alter table ... add column`

```sql
alter table prod.db.sample
add columns (
    new_column string comment 'new_column docs'
);
```

Nested struct:

```sql
alter table prod.db.sample
add column point struct<x: double, y: double>;

alter table prod.db.sample
add column point.z double;
```

Array of struct:

```sql
alter table prod.db.sample
add column points array<struct<x: double, y: double>>;

alter table prod.db.sample
add column points.element.z double;
```

Map:

```sql
alter table prod.db.sample
add column points map<struct<x: int>, struct<a: int>>;

alter table prod.db.sample
add column points.value.b int;
```

Добавлять fields в map key нельзя; обновляются только values.

Позиция:

```sql
alter table prod.db.sample
add column new_column bigint after other_column;
```

```sql
alter table prod.db.sample
add column nested.new_column bigint first;
```

Для Hive catalog `first`/`after` может упасть из-за HMS positional validation.

### `alter table ... rename column`

```sql
alter table prod.db.sample rename column data to payload;
alter table prod.db.sample rename column location.lat to latitude;
```

Nested rename изменяет только leaf field: `location.lat` становится `location.latitude`.

### `alter table ... alter column`

Используется для widening type, optionality, comments и reorder.

Безопасные widening conversions:

- `int` → `bigint`;
- `float` → `double`;
- `decimal(P,S)` → `decimal(P2,S)` при P2 > P; scale менять нельзя.

```sql
alter table prod.db.sample alter column measurement type double;
```

Comments:

```sql
alter table prod.db.sample alter column measurement type double comment 'unit is bytes per second';
alter table prod.db.sample alter column measurement comment 'unit is kilobytes per second';
```

Reorder:

```sql
alter table prod.db.sample alter column col first;
```

```sql
alter table prod.db.sample alter column nested.col after other_col;
```

Required → optional:

```sql
alter table prod.db.sample alter column id drop not null;
```

> [!info]
> Nullable → non-nullable через `set not null` не разрешено: Iceberg не может гарантировать отсутствие исторических null.

`alter column` не изменяет состав `struct`; для этого используйте add/drop nested fields.

### `alter table ... drop column`

```sql
alter table prod.db.sample drop column id;
alter table prod.db.sample drop column point.z;
```

Для Hive catalog drop не-last column может конфликтовать с HMS positional validation.

## SQL extensions для `alter table`

### `alter table ... add partition field`

```sql
alter table prod.db.sample add partition field catalog;
alter table prod.db.sample add partition field bucket(16, id);
alter table prod.db.sample add partition field truncate(4, data);
alter table prod.db.sample add partition field year(ts);
alter table prod.db.sample add partition field bucket(16, id) as shard;
```

Добавление partition field — metadata-only operation. Existing data не переписываются; новые data используют новую spec, старые остаются в прежнем layout. В metadata tables старые files имеют `null` для нового field.

Dynamic partition overwrite меняет semantics при изменении partitioning, потому что partitions определяются неявно. Для explicit overwrite используйте `DataFrameWriterV2`.

> [!note]
> При переходе с daily на hourly transform не обязательно удалять daily field. Его сохранение поддерживает совместимость существующих metadata queries.

> [!danger]
> При изменении partitioning меняется поведение dynamic overwrite. Например, после перехода days → hours overwrite будет заменять hourly partitions, но больше не day partitions.

### `alter table ... drop partition field`

```sql
alter table prod.db.sample drop partition field catalog;
alter table prod.db.sample drop partition field bucket(16, id);
alter table prod.db.sample drop partition field truncate(4, data);
alter table prod.db.sample drop partition field year(ts);
alter table prod.db.sample drop partition field shard;
```

Column остаётся в table schema. Операция metadata-only; старые data остаются в old layout.

> [!danger]
> Drop partition field меняет schema metadata tables (`files` и др.) и может сломать существующие metadata queries или изменить их результат.

### `alter table ... replace partition field`

```sql
alter table prod.db.sample replace partition field ts_day with day(ts);
alter table prod.db.sample replace partition field ts_day with day(ts) as day_of_ts;
```

### `alter table ... write ordered by`

Sort order применяется некоторыми engines при записи; например Spark `merge into` учитывает table ordering.

```sql
alter table prod.db.sample write ordered by category, id;
alter table prod.db.sample write ordered by category asc, id desc;
alter table prod.db.sample write ordered by category asc nulls last, id desc nulls first;
```

> [!info]
> Write order не гарантирует порядок rows при query; он влияет только на physical write.

Global ordering соответствует `order by`:

```sql
insert into prod.db.sample
select id, data, category, ts from another_table
order by ts, category;
```

Local ordering внутри task:

```sql
alter table prod.db.sample write locally ordered by category, id;
```

Сброс sort order:

```sql
alter table prod.db.sample write unordered;
```

### `alter table ... write distributed by partition`

Запрашивает одного writer на partition; default implementation — hash distribution:

```sql
alter table prod.db.sample write distributed by partition;
```

Можно сочетать с local sort:

```sql
alter table prod.db.sample write distributed by partition locally ordered by category, id;
```

### `alter table ... set identifier fields`

Identifier fields позволяют Flink SQL upsert при наличии соответствующих fields:

```sql
alter table prod.db.sample set identifier fields id;
alter table prod.db.sample set identifier fields id, data;
```

При установке fields должны быть `not null`. Новая команда полностью заменяет предыдущий набор.

### `alter table ... drop identifier fields`

```sql
alter table prod.db.sample drop identifier fields id;
alter table prod.db.sample drop identifier fields id, data;
```

Columns при этом из schema не удаляются.

### Branching и Tagging DDL

#### `alter table ... create branch`

Поддерживаются `if not exists`, `create or replace`, конкретный snapshot и retention.

```sql
alter table prod.db.sample create branch `audit-branch`;
alter table prod.db.sample create branch if not exists `audit-branch`;
alter table prod.db.sample create or replace branch `audit-branch`;
alter table prod.db.sample create branch `audit-branch` as of version 1234;
alter table prod.db.sample create branch `audit-branch`
as of version 1234 retain 30 days
with snapshot retention 3 snapshots 2 days;
```

#### `alter table ... create tag`

```sql
alter table prod.db.sample create tag `historical-tag`;
alter table prod.db.sample create tag if not exists `historical-tag`;
alter table prod.db.sample create or replace tag `historical-tag`;
alter table prod.db.sample create tag `historical-tag` as of version 1234;
alter table prod.db.sample create tag `historical-tag`
as of version 1234 retain 365 days;
```

#### Replace branch/tag

```sql
alter table prod.db.sample replace branch `audit-branch`
as of version 4567 retain 60 days;
```

```sql
alter table prod.db.sample replace tag `historical-tag`
as of version 4567 retain 60 days;
```

#### Drop branch/tag

```sql
alter table prod.db.sample drop branch `audit-branch`;
alter table prod.db.sample drop tag `historical-tag`;
```

## Iceberg views в Spark

Iceberg views — общая representation SQL view, рассчитанная на интерпретацию несколькими query engines. Spark integration поддерживает их начиная с Spark 3.4.

### Создание view

```sql
create view <viewName> as select * from <tableName>;
```

```sql
create view if not exists <viewName> as select * from <tableName>;
```

С comments и aliases:

```sql
create view <viewName> (ID comment 'Unique ID', ZIP comment 'Zipcode')
    comment 'View Comment'
    as select id, zip from <tableName>;
```

### View properties

```sql
create view <viewName>
    tblproperties ('key1' = 'val1', 'key2' = 'val2')
    as select * from <tableName>;
```

```sql
show tblproperties <viewName>;
```

### Custom metadata location

```sql
create view <viewName>
    tblproperties ('location' = '/path/to/custom-location')
as select * from <tableName>;
```

Metadata записываются в указанный location с добавлением `/metadata`, например `/path/to/custom-location/metadata`.

### Drop view

```sql
drop view <viewName>;
drop view if exists <viewName>;
```

### Replace view

```sql
create or replace view <viewName> (updated_id comment 'updated ID')
    tblproperties ('key1' = 'new_val1')
    as select id from <tableName>;
```

### Set/unset properties

```sql
alter view <viewName> set tblproperties ('key1' = 'val1', 'key2' = 'val2');
alter view <viewName> unset tblproperties ('key1', 'key2');
```

### Show views

```sql
show views;
show views in <catalog>;
show views in <namespace>;
show views in <catalog>.<namespace>;
```

### Показать create statement

```sql
show create table <viewName>;
```

### Детали view

```sql
describe [extended] <viewName>;
```
