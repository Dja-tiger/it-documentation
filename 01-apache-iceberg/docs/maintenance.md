---
title: Обслуживание таблиц
tags: [apache-iceberg, concepts, maintenance]
source_project: apache/iceberg
source_file: docs/docs/maintenance.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/maintenance.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Обслуживание

> [!info]
> Maintenance operations требуют экземпляр `Table`. Как загрузить существующую таблицу, см. [[java-api-quickstart|Java API quickstart]].

## Рекомендуемое обслуживание

### Expire snapshots

Каждая запись в Iceberg-таблицу создаёт новый **snapshot**, то есть версию таблицы. Snapshots используются для time travel, а таблицу можно rollback к любому допустимому snapshot.

Snapshots накапливаются, пока не будут удалены операцией `expireSnapshots`. Регулярный expiration рекомендуется, чтобы удалять больше не нужные data files и удерживать metadata table небольшими.

Пример удаляет snapshots старше одного дня:

```java
Table table = ...
long tsToExpire = System.currentTimeMillis() - (1000 * 60 * 60 * 24); // 1 day
table.expireSnapshots()
     .expireOlderThan(tsToExpire)
     .commit();
```

Для больших таблиц Spark action может выполнять expiration параллельно:

```java
Table table = ...
SparkActions
    .get()
    .expireSnapshots(table)
    .expireOlderThan(tsToExpire)
    .execute();
```

После expiration старые snapshots удаляются из metadata и больше недоступны для time-travel queries.

> [!info]
> Data files не удаляются, пока на них ссылается хотя бы один snapshot, доступный для time travel или rollback. Регулярный expiration snapshots удаляет ставшие неиспользуемыми data files.

### Удаление старых metadata files

Iceberg отслеживает table metadata с помощью JSON files. Каждое изменение таблицы создаёт новый metadata file, обеспечивая atomicity.

По умолчанию старые metadata files сохраняются для истории. Таблицам с частыми commit, например streaming jobs, может требоваться регулярная очистка.

Каждый metadata file отслеживает предыдущие файлы в поле `metadata-log`. Количество отслеживаемых файлов задаётся `write.metadata.previous-versions-max`.

Для автоматического удаления старых metadata files установите `write.metadata.delete-after-commit.enabled=true`. Iceberg сохранит до `write.metadata.previous-versions-max` отслеживаемых versions и при создании новой будет удалять самый старый отслеживаемый metadata file.

