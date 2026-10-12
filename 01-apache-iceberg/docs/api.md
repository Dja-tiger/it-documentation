---
title: "Java API"
tags: [apache-iceberg, api, java]
source_project: apache/iceberg
source_file: docs/docs/api.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/api.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Iceberg Java API

## Таблицы

Основная задача Iceberg API — управление table metadata: schema, partition spec, properties, metadata files и data files, содержащими данные таблицы.

Доступ к metadata и операциям осуществляется через интерфейс `Table`.

### Метаданные таблицы

`Table` предоставляет:

- `schema` — текущая [[schemas|schema]];
- `spec` — текущий partition spec;
- `properties` — map key-value [[configuration|properties]];
- `currentSnapshot` — текущий snapshot;
- `snapshots` — все допустимые snapshots;
- `snapshot(id)` — конкретный snapshot по ID;
- `location` — base location таблицы.

`refresh` обновляет объект до последней версии таблицы. Дополнительные helpers:

- `io` возвращает `FileIO` для чтения/записи table files;
- `locationProvider` возвращает `LocationProvider`, создающий paths для data/metadata files.

### Сканирование

#### На уровне файлов

Scan начинается созданием `TableScan` через `newScan`:

```java
TableScan scan = table.newScan();
```

`filter` и `select` возвращают новый настроенный `TableScan`:

```java
TableScan filteredScan = scan.filter(Expressions.equal("id", 5))
```

Configuration methods создают новый объект, поэтому `TableScan` immutable и не изменится неожиданно при совместном использовании потоками.

После настройки `planFiles`, `planTasks` и `schema` возвращают files, tasks и read projection:

```java
TableScan scan = table.newScan()
    .filter(Expressions.equal("id", 5))
    .select("id", "data");

Schema projection = scan.schema();
Iterable<CombinedScanTask> tasks = scan.planTasks();
```

Для time travel snapshot задаётся через `asOfTime` или `useSnapshot`.

#### На уровне строк

Row-level scan начинается с `ScanBuilder`:

```java
ScanBuilder scanBuilder = IcebergGenerics.read(table)
```

Для настройки используются `where` и `select`:

```java
scanBuilder.where(Expressions.equal("id", 5))
```

`build` выполняет scan и возвращает `CloseableIterable<Record>`:

```java
CloseableIterable<Record> result = IcebergGenerics.read(table)
        .where(Expressions.lessThan("id", 5))
        .build();
```

`Record` — Iceberg record из `org.apache.iceberg.data.Record` модуля `iceberg-data`.

### Update operations

`Table` предоставляет операции изменения таблицы. Они используют builder pattern `PendingUpdate`; изменение фиксируется при `PendingUpdate#commit`.

Пример schema update:

```java
table.updateSchema()
    .addColumn("count", Types.LongType.get())
    .commit();
```

Доступные операции:

- `updateSchema` — изменить schema;
- `updateSpec` — изменить partition spec;
- `updateStatistics` — обновить statistics files;
- `updatePartitionStatistics` — обновить statistics конкретной partition;
- `updateProperties` — изменить table properties;
- `updateLocation` — изменить base location;
- `expireSnapshots` — удалить старые snapshots;
- `manageSnapshots` — управлять snapshots;
- `newAppend` — append data files;
- `newFastAppend` — append data files без compaction metadata;
- `newOverwrite` — append files и удаление overwritten files;
- `newDelete` — удалить data files;
- `newRewrite` — заменить существующие data files новыми версиями;
- `newRowDelta` — удалить или заменить строки в существующих data files;
- `newTransaction` — создать table-level transaction;
- `rewriteManifests` — кластеризовать manifest data для ускорения scan planning;
- `replaceSortOrder` — заменить sort order;
- `newReplacePartitions` — dynamic overwrite partitions новыми данными.

### Транзакции

Transactions позволяют зафиксировать несколько изменений таблицы как одну atomic operation. Внутри transaction операции создаются теми же factory methods (`newAppend` и т. д.), а общий commit выполняется `commitTransaction`.

