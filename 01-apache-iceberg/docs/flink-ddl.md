---
title: "Flink DDL"
tags: [apache-iceberg, flink, ddl]
source_project: apache/iceberg
source_file: docs/docs/flink-ddl.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/flink-ddl.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# DDL commands

## `create catalog`

### Hive catalog

```sql
create catalog hive_catalog with (
  'type'='iceberg',
  'catalog-type'='hive',
  'uri'='thrift://localhost:9083',
  'clients'='5',
  'property-version'='1',
  'warehouse'='hdfs://nn:8020/warehouse/path'
);
```

Hive-specific properties:

- `uri` — HMS Thrift URI, required;
- `clients` — HMS client pool size, default 2;
- `warehouse` — Hive warehouse location; укажите, если не задан `hive-conf-dir` и в classpath нет корректного `hive-site.xml`;
- `hive-conf-dir` — каталог с `hive-site.xml`; если одновременно задан `warehouse`, он override `hive.metastore.warehouse.dir`;
- `hadoop-conf-dir` — каталог с `core-site.xml` и `hdfs-site.xml`.

> [!warning] Ограничение Hive Catalog
> HMS валидирует изменения schema **позиционно** (`hive.metastore.disallow.incompatible.col.type.changes`, default `true`). Drop non-last column или reorder могут упасть независимо от engine.
>
> Workaround: `hive.metastore.disallow.incompatible.col.type.changes=false` на HMS server или в embedded Hive catalog config. После отключения Hive engine может неверно читать mismatch schema из HMS, но Iceberg-aware engines продолжают читать schema из Iceberg metadata.

### Hadoop catalog

```sql
create catalog hadoop_catalog with (
  'type'='iceberg',
  'catalog-type'='hadoop',
  'warehouse'='hdfs://nn:8020/warehouse/path',
  'property-version'='1'
);
```

`warehouse` обязателен.

```sql
use catalog hadoop_catalog;
```

### REST catalog

```sql
create catalog rest_catalog with (
  'type'='iceberg',
  'catalog-type'='rest',
  'uri'='https://localhost/'
);
```

Properties: `uri` required; `credential` и `token` optional.

### Custom catalog

```sql
create catalog my_catalog with (
  'type'='iceberg',
  'catalog-impl'='com.my.custom.CatalogImpl',
  'my-additional-catalog-config'='my-value'
);
```

### Через YAML

```yaml
catalogs:
  - name: my_catalog
    type: iceberg
    catalog-type: hadoop
    warehouse: hdfs://nn:8020/warehouse/path
```

### Через init SQL

```sql
create catalog hive_catalog with (
  'type'='iceberg',
  'catalog-type'='hive',
  'uri'='thrift://localhost:9083',
  'warehouse'='hdfs://nn:8020/warehouse/path'
);

use catalog hive_catalog;
```

```bash
/path/to/bin/sql-client.sh -i /path/to/init.sql
```

## `create database`

По умолчанию используется `default`. Отдельная database:

```sql
create database iceberg_db;
use iceberg_db;
```

## `create table`

```sql
create table `hive_catalog`.`default`.`sample` (
    id bigint comment 'unique id',
    data string not null
) with ('format-version'='2');
```

Поддерживаются common Flink clauses:

- `partitioned by (column1, column2, ...)`; hidden partitioning во Flink DDL пока отсутствует;
- `comment '...'`;
- `with ('key'='value', ...)` → Iceberg table properties.

Custom location:

```sql
create table `hive_catalog`.`default`.`sample` (
    id bigint comment 'unique id',
    data string not null
) with (
    'format-version'='2',
    'location'='hdfs://nn:8020/custom-path'
);
```

Computed columns и watermark definition для Iceberg table create пока не поддерживаются.

### Primary key

PK должен быть unique и non-null и требуется для [[flink-writes#UPSERT|UPSERT]]. Constraint объявляется `not enforced`:

```sql
create table `hive_catalog`.`default`.`sample` (
    id bigint comment 'unique id',
    data string not null,
    primary key(`id`) not enforced
) with ('format-version'='2');
```

### `partitioned by`

```sql
create table `hive_catalog`.`default`.`sample` (
    id bigint comment 'unique id',
    data string not null
)
partitioned by (data)
with ('format-version'='2');
```

Iceberg hidden partitioning существует, но Flink DDL не умеет partition by function, поэтому создать hidden partition transform через него нельзя.

## `create table like`

```sql
create table `hive_catalog`.`default`.`sample` (
    id bigint comment 'unique id',
    data string
);

create table `hive_catalog`.`default`.`sample_like`
like `hive_catalog`.`default`.`sample`;
```

Копируются schema, partitioning и table properties.

## `alter table`

Поддерживаются properties и columns. Partition fields, watermarks и computed columns менять нельзя.

### Set / reset

```sql
alter table `hive_catalog`.`default`.`sample` set ('write.format.default'='avro');
alter table `hive_catalog`.`default`.`sample` reset ('write.format.default');
```

### Add

```sql
alter table `hive_catalog`.`default`.`sample`
add (col1 string comment 'new column', col2 bigint after id);
```

Identifier fields через primary key; все columns PK должны быть `not null`:

```sql
alter table `hive_catalog`.`default`.`sample`
add (primary key (id) not enforced);
```

### Drop

```sql
alter table `hive_catalog`.`default`.`sample` drop (col1, col2);
```

### Rename

```sql
alter table `hive_catalog`.`default`.`sample` rename col1 to col3;
```

### Modify

Поддерживаются safe widening (`int` → `bigint`), position, comment, required → optional и replace primary key. Optional → required запрещён.

```sql
alter table `hive_catalog`.`default`.`sample` modify (id bigint);
alter table `hive_catalog`.`default`.`sample` modify (col3 string first);
alter table `hive_catalog`.`default`.`sample` modify (col3 string comment 'updated comment');
alter table `hive_catalog`.`default`.`sample` modify (primary key (id, data) not enforced);
```

## Rename table

```sql
alter table `hive_catalog`.`default`.`sample`
rename to `hive_catalog`.`default`.`new_sample`;
```

## `drop table`

```sql
drop table `hive_catalog`.`default`.`sample`;
```
