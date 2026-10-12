---
title: "Flink Connector"
tags: [apache-iceberg, flink, connector]
source_project: apache/iceberg
source_file: docs/docs/flink-connector.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/flink-connector.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Flink Connector

Flink может создать mapping на Iceberg table напрямую без явного создания Iceberg catalog в Flink SQL. Для этого в table options используется `'connector'='iceberg'`.

Команда `create table test (...) with ('connector'='iceberg', ...)` создаёт Flink table в текущем Flink catalog (по умолчанию `GenericInMemoryCatalog`), которая лишь отображается на underlying Iceberg table; Iceberg metadata не управляются текущим Flink catalog.

Catalog properties можно передать через table properties connector; полный список — [[flink-configuration#Catalog configuration]].

## Таблица в Hive catalog

```sql
create table flink_table (
    id bigint,
    data string
) with (
    'connector'='iceberg',
    'catalog-name'='hive_prod',
    'uri'='thrift://localhost:9083',
    'warehouse'='hdfs://nn:8020/path/to/warehouse'
);
```

По умолчанию mapping идёт в `default_database.flink_table` Iceberg catalog.

Mapping на другую underlying table:

```sql
create table flink_table (
    id bigint,
    data string
) with (
    'connector'='iceberg',
    'catalog-name'='hive_prod',
    'catalog-database'='hive_db',
    'catalog-table'='hive_iceberg_table',
    'uri'='thrift://localhost:9083',
    'warehouse'='hdfs://nn:8020/path/to/warehouse'
);
```

> [!info]
> Underlying catalog database (`hive_db`) автоматически создаётся при первой записи, если ещё не существует.

## Таблица в Hadoop catalog

```sql
create table flink_table (
    id bigint,
    data string
) with (
    'connector'='iceberg',
    'catalog-name'='hadoop_prod',
    'catalog-type'='hadoop',
    'warehouse'='hdfs://nn:8020/path/to/warehouse'
);
```

## Таблица в REST catalog

```sql
create table flink_table (
    id bigint,
    data string
) with (
    'connector'='iceberg',
    'catalog-name'='rest_prod',
    'catalog-type'='rest',
    'uri'='https://localhost/',
    'credential'='xxxx',
    'token'='xxxx',
    'scope'='xxxx'
);
```

`credential`, `token`, `scope` optional в зависимости от authentication server.

## Custom catalog

```sql
create table flink_table (
    id bigint,
    data string
) with (
    'connector'='iceberg',
    'catalog-name'='custom_prod',
    'catalog-impl'='com.my.custom.CatalogImpl',
    'my-additional-catalog-config'='my-value'
);
```

## Полный пример

```sql
create table flink_table (
    id bigint,
    data string
) with (
    'connector'='iceberg',
    'catalog-name'='hive_prod',
    'uri'='thrift://localhost:9083',
    'warehouse'='file:///path/to/warehouse'
);

insert into flink_table values (1, 'AAA'), (2, 'BBB'), (3, 'CCC');

set execution.result-mode=tableau;
select * from flink_table;
```

```text
+----+------+
| id | data |
+----+------+
|  1 |  AAA |
|  2 |  BBB |
|  3 |  CCC |
+----+------+
3 rows in set
```
