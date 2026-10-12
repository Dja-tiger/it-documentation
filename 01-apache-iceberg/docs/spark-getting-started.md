---
title: "Spark — начало работы"
tags: [apache-iceberg, spark, integration]
source_project: apache/iceberg
source_file: docs/docs/spark-getting-started.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/spark-getting-started.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Начало работы

Текущая базовая версия Iceberg в этой базе знаний — **1.12.0**.

Spark на данный момент является compute engine с наиболее полной поддержкой операций Iceberg. Для знакомства с концепциями и возможностями Iceberg рекомендуется начать именно со Spark. Использование Iceberg с другими engines описано в соответствующих разделах интеграций.

## Использование Iceberg в Spark

Чтобы подключить Iceberg в Spark shell, используйте `--packages`:

```sh
spark-shell --packages org.apache.iceberg:iceberg-spark-runtime-{{ sparkVersionMajor }}:{{ icebergVersion }}
```

> [!info]
> Если Iceberg должен быть частью установки Spark, добавьте JAR `iceberg-spark-runtime-{{ sparkVersionMajor }}` в каталог Spark `jars`.

### Добавление catalogs

Iceberg предоставляет [[spark-configuration#Catalogs|catalogs]], позволяющие управлять таблицами SQL-командами и загружать их по имени. Catalogs настраиваются через properties `spark.sql.catalog.(catalog_name)`.

Следующая команда создаёт path-based catalog `local` для таблиц в `$PWD/warehouse` и добавляет поддержку Iceberg в built-in catalog Spark:

```sh
spark-sql --packages org.apache.iceberg:iceberg-spark-runtime-{{ sparkVersionMajor }}:{{ icebergVersion }}\
    --conf spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions \
    --conf spark.sql.catalog.spark_catalog=org.apache.iceberg.spark.SparkSessionCatalog \
    --conf spark.sql.catalog.spark_catalog.type=hive \
    --conf spark.sql.catalog.local=org.apache.iceberg.spark.SparkCatalog \
    --conf spark.sql.catalog.local.type=hadoop \
    --conf spark.sql.catalog.local.warehouse=$PWD/warehouse
```

### Создание таблицы

Чтобы создать первую Iceberg-таблицу, запустите `create table` через `spark-sql` или `spark.sql(...)`:

```sql
-- local is the path-based catalog defined above
create table local.db.table (id bigint, data string) using iceberg;
create table source (id bigint, data string) using parquet;
create table updates (id bigint, data string) using parquet;
```

Iceberg catalogs поддерживают полный набор SQL DDL, включая:

- `create table ... partitioned by`;
- `create table ... as select`;
- `alter table`;
- `drop table`.

Подробнее: [[spark-ddl|Spark DDL]].

### Запись

После создания таблицы данные можно добавить через `insert into`:

```sql
insert into local.db.table values (1, 'a'), (2, 'b'), (3, 'c');
insert into source values (10, 'd'), (11, 'ee');
insert into updates values (1, 'x'), (2, 'x'), (4, 'z');
insert into local.db.table select id, data from source where length(data) = 1;
```

Iceberg добавляет в Spark row-level SQL operations, включая `merge into` и `delete from`:

```sql
merge into local.db.table t using (select * from updates) u on t.id = u.id
when matched then update set t.data = u.data
when not matched then insert *;
```

Для DataFrames рекомендуется новый v2 write API:

```scala
spark.table("source").select("id", "data")
     .writeTo("local.db.table").append()
```

Старый `write` API поддерживается, но не рекомендуется.

### Чтение

В SQL таблица читается по имени:

```sql
select count(1) as count, data
from local.db.table
group by data;
```

SQL также рекомендуется для [[spark-queries#Просмотр метаданных таблицы|инспекции metadata tables]]. Например, все snapshots:

```sql
select * from local.db.table.snapshots;
```

Пример результата:

```text
+-------------------------+----------------+-----------+-----------+----------------------------------------------------+-----+
| committed_at            | snapshot_id    | parent_id | operation | manifest_list                                      | ... |
+-------------------------+----------------+-----------+-----------+----------------------------------------------------+-----+
| 2019-02-08 03:29:51.215 | 57897183625154 | null      | append    | s3://.../table/metadata/snap-57897183625154-1.avro | ... |
| ...                     | ...            | ...       | ...       | ...                                                | ... |
+-------------------------+----------------+-----------+-----------+----------------------------------------------------+-----+
```

DataFrame reads также поддерживают таблицы по имени:

```scala
val df = spark.table("local.db.table")
df.count()
```

### Совместимость типов

Spark и Iceberg поддерживают разные наборы типов. Iceberg выполняет конвертацию автоматически, но не все комбинации возможны, поэтому типы таблицы следует проектировать с учётом mapping.

#### Spark type → Iceberg type

Mapping применяется и при создании таблицы, и при записи через Spark.

| Spark | Iceberg | Примечание |
| --- | --- | --- |
| `boolean` | `boolean` | |
| `short` | `integer` | |
| `byte` | `integer` | |
| `integer` | `integer` | |
| `long` | `long` | |
| `float` | `float` | |
| `double` | `double` | |
| `date` | `date` | |
| `timestamp` | `timestamp with timezone` | |
| `timestamp_ntz` | `timestamp without timezone` | |
| `char` | `string` | |
| `varchar` | `string` | |
| `string` | `string` | |
| `binary` | `binary` | |
| `decimal` | `decimal` | |
| `struct` | `struct` | |
| `array` | `list` | |
| `map` | `map` | |

> [!info]
> Таблица описывает mapping при создании. При записи поддержка шире: numeric types Iceberg (`integer`, `long`, `float`, `double`, `decimal`) поддерживают promotion. Например, Spark `short`, `byte`, `integer` и `long` можно записывать в Iceberg `long`. В Iceberg `fixed` можно писать Spark `binary`, при этом длина проверяется.

#### Iceberg type → Spark type

| Iceberg | Spark | Примечание |
| --- | --- | --- |
| `boolean` | `boolean` | |
| `integer` | `integer` | |
| `long` | `long` | |
| `float` | `float` | |
| `double` | `double` | |
| `date` | `date` | |
| `time` | — | Не поддерживается |
| `timestamp with timezone` | `timestamp` | |
| `timestamp without timezone` | `timestamp_ntz` | |
| `string` | `string` | |
| `uuid` | `string` | |
| `fixed` | `binary` | |
| `binary` | `binary` | |
| `decimal` | `decimal` | |
| `struct` | `struct` | |
| `list` | `array` | |
| `map` | `map` | |
| nanosecond timestamp | — | Не поддерживается |
| nanosecond timestamp with timezone | — | Не поддерживается |
| `unknown` | `null` | Spark 4.0+ |
| `variant` | `variant` | Spark 4.0+ |
| `geometry` | — | Не поддерживается |
| `geography` | — | Не поддерживается |

### Следующие шаги

- [[spark-ddl|DDL: create, alter, drop]]
- [[spark-queries|Чтение и metadata tables]]
- [[spark-writes|Запись: insert into, merge into и DataFrameWriterV2]]
- [[spark-procedures|Обслуживание через stored procedures]]
