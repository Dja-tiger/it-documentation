---
title: "Flink — запись"
tags: [apache-iceberg, flink, writes, upsert, sink]
source_project: apache/iceberg
source_file: docs/docs/flink-writes.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/flink-writes.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Flink Writes

Iceberg поддерживает batch и streaming writes через DataStream API и Table API Flink. Flink Iceberg sink обеспечивает **exactly-once semantics**.

## Запись через SQL

Поддерживаются `insert into` и `insert overwrite`.

### `insert into`

Append из streaming job:

```sql
insert into `hive_catalog`.`default`.`sample` values (1, 'a');
insert into `hive_catalog`.`default`.`sample`
select id, data from other_kafka_table;
```

### `insert overwrite`

Overwrite доступен в batch job; streaming job `insert overwrite` не поддерживает. Для Iceberg overwrite атомарен.

```sql
insert overwrite sample values (1, 'a');
```

Конкретная partition:

```sql
insert overwrite `hive_catalog`.`default`.`sample`
partition(data='a')
select 6;
```

Для partitioned table:

- если в `partition` заданы **все** partition columns — static partition overwrite;
- если задан только prefix partition columns — query result записывается в dynamic partitions.

Для unpartitioned table `insert overwrite` полностью заменяет данные.

### `upsert`

Iceberg поддерживает UPSERT по primary key для format v2.

Вариант 1 — table property:

```sql
create table `hive_catalog`.`default`.`sample` (
    `id` int comment 'unique id',
    `data` string not null,
    primary key(`id`) not enforced
) with (
    'format-version'='2',
    'write.upsert.enabled'='true'
);
```

Это применяется ко всем write paths, если не override write option.

Вариант 2 — per-write hint:

```sql
insert into tableName /*+ options('upsert-enabled'='true') */
select ...;
```

Нужны format v2 и primary key / identifier fields.

> [!info]
> OVERWRITE и UPSERT взаимно исключаются. Для partitioned table в UPSERT source columns, на которых основаны partition transforms, должны входить в equality fields. Например, при `days(ts)` колонка `ts` должна входить в equality fields.

## Запись через DataStream

### Append

```java
StreamExecutionEnvironment env = ...;

DataStream<RowData> input = ... ;
Configuration hadoopConf = new Configuration();
TableLoader tableLoader = TableLoader.fromHadoopTable(
    "hdfs://nn:8020/warehouse/path",
    hadoopConf);

FlinkSink.forRowData(input)
    .tableLoader(tableLoader)
    .append();

env.execute("Test Iceberg DataStream");
```

Поддерживаются `DataStream<RowData>` и `DataStream<Row>`.

### Overwrite

```java
FlinkSink.forRowData(input)
    .tableLoader(tableLoader)
    .overwrite(true)
    .append();
```

### Upsert

Table должна быть v2 и иметь primary key:

```java
FlinkSink.forRowData(input)
    .tableLoader(tableLoader)
    .upsert(true)
    .append();
```

> [!info]
> Overwrite и upsert одновременно включать нельзя. Для partition transforms source columns должны входить в equality fields.

### Avro GenericRecord

`AvroGenericRecordToRowDataMapper` преобразует Avro `GenericRecord` в Flink `RowData`.

Требования:

- добавить `flink-avro` в classpath;
- не использовать shaded `iceberg-flink-runtime`, поскольку он shades Avro package; использовать non-shaded `iceberg-flink`.

```java
DataStream<org.apache.avro.generic.GenericRecord> dataStream = ...;

Schema icebergSchema = table.schema();

// Avro schema converted from Iceberg cannot be used directly because
// Iceberg time precision is microseconds while Flink Avro converters use milliseconds.
org.apache.avro.Schema avroSchema =
    AvroSchemaUtil.convert(icebergSchema, table.name());

GenericRecordAvroTypeInfo avroTypeInfo =
    new GenericRecordAvroTypeInfo(avroSchema);
RowType rowType = FlinkSchemaUtil.convert(icebergSchema);

FlinkSink.builderFor(
    dataStream,
    AvroGenericRecordToRowDataMapper.forAvroSchema(avroSchema),
    FlinkCompatibilityUtil.toTypeInfo(rowType))
  .table(table)
  .tableLoader(tableLoader)
  .append();
```

### Branch writes

```java
FlinkSink.forRowData(input)
    .tableLoader(tableLoader)
    .toBranch("audit-branch")
    .append();
```

## Метрики sink

### `IcebergStreamWriter`

Tags:

- `table` — полное имя, например `iceberg.my_db.my_table`;
- `subtask_index` — индекс writer subtask с 0.

