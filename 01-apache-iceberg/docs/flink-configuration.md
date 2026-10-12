---
title: "Flink — конфигурация"
tags: [apache-iceberg, flink, configuration]
source_project: apache/iceberg
source_file: docs/docs/flink-configuration.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/flink-configuration.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Flink Configuration

## Catalog configuration

```sql
create catalog <catalog_name> with (
  'type'='iceberg',
  '<config_key>'='<config_value>'
);
```

Общие properties:

| Property | Required | Values | Описание |
| --- | --- | --- | --- |
| `type` | ✔ | `iceberg` | Должен быть `iceberg` |
| `catalog-type` | — | `hive`, `hadoop`, `rest` | Built-in implementation; при custom `catalog-impl` не задавать |
| `catalog-impl` | — | class | Fully-qualified custom catalog; обязателен, если `catalog-type` отсутствует |
| `property-version` | — | `1` | Версия формата properties для backward compatibility |
| `cache-enabled` | — | true/false | Default `true` |
| `cache.expiration-interval-ms` | — | ms | Default `-1` без expiration; `0` запрещён |

Hive:

| Property | Required | Описание |
| --- | --- | --- |
| `uri` | ✔ | HMS Thrift URI |
| `clients` | — | HMS pool size, default 2 |
| `warehouse` | — | Warehouse location |
| `hive-conf-dir` | — | Каталог с `hive-site.xml`; `warehouse` override `hive.metastore.warehouse.dir` |
| `hadoop-conf-dir` | — | Каталог с `core-site.xml`, `hdfs-site.xml` |

Hadoop: `warehouse` required.

REST: `uri` required, `credential` и `token` optional.

## Runtime configuration

### Read options

Java builder:

```java
IcebergSource.forRowData()
    .tableLoader(TableLoader.fromCatalog(...))
    .assignerFactory(new SimpleSplitAssignerFactory())
    .streaming(true)
    .streamingStartingStrategy(StreamingStartingStrategy.INCREMENTAL_FROM_SNAPSHOT_ID)
    .startSnapshotId(3821550127947089987L)
    .monitorInterval(Duration.ofMillis(10L))
    .build();
```

SQL hint:

```sql
select * from tableName /*+ options('monitor-interval'='10s') */;
```

Некоторые options можно установить session-wide в Flink configuration:

```java
env.getConfig()
    .getConfiguration()
    .set(FlinkReadOptions.SPLIT_FILE_OPEN_COST_OPTION, 1000L);
```

Приоритет: **Read option → Flink configuration → Table property**.

| Read option | Flink configuration | Table property | Default | Описание |
| --- | --- | --- | --- | --- |
| `snapshot-id` | N/A | N/A | null | Time travel batch по snapshot ID |
| `case-sensitive` | `connector.iceberg.case-sensitive` | N/A | false | Case-sensitive column matching |
| `as-of-timestamp` | N/A | N/A | null | Latest snapshot на заданный timestamp ms |
| `starting-strategy` | `connector.iceberg.starting-strategy` | N/A | `INCREMENTAL_FROM_LATEST_SNAPSHOT` | Streaming start strategy: `TABLE_SCAN_THEN_INCREMENTAL`, `INCREMENTAL_FROM_LATEST_SNAPSHOT`, `INCREMENTAL_FROM_LATEST_SNAPSHOT_EXCLUSIVE`, `INCREMENTAL_FROM_EARLIEST_SNAPSHOT`, `INCREMENTAL_FROM_SNAPSHOT_ID`, `INCREMENTAL_FROM_SNAPSHOT_TIMESTAMP` (последняя для FLIP-27) |
| `start-snapshot-timestamp` | N/A | N/A | null | Latest snapshot as of timestamp ms, начало incremental |
| `start-snapshot-id` | N/A | N/A | null | Start snapshot |
| `end-snapshot-id` | N/A | N/A | latest | End snapshot |
| `branch` | N/A | N/A | `main` | Branch batch read |
| `tag` | N/A | N/A | null | Tag batch read |
| `start-tag` | N/A | N/A | null | Start tag incremental |
| `end-tag` | N/A | N/A | null | End tag incremental |
| `split-size` | `connector.iceberg.split-size` | `read.split.target-size` | 128 MB | Target combined input split |
| `split-lookback` | `connector.iceberg.split-lookback` | `read.split.planning-lookback` | 10 | Bins considered при combining |
| `split-file-open-cost` | `connector.iceberg.split-file-open-cost` | `read.split.open-file-cost` | 4 MB | Estimated file-open cost |
| `streaming` | `connector.iceberg.streaming` | N/A | false | Streaming/batch mode |
| `monitor-interval` | `connector.iceberg.monitor-interval` | N/A | 60s | Poll новых snapshots |
| `include-column-stats` | `connector.iceberg.include-column-stats` | N/A | false | Загружать value/null counts и bounds для data files |
| `max-planning-snapshot-count` | `connector.iceberg.max-planning-snapshot-count` | N/A | `Integer.MAX_VALUE` | Snapshots за enumeration в streaming |
| `limit` | `connector.iceberg.limit` | N/A | -1 | Max output rows |
| `max-allowed-planning-failures` | `connector.iceberg.max-allowed-planning-failures` | N/A | 3 | Consecutive planning failures; -1 никогда не fail job |
| `watermark-column` | `connector.iceberg.watermark-column` | N/A | null | Watermark column; заменяет split assigner на `OrderedSplitAssignerFactory` |
| `watermark-column-time-unit` | `connector.iceberg.watermark-column-time-unit` | N/A | `MICROSECONDS` | Для long watermark: DAYS/HOURS/MINUTES/SECONDS/MILLISECONDS/MICROSECONDS/NANOSECONDS |

