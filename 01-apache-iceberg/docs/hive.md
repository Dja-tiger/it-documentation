---
title: "Apache Hive"
tags: [apache-iceberg, hive, integration, catalog]
source_project: apache/iceberg
source_file: docs/docs/hive.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/hive.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Hive

Iceberg поддерживает чтение и запись Iceberg tables через Apache Hive с помощью Hive `StorageHandler`.

## Поддерживаемые возможности

Hive 4.0.0+ поддерживает:

- создание Iceberg table;
- identity-partitioned Iceberg table;
- partition spec с Iceberg transforms;
- CTAS;
- drop table;
- schema evolution с синхронизацией Hive/Iceberg schema;
- изменение partition schema и partition transforms;
- truncate table/partition и drop partition;
- migration Avro/Parquet/ORC non-ACID tables в Iceberg;
- чтение Iceberg table и schema;
- metadata tables;
- time travel;
- `insert into` и `insert overwrite`;
- copy-on-write `delete`, `update`, `merge`; CRUD для Iceberg v1;
- snapshot expiration;
- CTLT (`create table like`);
- Parquet compression type через table properties;
- изменение metadata location;
- rollback;
- соблюдение существующего Iceberg sort order при записи;
- создание, запись и drop branch/tag;
- expiration snapshots по snapshot ID, time range, retain-last-N и properties;
- set current snapshot по snapshot ID;
- rename table;
- conversion existing table → Iceberg;
- fast-forward branch и cherry-pick commit;
- создание branch от tag;
- set current snapshot по branch/tag;
- delete orphan files;
- full-table compaction;
- `show partitions` для Iceberg.

> [!warning]
> Hive DML operations для Iceberg работают только с **Tez execution engine**.

## Включение Iceberg support в Hive

Начиная с Iceberg 1.8.0 проект больше не выпускает отдельный Hive runtime connector. Для Hive 2.x/3.x используйте runtime connector из Iceberg 1.6.1 либо Hive 4.0.0+, где Iceberg integration встроена.

- Hive 4.1.x / 4.2.x включают Iceberg 1.9.1.
- Hive 4.0.x включает Iceberg 1.4.3.

### StorageHandler

Если Iceberg StorageHandler отсутствует в Hive classpath, Hive не способен загрузить/обновить Iceberg metadata. Чтобы таблицы не выглядели broken, Iceberg не добавляет handler, пока Hive support явно не включён.

Handler синхронизируется при переключении Hive engine support через два уровня configuration.

#### Hadoop configuration

Глобально:

```text
iceberg.engine.hive.enabled=true
```

Например, если property находится в `hive-site.xml`, который загружает Spark, все создаваемые Spark Iceberg tables будут публиковать Hive StorageHandler.

#### Table property

```java
Catalog catalog = ...;
Map<String, String> tableProperties = Maps.newHashMap();
tableProperties.put(TableProperties.ENGINE_HIVE_ENABLED, "true");
catalog.createTable(tableId, schema, spec, tableProperties);
```

Table-level `engine.hive.enabled` override global Hadoop config.

## Catalog Management

### Global Hive catalog

`HiveCatalog` integration поддерживает Hive 2.3.10, 3.1.3 или новее.

С точки зрения Hive engine в runtime существует один global catalog из Hadoop configuration. Iceberg, напротив, поддерживает Hive, Hadoop, Glue и custom catalogs, а также path-based tables без catalog.

Hive Metastore table может представлять три варианта загрузки Iceberg в зависимости от property `iceberg.catalog`:

1. property отсутствует → table загружается через `HiveCatalog` текущего HMS;
2. задано имя catalog → используется зарегистрированный custom catalog;
3. `iceberg.catalog=location_based_table` → table загружается напрямую по root location.

Для вариантов 2/3 Hive table в HMS выступает **overlay**, позволяющим Hive взаимодействовать с Iceberg table другого catalog/path.

### Custom Iceberg catalogs

Hadoop configuration:

| Key | Описание |
| --- | --- |
| `iceberg.catalog.<catalog_name>.type` | `hive`, `hadoop`; для custom можно оставить пустым |
| `iceberg.catalog.<catalog_name>.catalog-impl` | Custom implementation, обязателен без `type` |
| `iceberg.catalog.<catalog_name>.<key>` | Остальные catalog options |

