---
title: Производительность
tags: [apache-iceberg, concepts, performance]
source_project: apache/iceberg
source_file: docs/docs/performance.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/performance.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Производительность

- Iceberg рассчитан на огромные таблицы и используется в production, где **одна таблица** может содержать десятки петабайт данных.
- Даже многопетабайтные таблицы можно планировать для чтения на одном узле — без распределённого SQL-движка, который предварительно перебирает метаданные таблицы.

## Планирование сканирования

Scan planning — процесс определения файлов таблицы, которые необходимы для выполнения запроса.

В Iceberg планирование помещается на одном узле, поскольку метаданные позволяют отбрасывать не только **data files**, которые не содержат подходящих данных, но и ненужные **metadata files**.

Быстрое планирование на одном узле даёт:

- меньшую latency SQL-запросов — не требуется распределённое сканирование для планирования другого распределённого сканирования;
- доступ из любого клиента — отдельный процесс может напрямую читать данные Iceberg-таблицы.

### Фильтрация метаданных

Iceberg использует два уровня метаданных для отслеживания файлов snapshot:

- **manifest files** хранят список data files, partition data каждого файла и поколоночную статистику;
- **manifest list** хранит список manifest files snapshot и диапазон значений каждого partition field.

Для быстрого scan planning Iceberg сначала фильтрует manifests по диапазонам partition values из manifest list. Затем читает оставшиеся manifests и получает список data files. Поэтому manifest list фактически работает как индекс над manifest files и позволяет планировать запрос без чтения всех manifests.

Кроме диапазонов partition values, manifest list хранит количество добавленных и удалённых файлов в каждом manifest, что ускоряет операции вроде expiration snapshot.

### Фильтрация данных

Manifest files содержат tuple partition data и поколоночную статистику для каждого data file.

Во время планирования predicates запроса автоматически преобразуются в predicates по partition data и сначала применяются для отбрасывания data files. Затем используются `value counts`, `null counts`, нижние и верхние границы значений колонок, чтобы исключить файлы, которые не могут удовлетворить predicate запроса.

Используя lower/upper bounds уже на стадии планирования, Iceberg способен использовать физическую кластеризацию данных и исключать splits до запуска задач. В некоторых сценариях это даёт улучшение производительности примерно на порядок.
