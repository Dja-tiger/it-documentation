---
title: "Flink — запросы"
tags: [apache-iceberg, flink, queries, streaming, metadata-tables]
source_project: apache/iceberg
source_file: docs/docs/flink-queries.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/flink-queries.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Flink Queries

Iceberg поддерживает streaming и batch reads через DataStream API и Table API Flink.

## Чтение через SQL

Execution mode переключается session setting:

```sql
set execution.runtime-mode = streaming;
set execution.runtime-mode = batch;
```

### Batch read

```sql
set execution.runtime-mode = batch;
select * from sample;
```

### Streaming read

Iceberg может читать incremental data, начиная с исторического snapshot ID:

```sql
set execution.runtime-mode = streaming;
set table.dynamic-table-options.enabled=true;

-- Прочитать current snapshot, затем incremental snapshots после него
select * from sample
/*+ options('streaming'='true', 'monitor-interval'='1s') */;

-- Начать incremental после указанного snapshot; сам snapshot исключается
select * from sample
/*+ options(
  'streaming'='true',
  'monitor-interval'='1s',
  'start-snapshot-id'='3821550127947089987') */;
```

Полный список — [[flink-configuration#Read options]].

### FLIP-27 source для SQL

FLIP-27 refactored Source interface объединяет batch/streaming source model. Настройка:

```sql
-- Для Flink 1.19 и ниже default false; для 1.20+ default true
set table.exec.iceberg.use-flip27-source = false;
```

Остальные SQL options применимы и к FLIP-27 source.

### Branches и tags через SQL

```sql
-- Branch b1
select * from table /*+ options('branch'='b1') */;

-- Tag t1
select * from table /*+ options('tag'='t1') */;

-- Incremental от tag t1 до t2
select * from table
/*+ options(
  'streaming'='true',
  'monitor-interval'='1s',
  'start-tag'='t1',
  'end-tag'='t2') */;
```

## Чтение через DataStream

### Batch read

```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.createLocalEnvironment();
TableLoader tableLoader = TableLoader.fromHadoopTable("hdfs://nn:8020/warehouse/path");
DataStream<RowData> batch = FlinkSource.forRowData()
     .env(env)
     .tableLoader(tableLoader)
     .streaming(false)
     .build();

batch.print();
env.execute("Test Iceberg Batch Read");
```

### Streaming read

```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.createLocalEnvironment();
TableLoader tableLoader = TableLoader.fromHadoopTable("hdfs://nn:8020/warehouse/path");
DataStream<RowData> stream = FlinkSource.forRowData()
     .env(env)
     .tableLoader(tableLoader)
     .streaming(true)
     .startSnapshotId(3821550127947089987L)
     .build();

stream.print();
env.execute("Test Iceberg Streaming Read");
```

## DataStream с FLIP-27 source

FLIP-27 source interface появился в Flink 1.12 для устранения ограничений старого `SourceFunction` и унификации batch/streaming. Большинство Flink connectors постепенно перешли на него. `IcebergSource` FLIP-27 находится в `iceberg-flink`; в документации 1.12.0 функциональность всё ещё отмечена как experimental.

### Batch

```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.createLocalEnvironment();
TableLoader tableLoader = TableLoader.fromHadoopTable("hdfs://nn:8020/warehouse/path");

IcebergSource<RowData> source = IcebergSource.forRowData()
    .tableLoader(tableLoader)
    .assignerFactory(new SimpleSplitAssignerFactory())
    .build();

DataStream<RowData> batch = env.fromSource(
    source,
    WatermarkStrategy.noWatermarks(),
    "My Iceberg Source",
    TypeInformation.of(RowData.class));

batch.print();
env.execute("Test Iceberg Batch Read");
```

### Streaming

Пример начинает с latest snapshot **inclusive** и каждые 60 секунд ищет новые append-only snapshots. CDC read пока не поддерживается.

```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.createLocalEnvironment();
TableLoader tableLoader = TableLoader.fromHadoopTable("hdfs://nn:8020/warehouse/path");

IcebergSource source = IcebergSource.forRowData()
    .tableLoader(tableLoader)
    .assignerFactory(new SimpleSplitAssignerFactory())
    .streaming(true)
    .streamingStartingStrategy(StreamingStartingStrategy.INCREMENTAL_FROM_LATEST_SNAPSHOT)
    .monitorInterval(Duration.ofSeconds(60))
    .build();

DataStream<RowData> stream = env.fromSource(
    source,
    WatermarkStrategy.noWatermarks(),
    "My Iceberg Source",
    TypeInformation.of(RowData.class));

stream.print();
env.execute("Test Iceberg Streaming Read");
```

### Branches/tags через DataStream

```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.createLocalEnvironment();
TableLoader tableLoader = TableLoader.fromHadoopTable("hdfs://nn:8020/warehouse/path");

DataStream<RowData> branch = FlinkSource.forRowData()
    .env(env)
    .tableLoader(tableLoader)
    .branch("test-branch")
    .streaming(false)
    .build();

DataStream<RowData> tag = FlinkSource.forRowData()
    .env(env)
    .tableLoader(tableLoader)
    .tag("test-tag")
    .streaming(false)
    .build();

DataStream<RowData> incremental = FlinkSource.forRowData()
    .env(env)
    .tableLoader(tableLoader)
    .streaming(true)
    .startTag("test-tag")
    .build();
```

### Avro GenericRecord

FLIP-27 `IcebergSource` содержит `AvroGenericRecordReaderFunction`, преобразующий Iceberg rows в Avro `GenericRecord`.

Требования:

- `flink-avro` в classpath;
- нельзя использовать shaded `iceberg-flink-runtime`, потому что он shades Avro package; используйте non-shaded `iceberg-flink`.

```java
TableLoader tableLoader = ...;
Table table;
try (TableLoader loader = tableLoader) {
    loader.open();
    table = loader.loadTable();
}

AvroGenericRecordReaderFunction readerFunction =
    AvroGenericRecordReaderFunction.fromTable(table);

IcebergSource<GenericRecord> source =
    IcebergSource.<GenericRecord>builder()
        .tableLoader(tableLoader)
        .readerFunction(readerFunction)
        .assignerFactory(new SimpleSplitAssignerFactory())
        .build();

DataStream<Row> stream = env.fromSource(
    source,
    WatermarkStrategy.noWatermarks(),
    "Iceberg Source as Avro GenericRecord",
    new GenericRecordAvroTypeInfo(avroSchema));
```

## Watermarks из IcebergSource

Source-generated watermarks полезны для Flink Watermark Alignment и для предотвращения преждевременного trigger окон при concurrent чтении files.

Задайте `watermarkColumn`. Поддерживаются Iceberg types:

- `timestamp`;
- `timestamptz`;
- `long`.

Timestamp types уже несут precision. Для `long` нужно задать `watermarkTimeUnit`.

Watermarks строятся по column metrics data files и emit один раз на split. Если split объединяет много small files с разными time ranges, out-of-order window увеличивается и Flink state вынужден буферизовать больше данных. Для Watermark Alignment рекомендуется увеличить `read.split.open-file-cost`, чтобы small files не объединялись в один split. Цена — меньший read throughput при большом числе small files.

Функция требует column-level min/max statistics для watermark column. По умолчанию metrics собираются для первых 100 columns. При необходимости настройте `write.metadata.metrics.*`.

Timestamp watermark:

```java
DataStream<RowData> stream =
    env.fromSource(
        IcebergSource.forRowData()
            .tableLoader(tableLoader)
            .watermarkColumn("timestamp_column")
            .build(),
        WatermarkStrategy.<RowData>noWatermarks()
            .withTimestampAssigner(
                (record, eventTime) -> record.getTimestamp(pos, precision).getMillisecond()),
        SOURCE_NAME,
        TypeInformation.of(RowData.class));
```

Long watermark + alignment:

```java
DataStream<RowData> stream =
    env.fromSource(
        IcebergSource.forRowData()
            .tableLoader(tableLoader)
            .set(
                FlinkReadOptions.SPLIT_FILE_OPEN_COST,
                String.valueOf(TableProperties.SPLIT_SIZE_DEFAULT))
            .watermarkColumn("long_column")
            .watermarkTimeUnit(TimeUnit.MILLI_SCALE)
            .build(),
        WatermarkStrategy.<RowData>noWatermarks()
            .withWatermarkAlignment(watermarkGroup, maxAllowedWatermarkDrift),
        SOURCE_NAME,
        TypeInformation.of(RowData.class));
```

## Options

Read options можно задавать Java builder, SQL hint или частично session configuration. Полный reference: [[flink-configuration#Read options]].

## Metadata tables

Metadata table указывается через `$`: history для `db.table` → `db.table$history`.

### History

```sql
select * from prod.db.table$history;
```

| made_current_at | snapshot_id | parent_id | is_current_ancestor |
| --- | --- | --- | --- |
| 2019-02-08 03:29:51.215 | 5781947118336215154 | null | true |
| 2019-02-08 03:47:55.948 | 5179299526185056830 | 5781947118336215154 | true |
| 2019-02-09 16:24:30.13 | 296410040247533544 | 5179299526185056830 | false |
| 2019-02-09 16:32:47.336 | 2999875608062437330 | 5179299526185056830 | true |

`is_current_ancestor=false` означает snapshot из rollback lineage, который не является ancestor current state.

### Metadata Log Entries

```sql
select * from prod.db.table$metadata_log_entries;
```

| timestamp | file | latest_snapshot_id | latest_schema_id | latest_sequence_number |
| --- | --- | --- | --- | --- |
| 2022-07-28 10:43:52.93 | `s3://.../00000-....metadata.json` | null | null | null |
| 2022-07-28 10:43:57.487 | `s3://.../00001-....metadata.json` | 170260833677645300 | 0 | 1 |

### Snapshots

```sql
select * from prod.db.table$snapshots;
```

| committed_at | snapshot_id | parent_id | operation | manifest_list | summary |
| --- | --- | --- | --- | --- | --- |
| 2019-02-08 03:29:51.215 | 57897183625154 | null | append | `s3://.../snap-...avro` | `{..., flink.job-id -> 2e274e...}` |

History + application ID:

```sql
select
    h.made_current_at,
    s.operation,
    h.snapshot_id,
    h.is_current_ancestor,
    s.summary['flink.job-id']
from prod.db.table$history h
join prod.db.table$snapshots s
  on h.snapshot_id = s.snapshot_id
order by made_current_at;
```

### Files

```sql
select * from prod.db.table$files;
```

Содержит current data files и file-level metadata: `content`, `file_path`, format, spec/partition, record count, size, column/value/null/nan counts, lower/upper bounds, key metadata, split offsets, equality IDs, sort order ID.

### Manifests

```sql
select * from prod.db.table$manifests;
```

Возвращает path/length/spec, snapshot ID, added/existing/deleted file counts и `partition_summaries`. `partition_summaries` fields соответствуют manifest `field_summary` в порядке: `contains_null`, `contains_nan`, `lower_bound`, `upper_bound`. `contains_nan=null` означает, что metadata не содержат этот признак, обычно в v1 tables.

### Partitions

```sql
select * from prod.db.table$partitions;
```

Содержит partition/spec ID, record/file counts, data bytes, position/equality delete counts и last-updated metadata. Для unpartitioned table fields `partition` и `spec_id` отсутствуют.

### All Metadata Tables

> [!danger]
> `all_*` tables могут возвращать более одной row на один data/manifest file, потому что metadata file может участвовать в нескольких snapshots.

Все data files:

```sql
select * from prod.db.table$all_data_files;
```

Все manifests:

```sql
select * from prod.db.table$all_manifests;
```

### References

```sql
select * from prod.db.table$refs;
```

| name | type | snapshot_id | max_reference_age_in_ms | min_snapshots_to_keep | max_snapshot_age_in_ms |
| --- | --- | --- | --- | --- | --- |
| main | BRANCH | 4686954189838128572 | 10 | 20 | 30 |
| testTag | TAG | 4686954189838128572 | 10 | null | null |