Hive CLI — другой HiveCatalog:

```sql
set iceberg.catalog.another_hive.type=hive;
set iceberg.catalog.another_hive.uri=thrift://example.com:9083;
set iceberg.catalog.another_hive.clients=10;
set iceberg.catalog.another_hive.warehouse=hdfs://example.com:8020/warehouse;
```

HadoopCatalog:

```sql
set iceberg.catalog.hadoop.type=hadoop;
set iceberg.catalog.hadoop.warehouse=hdfs://example.com:8020/warehouse;
```

GlueCatalog:

```sql
set iceberg.catalog.glue.type=glue;
set iceberg.catalog.glue.warehouse=s3://my-bucket/my/key/prefix;
set iceberg.catalog.glue.lock.table=myGlueLockTable;
```

## DDL Commands

### `create table`

#### Non-partitioned table

```sql
create external table x (i int) stored by iceberg;
```

Если на cluster настроен `MetaStoreMetadataTransformer`, managed-looking Hive DDL можно автоматически преобразовать в external table:

```sql
create table x (i int) stored by iceberg;
```

Default file format — Parquet. Можно выбрать ORC:

```sql
create table x (i int) stored by iceberg stored as orc;
```

#### Partitioned table

Identity partitioning:

```sql
create table x (i int)
partitioned by (j int)
stored by iceberg;
```

Физические Hive partitions в HMS не создаются — partition data становятся Iceberg identity partitions.

```sql
describe x;
```

Пример output:

| col_name | data_type | comment |
| --- | --- | --- |
| i | int | |
| j | int | |
| | null | null |
| # Partition Transform Information | null | null |
| # col_name | transform_type | null |
| j | IDENTITY | null |

Hive 4 поддерживает Iceberg partition transforms через `partitioned by spec`:

```sql
create table x (i int, ts timestamp)
partitioned by spec (month(ts), bucket(2, i))
stored by iceberg;

describe x;
```

Transforms:

- `years(ts)`;
- `months(ts)`;
- `days(ts)` / `date(ts)`;
- `hours(ts)` / `date_hour(ts)`;
- `bucket(N, col)`;
- `truncate(L, col)` — string length или numeric bins.

### CTAS

Iceberg CTAS отличается от native Hive: table и Hive entry создаются **в начале** query, data commit — после успешного завершения. Поэтому временно table может существовать пустой.

```sql
create table target
partitioned by spec (year(year_field), identity_field)
stored by iceberg
as
select * from source;
```

### CTLT

```sql
create table target like source stored by iceberg;
```

### External overlay существующей Iceberg table

#### HiveCatalog table

Если table создана `HiveCatalog` с Hive support, она уже видна Hive и overlay не нужен.

#### Custom catalog table

```sql
set iceberg.catalog.hadoop_cat.type=hadoop;
set iceberg.catalog.hadoop_cat.warehouse=hdfs://example.com:8020/hadoop_cat;

create external table database_a.table_a
stored by 'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler'
tblproperties ('iceberg.catalog'='hadoop_cat');
```

Если `iceberg.catalog` отсутствует и на table, и global config, default — `HiveCatalog`.

#### Path-based Hadoop table

```sql
create external table table_a
stored by 'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler'
location 'hdfs://some_bucket/some_path/table_a'
tblproperties ('iceberg.catalog'='location_based_table');
```

#### Managed overlay custom catalog

```sql
set iceberg.catalog.hadoop_cat.type=hadoop;
set iceberg.catalog.hadoop_cat.warehouse=hdfs://example.com:8020/hadoop_cat;

create table database_a.table_a (
    id bigint,
    name string
)
partitioned by (dept string)
stored by 'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler'
tblproperties ('iceberg.catalog'='hadoop_cat');
```

> [!danger]
> Если target уже существует в custom catalog, Hive создаст **managed overlay**. Технически `external` можно опустить, но это не рекомендуется: случайный `drop table` со стороны Hive способен удалить shared data files underlying Iceberg table.

## `alter table`

### Table properties

Для `HiveCatalog` Iceberg properties и HMS properties синхронизируются. Для других catalog implementations это не гарантируется.

```sql
alter table t set tblproperties('...'='...');
```

### Schema evolution