| Metric | Type | Описание |
| --- | --- | --- |
| `lastFlushDurationMs` | Gauge | Время flush/upload writer subtask на checkpoint, ms |
| `flushedDataFiles` | Counter | Flushed/uploaded data files |
| `flushedDeleteFiles` | Counter | Flushed/uploaded delete files |
| `flushedReferencedDataFiles` | Counter | Data files, на которые ссылаются flushed delete files |
| `dataFilesSizeHistogram` | Histogram | Distribution размеров data files, bytes |
| `deleteFilesSizeHistogram` | Histogram | Distribution размеров delete files, bytes |

Histogram metrics требуют `org.apache.flink:flink-metrics-dropwizard`, который Flink не поставляет по умолчанию. Без него остальные metrics продолжают публиковаться, histograms отсутствуют.

### `IcebergFilesCommitter`

Tag: `table`.

| Metric | Type | Описание |
| --- | --- | --- |
| `lastCheckpointDurationMs` | Gauge | Время checkpoint state committer |
| `lastCommitDurationMs` | Gauge | Время Iceberg commit |
| `committedDataFilesCount` | Counter | Committed data files |
| `committedDataFilesRecordCount` | Counter | Records в committed data files |
| `committedDataFilesByteCount` | Counter | Bytes data files |
| `committedDeleteFilesCount` | Counter | Delete files |
| `committedDeleteFilesRecordCount` | Counter | Records delete files |
| `committedDeleteFilesByteCount` | Counter | Bytes delete files |
| `elapsedSecondsSinceLastSuccessfulCommit` | Gauge | Секунды с последнего успешного Iceberg commit |

`elapsedSecondsSinceLastSuccessfulCommit` удобна для alerting. Iceberg commit выполняется после успешного Flink checkpoint в `notifyCheckpointComplete`, но возможны ситуации, когда Flink checkpoints успешны, а Iceberg commits падают, либо callback не вызывается. При checkpoint interval 5 минут разумный alert example: `elapsedSecondsSinceLastSuccessfulCommit > 60 minutes`.

## Write options

Java:

```java
FlinkSink.Builder builder = FlinkSink.forRow(dataStream, SimpleDataUtil.FLINK_SCHEMA)
    .table(table)
    .tableLoader(tableLoader)
    .set("write-format", "orc")
    .set(FlinkWriteOptions.OVERWRITE_MODE, "true");
```

SQL:

```sql
insert into tableName /*+ options('upsert-enabled'='true') */
select ...;
```

