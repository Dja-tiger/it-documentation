---
title: "Spark — конфигурация"
tags: [apache-iceberg, spark, configuration]
source_project: apache/iceberg
source_file: docs/docs/spark-configuration.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/spark-configuration.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Конфигурация Spark

## Catalogs

Spark предоставляет API подключаемых table catalogs для загрузки, создания и управления Iceberg-таблицами. Catalogs конфигурируются properties с префиксом `spark.sql.catalog`.

Hive catalog `hive_prod`:

```plain
spark.sql.catalog.hive_prod = org.apache.iceberg.spark.SparkCatalog
spark.sql.catalog.hive_prod.type = hive
spark.sql.catalog.hive_prod.uri = thrift://metastore-host:port
# omit uri to use the same URI as Spark: hive.metastore.uris in hive-site.xml
```

REST catalog `rest_prod`:

```plain
spark.sql.catalog.rest_prod = org.apache.iceberg.spark.SparkCatalog
spark.sql.catalog.rest_prod.type = rest
spark.sql.catalog.rest_prod.uri = http://localhost:8080
```

Directory-based catalog в HDFS:

```plain
spark.sql.catalog.hadoop_prod = org.apache.iceberg.spark.SparkCatalog
spark.sql.catalog.hadoop_prod.type = hadoop
spark.sql.catalog.hadoop_prod.warehouse = hdfs://nn:8020/warehouse/path
```

