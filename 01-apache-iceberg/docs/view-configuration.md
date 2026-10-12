---
title: Конфигурация представлений
tags: [apache-iceberg, views, configuration]
source_project: apache/iceberg
source_file: docs/docs/view-configuration.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/view-configuration.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Конфигурация

## Свойства представления

Iceberg views поддерживают properties, позволяющие настраивать поведение представлений. Ниже перечислены доступные свойства.

| Property | Default | Описание |
| --- | --- | --- |
| `write.metadata.compression-codec` | `gzip` | Codec сжатия метаданных: `none` или `gzip` |
| `write.metadata.path` | view location + `/metadata` | Базовый путь для metadata files представления. Если свойство задано явно, metadata files записываются непосредственно в этот путь без дополнительного `/metadata` |
| `version.history.num-entries` | `10` | Количество сохраняемых `versions` |
| `replace.drop-dialect.allowed` | `false` | Разрешено ли удалять SQL dialect во время операции replace |

### Свойства поведения представления

| Property | Default | Описание |
| --- | --- | --- |
| `commit.retry.num-retries` | `4` | Количество повторных попыток commit до ошибки |
| `commit.retry.min-wait-ms` | `100` | Минимальная задержка между повторными попытками commit, мс |
| `commit.retry.max-wait-ms` | `60000` (1 мин) | Максимальная задержка между повторными попытками commit, мс |
| `commit.retry.total-timeout-ms` | `1800000` (30 мин) | Общий timeout всех повторных попыток commit, мс |