Полный reference: [[flink-configuration#Write options]].

## Distribution mode

Streaming writer поддерживает `HASH` и `RANGE`. Настраивается `FlinkSink.Builder.distributionMode(...)` или write option.

### HASH

Hash distribution делает shuffle по:

- partition key для partitioned table;
- equality fields для unpartitioned table.

Используется Flink `DataStream#keyBy`.

Ограничения:

1. Плохо работает со skewed data.
2. При низкой cardinality partition/equality key может давать неравномерный traffic.
3. Writer parallelism фактически ограничен cardinality hash key: при 10 distinct keys traffic получат не более 10 writer tasks, даже если configured parallelism выше.

### RANGE — experimental

Range distribution использует partition key или table sort order и custom range partitioner. Он собирает traffic statistics и строит ranges так, чтобы равномернее распределять data между writers.

RANGE выполняет только shuffle по ranges; rows **не сортируются внутри data file**, потому что streaming writer это пока не поддерживает.

#### Сценарии

RANGE применим, если table:

- partitioned;
- имеет SortOrder.

Если partitioned table не имеет SortOrder, в качестве sort key используются partition columns. Если SortOrder задан — используется он.

Range полезен при skew:

- recent event-time partitions значительно тяжелее long-tail historical partitions;
- country code с очень разным traffic;
- event type с hot categories.

Также он может кластеризовать по non-partition column: например table partitioned по ingestion hour, а queries фильтруют `device_id`/`country_code`. SortOrder по такой колонке может улучшить pruning/read performance.

#### Traffic statistics

Каждый shuffle subtask собирает statistics; coordinator агрегирует их каждый checkpoint и broadcast обратно subtasks. Новая distribution может примениться только в следующем checkpoint, поэтому реакция на изменение traffic занимает до двух checkpoint cycles.

Low cardinality: `HashMap` считает traffic каждого key. Новый key до обучения distribution round-robin распределяется по writers.

High cardinality: reservoir sampling строит ranges без хранения всех keys. Memory/network footprint низкий, но один очень hot key может всё равно создать imbalance.

#### Usage

```java
FlinkSink.forRowData(input)
    .distributionMode(DistributionMode.RANGE)
    .rangeDistributionStatisticsType(StatisticsType.Auto)
    .rangeDistributionSortKeyBaseWeight(0.0d)
    .append();
```

### Overhead

Hash/range shuffle требует serialization/deserialization и network I/O, поэтому CPU usage растёт. RANGE дополнительно собирает и агрегирует statistics. При `Auto` memory overhead обычно небольшой; `Map` нельзя использовать при высокой cardinality — возможны большой heap footprint и network exchange.

## Важное замечание для streaming jobs

Flink streaming writes хранят last committed checkpoint ID в snapshot summary, а uncommitted data — во временных files. Поэтому [[maintenance#Expire snapshots|expiration snapshots]] и [[maintenance#Удаление orphan files|orphan cleanup]] способны повредить состояние job, если retention слишком короткий.

Сохраняйте последний snapshot данного Flink job — он определяется `flink.job-id` в snapshot summary — и удаляйте только достаточно старые orphan files.

## SinkV2 implementation

Первоначальный `FlinkSink` создан до появления современного Flink SinkV2 API и реализован custom chain `StreamOperator`, заканчивающийся `DiscardingSink`.

Flink 1.15 добавил SinkV2 (FLIP-191). На нём построен новый `IcebergSink`, который служит основой для table maintenance и других функций. В Iceberg 1.12.0 implementation всё ещё помечена experimental.

### SQL

```sql
set table.exec.iceberg.use-v2-sink = true;
```

### DataStream

Замените `FlinkSink` на `IcebergSink` в examples.

> [!warning]
> В `IcebergSink` используется `uidSuffix`, а не `uidPrefix`.

### Post-commit maintenance

`IcebergSink` может запускать maintenance после каждого commit без отдельного maintenance job:

- `rewriteDataFiles()` — compaction;
- `expireSnapshots()`;
- `deleteOrphanFiles()`;
- `convertEqualityDeletes()` — equality deletes → deletion vectors; нужны equality fields и format >= 3.

```java
IcebergSink.forRowData(dataStream)
    .table(table)
    .tableLoader(tableLoader)
    .upsert(true)
    .equalityFieldColumns(List.of("id"))
    .rewriteDataFiles()
    .convertEqualityDeletes()
    .append();
```

Полный reference: [[flink-maintenance#IcebergSink с post-commit integration]].

## Flink Dynamic Iceberg Sink

Dynamic Sink позволяет:

1. писать из одного sink в произвольное число Iceberg tables;
2. динамически создавать и обновлять tables по user routing logic;
3. динамически выполнять schema и partition evolution без restart Flink job.

Вся routing/configuration информация передаётся через `DynamicRecord`.

```java
DynamicIcebergSink.forInput(dataStream)
    .generator((inputRecord, out) -> out.collect(
        new DynamicRecord(
            TableIdentifier.of("db", "table"),
            "branch",
            SCHEMA,
            (RowData) inputRecord,
            PartitionSpec.unpartitioned(),
            DistributionMode.HASH,
            2)))
    .catalogLoader(CatalogLoader.hive("hive", new Configuration(), Map.of()))
    .writeParallelism(10)
    .immediateTableUpdate(true)
    .append();
```

### Configuration example

```java
DynamicIcebergSink.Builder<RowData> builder =
    DynamicIcebergSink.forInput(inputStream);

builder.set("write.parquet.compression-codec", "gzip");

builder
    .writeParallelism(4)
    .uidPrefix("dynamic-sink")
    .cacheMaxSize(500)
    .cacheRefreshMs(5000);

builder.generator(new CustomRecordGenerator());
builder.append();
```

### Dynamic routing

```java
public class CustomRecordGenerator implements DynamicRecordGenerator<RowData> {
    @Override
    public DynamicRecord generate(RowData row) {
        DynamicRecord record = new DynamicRecord();
        TableIdentifier tableIdentifier = TableIdentifier.of(database, tableName);
        record.setTableIdentifier(tableIdentifier);
        record.setData(row);
        record.writeParallelism(2);
        return record;
    }
}

DynamicIcebergSink.Builder<RowData> builder =
    DynamicIcebergSink.forInput(inputStream);
builder.generator(new CustomRecordGenerator());
builder.append();
```

На каждую input row generator должен сформировать `DynamicRecord`:

| Property | Описание |
| --- | --- |
| `TableIdentifier` | Target table |
| `Branch` | Target branch, optional |
| `Schema` | Schema record |
| `Spec` | Ожидаемый partition spec |
| `RowData` | Row payload |
| `DistributionMode` | `NONE`, `HASH` или `null`. При `null` shuffle отсутствует, кроме случая непустых equality fields — тогда fallback HASH |
| `Parallelism` | Max writers для конкретного table/branch/schema/spec WriteTarget |
| `UpsertMode` | Override `write.upsert.enabled`, optional |
| `EqualityFields` | Equality fields; если unset, используются schema identifier fields для distribution и delete inference. Identifier fields сами по себе upsert не включают |

### Schema evolution Dynamic Sink

Алгоритм:

1. Если input schema точно совпадает с одной из table schemas — используется она.
2. Иначе sink пытается адаптировать input под существующую schema, например добавить `null` для optional column table.
3. Если это невозможно — эволюционирует table schema в рамках разрешённых изменений.

Поддерживается:

- add columns;
- widening (`Integer` → `Long`, `Float` → `Double`);
- required → optional;
- drop columns — **выключено по умолчанию**.

Drop выключен из-за late/out-of-order data. После удаления field остаётся в historical schemas, но обычные queries его уже не видят. Если позже появится column с тем же именем, будет создан новый field ID; historical значения старой column к ней не относятся.

Не поддерживается rename columns: matching основан на именах, а rename потребовал бы внешних hints/metadata.

### Caching

Два независимых cache:

- table metadata cache — schema/spec и другие metadata; `cacheMaxSize`;
- input schema cache — schemas и результаты compatibility per table; `inputSchemasPerTableCacheMaxSize`.

При несовместимой schema trigger update выполняется immediate либо centralized executor согласно `immediateTableUpdate`. Centralized update снижает нагрузку на Catalog, но может создавать backpressure.

Для лучшего cache hit-rate переиспользуйте один и тот же object `DynamicRecord.schema`, если schema не меняется.

### Builder configuration

| Method | Описание |
| --- | --- |
| `overwrite(boolean)` | Overwrite mode |
| `writeParallelism(int)` | Writer parallelism |
| `uidPrefix(String)` | Operator UID prefix |
| `snapshotProperties(Map)` | Snapshot metadata |
| `toBranch(String)` | Branch |
| `cacheMaxSize(int)` | Table metadata cache size |
| `cacheRefreshMs(long)` | Refresh interval |
| `inputSchemasPerTableCacheMaxSize(int)` | Input schemas per table cache |
| `immediateTableUpdate(boolean)` | Immediate schema/spec update; default false |
| `set(String,String)` | Iceberg write property |
| `setAll(Map)` | Несколько properties |
| `tableCreator(TableCreator)` | Custom create table properties/location |
| `dropUnusedColumns(boolean)` | Разрешить drop columns, отсутствующих во входной schema |
| `shuffleSinkSlotSharingGroup(String)` | Slot sharing group shuffle sink |
| `generatorSlotSharingGroup(String)` | Slot sharing group generator + forward sink chain |

### Distribution modes Dynamic Sink

| Mode | Behavior |
| --- | --- |
| `NONE` | Round-robin writers; если equality fields заданы — по equality fields |
| `HASH` | Partition key либо equality fields; одинаковая partition/key идёт одному writer |
| `null` | Forward mode без distribution/shuffle |

#### Forward mode

Constructor `DynamicRecord` без `distributionMode` создаёт forward path. Records идут processor → writer по forward edge, позволяя Flink operator chaining. Это полезно для high-throughput pipelines, где upstream уже правильно распределяет данные и network shuffle слишком дорог.

Table metadata updates здесь всегда immediate независимо от `immediateTableUpdate`, потому что отдельный table-update operator намеренно отсутствует.

В одной pipeline можно смешивать regular и forward records:

- **shuffle sink** — normal HASH/round-robin distribution;
- **forward sink** — bypass distribution; `writeParallelism` sink не применяется.

> [!warning]
> 1. Schema changes в forward path всегда immediate; при high volume это может создавать много конфликтующих Catalog commits и временно снижать throughput. Желательно заранее обновлять schema либо учитывать temporary disruption.
> 2. Forward path полностью пропускает distribution, поэтому upstream обязан корректно распределить данные; иначе writes будут skewed/unbalanced.

### Notes

- `RANGE` Dynamic Sink пока не поддерживает; при указании fallback в `HASH`.
- Sink properties имеют приоритет над table properties.
- Dynamic Sink не поддерживает upgrade table format version на лету. Job не должен работать во время upgrade v2 → v3.
