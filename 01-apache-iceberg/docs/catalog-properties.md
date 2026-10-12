---
title: "Свойства каталогов"
tags: [apache-iceberg, catalogs, configuration]
source_project: apache/iceberg
source_file: docs/docs/catalog-properties.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/catalog-properties.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Свойства каталогов

## Общие свойства

Iceberg catalogs используют catalog properties для настройки поведения.

| Property | Default | Описание |
| --- | --- | --- |
| `catalog-impl` | null | Custom implementation `Catalog` для engine |
| `io-impl` | null | Custom implementation `FileIO` |
| `warehouse` | null | Root path data warehouse |
| `uri` | null | URI, например Hive Metastore URI |
| `clients` | 2 | Размер client pool |
| `cache-enabled` | true | Кэшировать catalog entries |
| `cache.expiration-interval-ms` | 30000 | Время локального cache, ms; `0` отключает caching, отрицательное значение отключает expiration |
| `metrics-reporter-impl` | `org.apache.iceberg.metrics.LoggingMetricsReporter` | Custom `MetricsReporter`; см. [[metrics-reporting]] |
| `unique-table-location` | false | Использовать уникальный location для новых tables |
| `encryption.kms-impl` | null | Custom `KeyManagementClient` для KMS; см. [[encryption]] |

`HadoopCatalog` и `HiveCatalog` получают properties в constructors. Custom catalog читает их через `Catalog.initialize(catalogName, catalogProperties)`.

Compute engines передают эти properties по-своему:

- Spark — через session/catalog configuration; см. [[spark-configuration#Catalogs]];
- Flink — через `create catalog`; см. [[flink#Добавление catalogs]].

## REST catalog properties

Client configuration и authentication REST catalog вынесены в [[rest-catalog#Configuration|REST Catalog]].

## Lock catalog properties

Некоторые catalog implementations используют locks при commit.

| Property | Default | Описание |
| --- | --- | --- |
| `lock-impl` | null | Custom lock manager; точный interface зависит от catalog |
| `lock.table` | null | Auxiliary lock table, например [[aws#DynamoDB Lock Manager|DynamoDB lock manager]] |
| `lock.acquire-interval-ms` | 5000 (5 s) | Пауза между попытками получить lock |
| `lock.acquire-timeout-ms` | 180000 (3 min) | Максимальное время попыток acquisition |
| `lock.heartbeat-interval-ms` | 3000 (3 s) | Heartbeat interval после получения lock |
| `lock.heartbeat-timeout-ms` | 15000 (15 s) | Без heartbeat дольше этого времени lock считается expired |

## Hadoop configuration

### HadoopTables Lock Configuration

При использовании `HadoopTables` без catalog properties lock настраиваются с prefix `iceberg.tables.hadoop.`. Это обеспечивает atomic commits на filesystems вроде S3, где нет native mutual exclusion на запись.

Для DynamoDB:

```text
iceberg.tables.hadoop.lock-impl=org.apache.iceberg.aws.dynamodb.DynamoDbLockManager
iceberg.tables.hadoop.lock.table=<dynamodb-table-name>
```

Подробнее: [[aws#DynamoDB Lock Manager]].

### Hive Metastore Configuration

HMS locking состоит из двух стадий:

1. **Lock Creation** — создать lock в HMS и поставить в queue;
2. **Lock Check** — проверять, что lock получен.

| Property | Default | Описание |
| --- | --- | --- |
| `iceberg.hive.client-pool-size` | 5 | Размер Hive client pool |
| `iceberg.hive.lock-creation-timeout-ms` | 180000 | Max время создания lock |
| `iceberg.hive.lock-creation-min-wait-ms` | 50 | Min pause между retries создания |
| `iceberg.hive.lock-creation-max-wait-ms` | 5000 | Max pause между retries создания |
| `iceberg.hive.lock-timeout-ms` | 180000 | Max время acquisition |
| `iceberg.hive.lock-check-min-wait-ms` | 50 | Min pause между lock checks |
| `iceberg.hive.lock-check-max-wait-ms` | 5000 | Max pause между lock checks |
| `iceberg.hive.lock-heartbeat-interval-ms` | 240000 (4 min) | Heartbeat interval HMS lock |
| `iceberg.hive.metadata-refresh-max-retries` | 2 | Retries при missing metadata file |
| `iceberg.hive.table-level-lock-evict-ms` | 600000 (10 min) | TTL JVM table lock |
| `iceberg.engine.hive.lock-enabled` | true | Использовать HMS locks для atomic commits |

`iceberg.hive.lock-check-max-wait-ms` и heartbeat interval должны быть меньше transaction timeout HMS (`hive.txn.timeout` или `metastore.txn.timeout`), иначе HMS успеет expire lock до следующей проверки.

> [!danger]
> `iceberg.engine.hive.lock-enabled=false` разрешает `HiveCatalog` commit без Hive locks. Это безопасно **только если одновременно выполнены все условия**:
>
> - HMS содержит fix HIVE-26882;
> - при MySQL/MariaDB HMS содержит fix HIVE-28121;
> - все другие HiveCatalog writers этих tables используют Iceberg 1.3+;
> - у всех них Hive locks на commit также отключены.
>
> Нарушение условий создаёт риск corruption Iceberg table.

Даже при global `false` можно включить lock для отдельной table property:

```text
engine.hive.lock-enabled=true
```