Hive schema синхронизируется с Iceberg schema даже если её изменил Spark/Impala/Java API.

Rename table:

```sql
alter table orders rename to renamed_orders;
```

Add column:

```sql
alter table orders add columns (nickname string);
```

Rename column:

```sql
alter table orders change column item fruit string;
```

Reorder:

```sql
alter table orders change column quantity quantity int after price;
```

Safe widening type:

```sql
alter table orders change column price price long;
```

Drop columns через `replace columns`:

```sql
alter table orders replace columns (remaining string);
```

> [!info]
> `replace columns` для Iceberg предназначен только для удаления fields. Попытка задать columns в новом порядке вызовет error.

### Partition evolution

Новые identity partitions:

```sql
alter table default.customers set partition spec (last_name);
```

Transforms:

```sql
alter table orders set partition spec (month(ts));
```

### Migration existing Hive table

Avro/Parquet/ORC external table можно преобразовать без переписывания data files:

```sql
alter table t set tblproperties (
  'storage_handler'='org.apache.iceberg.mr.hive.HiveIcebergStorageHandler'
);
```

Создаются Iceberg metadata files; после этого table используется как обычная Iceberg table.

### Drop partitions

```sql
alter table orders
  drop partition (buy_date == '2023-01-01', market_price > 1000),
       partition (buy_date == '2024-01-01', market_price <= 2000);
```

Partition spec здесь поддерживает только identity partition columns, не transforms.

### Branches и tags

#### Create branch

```sql
alter table test create branch branch1;

alter table test create branch branch1
for system_version as of 3369973735913135680;

alter table test create branch branch1
for system_time as of '2023-09-16 09:46:38.939 Etc/UTC';

alter table test create branch branch1
for system_version as of 3369973735913135680
with snapshot retention 5 snapshots;

alter table test create branch branch1 for tag as of tag1;
```

#### Create tag

```sql
alter table test create tag tag1;

alter table test create tag tag1
for system_version as of 3369973735913135680;

alter table test create tag tag1
for system_time as of '2023-09-16 09:46:38.939 Etc/UTC';
```

#### Drop branch/tag

```sql
alter table test drop branch branch1;
alter table test drop branch if exists branch1;

alter table test drop tag tag1;
alter table test drop tag if exists tag1;
```

#### Fast-forward

Branch должен быть ancestor source branch:

```sql
alter table test execute fast-forward 'branch1' 'main';
alter table test execute fast-forward 'branch1' 'branch2';
```

#### Cherry-pick

В Hive 4 cherry-pick snapshot поддерживается только для `main`:

```sql
alter table test execute cherry-pick 8602659039622823857;
```

### `truncate table`

```sql
truncate table t;
```

Partition:

```sql
truncate table orders
partition (customer_id = 1, first_name = 'John');
```

Только identity partitions.

### `drop table`

```sql
drop table if exists table_name purge;
```

### Metadata location

Metadata location можно изменить только на path, содержащий **точно тот же metadata JSON**. Сначала table должна быть отдельно migrated в Iceberg; migration и смену location нельзя объединить в один шаг.

```sql
alter table t set tblproperties (
  'metadata_location'='<path>/hivemetadata/00003-a1ada2b8-fc86-4b5b-8c91-400b6b46d0f2.metadata.json'
);
```

## DML Commands

### `select`

Hive `select` работает как обычно, но Iceberg planning даёт преимущества:

- filesystem listing не требуется;
- нет listing partitions из HMS;
- advanced partition filtering без явных partition keys в query;
- можно масштабироваться на большее число partitions.

Read optimizations:

1. Predicate pushdown: Hive `where` push down в Iceberg `TableScan`, Parquet/ORC readers.
2. Column projection: `select` columns передаются readers.
3. Hive 4.x: execution engine Tez.

Часть редко используемых optimizations пока отсутствует. Query planning в Hive по-прежнему использует statistics из MetaStore.

Branch read:

```sql
select * from default.test.branch_branch1;
```

### `insert into`

```sql
insert into table_a values ('a', 1);
insert into table_a select ...;
```

Multi-table insert поддерживается, но **не атомарен между tables**: commits происходят последовательно. Изменения каждой отдельной table атомарны, но failure может оставить часть tables committed.

Branch write:

