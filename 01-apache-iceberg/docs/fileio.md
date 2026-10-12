---
title: "FileIO"
tags: [apache-iceberg, api, fileio, storage]
source_project: apache/iceberg
source_file: docs/docs/fileio.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/fileio.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Iceberg FileIO

## Обзор

Iceberg предоставляет гибкую абстракцию над чтением и записью data/metadata files. Интерфейс `FileIO` позволяет библиотеке Iceberg взаимодействовать с underlying storage layer. `FileIO` используется для всех metadata operations на стадиях job planning и commit.

## Файлы Iceberg

Metadata Iceberg-таблицы хранят absolute path каждого data file, что отделяет логическую таблицу от физического layout. Изменение состояния таблицы выполняется записью новых metadata files и никогда не требует rename файлов.

Поэтому требования к файловым операциям невелики. Реализация `FileIO` должна уметь:

- читать файлы;
- записывать файлы;
- выполнять seek к произвольной позиции stream.

## Использование в processing engines

Чтение и запись самих data files — ответственность processing engine и происходит во время task execution. После записи data files engine использует `FileIO` для создания новых Iceberg metadata files, фиксирующих новое состояние таблицы.

Конкретная реализация `FileIO` выбирается по типу storage. Iceberg включает реализации для популярных backends:

- Amazon S3;
- Google Cloud Storage;
- Object Service Storage, включая HTTPS;
- Dell Enterprise Cloud Storage;
- Hadoop — adapter для любой реализации Hadoop `FileSystem`.
