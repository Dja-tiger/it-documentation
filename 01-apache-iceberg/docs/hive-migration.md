---
title: "Миграция Hive → Iceberg"
tags: [apache-iceberg, migration, hive]
source_project: apache/iceberg
source_file: docs/docs/hive-migration.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/hive-migration.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Миграция Hive tables

Apache Hive tables в ORC, Parquet и Avro можно мигрировать в Iceberg. Поскольку Hive tables не поддерживают snapshot history, достаточно перенести **актуальные data files**.

Iceberg поддерживает все три migration actions для Hive:

- Snapshot Table;
- Migrate Table;
- Add Files.

Initial migration создаёт Iceberg table с existing schema и commit всех data files всех partitions. Новые files, появившиеся позднее в source Hive table, добавляются через Add Files.

## Включение migration

Hive migration actions реализованы Spark Integration module как [[spark-procedures|Spark Procedures]] и входят в Spark runtime JAR Iceberg.

## Snapshot Hive table → Iceberg

```sql
call catalog_name.system.snapshot('db.source', 'db.dest');
```

Подробности: [[spark-procedures#snapshot]].

## Migrate Hive table → Iceberg

```sql
call catalog_name.system.migrate('db.sample');
```

Подробности: [[spark-procedures#migrate]].

## Добавление files из Hive table

```sql
call spark_catalog.system.add_files(
    table => 'db.tbl',
    source_table => 'db.src_tbl'
);
```

Подробности: [[spark-procedures#add_files]].