```sql
insert into default.test.branch_branch1 values ('a', 1);
insert into default.test.branch_branch1 select ...;
```

Multi-table:

```sql
from customers
   insert into target1 select customer_id, first_name
   insert into target2 select last_name, customer_id;
```

Partition-level:

```sql
insert into table_a
partition (customer_id = 1, first_name = 'John')
values (1, 2);
```

Только identity partition columns.

### `insert overwrite`

Atomic overwrite:

```sql
insert overwrite table target
select * from source;
```

Для unpartitioned table заменяется всё содержимое. Для partitioned table заменяются partitions, для которых query произвёл rows.

Partition:

```sql
insert overwrite table target
partition (customer_id = 1, first_name = 'John')
select * from source;
```

### `delete from`

```sql
delete from target
where id > 1 and id < 10;

delete from target
where id in (select id from source);

delete from target
where id in (select min(customer_id) from source);
```

Если filter полностью покрывает partitions — metadata-only delete. Иначе переписываются только затронутые data files.

### `update`

```sql
update target
set first_name = 'Raj'
where id > 1 and id < 10;

update target
set first_name = 'Raj'
where id in (select id from source);
```

### `merge into`

```sql
merge into target as t
using source s
on t.id = s.id
when matched and s.op = 'delete' then delete
when matched and t.count is null and s.op = 'increment'
  then update set t.count = 0
when matched and s.op = 'increment'
  then update set t.count = t.count + 1
when not matched
  then insert values (s.a, s.b, s.c);
```

При нескольких `when matched` применяется первое подходящее условие. Одна target row не может обновляться несколькими source rows.

## Metadata tables

В Hive доступны:

- `all_data_files`;
- `all_delete_files`;
- `all_entries`;
- `all_files`;
- `all_manifests`;
- `data_files`;
- `delete_files`;
- `entries`;
- `files`;
- `history`;
- `manifests`;
- `metadata_log_entries`;
- `partitions`;
- `refs`;
- `snapshots`.

Reference через `<db>.<table>.<metadata_table>`:

```sql
select * from default.table_a.files;
```

Metadata tables поддерживают projection/join/filter как обычные Hive tables.

## Time travel

По time:

```sql
select * from table_a
for system_time as of '2021-08-09 10:35:57';
```

По snapshot ID:

```sql
select * from table_a
for system_version as of 1234567;
```

## Snapshot expiration

Каждая write создаёт snapshot. Старые snapshots следует периодически expire для очистки неиспользуемых data files и уменьшения metadata.

По timestamp:

```sql
alter table test_table
execute expire_snapshots('2021-12-09 05:39:18.689000000');
```

Hive 4 также поддерживает expiration по snapshot ID, диапазону времени, retention последних N snapshots и table properties.

## Delete orphan files

```sql
alter table table_a execute delete orphan-files;

alter table table_a
execute delete orphan-files
older than ('2021-12-09 05:39:18.689000000');
```

## Type compatibility

Auto-conversion выключен по умолчанию:

| Config | Default | Описание |
| --- | --- | --- |
| `iceberg.mr.schema.auto.conversion` | false | Разрешать Hive type auto-conversion |

### Hive → Iceberg

| Hive | Iceberg | Примечание |
| --- | --- | --- |
| boolean | boolean | |
| short | integer | auto-conversion |
| byte | integer | auto-conversion |
| integer | integer | |
| long | long | |
| float | float | |
| double | double | |
| date | date | |
| timestamp | timestamp without timezone | |
| timestamplocaltz | timestamp with timezone | Hive 3 only |
| interval_year_month | — | not supported |
| interval_day_time | — | not supported |
| char | string | auto-conversion |
| varchar | string | auto-conversion |
| string | string | |
| binary | binary | |
| decimal | decimal | |
| struct | struct | |
| list | list | |
| map | map | |
| union | — | not supported |

## Rollback

До latest snapshot перед timestamp:

```sql
alter table ice_t
execute rollback('2022-05-12 00:00:00');
```

До snapshot ID:

```sql
alter table ice_t execute rollback(1111);
```

## Compaction

Hive 4 поддерживает full-table compaction двумя equivalent syntaxes:

```sql
alter table t compact 'major';
```

```sql
optimize table t rewrite data;
```
