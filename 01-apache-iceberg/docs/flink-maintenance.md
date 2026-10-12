---
title: "Flink TableMaintenance"
tags: [apache-iceberg, flink, maintenance, compaction, snapshots, deletion-vectors]
source_project: apache/iceberg
source_file: docs/docs/flink-maintenance.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/flink-maintenance.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Flink TableMaintenance

## Flink Table Maintenance — Batch Mode

### Rewrite files action

Iceberg предоставляет API для объединения small files в более крупные через Flink batch jobs. Поведение Flink action соответствует [[maintenance#Компактизация data files|Spark rewriteDataFiles]].

```java
import org.apache.iceberg.flink.actions.Actions;

TableLoader tableLoader = TableLoader.fromCatalog(
    CatalogLoader.hive("my_catalog", configuration, properties),
    TableIdentifier.of("database", "table")
);

Table table = tableLoader.loadTable();
RewriteDataFilesActionResult result = Actions.forTable(table)
        .rewriteDataFiles()
        .execute();
```

Подробности API см. в Javadoc `RewriteDataFilesAction` соответствующей версии Iceberg.

## Flink Table Maintenance — Streaming Mode

### Обзор

Для Iceberg-таблиц в Flink streaming environments автоматизированное обслуживание — expiration snapshots, compaction small files и cleanup orphan files — критично для производительности запросов, управляемого объёма metadata и эффективного использования storage.

Исторически такие операции в основном выполнялись Iceberg Spark Actions, что вынуждало поддерживать отдельную Spark-инфраструктуру даже тогда, когда основной data pipeline работал на Flink. Это увеличивало архитектурную и эксплуатационную сложность.

`TableMaintenance` API позволяет Flink jobs выполнять maintenance **нативно**: либо как часть существующего streaming pipeline, либо как отдельный Flink job. Это уменьшает зависимость от внешних compute systems и упрощает автоматизацию.

### Поддерживаемые задачи

#### ExpireSnapshots

Удаляет старые snapshots и связанные с ними более не используемые files. При commit внутри используется `cleanExpiredFiles(true)`, поэтому expired metadata/files очищаются автоматически.

```java
.add(ExpireSnapshots.builder()
    .maxSnapshotAge(Duration.ofDays(7))
    .retainLast(10)
    .deleteBatchSize(1000))
```

#### RewriteDataFiles

Compact small files до целевого размера. Поддерживает partial-progress commits и ограничение максимального объёма rewrite за один запуск.

```java
.add(RewriteDataFiles.builder()
    .targetFileSizeBytes(256 * 1024 * 1024)
    .minFileSizeBytes(32 * 1024 * 1024)
    .partialProgressEnabled(true)
    .partialProgressMaxCommits(5))
```

#### DeleteOrphanFiles

Удаляет files, которые не referenced ни одним metadata file Iceberg table и потому считаются orphan. Проверяется table location.

```java
.add(DeleteOrphanFiles.builder()
    .minAge(Duration.ofDays(3))
    .deleteBatchSize(1000))
```

#### ConvertEqualityDeletes

Преобразует equality delete files, staged в source branch, в deletion vectors (DV) target branch. Требуется table format version **>= 3**, поскольку DVs появились в format v3.

Типичный сценарий: Flink `IcebergSink` пишет новые data files и equality deletes в staging branch; converter разрешает equality conditions в row positions, строит DVs и commit одновременно data files + DVs в target branch.

Один trigger запускает один conversion cycle. Pipeline разбит на parallel stages:

`planner → reader → PK index → DV writer → committer`

Задача использует тот же maintenance-framework lock, что и остальные задачи, поэтому compaction и conversion одной таблицы не выполняются конкурентно.

```java
.add(ConvertEqualityDeletes.builder()
    .stagingBranch("staging")
    .equalityFieldColumns(ImmutableList.of("id"))
    .scheduleOnEqDeleteFileCount(10)
    .parallelism(4))
```

##### Требования и layout staging branch

- Table format version должен быть `>= 3`. Проверка выполняется на старте job, поэтому ошибочная конфигурация fail fast.
- Row lineage пока не поддерживается.
- Staging branch может содержать новые data files, equality delete files и deletion vectors, но **не должен содержать v2 positional delete files**. Planner завершится ошибкой при обнаружении такого delete.
- Staging branch **не должен удалять data files**. Не запускайте compaction/rewrite на staging branch. `RewriteDataFiles` следует выполнять на target branch; общий maintenance lock обеспечит сериализацию с converter.
- `equalityFieldColumns` обязателен, должен быть непустым и точно совпадать с equality fields, которыми writer создавал staged equality delete files (`IcebergSink.Builder#equalityFieldColumns`). `equalityFieldIds` каждого staged equality-delete file должен точно соответствовать этому набору; mismatch завершает cycle ошибкой.
- Source columns partition transforms для каждого staged equality delete должны быть subset equality columns.

##### Семантика branches

Если `stagingBranch` и `targetBranch` различаются:

- converter читает equality deletes из staging;
- commit resolved data files и DVs идёт в target;
- staging branch самой задачей не изменяется.

Если `stagingBranch == targetBranch`:

- conversion выполняется in-place как equality-delete-to-DV compaction;
- при cold start просматривается вся история branch, поэтому equality deletes, записанные до запуска converter, тоже обрабатываются;
- pure-insert snapshots общей branch пропускаются без полного conversion cycle.

За один trigger обрабатывается только **самый старый необработанный** staging snapshot. Если writer создаёт staging snapshots быстрее converter, они образуют очередь. Настройте `scheduleOnInterval`, `scheduleOnEqDeleteFileCount`, `scheduleOnCommitCount` и `TableMaintenance.rateLimit` так, чтобы converter успевал за ingestion rate.

##### State и restart

PK-index worker хранит keyed row-position index target branch во Flink state и поддерживает его **инкрементально между checkpoints**. Каждый cycle применяет только commits target branch после последнего проиндексированного snapshot. Результирующий index сохраняется следующим Flink checkpoint.

После failover worker восстанавливает последний checkpointed index вместо full rebuild. Размер state масштабируется с количеством live rows в таблице для выбранных equality columns. Поэтому state backend, checkpoint storage и TaskManager memory нужно рассчитывать соответствующим образом.

> [!tip]
> Для PK index предпочтителен **RocksDB state backend**: index способен превысить доступный heap, а RocksDB spill data на local disk вместо `OutOfMemoryError`.

Полный reindex target head выполняется только в отдельных случаях:

- cold start без checkpoint;
- внешний commit продвинул target дальше indexed snapshot;
- planner обнаружил divergence target branch от indexed snapshot — rollback, replace-main или expired marker;
- staging snapshot планируется повторно, потому что предыдущий cycle не успел commit.

`equalityFieldColumns` сохраняется в operator state. Изменить этот набор при restart из savepoint **нельзя**: job fail fast при restore. При изменении equality fields нужен clean state без старого savepoint.

Committer намеренно stateless. После restart planner восстанавливает позицию, проходя target branch и ища marker property `equality-convert-staging-snapshot`, который пишет committer. Если marker больше недоступен в target history из-за rollback, replace-main или expiration snapshot, planner завершается ошибкой и требует ручного вмешательства.

##### Конкурентные commits в target branch

Внешние commits обнаруживаются `RowDelta.validateFromSnapshot`. Конфликтующий conversion cycle fail на commit; следующий trigger reindex PK index с нового target head и повторяет обработку.

> [!warning]
> Не рекомендуется держать постоянных конкурентных writers в target branch. Conflict detection выполняется только на стадии commit, поэтому проигравший cycle уже потратил ресурсы на чтение data files, lookup PK index и создание DV files. Эти результаты выбрасываются, а abandoned DVs остаются до `DeleteOrphanFiles`. Если внешний writer продвигает target быстрее, чем converter завершает cycle, возможен livelock — conversion будет постоянно проигрывать race и не сможет догнать поток.

Допустимые модели:

- `IcebergSink` — единственный writer в `stagingBranch`, converter — единственный writer в `targetBranch`; остальные maintenance tasks используют общий `TriggerLockFactory` и не race с converter;
- редкие ad-hoc commits target branch допустимы — следующий trigger reindex и продолжит работу.

## Управление lock

`TriggerLockFactory` координирует maintenance tasks и не даёт одновременно выполнять конфликтующие операции для одной таблицы.

Locks нужны для:

- **Concurrent access** — несколько Flink jobs могут одновременно попытаться выполнить maintenance;
- **Data consistency** — для таблицы выполняется одна maintenance operation за раз;
- **Resource management** — исключаются конкурирующие тяжёлые rewrites;
- **Avoid duplicate work** — даже один scheduler может породить несколько экземпляров задачи, которые иначе будут переписывать одни и те же files.

### JDBC Lock Factory

```java
Map<String, String> jdbcProps = new HashMap<>();
jdbcProps.put("jdbc.user", "flink");
jdbcProps.put("jdbc.password", "flinkpw");
jdbcProps.put("flink-maintenance.lock.jdbc.init-lock-tables", "true");

TriggerLockFactory lockFactory = new JdbcLockFactory(
    "jdbc:postgresql://localhost:5432/iceberg",
    "catalog.db.table",
    jdbcProps
);
```

### ZooKeeper Lock Factory

```java
TriggerLockFactory lockFactory = new ZkLockFactory(
    "localhost:2181",
    "catalog.db.table",
    60000,
    15000,
    3000,
    3
);
```

### Flink-managed lock

Lock можно хранить внутри самого Flink без внешней системы. Требование: для одной таблицы не должно существовать параллельных независимых TableMaintenance jobs.

## Быстрый старт

```java
StreamExecutionEnvironment env =
    StreamExecutionEnvironment.getExecutionEnvironment();

TableLoader tableLoader = TableLoader.fromCatalog(
    CatalogLoader.hive("my_catalog", configuration, properties),
    TableIdentifier.of("database", "table")
);

Map<String, String> jdbcProps = new HashMap<>();
jdbcProps.put("jdbc.user", "flink");
jdbcProps.put("jdbc.password", "flinkpw");

TriggerLockFactory lockFactory = new JdbcLockFactory(
    "jdbc:postgresql://localhost:5432/iceberg",
    "catalog.db.table",
    jdbcProps
);

// Option 1: external lock factory (планируется deprecation начиная с 1.12)
TableMaintenance.forTable(env, tableLoader, lockFactory)

// Option 2: Flink-managed lock
TableMaintenance.forTable(env, tableLoader)
    .uidSuffix("my-maintenance-job")
    .rateLimit(Duration.ofMinutes(10))
    .lockCheckDelay(Duration.ofSeconds(10))
    .add(ExpireSnapshots.builder()
        .scheduleOnCommitCount(10)
        .maxSnapshotAge(Duration.ofMinutes(10))
        .retainLast(5)
        .deleteBatchSize(5)
        .parallelism(8))
    .add(RewriteDataFiles.builder()
        .scheduleOnDataFileCount(10)
        .targetFileSizeBytes(128 * 1024 * 1024)
        .partialProgressEnabled(true)
        .partialProgressMaxCommits(10))
    .append();

env.execute("Table Maintenance Job");
```

## Configuration options

### `TableMaintenance` Builder

| Method | Описание | Default |
| --- | --- | --- |
| `uidSuffix(String)` | Уникальный suffix operator/job | Random UUID |
| `rateLimit(Duration)` | Минимальный interval между executions | 60 seconds |
| `lockCheckDelay(Duration)` | Задержка перед повторной проверкой lock | 30 seconds |
| `parallelism(int)` | Default parallelism maintenance tasks | System default |
| `maxReadBack(int)` | Max snapshots, просматриваемых при initialization | 100 |

### Общие настройки maintenance task

| Method | Описание | Default |
| --- | --- | --- |
| `scheduleOnCommitCount(int)` | Trigger после N commits | Не задан |
| `scheduleOnDataFileCount(int)` | Trigger после N data files | Не задан |
| `scheduleOnDataFileSize(long)` | Trigger после суммарного data-file size | Не задан |
| `scheduleOnPosDeleteFileCount(int)` | Trigger после N positional delete files | Не задан |
| `scheduleOnPosDeleteRecordCount(long)` | Trigger после N positional delete records | Не задан |
| `scheduleOnEqDeleteFileCount(int)` | Trigger после N equality delete files | Не задан |
| `scheduleOnEqDeleteRecordCount(long)` | Trigger после N equality delete records | Не задан |
| `scheduleOnInterval(Duration)` | Trigger по времени | Не задан |

### ExpireSnapshots

| Method | Описание | Default |
| --- | --- | --- |
| `maxSnapshotAge(Duration)` | Максимальный возраст snapshot | 5 days |
| `retainLast(int)` | Минимум snapshots для сохранения | 1 |
| `deleteBatchSize(int)` | Files в одном delete batch | 1000 |
| `planningWorkerPoolSize(int)` | Worker threads planning | Shared worker pool |
| `cleanExpiredMetadata(boolean)` | Удалять expired schemas/specs и metadata | true |

### RewriteDataFiles

| Method | Описание | Default |
| --- | --- | --- |
| `targetFileSizeBytes(long)` | Target rewritten file size | Table property / 512 MB |
| `minFileSizeBytes(long)` | Ниже этого размера file candidate | 75% target |
| `maxFileSizeBytes(long)` | Выше этого размера file candidate | 180% target |
| `minInputFiles(int)` | Min files для trigger rewrite | 5 |
| `deleteFileThreshold(int)` | Min delete-file count per data file | `Integer.MAX_VALUE` |
| `rewriteAll(boolean)` | Rewrite независимо от thresholds | false |
| `maxFileGroupSizeBytes(long)` | Max total size одной file group | 100 GB |
| `maxFilesToRewrite(int)` | Max eligible files за execution | null / unlimited |
| `partialProgressEnabled(boolean)` | Incremental commits | false |
| `partialProgressMaxCommits(int)` | Max commits partial progress | 10 |
| `maxRewriteBytes(long)` | Max bytes за execution | `Long.MAX_VALUE` |
| `filter(Expression)` | File selection filter | `Expressions.alwaysTrue()` |
| `maxFileGroupInputFiles(long)` | Max input files в file group | `Long.MAX_VALUE` |

### DeleteOrphanFiles

| Method | Описание | Default |
| --- | --- | --- |
| `location(String)` | Root recursive listing | Table location |
| `usePrefixListing(boolean)` | Prefix listing через `SupportsPrefixOperations`; false использует recursive listing | true |
| `prefixMismatchMode(PrefixMismatchMode)` | `ERROR`, `IGNORE`, `DELETE` при mismatch scheme/authority | `ERROR` |
| `equalSchemes(Map)` | Эквивалентные filesystem schemes | `s3n→s3`, `s3a→s3` |
| `equalAuthorities(Map)` | Эквивалентные authorities | Empty |
| `minAge(Duration)` | Удалять orphan старше | 3 days |
| `planningWorkerPoolSize(int)` | Planning threads | Shared worker pool |

> [!warning]
> При object storage `usePrefixListing=false` может требовать большого числа recursive list API calls. При `true` FileIO обязан реализовывать `SupportsPrefixOperations`.

### ConvertEqualityDeletes

| Method | Описание | Default |
| --- | --- | --- |
| `stagingBranch(String)` | Source branch с equality deletes/data files | **Required** |
| `targetBranch(String)` | Branch для resolved data + DVs | `main` |
| `equalityFieldColumns(List<String>)` | PK/equality columns; должны совпадать writer | **Required, non-empty** |

> [!note]
> `ConvertEqualityDeletes` требует table format version >= 3.

## Полный пример maintenance job

```java
public class TableMaintenanceJob {
    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env =
            StreamExecutionEnvironment.getExecutionEnvironment();
        env.enableCheckpointing(60000);

        TableLoader tableLoader = TableLoader.fromCatalog(
            CatalogLoader.hive("my_catalog", configuration),
            TableIdentifier.of("database", "table")
        );

        Map<String, String> jdbcProps = new HashMap<>();
        jdbcProps.put("jdbc.user", "flink");
        jdbcProps.put("jdbc.password", "flinkpw");
        jdbcProps.put(
            "flink-maintenance.lock.jdbc.init-lock-tables",
            "true");

        TriggerLockFactory lockFactory = new JdbcLockFactory(
            "jdbc:postgresql://localhost:5432/iceberg",
            "catalog.db.table",
            jdbcProps
        );

        TableMaintenance.forTable(env, tableLoader, lockFactory)
            .uidSuffix("production-maintenance")
            .rateLimit(Duration.ofMinutes(15))
            .lockCheckDelay(Duration.ofSeconds(30))
            .parallelism(4)

            .add(ExpireSnapshots.builder()
                .maxSnapshotAge(Duration.ofDays(7))
                .retainLast(10))

            .add(RewriteDataFiles.builder()
                .targetFileSizeBytes(256 * 1024 * 1024)
                .minFileSizeBytes(32 * 1024 * 1024)
                .scheduleOnDataFileCount(20)
                .partialProgressEnabled(true)
                .partialProgressMaxCommits(5)
                .maxRewriteBytes(2L * 1024 * 1024 * 1024)
                .parallelism(6))

            .add(DeleteOrphanFiles.builder()
                .minAge(Duration.ofDays(5)))

            .append();

        env.execute("Iceberg Table Maintenance");
    }
}
```

## IcebergSink с post-commit integration

SinkV2 `IcebergSink` может автоматически добавлять maintenance topology после успешных commits.

### DataStream API

```java
IcebergSink.forRowData(dataStream)
    .table(table)
    .tableLoader(tableLoader)
    .rewriteDataFiles(Map.of(
        RewriteDataFilesConfig.MAX_BYTES, "1073741824"))
    .expireSnapshots(Map.of(
        ExpireSnapshotsConfig.RETAIN_LAST, "5",
        ExpireSnapshotsConfig.MAX_SNAPSHOT_AGE_SECONDS, "604800"))
    .deleteOrphanFiles(Map.of(
        DeleteOrphanFilesConfig.MIN_AGE_SECONDS, "259200"))
    .append();
```

`convertEqualityDeletes()` требует equality fields и format >= 3. По умолчанию выполняет in-place conversion в write branch:

```java
IcebergSink.forRowData(dataStream)
    .table(table)
    .tableLoader(tableLoader)
    .upsert(true)
    .equalityFieldColumns(List.of("id"))
    .convertEqualityDeletes()
    .append();
```

### Настройка через string properties

```java
Map<String, String> flinkConf = new HashMap<>();

flinkConf.put("flink-maintenance.rewrite.enabled", "true");
flinkConf.put("flink-maintenance.expire-snapshots.enabled", "true");
flinkConf.put("flink-maintenance.delete-orphan-files.enabled", "true");
flinkConf.put("flink-maintenance.convert-equality-deletes.enabled", "true");

flinkConf.put("flink-maintenance.rewrite.max-bytes", "1073741824");

flinkConf.put("flink-maintenance.expire-snapshots.retain-last", "5");
flinkConf.put(
    "flink-maintenance.expire-snapshots.max-snapshot-age-seconds",
    "604800");

flinkConf.put(
    "flink-maintenance.delete-orphan-files.min-age-seconds",
    "259200");

flinkConf.put(
    "flink-maintenance.convert-equality-deletes.target-branch",
    "main");

// External JDBC lock configuration is deprecated for a single Flink job.
flinkConf.put("flink-maintenance.lock.type", "jdbc");
flinkConf.put(
    "flink-maintenance.lock.jdbc.uri",
    "jdbc:postgresql://localhost:5432/iceberg");
flinkConf.put("flink-maintenance.lock.lock-id", "catalog.db.table");

IcebergSink.forRowData(dataStream)
    .table(table)
    .tableLoader(tableLoader)
    .setAll(flinkConf)
    .append();
```

### SQL example

```sql
set 'table.exec.iceberg.use-v2-sink' = 'true';
set 'flink-maintenance.rewrite.enabled' = 'true';
set 'flink-maintenance.expire-snapshots.enabled' = 'true';
set 'flink-maintenance.delete-orphan-files.enabled' = 'true';
set 'flink-maintenance.convert-equality-deletes.enabled' = 'true';

set 'flink-maintenance.rewrite.max-bytes' = '1073741824';
set 'flink-maintenance.expire-snapshots.retain-last' = '5';
set 'flink-maintenance.delete-orphan-files.min-age-seconds' = '259200';

set 'flink-maintenance.lock.type' = 'jdbc';
set 'flink-maintenance.lock.lock-id' = 'catalog.db.table';
set 'flink-maintenance.lock.jdbc.uri' = 'jdbc:postgresql://localhost:5432/iceberg';
set 'flink-maintenance.lock.jdbc.init-lock-table' = 'true';

insert into db.tbl select ...;
```

Те же properties можно сохранить в table DDL:

```sql
create table db.tbl (
  ...
) with (
  'connector' = 'iceberg',
  'catalog-name' = 'my_catalog',
  'catalog-database' = 'db',
  'catalog-table' = 'tbl',
  'flink-maintenance.rewrite.enabled' = 'true',
  'flink-maintenance.expire-snapshots.enabled' = 'true',
  'flink-maintenance.delete-orphan-files.enabled' = 'true',
  'flink-maintenance.rewrite.max-bytes' = '1073741824',
  'flink-maintenance.expire-snapshots.retain-last' = '5',
  'flink-maintenance.delete-orphan-files.min-age-seconds' = '259200',
  'flink-maintenance.lock.type' = 'jdbc',
  'flink-maintenance.lock.lock-id' = 'catalog.db.table',
  'flink-maintenance.lock.jdbc.uri' = 'jdbc:postgresql://localhost:5432/iceberg',
  'flink-maintenance.lock.jdbc.init-lock-table' = 'true'
);
```

## IcebergSink maintenance configuration

### Enable flags

| Key | Описание | Default |
| --- | --- | --- |
| `flink-maintenance.rewrite.enabled` | Compaction data files | false |
| `flink-maintenance.expire-snapshots.enabled` | Expire snapshots | false |
| `flink-maintenance.delete-orphan-files.enabled` | Delete orphan files | false |
| `flink-maintenance.convert-equality-deletes.enabled` | Equality deletes → DVs; equality fields + format >= 3 | false |

### Rewrite Data Files

| Key | Описание | Default |
| --- | --- | --- |
| `flink-maintenance.rewrite.schedule.commit-count` | Trigger после N commits | 10 |
| `flink-maintenance.rewrite.schedule.data-file-count` | Trigger после N data files | 1000 |
| `flink-maintenance.rewrite.schedule.data-file-size` | Trigger после total bytes | 107374182400 (100 GB) |
| `flink-maintenance.rewrite.schedule.interval-second` | Time trigger | 600 |
| `flink-maintenance.rewrite.max-bytes` | Max rewrite bytes/execution | `Long.MAX_VALUE` |
| `flink-maintenance.rewrite.partial-progress.enabled` | Partial commits | false |
| `flink-maintenance.rewrite.partial-progress.max-commits` | Max partial commits | 10 |

### Expire Snapshots

| Key | Описание | Default |
| --- | --- | --- |
| `flink-maintenance.expire-snapshots.schedule.commit-count` | Trigger commits | 10 |
| `flink-maintenance.expire-snapshots.schedule.interval-second` | Time trigger | 3600 |
| `flink-maintenance.expire-snapshots.max-snapshot-age-seconds` | Max age | Not set |
| `flink-maintenance.expire-snapshots.retain-last` | Min retained | Not set |
| `flink-maintenance.expire-snapshots.delete-batch-size` | Delete batch | 1000 |
| `flink-maintenance.expire-snapshots.clean-expired-metadata` | Clean schemas/specs | true |
| `flink-maintenance.expire-snapshots.planning-worker-pool-size` | Planning workers | Shared pool |

### Delete Orphan Files

| Key | Описание | Default |
| --- | --- | --- |
| `flink-maintenance.delete-orphan-files.schedule.interval-second` | Time trigger | 3600 |
| `flink-maintenance.delete-orphan-files.min-age-seconds` | Min file age | 259200 (3 days) |
| `flink-maintenance.delete-orphan-files.delete-batch-size` | Delete batch | 1000 |
| `flink-maintenance.delete-orphan-files.location` | Listing root | Table location |
| `flink-maintenance.delete-orphan-files.use-prefix-listing` | Prefix listing | true |
| `flink-maintenance.delete-orphan-files.planning-worker-pool-size` | Planning workers | Shared pool |
| `flink-maintenance.delete-orphan-files.equal-schemes` | Equivalent schemes | `s3n=s3,s3a=s3` |
| `flink-maintenance.delete-orphan-files.equal-authorities` | Equivalent authorities | Not set |
| `flink-maintenance.delete-orphan-files.prefix-mismatch-mode` | `ERROR`, `IGNORE`, `DELETE` | `ERROR` |

### Convert Equality Deletes

| Key | Описание | Default |
| --- | --- | --- |
| `flink-maintenance.convert-equality-deletes.target-branch` | Target branch DVs | Not set = in-place |
| `flink-maintenance.convert-equality-deletes.schedule.commit-count` | Trigger commits | 1 |
| `flink-maintenance.convert-equality-deletes.schedule.interval-second` | Time trigger | Not set |

## Lock configuration через SQL/properties

### JDBC

| Key | Описание | Default |
| --- | --- | --- |
| `flink-maintenance.lock.type` | `jdbc` | — |
| `flink-maintenance.lock.lock-id` | Unique table lock ID | — |
| `flink-maintenance.lock.jdbc.uri` | JDBC URI | — |
| `flink-maintenance.lock.jdbc.init-lock-table` | Auto-create table | false |

### ZooKeeper

| Key | Описание | Default |
| --- | --- | --- |
| `flink-maintenance.lock.type` | `zookeeper` | — |
| `flink-maintenance.lock.lock-id` | Unique lock ID | — |
| `flink-maintenance.lock.zookeeper.uri` | ZK URI | — |
| `flink-maintenance.lock.zookeeper.session-timeout-ms` | Session timeout | 60000 |
| `flink-maintenance.lock.zookeeper.connection-timeout-ms` | Connection timeout | 15000 |
| `flink-maintenance.lock.zookeeper.max-retries` | Max retries | 3 |
| `flink-maintenance.lock.zookeeper.base-sleep-ms` | Base retry sleep | 3000 |
| `flink-maintenance.lock.zookeeper.max-sleep-ms` | Max exponential-backoff sleep | 10000 |
| `flink-maintenance.lock.zookeeper.retry-policy` | `ONE_TIME`, `N_TIME`, `BOUNDED_EXPONENTIAL_BACKOFF`, `UNTIL_ELAPSED`, `EXPONENTIAL_BACKOFF` | `EXPONENTIAL_BACKOFF` |

### Coordinator/Flink-managed lock

`flink-maintenance.lock.type` оставить пустым или не задавать.

## Best practices

### Resource management

- используйте dedicated slot sharing groups для maintenance tasks;
- выбирайте parallelism относительно доступных cluster resources;
- включайте checkpointing для fault tolerance.

### Scheduling

- не запускайте tasks слишком часто; используйте `rateLimit`;
- для write-heavy tables удобен `scheduleOnCommitCount`;
- для контроля количества small files — `scheduleOnDataFileCount`.

### Performance tuning

- подберите `deleteBatchSize` относительно storage performance и heap;
- для больших rewrites включайте partial progress;
- задавайте разумный `maxRewriteBytes`;
- `maxFileGroupSizeBytes` помогает дробить огромные FileGroups и увеличивать parallelism.

## Troubleshooting

### `OutOfMemoryError` при удалении files

Причина — слишком большой delete batch, особенно после long retention или bulk deletion. Уменьшите batch:

```java
.deleteBatchSize(500)
```

### Lock conflicts

Несколько jobs конкурируют за lock. Увеличьте delay и уменьшите частоту запуска:

```java
.lockCheckDelay(Duration.ofMinutes(1))
.rateLimit(Duration.ofMinutes(10))
```

### Медленные rewrite operations

Большие таблицы с тысячами small files могут пытаться переписать терабайты за один execution. Включите incremental commits и limit:

```java
.partialProgressEnabled(true)
.partialProgressMaxCommits(3)
.maxRewriteBytes(1L * 1024 * 1024 * 1024)
```
