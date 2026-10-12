---
title: "Java API — быстрый старт"
tags: [apache-iceberg, api, java]
source_project: apache/iceberg
source_file: docs/docs/java-api-quickstart.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/java-api-quickstart.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Java API — быстрый старт

## Создание таблицы

Таблицы создаются либо через `Catalog`, либо через реализацию интерфейса `Tables`.

### Использование Hive catalog

Hive catalog подключается к Hive Metastore и хранит в нём информацию об Iceberg-таблицах. `HiveCatalog` инициализируется именем и набором properties. См. [[catalog-properties|свойства catalog]].

```java
import java.util.HashMap;
import java.util.Map;

import org.apache.iceberg.hive.HiveCatalog;

HiveCatalog catalog = new HiveCatalog();
catalog.setConf(spark.sparkContext().hadoopConfiguration());  // Optionally use Spark's Hadoop configuration

Map <String, String> properties = new HashMap<String, String>();
properties.put("warehouse", "...");
properties.put("uri", "...");

catalog.initialize("hive", properties);
```

`HiveCatalog` реализует интерфейс `Catalog`, который определяет методы работы с таблицами: `createTable`, `loadTable`, `renameTable`, `dropTable` и другие.

Для создания таблицы передайте `Identifier`, `Schema` и начальные metadata:

```java
import org.apache.iceberg.Table;
import org.apache.iceberg.catalog.TableIdentifier;

TableIdentifier name = TableIdentifier.of("logging", "logs");
Table table = catalog.createTable(name, schema, spec);

// or to load an existing table, use the following line
Table table = catalog.loadTable(name);
```

Schema и partition spec создаются ниже.

### Использование Hadoop catalog

`HadoopCatalog` не требует Hive Metastore, но должен использоваться с HDFS или похожей filesystem, поддерживающей atomic rename. Concurrent writes через Hadoop catalog небезопасны на local FS или S3.

```java
import org.apache.hadoop.conf.Configuration;
import org.apache.iceberg.hadoop.HadoopCatalog;

Configuration conf = new Configuration();
String warehousePath = "hdfs://host:8020/warehouse_path";
HadoopCatalog catalog = new HadoopCatalog(conf, warehousePath);
```

Как и Hive catalog, `HadoopCatalog` реализует `Catalog` и предоставляет `createTable`, `loadTable`, `dropTable` и другие методы.

```java
import org.apache.iceberg.Table;
import org.apache.iceberg.catalog.TableIdentifier;

TableIdentifier name = TableIdentifier.of("logging", "logs");
Table table = catalog.createTable(name, schema, spec);

// or to load an existing table, use the following line
Table table = catalog.loadTable(name);
```

### Таблицы в Spark

Spark может работать с таблицей по имени через `HiveCatalog`:

```java
// spark.sql.catalog.hive_prod = org.apache.iceberg.spark.SparkCatalog
// spark.sql.catalog.hive_prod.type = hive
spark.table("logging.logs");
```

Таблицу, созданную `HadoopCatalog`, Spark может загрузить по path:

```java
spark.read.format("iceberg").load("hdfs://host:8020/warehouse_path/logging/logs");
```

## Схемы

### Создание schema

Пример schema для таблицы `logs`:

```java
import org.apache.iceberg.Schema;
import org.apache.iceberg.types.Types;

Schema schema = new Schema(
      Types.NestedField.required(1, "level", Types.StringType.get()),
      Types.NestedField.required(2, "event_time", Types.TimestampType.withZone()),
      Types.NestedField.required(3, "message", Types.StringType.get()),
      Types.NestedField.optional(4, "call_stack", Types.ListType.ofRequired(5, Types.StringType.get()))
    );
```

При прямом использовании Iceberg API field IDs обязательны. Конвертеры Spark, Avro и Parquet schema назначают IDs автоматически.

При создании таблицы все IDs schema переназначаются, чтобы гарантировать уникальность.

### Конвертация schema из Avro

```java
import org.apache.avro.Schema;
import org.apache.avro.Schema.Parser;
import org.apache.iceberg.avro.AvroSchemaUtil;

Schema avroSchema = new Parser().parse("{\"type\": \"record\" , ... }");
Schema icebergSchema = AvroSchemaUtil.toIceberg(avroSchema);
```