### Write options

```java
FlinkSink.Builder builder = FlinkSink.forRow(dataStream, SimpleDataUtil.FLINK_SCHEMA)
    .table(table)
    .tableLoader(tableLoader)
    .set("write-format", "orc")
    .set(FlinkWriteOptions.OVERWRITE_MODE, "true");
```

```sql
insert into tableName /*+ options('upsert-enabled'='true') */
select ...;
```

| Flink option | Default | Описание |
| --- | --- | --- |
| `write-format` | `write.format.default` | parquet/avro/orc |
| `target-file-size-bytes` | table property | Override target size |
| `upsert-enabled` | `write.upsert.enabled` | Override upsert |
| `overwrite-enabled` | false | Overwrite; нельзя вместе с UPSERT |
| `distribution-mode` | `write.distribution-mode` | Override; RANGE experimental |
| `range-distribution-statistics-type` | `Auto` | `Map`, `Sketch`, `Auto` |
| `range-distribution-sort-key-base-weight` | `0.0` | Base weight sort key относительно target traffic per writer |
| `compression-codec` | table property | Codec |
| `compression-level` | table property | Parquet/Avro level |
| `compression-strategy` | ORC table property | ORC strategy |
| `write-parallelism` | upstream operator | Writer parallelism |
| `branch` | `main` | Target branch |
| `uid-suffix` | table property | UID suffix IcebergSink |
| `shred-variants` | table property | Variant shredding |
| `variant-inference-buffer-size` | table property | Variant inference rows |
| `flink-maintenance.rewrite.enabled` | false | Post-commit compaction в SinkV2 |
| `flink-maintenance.expire-snapshots.enabled` | false | Post-commit expiration |
| `flink-maintenance.delete-orphan-files.enabled` | false | Post-commit orphan cleanup |
| `flink-maintenance.convert-equality-deletes.enabled` | false | Equality deletes → DVs; format v3 + equality fields |

#### Range statistics type

- `Map` — точный count каждого key; low cardinality (сотни/тысячи);
- `Sketch` — reservoir sampling; high cardinality (миллионы), низкий memory footprint;
- `Auto` — начинает с Map, при cardinality > 10 000 переключается на Sketch.

#### Range sort-key base weight

`range-distribution-sort-key-base-weight=0.0` задаёт минимальный относительный вес каждого sort key. Это предотвращает слишком большое количество small files, если sort key совпадает с partition value, а long-tail partitions имеют мало traffic.

Например, writer parallelism = 10, total traffic weight = 10 000, target на writer = 1 000. Значение `2.0` даёт каждому key минимум 2% target (=20), то есть на writer окажется не более ~50 малых partition files, даже если реальные веса этих keys малы.

Эта настройка применима к `StatisticsType.Map`. Для `Sketch` high-cardinality columns обычно не должны быть partition columns: иначе появится слишком много partitions/small files; sketch partitioner делит key space на ordered ranges.

### Execution options

Session SQL:

```sql
set 'table.exec.iceberg.infer-source-parallelism' = 'false';
```

| Flink configuration | Default | Описание |
| --- | --- | --- |
| `table.exec.iceberg.infer-source-parallelism` | true | Batch source parallelism выводится из числа scan splits, ограничивается max и query limit; streaming не infer |
| `table.exec.iceberg.infer-source-parallelism.max` | 100 | Max inferred source parallelism |
| `table.exec.iceberg.fetch-batch-record-count` | 2048 | Target records per fetch batch source reader |
| `table.exec.iceberg.worker-pool-size` | `max(2, available cpu)` | Pool planning/scanning manifests; связан с `iceberg.worker.num-threads` |
| `table.exec.iceberg.use-v2-sink` | false | Включить SinkV2 `IcebergSink`; см. [[flink-writes#SinkV2 implementation]] |