Это удаляет только **tracked** metadata files. Уже потерявшие tracking orphan metadata files очищаются механизмом [[#Удаление orphan files]].

| Property | Default | Описание |
| --- | --- | --- |
| `write.metadata.delete-after-commit.enabled` | false | Удалять самый старый **tracked** metadata file после каждого commit |
| `write.metadata.previous-versions-max` | 100 | Максимум предыдущих metadata files в tracking |

Примеры:

- При `delete-after-commit=false` и `previous-versions-max=10` после 100 commits будет 10 tracked metadata files и 90 orphan metadata files. Позднее включение `delete-after-commit=true` их не удалит, потому что они уже не tracked; нужна orphan-file cleanup.
- При `delete-after-commit=true` и `previous-versions-max=20` после 21-го commit останется 20 tracked metadata files, а самый старый будет удалён writer. Каждый следующий commit будет удалять очередной oldest file.

См. [[configuration#Свойства записи|write properties]].

### Удаление orphan files

В Spark и других distributed processing engines failures задач/jobs могут оставлять файлы, на которые не ссылаются table metadata. В некоторых случаях обычный expiration snapshots не способен определить, что файл больше не нужен.

Для очистки orphan files в location таблицы используется `deleteOrphanFiles`:

```java
Table table = ...
SparkActions
    .get()
    .deleteOrphanFiles(table)
    .execute();
```

При большом количестве data/metadata files операция может выполняться долго. Её рекомендуется запускать периодически, но обычно реже, чем другие maintenance operations.

> [!danger]
> Опасно удалять orphan files с retention interval меньше максимально ожидаемого времени записи. In-progress файлы могут быть ошибочно признаны orphan и удалены, что повредит таблицу. Default interval — 3 дня.

> [!danger]
> Iceberg сравнивает строковые представления путей. В некоторых filesystem путь может со временем измениться, продолжая указывать на тот же файл. Например, после изменения HDFS authority старые URL в metadata не совпадут с результатом текущего listing. Запуск `RemoveOrphanFiles` в такой ситуации **может привести к потере данных**. Убедитесь, что пути в MetadataTables соответствуют путям Hadoop FileSystem API.

## Дополнительное обслуживание

Некоторым таблицам требуется дополнительное обслуживание. Streaming queries могут создавать много small files, которые стоит compact. Другие таблицы выигрывают от rewrite manifests, ускоряющего поиск данных.

### Компактизация data files

Iceberg отслеживает каждый data file. Чем их больше, тем больше metadata в manifests. Small files увеличивают объём metadata и overhead на открытие файлов.

`rewriteDataFiles` в Spark объединяет small files в более крупные:

```java
Table table = ...
SparkActions
    .get()
    .rewriteDataFiles(table)
    .filter(Expressions.equal("date", "2020-08-18"))
    .option("target-file-size-bytes", Long.toString(500 * 1024 * 1024)) // 500 MB
    .execute();
```

Metadata table `files` удобна для анализа размеров data files и выбора момента для compaction partitions.

### Rewrite manifests

Iceberg использует manifest list и manifest files как metadata index для ускорения query planning и pruning data files.

Manifests автоматически compact в порядке добавления. Это эффективно, когда write pattern совпадает с типичными read filters. Например, последовательная запись hourly partitions хорошо соответствует time-range filters.

Если write pattern не совпадает с query pattern, metadata можно перегруппировать через `rewriteManifests` / Spark action `rewriteManifests`.

```java
Table table = ...
SparkActions
    .get()
    .rewriteManifests(table)
    .rewriteIf(file -> file.length() < 10 * 1024 * 1024) // 10 MB
    .execute();
```

### Rewrite position delete files

Iceberg умеет переписывать position delete files для двух задач:

- **Minor compaction** — объединить small position delete files в крупные, уменьшив metadata и overhead открытия;
- **Filter dangling records** — при rewrite отбросить записи, ссылающиеся на data files, которые больше не live.

```java
Table table = ...
SparkActions
    .get()
    .rewritePositionDeletes(table)
    .execute();
```

Затрагиваются только выбранные для rewrite files. Для metadata-only удаления целых dangling delete files используется следующий action.

### Удаление dangling delete files

Delete file считается dangling, если его deletes больше не применимы ни к одному live data file. `removeDanglingDeleteFiles` сканирует текущий snapshot и удаляет из metadata целые delete files, которые можно однозначно определить как dangling:

- delete files в partitions без live data files;
- position delete files с data sequence number меньше sequence number любого data file той же partition; deletion vectors удаляются, когда referenced data file больше не live;
- equality delete files с data sequence number меньше либо равным sequence number любого data file той же partition.

Это metadata-only операция: data/delete files физически не переписываются. Action удаляет ссылки на целые delete files и не фильтрует отдельные dangling records из файлов, в которых также есть валидные записи. Для unpartitioned tables action — no-op, поскольку dangling deletes удаляются table-wide на каждом commit.

```java
Table table = ...
SparkActions
    .get()
    .removeDanglingDeleteFiles(table)
    .execute();
```

Spark SQL procedure для action отсутствует. При compaction `rewriteDataFiles` может удалять dangling delete files при `remove-dangling-deletes=true`; `rewritePositionDeletes` фильтрует dangling records в переписываемых position delete files.

### Вычисление table statistics

`computeTableStats` собирает Number of Distinct Values (NDV) для колонок, записывает statistics file формата Puffin и регистрирует его в table metadata. Query engines могут использовать эти statistics для cost-based optimization.

По умолчанию stats собираются для всех top-level primitive columns текущего snapshot. Можно выбрать другой snapshot и/или subset колонок.

```java
Table table = ...
SparkActions
    .get()
    .computeTableStats(table)
    .columns("col1", "col2")
    .execute();
```

В Spark SQL доступна процедура `compute_table_stats`.

### Вычисление partition statistics

`computePartitionStats` вычисляет partition statistics для partitioned table и регистрирует resulting statistics file в metadata. Вычисление выполняется incrementally от последнего snapshot, для которого уже есть partition statistics file, до выбранного snapshot (по умолчанию current). Если предыдущей статистики нет, выполняется full computation.

```java
Table table = ...
SparkActions
    .get()
    .computePartitionStats(table)
    .execute();
```

В Spark SQL доступна процедура `compute_partition_stats`.

## Другие actions

Следующие actions не относятся к регулярному обслуживанию, но полезны после drop table и при переносе таблицы.

### Удаление reachable files

`deleteReachableFiles` удаляет все файлы, на которые ссылается указанный table metadata file: data files, delete files, manifests, manifest lists и metadata files. Это полезно для очистки storage после drop table с выключенным `purge`, например если catalog не способен удалить файлы самостоятельно.

```java
String metadataLocation = ... // path to the table's metadata.json file
FileIO io = ...               // FileIO able to read and delete the table's files
SparkActions
    .get()
    .deleteReachableFiles(metadataLocation)
    .io(io)
    .execute();
```

Action принимает путь к `metadata.json`, а не `Table`, поскольку предназначен для запуска уже после удаления таблицы из catalog.

> [!danger]
> Операция необратимо удаляет **все reachable files** таблицы. Используйте её только после drop table и только когда данные больше не нужны. Если другие таблицы разделяют файлы с этой таблицей, например созданы через `snapshot`, их данные будут повреждены.

### Rewrite table path

`rewriteTablePath` подготавливает копию metadata files, в которой каждый absolute path, начинающийся с source prefix, заменён target prefix. Это может быть начальной стадией полного или incremental копирования таблицы в новое location, например для disaster recovery.

```java
Table table = ...
SparkActions
    .get()
    .rewriteTablePath(table)
    .rewriteLocationPrefix("s3://bucket/old-table-location", "s3://bucket/new-table-location")
    .execute();
```

Action возвращает имя последнего переписанного `metadata.json` и location файла-плана с source/target paths всех файлов, которые нужно скопировать. Metadata и position delete files с обновлёнными путями записываются во staging directory, но сами файлы в target location не копируются — для этого нужен отдельный file-copy tool.

В Spark SQL также доступна процедура `rewrite_table_path`.
