---
title: "Spark — запросы"
tags: [apache-iceberg, spark, queries, time-travel, metadata-tables]
source_project: apache/iceberg
source_file: docs/docs/spark-queries.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/spark-queries.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Spark Queries

Сначала настройте [[spark-configuration|Spark catalogs]]. Iceberg использует Apache Spark DataSourceV2 API.

## SQL-запросы

Идентификатор Spark table включает [[spark-configuration#Использование catalogs|catalog name]]:

```sql
select * from prod.db.table; -- catalog: prod, namespace: db, table: table
```

Metadata tables (`history`, `snapshots` и др.) используют имя Iceberg table как namespace. Например `files`:

```sql
select * from prod.db.table.files;
```

Пример результата:

| content | file_path | file_format | spec_id | partition | record_count | file_size_in_bytes | column_sizes | value_counts | null_value_counts | nan_value_counts | lower_bounds | upper_bounds | key_metadata | split_offsets | equality_ids | sort_order_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | `s3:/.../00000-3-....parquet` | PARQUET | 0 | `{1999-01-01, 01}` | 1 | 597 | `[1 -> 90, 2 -> 62]` | `[1 -> 1, 2 -> 1]` | `[1 -> 0, 2 -> 0]` | `[]` | `[1 -> , 2 -> c]` | `[1 -> , 2 -> c]` | null | `[4]` | null | null |

### Spark SQL functions

Iceberg добавляет SQL functions в каждый Iceberg catalog для просмотра результата partition transforms и построения filters, совпадающих с partition transforms. Functions доступны только через `SparkCatalog`, а не built-in catalog.

> [!note]
> Spark до 4.2.0 не поддерживает `V2Function` в session catalog. Вызовы вроде `spark_catalog.system.bucket(...)` не работают даже при `SparkSessionCatalog`. Используйте отдельный `org.apache.iceberg.spark.SparkCatalog`.

Namespace — `system`:

```sql
select system.iceberg_version();

select system.bucket(16, id), system.days(ts)
from prod.db.table;
```

Явный catalog:

```sql
select prod.system.bucket(16, id)
from prod.db.table;
```

> [!info]
> В `partitioned by` используются singular transforms `year(ts)`, `month(ts)`. SQL functions имеют plural names `system.years(ts)`, `system.months(ts)`.

| Function | Input types | Return | Example |
| --- | --- | --- | --- |
| `system.iceberg_version()` | none | string | `select system.iceberg_version();` |
| `system.bucket(numBuckets, col)` | date, tinyint, smallint, int, bigint, timestamp, timestamp_ntz, decimal, string, binary | int | `select system.bucket(16, id) from prod.db.table;` |
| `system.years(col)` | date, timestamp, timestamp_ntz | int | `select system.years(ts) from prod.db.table;` |
| `system.months(col)` | date, timestamp, timestamp_ntz | int | `select system.months(ts) from prod.db.table;` |
| `system.days(col)` | date, timestamp, timestamp_ntz | date | `select * from prod.db.table where system.days(ts) = date('2025-03-01');` |
| `system.hours(col)` | timestamp, timestamp_ntz | int | `select system.hours(ts) from prod.db.table;` |
| `system.truncate(width, col)` | tinyint, smallint, int, bigint, decimal, string, binary | тип `col` | `select system.truncate(4, data) from prod.db.table;` |

Все transform functions возвращают `null` для `null` input.

`years`, `months`, `days`, `hours` возвращают **Iceberg transform values**, а не обычные extracted calendar fields. `years` — число лет от 1970-01-01, `months` — месяцев от 1970-01, `hours` — часов от epoch. `days` возвращает `date`: для date тот же value, для timestamp отбрасывается time.

Для numeric input `truncate(width,col)` округляет вниз до ближайшего multiple `width`; для string/binary оставляет первые `width` символов/bytes.

### Time travel через SQL

Spark поддерживает `timestamp as of` и `version as of`. Version может быть long snapshot ID либо string branch/tag.

> [!info]
> Если branch/tag имеет имя, совпадающее со snapshot ID, при `version as of '1'` приоритет будет у snapshot ID `1`, а не у reference с таким именем. Используйте names вроде `snapshot-1`.

```sql
select * from prod.db.table timestamp as of '1986-10-26 01:21:00';
select * from prod.db.table version as of 10963874102873;
select * from prod.db.table version as of 'audit-branch';
select * from prod.db.table version as of 'historical-snapshot';
```

Также поддерживаются SQL-standard forms:

```sql
select * from prod.db.table for system_time as of '1986-10-26 01:21:00';
select * from prod.db.table for system_version as of 10963874102873;
select * from prod.db.table for system_version as of 'audit-branch';
select * from prod.db.table for system_version as of 'historical-snapshot';
```

Unix timestamp в seconds:

```sql
select * from prod.db.table timestamp as of 499162860;
select * from prod.db.table for system_time as of 499162860;
```

Branch/tag можно адресовать synthetic identifier:

```sql
select * from prod.db.table.`branch_audit-branch`;
select * from prod.db.table.`tag_historical-snapshot`;
```

Names с `-` требуют backticks. Synthetic branch/tag identifier нельзя комбинировать с `version as of`.

#### Выбор schema в time travel

Разные формы используют разные schema:

- конкретный snapshot ID или timestamp → **snapshot schema**;
- branch → **current table schema**;
- tag → **schema snapshot, на который указывает tag**.

```sql
select * from prod.db.table timestamp as of '1986-10-26 01:21:00'; -- snapshot schema
select * from prod.db.table version as of 10963874102873;          -- snapshot schema
select * from prod.db.table version as of 'audit-branch';          -- table schema
select * from prod.db.table.`branch_audit-branch`;                 -- table schema
select * from prod.db.table version as of 'historical-snapshot';   -- snapshot schema
select * from prod.db.table.`tag_historical-snapshot`;             -- snapshot schema
```

Пример эволюции:

```sql
create table prod.db.orders (
  id bigint,
  status string
) using iceberg;

insert into prod.db.orders values (1, 'NEW'), (2, 'PAID');

alter table prod.db.orders add column total double;
insert into prod.db.orders values (3, 'PAID', 100.0);
```

Пусть initial snapshot S1 имеет ID 101. Snapshot/time travel возвращает только `(id,status)`:

```sql
select * from prod.db.orders version as of 101;
select * from prod.db.orders timestamp as of '2025-01-01 10:00:00';
```

Создадим branch/tag на S1:

```sql
alter table prod.db.orders create branch audit_branch as of version 101;
alter table prod.db.orders create tag first_load as of version 101;
```

Branch использует current table schema `(id,status,total)`; для исторических rows `total=null`:

```sql
select * from prod.db.orders version as of 'audit_branch';
select * from prod.db.orders.`branch_audit_branch`;
```

Tag использует S1 schema и возвращает только `(id,status)`:

```sql
select * from prod.db.orders version as of 'first_load';
select * from prod.db.orders.`tag_first_load`;
```

## DataFrame queries

```scala
val df = spark.table("prod.db.table")
```

### Catalogs с DataFrameReader

`spark.read.format("iceberg").load(table)` и `spark.table(table)` разрешают identifiers в следующем порядке приоритета:

1. `file:///path/to/table` — HadoopTable по path;
2. `tablename` — `currentCatalog.currentNamespace.tablename`;
3. `catalog.tablename` — table из указанного catalog;
4. `namespace.tablename` — namespace current catalog;
5. `catalog.namespace.tablename`;
6. `namespace1.namespace2.tablename` — nested namespace current catalog.

Matching catalog имеет приоритет над namespace resolution.

### Time travel через DataFrame

Read options:

- `snapshot-id` — конкретный snapshot;
- `as-of-timestamp` — current snapshot на момент, ms;
- `branch` — head branch; нельзя сочетать с `as-of-timestamp`;
- `tag` — snapshot tag; также нельзя сочетать с `as-of-timestamp`.

```scala
spark.read
    .option("as-of-timestamp", "499162860000")
    .format("iceberg")
    .load("path/to/table")
```

```scala
spark.read
    .option("snapshot-id", 10963874102873L)
    .format("iceberg")
    .load("path/to/table")
```

```scala
spark.read
    .option(SparkReadOptions.TAG, "historical-snapshot")
    .format("iceberg")
    .load("path/to/table")
```

```scala
spark.read
    .option(SparkReadOptions.BRANCH, "audit-branch")
    .format("iceberg")
    .load("path/to/table")
```

### Incremental read

- `start-snapshot-id` — exclusive;
- `end-snapshot-id` — inclusive; default current.

```scala
spark.read
  .format("iceberg")
  .option("start-snapshot-id", "10963874102873")
  .option("end-snapshot-id", "63874143573109")
  .load("path/to/table")
```

> [!info]
> Incremental read сейчас возвращает только данные `append` operations; `replace`, `overwrite`, `delete` не поддерживаются. Работает с format v1/v2, но не имеет SQL syntax.

## Просмотр metadata tables

Iceberg metadata tables позволяют исследовать history, snapshots, files и другую metadata. Имя строится добавлением metadata-table name к имени таблицы: `db.table.history`.

### History

```sql
select * from prod.db.table.history;
```

| made_current_at | snapshot_id | parent_id | is_current_ancestor |
| --- | --- | --- | --- |
| 2019-02-08 03:29:51.215 | 5781947118336215154 | null | true |
| 2019-02-08 03:47:55.948 | 5179299526185056830 | 5781947118336215154 | true |
| 2019-02-09 16:24:30.13 | 296410040247533544 | 5179299526185056830 | false |
| 2019-02-09 16:32:47.336 | 2999875608062437330 | 5179299526185056830 | true |
| 2019-02-09 19:42:03.919 | 8924558786060583479 | 2999875608062437330 | true |
| 2019-02-09 19:49:16.343 | 6536733823181975045 | 8924558786060583479 | true |

Row с `is_current_ancestor=false` — commit, который был rollback/отошёл от current lineage.

### Metadata Log Entries

```sql
select * from prod.db.table.metadata_log_entries;
```

| timestamp | file | latest_snapshot_id | latest_schema_id | latest_sequence_number |
| --- | --- | --- | --- | --- |
| 2022-07-28 10:43:52.93 | `s3://.../00000-....metadata.json` | null | null | null |
| 2022-07-28 10:43:57.487 | `s3://.../00001-....metadata.json` | 170260833677645300 | 0 | 1 |
| 2022-07-28 10:43:58.25 | `s3://.../00002-....metadata.json` | 958906493976709774 | 0 | 2 |

### Snapshots

```sql
select * from prod.db.table.snapshots;
```

| committed_at | snapshot_id | parent_id | operation | manifest_list | summary |
| --- | --- | --- | --- | --- | --- |
| 2019-02-08 03:29:51.215 | 57897183625154 | null | append | `s3://.../snap-57897183625154-1.avro` | `{added-records -> 2478404, ...}` |

Можно join history и snapshots, чтобы увидеть writer application:

```sql
select
    h.made_current_at,
    s.operation,
    h.snapshot_id,
    h.is_current_ancestor,
    s.summary['spark.app.id']
from prod.db.table.history h
join prod.db.table.snapshots s
  on h.snapshot_id = s.snapshot_id
order by made_current_at;
```

### Entries

Current manifest entries для data/delete files:

```sql
select * from prod.db.table.entries;
```

Основные columns:

- `status` — addition/deletion state;
- `snapshot_id` — snapshot, где file добавлен/удалён;
- `sequence_number` — ordering changes;
- `file_sequence_number` — когда file был добавлен;
- `data_file` — struct metadata data/delete file;
- `readable_metrics` — human-readable map поколоночных metrics из `data_file`.

Пример:

| status | snapshot_id | sequence_number | file_sequence_number | data_file | readable_metrics |
| --- | --- | --- | --- | --- | --- |
| 2 | 57897183625154 | 0 | 0 | `{"content":0,"file_path":"s3:/...parquet",...}` | `{"c1":{"column_size":103,"value_count":15,...}}` |

### Files

```sql
select * from prod.db.table.files;
```

| content | file_path | file_format | spec_id | record_count | file_size_in_bytes | column_sizes | value_counts | null_value_counts | nan_value_counts | lower_bounds | upper_bounds | key_metadata | split_offsets | equality_ids | sort_order_id | readable_metrics |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | `s3:/.../data/00042-...parquet` | PARQUET | 0 | 1 | 652 | `{1:52,2:48}` | `{1:1,2:1}` | `{1:0,2:0}` | `{}` | `{1:,2:d}` | `{1:,2:d}` | null | `[4]` | null | 0 | `{...}` |
| 1 | `s3:/.../00081-...-deletes.parquet` | PARQUET | 0 | 1 | 1560 | `{...}` | `{...}` | `{...}` | `{}` | `{...}` | `{...}` | null | `[4]` | null | null | `{...}` |
| 2 | `s3:/.../00047-...parquet` | PARQUET | 0 | 126506 | 28613985 | `{...}` | `{...}` | `{...}` | `{}` | `{...}` | `{...}` | null | null | `[1]` | 0 | `{...}` |

`content`:

- `0` — Data;
- `1` — Position Deletes;
- `2` — Equality Deletes.

Только current data/delete files: `data_files`, `delete_files`. Across all tracked snapshots: `all_files`, `all_data_files`, `all_delete_files`.

### Manifests

```sql
select * from prod.db.table.manifests;
```

| content | path | length | partition_spec_id | added_snapshot_id | added_data_files_count | existing_data_files_count | deleted_data_files_count | added_delete_files_count | existing_delete_files_count | deleted_delete_files_count | partition_summaries |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | `s3://.../metadata/...-m0.avro` | 4479 | 0 | 6668963634911763636 | 8 | 0 | 0 | 0 | 0 | 0 | `[[false,null,2019-05-13,2019-05-15]]` |

`partition_summaries` соответствует `field_summary` manifest list в порядке:

1. `contains_null`;
2. `contains_nan`;
3. `lower_bound`;
4. `upper_bound`.

`contains_nan=null` означает, что информация отсутствует; типичный случай — v1 table, где поле не заполнялось.

### Partitions

```sql
select * from prod.db.table.partitions;
```

| partition | spec_id | record_count | file_count | total_data_file_size_in_bytes | position_delete_record_count | position_delete_file_count | equality_delete_record_count | equality_delete_file_count | last_updated_at(μs) | last_updated_snapshot_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `{20211001, 11}` | 0 | 1 | 1 | 100 | 2 | 1 | 0 | 0 | 1633086034192000 | 9205185327307503337 |
| `{20211002, 11}` | 0 | 4 | 3 | 500 | 1 | 1 | 0 | 0 | 1633172537358000 | 867027598972211003 |
| `{20211001, 10}` | 0 | 7 | 4 | 700 | 0 | 0 | 0 | 0 | 1633082598716000 | 3280122546965981531 |
| `{20211002, 10}` | 0 | 3 | 2 | 400 | 0 | 0 | 1 | 1 | 1633169159489000 | 6941468797545315876 |

Unpartitioned table не содержит `partition`/`spec_id` fields. Metadata table показывает partitions с data **или delete files** current snapshot; deletes не применяются к record counts, поэтому partition может отображаться даже если все logical rows помечены delete files.

### Positional Delete Files

```sql
select * from prod.db.table.position_deletes;
```

| file_path | pos | row | partition | spec_id | delete_file_path |
| --- | --- | --- | --- | --- | --- |
| `s3:/.../data.parquet` | 1 | 0 | `{20211001, 11}` | 0 | `s3:/.../deletes.parquet` |

### All Metadata Tables

`all_*` tables являются union metadata across all tracked snapshots.

> [!danger]
> `all_*` могут возвращать несколько rows для одного data/manifest file, потому что один metadata file может входить в несколько snapshots.

#### All Data Files

```sql
select * from prod.db.table.all_data_files;
```

Возвращает file metadata всех data files из всех tracked snapshots, включая partition, record/file sizes, column/value/null/nan counts, bounds, split offsets, equality IDs, sort order и `readable_metrics`.

#### All Delete Files

```sql
select * from prod.db.table.all_delete_files;
```

Возвращает position/equality delete files из всех tracked snapshots с тем же набором file-level metadata.

#### All Entries

```sql
select * from prod.db.table.all_entries;
```

Возвращает manifest entries для data/delete files across all snapshots: `status`, `snapshot_id`, sequence numbers, `data_file`, `readable_metrics`.

#### All Manifests

```sql
select * from prod.db.table.all_manifests;
```

Помимо обычных manifest fields включает `reference_snapshot_id`, показывающий snapshot, через который manifest попал в результат. `partition_summaries` имеет тот же порядок fields: null/nan flags и lower/upper bounds.

### References

```sql
select * from prod.db.table.refs;
```

| name | type | snapshot_id | max_reference_age_in_ms | min_snapshots_to_keep | max_snapshot_age_in_ms |
| --- | --- | --- | --- | --- | --- |
| main | BRANCH | 4686954189838128572 | 10 | 20 | 30 |
| testTag | TAG | 4686954189838128572 | 10 | null | null |

### Metadata через DataFrame

```scala
spark.read.format("iceberg").load("db.table.files")
spark.read.format("iceberg").load("hdfs://nn:8020/path/to/table#files")
```

### Time travel metadata tables

```sql
select * from prod.db.table.manifests timestamp as of '2021-09-20 08:00:00';
select * from prod.db.table.partitions version as of 10963874102873;
```

DataFrame:

```scala
spark.read
  .format("iceberg")
  .option("snapshot-id", 10963874102873L)
  .load("db.table.files")
```
