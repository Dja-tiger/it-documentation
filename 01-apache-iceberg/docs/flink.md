---
title: "Flink — начало работы"
tags: [apache-iceberg, flink, integration]
source_project: apache/iceberg
source_file: docs/docs/flink.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/flink.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

> [!tip]
> Для быстрого знакомства с Iceberg + Flink используйте официальный Flink Quickstart. Здесь приведён полный reference интеграции.

Apache Iceberg поддерживает как DataStream API, так и Table API Apache Flink.

| Возможность | Flink | Примечание |
| --- | --- | --- |
| [[flink-ddl#CREATE CATALOG|SQL create catalog]] | ✔️ | |
| [[flink-ddl#CREATE DATABASE|SQL create database]] | ✔️ | |
| [[flink-ddl#CREATE TABLE|SQL create table]] | ✔️ | |
| [[flink-ddl#CREATE TABLE LIKE|SQL create table like]] | ✔️ | |
| [[flink-ddl#ALTER TABLE|SQL alter table]] | ✔️ | Properties и columns; partition changes не поддерживаются |
| [[flink-ddl#DROP TABLE|SQL drop table]] | ✔️ | |
| [[flink-queries#Чтение через SQL|SQL select]] | ✔️ | Streaming и batch |
| [[flink-writes#insert into|SQL insert into]] | ✔️ | Streaming и batch |
| [[flink-writes#insert overwrite|SQL insert overwrite]] | ✔️ | Batch |
| [[flink-queries#Чтение через DataStream|DataStream read]] | ✔️ | |
| [[flink-writes#Append|DataStream append]] | ✔️ | |
| [[flink-writes#Overwrite|DataStream overwrite]] | ✔️ | |
| [[flink-queries#Metadata tables|Metadata tables]] | ✔️ | |
| [[flink-maintenance#Rewrite files action|Rewrite files action]] | ✔️ | |

## Подготовка Flink SQL Client

Для первого знакомства рекомендуется Flink SQL Client. Iceberg runtime компилируется с Scala 2.12, поэтому рекомендуется Flink соответствующей major-версии с Scala 2.12.

```bash
FLINK_VERSION={{ flinkVersion }}
SCALA_VERSION=2.12
APACHE_FLINK_URL=https://archive.apache.org/dist/flink/
wget ${APACHE_FLINK_URL}/flink-${FLINK_VERSION}/flink-${FLINK_VERSION}-bin-scala_${SCALA_VERSION}.tgz
tar xzvf flink-${FLINK_VERSION}-bin-scala_${SCALA_VERSION}.tgz
```

Standalone Flink cluster в Hadoop environment:

```bash
APACHE_HADOOP_URL=https://archive.apache.org/dist/hadoop/
HADOOP_VERSION=2.8.5
wget ${APACHE_HADOOP_URL}/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz
tar xzvf hadoop-${HADOOP_VERSION}.tar.gz
HADOOP_HOME=`pwd`/hadoop-${HADOOP_VERSION}

export HADOOP_CLASSPATH=`$HADOOP_HOME/bin/hadoop classpath`

cd flink-${FLINK_VERSION}/
./bin/start-cluster.sh
```

Iceberg содержит отдельный `flink-runtime` module, генерирующий bundled jar. После сборки проекта он находится в `<iceberg-root-dir>/flink/v{{ flinkVersionMajor }}/flink-runtime/build/libs`; также jar опубликован в Apache Maven repository.

```bash
export HADOOP_CLASSPATH=`$HADOOP_HOME/bin/hadoop classpath`

# Flink 1.15 и ниже
./bin/sql-client.sh embedded -j <flink-runtime-directory>/iceberg-flink-runtime-{{ flinkVersionMajor }}-{{ icebergVersion }}.jar shell

# Flink 1.16+ имеет regression загрузки external jars через -j (FLINK-30035).
# Поместите runtime jar в flink/lib.
./bin/sql-client.sh embedded shell
```

По умолчанию Iceberg поставляет Hadoop jars для Hadoop catalog. Для Hive catalog при запуске SQL Client также загрузите Hive jars. Flink предоставляет bundled Hive connector:

```bash
export HADOOP_CLASSPATH=`$HADOOP_HOME/bin/hadoop classpath`

ICEBERG_VERSION={{ icebergVersion }}
MAVEN_URL=https://repo1.maven.org/maven2
ICEBERG_MAVEN_URL=${MAVEN_URL}/org/apache/iceberg
ICEBERG_PACKAGE=iceberg-flink-runtime
FLINK_VERSION_MAJOR={{ flinkVersionMajor }}
wget ${ICEBERG_MAVEN_URL}/${ICEBERG_PACKAGE}-${FLINK_VERSION_MAJOR}/${ICEBERG_VERSION}/${ICEBERG_PACKAGE}-${FLINK_VERSION_MAJOR}-${ICEBERG_VERSION}.jar -P lib/

HIVE_VERSION=2.3.9
SCALA_VERSION=2.12
FLINK_VERSION={{ flinkVersion }}
FLINK_CONNECTOR_URL=${MAVEN_URL}/org/apache/flink
FLINK_CONNECTOR_PACKAGE=flink-sql-connector-hive
wget ${FLINK_CONNECTOR_URL}/${FLINK_CONNECTOR_PACKAGE}-${HIVE_VERSION}_${SCALA_VERSION}/${FLINK_VERSION}/${FLINK_CONNECTOR_PACKAGE}-${HIVE_VERSION}_${SCALA_VERSION}-${FLINK_VERSION}.jar

./bin/sql-client.sh embedded shell
```

## Python API Flink

> [!info]
> PyFlink 1.6.1 имеет известную проблему на macOS Apple Silicon (FLINK-28786).

```bash
pip install apache-flink=={{ flinkVersion }}
```

Добавьте runtime JAR в PyFlink:

```python
import os

from pyflink.datastream import StreamExecutionEnvironment

env = StreamExecutionEnvironment.get_execution_environment()
iceberg_flink_runtime_jar = os.path.join(os.getcwd(), "iceberg-flink-runtime-{{ flinkVersionMajor }}-{{ icebergVersion }}.jar")

env.add_jars("file://{}".format(iceberg_flink_runtime_jar))
```

Альтернативы: `env.add_jars(...)` или `pipeline.jars` через TableEnvironment configuration.

Создание custom catalog через Python Table API:

```python
from pyflink.table import StreamTableEnvironment
table_env = StreamTableEnvironment.create(env)
table_env.execute_sql("""
create catalog my_catalog with (
    'type'='iceberg',
    'catalog-impl'='com.my.custom.CatalogImpl',
    'my-additional-catalog-config'='my-value'
)
""")
```

Запрос:

```python
(table_env
    .sql_query("select PULocationID, DOLocationID, passenger_count from my_catalog.nyc.taxis limit 5")
    .execute()
    .print())
```

```text
+----+----------------------+----------------------+--------------------------------+
| op |         PULocationID |         DOLocationID |                passenger_count |
+----+----------------------+----------------------+--------------------------------+
| +I |                  249 |                   48 |                            1.0 |
| +I |                  132 |                  233 |                            1.0 |
| +I |                  164 |                  107 |                            1.0 |
| +I |                   90 |                  229 |                            1.0 |
| +I |                  137 |                  249 |                            1.0 |
+----+----------------------+----------------------+--------------------------------+
5 rows in set
```

## Добавление catalogs

Catalog создаётся Flink SQL:

```sql
create catalog <catalog_name> with (
  'type'='iceberg',
  '<config_key>' = '<config_value>'
);
```

Общие properties:

- `type` — обязательно `iceberg`;
- `catalog-type` — built-in: `hive`, `hadoop`, `rest`, `glue`, `jdbc`, `nessie`; для custom с `catalog-impl` не задаётся;
- `catalog-impl` — fully-qualified custom Catalog class;
- `property-version` — текущая версия `1`;
- `cache-enabled` — default `true`;
- `cache.expiration-interval-ms` — local cache TTL, default `-1` (без expiration), `0` не разрешён.

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

### REST catalog

```sql
create catalog rest_catalog with (
  'type'='iceberg',
  'catalog-type'='rest',
  'uri'='https://localhost/'
);
```

## Создание таблицы

```sql
create table `hive_catalog`.`default`.`sample` (
    id bigint comment 'unique id',
    data string
);
```

## Запись

Streaming append:

```sql
insert into `hive_catalog`.`default`.`sample` values (1, 'a');
insert into `hive_catalog`.`default`.`sample` select id, data from other_kafka_table;
```

Atomic overwrite доступен в batch job, но не streaming:

```sql
insert overwrite `hive_catalog`.`default`.`sample` values (1, 'a');
insert overwrite `hive_catalog`.`default`.`sample` partition(data='a') select 6;
```

DataStream:

```java
StreamExecutionEnvironment env = ...;
DataStream<RowData> input = ... ;
Configuration hadoopConf = new Configuration();
TableLoader tableLoader = TableLoader.fromHadoopTable("hdfs://nn:8020/warehouse/path", hadoopConf);

FlinkSink.forRowData(input)
    .tableLoader(tableLoader)
    .append();

env.execute("Test Iceberg DataStream");
```

Branch write:

```java
FlinkSink.forRowData(input)
    .tableLoader(tableLoader)
    .toBranch("audit-branch")
    .append();
```

Подробнее: [[flink-writes|Flink Writes]].

## Чтение

Batch:

```sql
set execution.runtime-mode = batch;
select * from `hive_catalog`.`default`.`sample`;
```

Streaming incremental:

```sql
set execution.runtime-mode = streaming;
set table.dynamic-table-options.enabled=true;

select * from `hive_catalog`.`default`.`sample`
/*+ options('streaming'='true', 'monitor-interval'='1s')*/;

select * from `hive_catalog`.`default`.`sample`
/*+ options('streaming'='true', 'monitor-interval'='1s', 'start-snapshot-id'='3821550127947089987')*/;
```

Snapshots metadata table:

```sql
select * from `hive_catalog`.`default`.`sample$snapshots`;
```

Java API batch:

```java
DataStream<RowData> batch = FlinkSource.forRowData()
     .env(env)
     .tableLoader(tableLoader)
     .streaming(false)
     .build();
```

## Конвертация типов

Iceberg автоматически преобразует Flink/Iceberg types. При записи типов, которых нет во Flink, например UUID, Iceberg принимает совместимое Flink representation и выполняет conversion.

### Flink → Iceberg

| Flink | Iceberg | Примечание |
| --- | --- | --- |
| `boolean` | `boolean` | |
| `tinyint` | `integer` | |
| `smallint` | `integer` | |
| `integer` | `integer` | |
| `bigint` | `long` | |
| `float` | `float` | |
| `double` | `double` | |
| `char` | `string` | |
| `varchar` | `string` | |
| `string` | `string` | |
| `binary` | `fixed` | |
| `varbinary` | `binary` | |
| `decimal` | `decimal` | |
| `date` | `date` | |
| `time` | `time` | |
| `timestamp` | timestamp without timezone | |
| `timestamp_ltz` | timestamp with timezone | |
| `array` | `list` | |
| `map` | `map` | |
| `multiset` | `map` | |
| `row` | `struct` | |
| `variant` | `variant` | Flink 2.x |
| `raw` | — | Не поддерживается |
| `interval` | — | Не поддерживается |
| `structured` | — | Не поддерживается |
| timestamp with zone | — | Не поддерживается |
| `distinct` | — | Не поддерживается |
| `null` | — | Не поддерживается |
| `symbol` | — | Не поддерживается |
| `logical` | — | Не поддерживается |

### Iceberg → Flink

| Iceberg | Flink | Примечание |
| --- | --- | --- |
| `boolean` | `boolean` | |
| `struct` | `row` | |
| `list` | `array` | |
| `map` | `map` | |
| `integer` | `integer` | |
| `long` | `bigint` | |
| `float` | `float` | |
| `double` | `double` | |
| `date` | `date` | |
| `time` | `time` | |
| timestamp without timezone | `timestamp(6)` | |
| timestamp with timezone | `timestamp_ltz(6)` | |
| `string` | `varchar(2147483647)` | |
| `uuid` | `binary(16)` | |
| `fixed(N)` | `binary(N)` | |
| `binary` | `varbinary(2147483647)` | |
| `decimal(P,S)` | `decimal(P,S)` | |
| nanosecond timestamp | `timestamp(9)` | |
| nanosecond timestamp with timezone | `timestamp_ltz(9)` | |
| `unknown` | `null` | |
| `variant` | `variant` | Flink 2.x |
| `geometry` | — | Не поддерживается |
| `geography` | — | Не поддерживается |

## Пока не поддерживается

- Создание Iceberg table со hidden partitioning через Flink DDL — Flink не умеет partition function в DDL;
- computed columns Iceberg table.