### Конвертация schema из Spark

```java
import org.apache.iceberg.spark.SparkSchemaUtil;

Schema schema = SparkSchemaUtil.schemaForTable(sparkSession, tableName);
```

## Партиционирование

### Создание partition spec

Partition spec описывает, как Iceberg должен группировать records в data files. Spec создаётся для schema таблицы через builder.

Следующий пример партиционирует `logs` по часу `event_time` и по `level`:

```java
import org.apache.iceberg.PartitionSpec;

PartitionSpec spec = PartitionSpec.builderFor(schema)
      .hour("event_time")
      .identity("level")
      .build();
```

Подробнее о transforms — в Iceberg Specification, раздел Partitioning.

## Ветвление и теги

### Создание branches и tags

Branches/tags создаются через `ManageSnapshots` API:

```java
/* Create a branch test-branch which is retained for 1 week, and the latest 2 snapshots on test-branch will always be retained.
Snapshots on test-branch which are created within the last hour will also be retained. */

String branch = "test-branch";
table.manageSnapshots()
    .createBranch(branch, 3)
    .setMinSnapshotsToKeep(branch, 2)
    .setMaxSnapshotAgeMs(branch, 3600000)
    .setMaxRefAgeMs(branch, 604800000)
    .commit();

// Create a tag historical-tag at snapshot 10 which is retained for a day
String tag = "historical-tag"
table.manageSnapshots()
    .createTag(tag, 10)
    .setMaxRefAgeMs(tag, 86400000)
    .commit();
```

### Commit в branches

Для записи в branch у операции задаётся `toBranch`. Полный список update operations см. [[api#Update operations|Java API]].

```java
// Append FILE_A to branch test-branch
String branch = "test-branch";

table.newAppend()
    .appendFile(FILE_A)
    .toBranch(branch)
    .commit();

// Perform row level updates on "test-branch"
table.newRowDelta()
    .addRows(DATA_FILE)
    .addDeletes(DELETES)
    .toBranch(branch)
    .commit();

// Perform a rewrite operation replacing SMALL_FILE_1 and SMALL_FILE_2 on "test-branch" with compactedFile.
table.newRewrite()
    .rewriteFiles(ImmutableSet.of(SMALL_FILE_1, SMALL_FILE_2), ImmutableSet.of(compactedFile))
    .toBranch(branch)
    .commit();
```

### Чтение branches и tags

Чтение выполняется через обычный Table Scan API с `useRef`. Для branch используется head snapshot. Одновременное чтение branch и указание `asOfSnapshotId` в scan не поддерживается.

```java
// Read from the head snapshot of test-branch
TableScan branchRead = table.newScan().useRef("test-branch");

// Read from the snapshot referenced by audit-tag
TableScan tagRead = table.newScan().useRef("audit-tag");
```

### Replace и fast-forward branches/tags

Snapshot, на который указывает существующий branch/tag, можно изменить через `replace` API. Fast-forward аналогичен git fast-forward: target branch продвигается к head source branch/tag, если target является ancestor source. Retention properties target branch по умолчанию сохраняются.

```java
// Update "test-branch" to point to snapshot 4
table.manageSnapshots()
     .replaceBranch(branch, 4)
     .commit()

String tag = "audit-tag";
// Replace "audit-tag" to point to snapshot 3 and update its retention
table.manageSnapshots()
     .replaceBranch(tag, 4)
     .setMaxRefAgeMs(1000)
     .commit()
```

### Обновление retention properties

`setMaxRefAgeMs` меняет retention самой ссылки branch/tag. Для snapshots branch используются `setMinSnapshotsToKeep` и `setMaxSnapshotAgeMs`.

```java
String branch = "test-branch";
table.manageSnapshots()
    .setMinSnapshotsToKeep(branch, 10)
    .setMaxSnapshotAgeMs(branch, 7200000)
    .setMaxRefAgeMs(branch, 604800000)
    .commit();

table.manageSnapshots()
    .setMaxRefAgeMs("test-tag", 604800000)
    .commit();
```

### Удаление branches и tags

```java
// Remove test-branch
table.manageSnapshots()
     .removeBranch("test-branch")
     .commit()

// Remove test-tag
table.manageSnapshots()
     .removeTag("test-tag")
     .commit()
```
