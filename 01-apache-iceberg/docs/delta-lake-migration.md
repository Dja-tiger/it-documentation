---
title: "Миграция Delta Lake → Iceberg"
tags: [apache-iceberg, migration, delta-lake]
source_project: apache/iceberg
source_file: docs/docs/delta-lake-migration.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/delta-lake-migration.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Миграция Delta Lake tables

Delta Lake — table format поверх Parquet с time travel и versioning. При migration Delta Lake → Iceberg обычно желательно сохранить **всю snapshot/transaction history**, а не только current files.

В Iceberg 1.12.0 для Delta Lake поддерживается action **Snapshot Table**. Delta Lake содержит transaction log, поэтому все доступные transactions source table последовательно преобразуются в Iceberg transactions новой table.

Data files, появившиеся после initial migration, относятся к новым Delta transactions. Для их incremental переноса планируется action **Add Transaction** — вариант Add Files; в документации 1.12.0 он всё ещё находится в разработке.

## Включение Delta migration

Module `iceberg-delta-lake` не входит в Spark/Flink runtime jars. Минимальные dependencies, указанные upstream:

- `iceberg-delta-lake`;
- `delta-standalone_2.13:0.6.0`;
- `delta-storage:2.2.0`.

### Совместимость

Module собирается и тестируется с **Delta Standalone 0.6.0** и поддерживает Delta tables с protocol:

- `minReaderVersion = 1`;
- `minWriterVersion = 2`.

Более новые protocol features Delta могут быть несовместимы и должны проверяться относительно Delta Lake protocol versioning.

### API

`iceberg-delta-lake` предоставляет интерфейс:

```text
DeltaLakeToIcebergMigrationActionsProvider
```

Поддерживаемый action:

- `snapshotDeltaLakeTable` — snapshot existing Delta Lake table в Iceberg table.

Default implementation:

```java
DeltaLakeToIcebergMigrationActionsProvider defaultActions =
    DeltaLakeToIcebergMigrationActionsProvider.defaultActions();
```

## Snapshot Delta Lake table → Iceberg

`snapshotDeltaLakeTable` читает Delta transactions и преобразует их в новую Iceberg table с той же schema и partitioning в одной Iceberg transaction. Original Delta table не меняется.

Новая Iceberg table может принимать новые writes независимо от source, однако initial snapshot использует **original Delta data files**. Existing files добавляются в Iceberg metadata и читаются через name-to-id mapping, построенный из original schema.

При дальнейших insert/overwrite новые files создаются в location snapshot table. По умолчанию location совпадает с source Delta table, но можно указать отдельный location.

> [!danger]
> Snapshot table не является единственным владельцем shared source data files. Поэтому операции вроде `expire_snapshots`, которые физически удаляют files, запрещены. Metadata-only deletes допустимы.
>
> Любая операция source Delta table, физически удаляющая original files, нарушит целостность snapshot Iceberg table. Например, если `delete`/vacuum на source удалит shared file, Iceberg больше не сможет его прочитать.

### Обязательные inputs

| Input | API | Описание |
| --- | --- | --- |
| Source table location | `sourceTableLocation` argument | Location Delta table |
| New Iceberg identifier | `.as(TableIdentifier)` | Namespace + table name |
| Iceberg catalog | `.icebergCatalog(Catalog)` | Catalog для target |
| Hadoop Configuration | `.deltaLakeConfiguration(Configuration)` | Config для чтения source Delta table |

Дополнительные options доступны в `SnapshotDeltaLakeTable` API.

### Output

| Name | Type | Описание |
| --- | --- | --- |
| `imported_files_count` | long | Число files, добавленных в новую table |

### Properties target table

По умолчанию добавляются:

| Property | Value | Описание |
| --- | --- | --- |
| `snapshot_source` | `delta` | Source format |
| `original_location` | Delta table location | Absolute original path |
| `schema.name-mapping.default` | JSON mapping from schema | Name mapping для чтения Delta Parquet files |

### Пример

```java
import org.apache.iceberg.catalog.TableIdentifier;
import org.apache.iceberg.catalog.Catalog;
import org.apache.hadoop.conf.Configuration;
import org.apache.iceberg.delta.DeltaLakeToIcebergMigrationActionsProvider;

String sourceDeltaLakeTableLocation = "s3://my-bucket/delta-table";
String destTableLocation = "s3://my-bucket/iceberg-table";
TableIdentifier destTableIdentifier =
    TableIdentifier.of("my_db", "my_table");
Catalog icebergCatalog = ...;
Configuration hadoopConf = ...;

DeltaLakeToIcebergMigrationActionsProvider.defaultActions()
    .snapshotDeltaLakeTable(sourceDeltaLakeTableLocation)
    .as(destTableIdentifier)
    .icebergCatalog(icebergCatalog)
    .tableLocation(destTableLocation)
    .deltaLakeConfiguration(hadoopConf)
    .tableProperty("my_property", "my_value")
    .execute();
```