> [!info]
> Hive-based `SparkCatalog` загружает только Iceberg-таблицы. Если в том же Hive Metastore нужны и не-Iceberg таблицы, используйте [[#Замена session catalog|session catalog]].

### Конфигурация catalog

Catalog создаётся property `spark.sql.catalog.(catalog-name)`, значением которой является implementation class.

Iceberg предоставляет две реализации:

- `org.apache.iceberg.spark.SparkCatalog` — Hive, Hadoop, REST, Glue, JDBC, Nessie;
- `org.apache.iceberg.spark.SparkSessionCatalog` — добавляет Iceberg в built-in catalog Spark, делегируя не-Iceberg таблицы native catalog.

Основные properties:

| Property | Values / Default | Описание |
| --- | --- | --- |
| `spark.sql.catalog.<name>.type` | `hive`, `hadoop`, `rest`, `glue`, `jdbc`, `nessie` | Выбирает `HiveCatalog`, `HadoopCatalog`, `RESTCatalog`, `GlueCatalog`, `JdbcCatalog` или `NessieCatalog`; для custom можно не задавать |
| `spark.sql.catalog.<name>.catalog-impl` | — | Custom `Catalog`; обязателен, если `type` не задан |
| `spark.sql.catalog.<name>.io-impl` | — | Custom `FileIO` |
| `spark.sql.catalog.<name>.metrics-reporter-impl` | — | Custom `MetricsReporter` |
| `spark.sql.catalog.<name>.default-namespace` | `default` | Namespace по умолчанию |
| `spark.sql.catalog.<name>.uri` | `thrift://host:port` | HMS URI для Hive или REST URL для REST catalog |
| `spark.sql.catalog.<name>.warehouse` | `hdfs://nn:8020/warehouse/path` | Base warehouse path |
| `spark.sql.catalog.<name>.cache-enabled` | `true` | Включает catalog cache |
| `spark.sql.catalog.<name>.cache.expiration-interval-ms` | `30000` | TTL cache; `-1` отключает expiration, `0` полностью отключает caching независимо от `cache-enabled` |
| `spark.sql.catalog.<name>.table-default.<propertyKey>` | — | Default table property для создаваемых таблиц, если пользователь не override |
| `spark.sql.catalog.<name>.table-override.<propertyKey>` | — | Принудительное table property, которое пользователь не может override при create |
| `spark.sql.catalog.<name>.view-default.<propertyKey>` | — | Default view property |
| `spark.sql.catalog.<name>.view-override.<propertyKey>` | — | Принудительное view property |
| `spark.sql.catalog.<name>.use-nullable-query-schema` | `true` | Для CTAS/RTAS: `true` делает все fields nullable; `false` сохраняет nullability query schema. Spark 3.5+ |

Дополнительные параметры: [[catalog-properties|общая конфигурация catalogs]].

### Использование catalogs

Catalog name входит в идентификатор таблицы:

```sql
select * from hive_prod.db.table;
```

Spark 3 хранит current catalog/namespace, поэтому их можно опустить:

```sql
use hive_prod.db;
select * from table;
```

Текущий namespace: `show current namespace`.

### Замена session catalog

Чтобы built-in `spark_catalog` поддерживал Iceberg, настройте `SparkSessionCatalog`:

```plain
spark.sql.catalog.spark_catalog = org.apache.iceberg.spark.SparkSessionCatalog
spark.sql.catalog.spark_catalog.type = hive
```

Он оборачивает session catalog Spark: Iceberg-таблицы обрабатывает Iceberg, остальные — built-in catalog. Поэтому один HMS может содержать оба типа таблиц.

> [!note]
> Spark до 4.2.0 не поддерживает `V2Function` в session catalog. Catalog-scoped functions `system.bucket`, `system.days`, `system.iceberg_version` недоступны через `spark_catalog`. Для них настройте отдельный `SparkCatalog`.

### Hadoop configuration на уровне catalog

Как и `spark.hadoop.*`, можно задавать Hadoop settings только для конкретного catalog через `spark.sql.catalog.<name>.hadoop.*`; они имеют приоритет над global `spark.hadoop.*` только для Iceberg:

```plain
spark.sql.catalog.hadoop_prod.hadoop.fs.s3a.endpoint = http://aws-local:9000
```

### Custom catalog

```plain
spark.sql.catalog.custom_prod = org.apache.iceberg.spark.SparkCatalog
spark.sql.catalog.custom_prod.catalog-impl = com.my.custom.CatalogImpl
spark.sql.catalog.custom_prod.my-additional-catalog-config = my-value
```

## SQL Extensions

Начиная с Iceberg 0.11.0 extension module добавляет Spark SQL commands вроде `call` и `alter table ... write ordered by`.

| Spark property | Implementation |
| --- | --- |
| `spark.sql.extensions` | `org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions` |

## Runtime configuration

### Приоритет настроек

Effective configuration read/write определяется в порядке:

1. DataSource API read/write options, явно переданные `.option(...)`;
2. Spark Session Configuration (`spark.conf.set`, `spark-defaults.conf`, `--conf`);
3. table properties (`alter table ... set tblproperties`);
4. default value.

Если параметр отсутствует на верхнем уровне, используется следующий.

### Spark SQL options

```scala
val spark = SparkSession.builder()
  .appName("IcebergExample")
  .master("local[*]")
  .config("spark.sql.catalog.my_catalog", "org.apache.iceberg.spark.SparkCatalog")
  .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
  .config("spark.sql.iceberg.vectorization.enabled", "false")
  .getOrCreate()
```

| Spark option | Default | Описание |
| --- | --- | --- |
| `spark.sql.iceberg.vectorization.enabled` | Table default | Vectorized reads data files |
| `spark.sql.iceberg.check-nullability` | `true` | Проверять nullability write schema относительно table schema |
| `spark.sql.iceberg.check-ordering` | `true` | Проверять порядок колонок write schema относительно table schema |
| `spark.sql.iceberg.planning.preserve-data-grouping` | `false` | Совмещать scan tasks одной partition в одном read split; используется Storage Partitioned Joins |
| `spark.sql.iceberg.aggregate-push-down.enabled` | `true` | Pushdown `max`, `min`, `count` |
| `spark.sql.iceberg.distribution-mode` | см. [[spark-writes#Режимы распределения при записи]] | Стратегия распределения write data |
| `spark.wap.id` | `null` | WAP snapshot staging ID |
| `spark.wap.branch` | `null` | WAP branch name |
| `spark.sql.iceberg.shred-variants` | Table default | Shredded Parquet encoding для `variant` |
| `spark.sql.iceberg.variant-inference-buffer-size` | Table default | Rows buffer для inference variant shredding |
| `spark.sql.iceberg.compression-codec` | Table default | Write codec (`zstd`, `snappy`, ...) |
| `spark.sql.iceberg.compression-level` | Table default | Compression level Parquet/Avro |
| `spark.sql.iceberg.compression-strategy` | Table default | ORC compression strategy |
| `spark.sql.iceberg.data-planning-mode` | `AUTO` | `AUTO`, `LOCAL`, `DISTRIBUTED` для data files |
| `spark.sql.iceberg.delete-planning-mode` | `AUTO` | Planning mode delete files |
| `spark.sql.iceberg.advisory-partition-size` | Table default | Advisory bytes для AQE при записи; влияет на output file sizing |
| `spark.sql.iceberg.read.split-size` | Table default | Override `read.split.target-size`; session value отключает adaptive split sizing |
| `spark.sql.iceberg.locality.enabled` | `false` | Report locality для task placement |
| `spark.sql.iceberg.executor-cache.enabled` | `true` | Executor-side cache, сейчас используется для Delete Files |
| `spark.sql.iceberg.executor-cache.timeout` | `10` | TTL executor cache, минуты |
| `spark.sql.iceberg.executor-cache.max-entry-size` | 64 MB | Максимальный размер cache entry |
| `spark.sql.iceberg.executor-cache.max-total-size` | 128 MB | Общий лимит executor cache |
| `spark.sql.iceberg.executor-cache.locality.enabled` | `false` | Locality-aware executor cache |
| `spark.sql.iceberg.merge-schema` | `false` | Автоматически добавлять отсутствующие columns в table schema |
| `spark.sql.iceberg.view.schema-binding-mode` | `BINDING` | `BINDING` — только widening; `COMPENSATION` — любой ANSI cast |
| `spark.sql.iceberg.report-column-stats` | `true` | Передавать Puffin statistics в Spark CBO; CBO должен быть enabled |
| `spark.sql.iceberg.read.adaptive-split-size.enabled` | Table default | Adaptive split sizing по scan size и parallelism |
| `spark.sql.iceberg.read.adaptive-split-size.parallelism` | `max(spark.default.parallelism, spark.sql.shuffle.partitions)` | Parallelism для adaptive sizing, должен быть > 0 |
| `spark.sql.iceberg.async-micro-batch-planning-enabled` | `false` | Async planning micro-batches с prefetch file scan tasks |

### Read options

```scala
spark.read
    .option("snapshot-id", 10963874102873L)
    .table("catalog.db.table")
```

| Option | Default | Описание |
| --- | --- | --- |
| `snapshot-id` | latest | Snapshot ID |
| `as-of-timestamp` | latest | Timestamp ms; выбирается snapshot, current на этот момент |
| `split-size` | table property | Override `read.split.target-size` и metadata target size |
| `lookback` | table property | Override planning lookback |
| `file-open-cost` | table property | Override open-file cost |
| `vectorization-enabled` | table property | Override Parquet vectorization |
| `batch-size` | table property | Override vectorized batch size |
| `stream-from-timestamp` | none | Начало streaming read, ms; если раньше oldest ancestor, используется oldest |
| `streaming-max-files-per-micro-batch` | `INT_MAX` | Максимум файлов на micro-batch |
| `streaming-max-rows-per-micro-batch` | `INT_MAX` | Soft maximum rows: следующий файл включается целиком, дополнительные уже не добавляются при превышении |
| `async-micro-batch-planning-enabled` | `false` | Async prefetch planning |
| `streaming-snapshot-polling-interval-ms` | `30000` | Poll interval async planner |
| `async-queue-preload-file-limit` | `100` | Начальное число files в background queue |
| `async-queue-preload-row-limit` | `100000` | Начальное число rows в background queue |

### Write options

```scala
df.writeTo("catalog.db.table")
    .option("write-format", "avro")
    .option("snapshot-property.key", "value")
    .append()
```

| Option | Default | Описание |
| --- | --- | --- |
| `write-format` | `write.format.default` | Формат этой операции: parquet/avro/orc |
| `target-file-size-bytes` | table property | Override target file size |
| `check-nullability` | `true` | Проверка nullability |
| `snapshot-property.<custom-key>` | `null` | Добавляет custom key/value в snapshot summary; prefix обязателен только DSv2 |
| `fanout-enabled` | `false` | Override `write.spark.fanout.enabled` |
| `check-ordering` | `true` | Проверять соответствие порядка schema |
| `isolation-level` | `null` | `null` — без проверок; `serializable` — проверка concurrent inserts/deletes в destination partitions; `snapshot` — concurrent deletes |
| `validate-from-snapshot-id` | `null` | Base snapshot для conflict validation; если null — oldest known snapshot |
| `compression-codec` | table property | Override codec |
| `compression-level` | table property | Override level Parquet/Avro |
| `compression-strategy` | ORC table property | Override ORC strategy |
| `distribution-mode` | см. [[spark-writes#Режимы распределения при записи]] | Override write distribution |
| `delete-granularity` | `file` | Override delete granularity |
| `shred-variants` | `false` | Override variant shredding |
| `variant-inference-buffer-size` | `100` | Override inference buffer |
| `use-merge-append-for-streaming` | `false` | В streaming append использовать merge append вместо fast append, чтобы manifests merged на commit, а не накапливались как small manifests |

`CommitMetadata` позволяет добавлять custom metadata в snapshot summary во время SQL execution, например для аудита/change tracking:

```java
import org.apache.iceberg.spark.CommitMetadata;

Map<String, String> properties = Maps.newHashMap();
properties.put("property_key", "property_value");
CommitMetadata.withCommitProperties(properties,
        () -> {
            spark.sql("DELETE FROM " + tableName + " where id = 1");
            return 0;
        },
        RuntimeException.class);
```