```java
Transaction t = table.newTransaction();

// commit operations to the transaction
t.newDelete().deleteFromRowFilter(filter).commit();
t.newAppend().appendFile(data).commit();

// commit all the changes to the table
t.commitTransaction();
```

## Типы

Типы Iceberg находятся в package `org.apache.iceberg.types`.

### Primitive types

Instances primitive types доступны через static methods классов типов. Для типов без параметров используется `get`, для параметризованных — factory methods:

```java
Types.IntegerType.get()    // int
Types.DoubleType.get()     // double
Types.DecimalType.of(9, 2) // decimal(9, 2)
```

### Nested types

`struct`, `map`, `list` создаются factory methods соответствующих type classes.

Map keys/values и list elements, как и struct fields, отслеживаются как nested fields: у них есть [[evolution#Корректность|field IDs]] и nullability.

Struct fields создаются через `NestedField.optional` / `NestedField.required`. Nullability map value/list element задаётся factory method.

```java
// struct<1 id: int, 2 data: optional string>
StructType struct = StructType.of(
    Types.NestedField.required(1, "id", Types.IntegerType.get()),
    Types.NestedField.optional(2, "data", Types.StringType.get())
  )
```

```java
// map<1 key: int, 2 value: optional string>
MapType map = MapType.ofOptional(
    1, 2,
    Types.IntegerType.get(),
    Types.StringType.get()
  )
```

```java
// array<1 element: int>
ListType list = ListType.ofRequired(1, IntegerType.get());
```

## Expressions

Expressions используются для настройки table scans. Они создаются factory methods класса `Expressions`.

Поддерживаемые predicate expressions:

- `isNull`, `notNull`;
- `equal`, `notEqual`;
- `lessThan`, `lessThanOrEqual`;
- `greaterThan`, `greaterThanOrEqual`;
- `in`, `notIn`;
- `startsWith`, `notStartsWith`.

Логические операции: `and`, `or`, `not`.

Константы: `alwaysTrue`, `alwaysFalse`.

### Binding expressions

Сразу после создания expression является unbound. Перед использованием оно связывается с data type, чтобы определить field ID, соответствующий имени, и привести predicate literals к типу колонки.

Например, для `lessThan("x", 10)` Iceberg сначала определяет, к какой колонке относится `"x"`, затем приводит `10` к типу этой колонки. Одно и то же expression может быть связано, например, со `struct<1 x: long, 2 y: long>` или `struct<11 x: int, 12 y: int>`.

```java
table.newScan()
    .filter(Expressions.greaterThanOrEqual("x", 5))
    .filter(Expressions.lessThan("x", 10))
```

## Модули

Поддержка Iceberg организована по library modules:

- `iceberg-common` — utility classes;
- `iceberg-api` — public API: expressions, types, tables, operations;
- `iceberg-arrow` — реализация type system для Apache Arrow как in-memory format;
- `iceberg-aws` — реализации API для AWS S3 и AWS Glue Data Catalog;
- `iceberg-core` — реализации Iceberg API и поддержка Avro data files; **основная dependency для processing engines**;
- `iceberg-parquet` — optional module для Parquet;
- `iceberg-orc` — optional module для ORC (experimental);
- `iceberg-hive-metastore` — реализация Iceberg tables поверх Hive Metastore Thrift client.

Модули интеграций и tooling:

- `iceberg-spark` — Spark Datasource V2 API для Iceberg с submodules по версиям Spark; для shaded version используются runtime jars;
- `iceberg-flink` — Flink Table/DataStream API; shaded artifact — `iceberg-flink-runtime`;
- `iceberg-mr` — MapReduce/Hive InputFormats и SerDes; для Hive — `iceberg-hive-runtime`;
- `iceberg-nessie` — интеграция metadata history/operations с Project Nessie;
- `iceberg-data` — client library для чтения Iceberg из JVM applications;
- `iceberg-runtime` — генерирует shaded runtime jar для интеграции Spark с Iceberg.
