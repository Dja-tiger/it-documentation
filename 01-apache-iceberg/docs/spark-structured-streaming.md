---
title: "Spark Structured Streaming"
tags: [apache-iceberg, spark, streaming]
source_project: apache/iceberg
source_file: docs/docs/spark-structured-streaming.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/spark-structured-streaming.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Spark Structured Streaming

Iceberg использует Apache Spark DataSourceV2 API. DSv2 развивается и имеет разные уровни поддержки в разных версиях Spark.

## Streaming reads

Iceberg поддерживает incremental processing в Structured Streaming, начиная с исторического timestamp:

```scala
val df = spark.readStream
    .format("iceberg")
    .option("stream-from-timestamp", Long.toString(streamStartTimestamp))
    .load("database.table_name")
```

> [!warning]
> Iceberg поддерживает streaming read только из `append` snapshots. `overwrite` snapshot по умолчанию вызывает exception; его можно игнорировать через `streaming-skip-overwrite-snapshots=true`. Аналогично delete snapshots вызывают exception, а `streaming-skip-delete-snapshots=true` позволяет их пропустить.

### Ограничение input rate

Для размера micro-batch доступны:

- `streaming-max-files-per-micro-batch` — максимум файлов в micro-batch;
- `streaming-max-rows-per-micro-batch` — soft maximum строк: следующий unprocessed file включается целиком, но дополнительные файлы не берутся, если превысят limit.

Если заданы оба, срабатывает тот limit, который достигнут первым.

```scala
val df = spark.readStream
    .format("iceberg")
    .option("streaming-max-files-per-micro-batch", "1")
    .load("database.table_name")
```

```scala
val df = spark.readStream
    .format("iceberg")
    .option("streaming-max-rows-per-micro-batch", "1000")
    .load("database.table_name")
```

> [!info]
> Rate limiting работает не только с default `Trigger.ProcessingTime`, но и с `Trigger.AvailableNow`, позволяя разбить однократную обработку всего backlog на несколько micro-batches. С deprecated `Trigger.Once` эти options игнорируются.

### Асинхронное планирование micro-batch

При `async-micro-batch-planning-enabled=true` Iceberg обрабатывает текущий micro-batch и параллельно планирует следующие. Это уменьшает idle time и может повысить throughput, но увеличивает memory consumption и snapshot detection latency. Дополнительные options перечислены в [[spark-configuration#Read options]].

## Streaming writes

Для записи используется `DataStreamWriter`:

```scala
data.writeStream
    .format("iceberg")
    .outputMode("append")
    .trigger(Trigger.ProcessingTime(1, TimeUnit.MINUTES))
    .option("checkpointLocation", checkpointPath)
    .toTable("database.table_name")
```

Для directory-based Hadoop catalog:

```scala
data.writeStream
    .format("iceberg")
    .outputMode("append")
    .trigger(Trigger.ProcessingTime(1, TimeUnit.MINUTES))
    .option("path", "hdfs://nn:8020/path/to/table")
    .option("checkpointLocation", checkpointPath)
    .start()
```

Поддерживаются output modes:

- `append` — добавляет rows каждого micro-batch;
- `complete` — заменяет содержимое таблицы каждый micro-batch.

До запуска stream таблица должна быть создана. См. [[spark-ddl#CREATE TABLE]].

Experimental continuous processing Spark не поддерживается, потому что его interface не предоставляет требуемый commit output.

### Partitioned table

Iceberg требует, чтобы внутри write task данные были сгруппированы по partition values. В batch workload это обычно достигается explicit sort/distribution, но repartition/sort увеличивают latency streaming workload. Для streaming можно включить fanout writer:

```scala
data.writeStream
    .format("iceberg")
    .outputMode("append")
    .trigger(Trigger.ProcessingTime(1, TimeUnit.MINUTES))
    .option("fanout-enabled", "true")
    .option("checkpointLocation", checkpointPath)
    .toTable("database.table_name")
```

Fanout writer открывает файлы для каждого partition value и держит их открытыми до завершения task. Для batch его использовать не рекомендуется: sorting output rows там обычно дешевле.

## Обслуживание streaming tables

Streaming writes быстро создают новые table versions и большой объём metadata. Рекомендуется управлять commit rate, регулярно expire snapshots и очищать metadata files.

### Частота commit

Высокая частота commit порождает много data files, manifests и snapshots. Рекомендуемый trigger interval — минимум 1 минута; при необходимости его следует увеличить.

### Expire old snapshots

Каждый batch создаёт snapshot. При частых commit snapshots быстро накапливаются, поэтому streaming tables необходимо регулярно обслуживать. По умолчанию `expire_snapshots` удаляет snapshots старше пяти дней. См. [[maintenance#Expire snapshots]] и [[spark-procedures#expire_snapshots]].

### Компактизация data files

Streaming обычно пишет небольшие объёмы и создаёт small files. [[maintenance#Компактизация data files|Compaction]] уменьшает metadata и стоимость чтения; в Spark используется `rewrite_data_files`.

### Rewrite manifests

Для уменьшения write latency streaming Iceberg может выполнять fast append без автоматической compaction manifests, из-за чего появляются small manifests. Их следует периодически переписывать через [[spark-procedures#rewrite_manifests|rewrite_manifests]].
