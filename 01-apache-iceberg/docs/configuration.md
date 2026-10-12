---
title: Конфигурация таблиц
tags: [apache-iceberg, concepts, configuration]
source_project: apache/iceberg
source_file: docs/docs/configuration.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/configuration.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Конфигурация

## Свойства таблицы

Iceberg-таблицы поддерживают table properties, с помощью которых настраивается поведение таблицы, например целевой размер split при чтении.

### Свойства чтения

| Property | Default | Описание |
| --- | --- | --- |
| `read.split.target-size` | 134217728 (128 MB) | Целевой размер при объединении input splits с данными |
| `read.split.metadata-target-size` | 33554432 (32 MB) | Целевой размер при объединении metadata input splits |
| `read.split.planning-lookback` | 10 | Количество bins, рассматриваемых при объединении input splits |
| `read.split.open-file-cost` | 4194304 (4 MB) | Оценочная стоимость открытия файла; используется как минимальный вес при объединении splits |
| `read.split.adaptive-size.enabled` | true | Разрешает адаптивно подбирать размер split относительно размера scan и доступного parallelism, если split size не задан явно |
| `read.parquet.vectorization.enabled` | true | Использовать ли vectorized reads для Parquet |
| `read.parquet.vectorization.batch-size` | 5000 | Размер batch для vectorized Parquet reads |
| `read.orc.vectorization.enabled` | false | Использовать ли vectorized reads для ORC |
| `read.orc.vectorization.batch-size` | 5000 | Размер batch для vectorized ORC reads |
| `read.data-planning-mode` | auto | Режим планирования data manifests: `auto`, `local` или `distributed` |
| `read.delete-planning-mode` | auto | Режим планирования delete manifests: `auto`, `local` или `distributed` |

### Свойства записи

| Property | Default | Описание |
| --- | --- | --- |
| `write.format.default` | parquet | Формат data files по умолчанию: `parquet`, `avro` или `orc` |
| `write.delete.format.default` | формат data file | Формат delete files по умолчанию: `parquet`, `avro` или `orc` |
| `write.parquet.row-group-size-bytes` | 134217728 (128 MB) | Размер Parquet row group |
| `write.parquet.row-group-size-track-uncompressed` | false | Учитывать raw data size для более точного соблюдения target row-group size при использовании compression codecs |
| `write.parquet.page-size-bytes` | 1048576 (1 MB) | Размер Parquet page |
| `write.parquet.page-version` | v1 | Версия Parquet data page: `v1` (DataPage V1) или `v2` (DataPage V2) |
| `write.parquet.page-row-limit` | 20000 | Лимит строк в Parquet page |
| `write.parquet.dict-size-bytes` | 2097152 (2 MB) | Размер страницы Parquet dictionary |
| `write.parquet.compression-codec` | zstd | Codec: `zstd`, `brotli`, `lz4`, `gzip`, `snappy`, `uncompressed` |
| `write.parquet.compression-level` | null | Уровень сжатия Parquet |
| `write.parquet.shred-variants` | false | При `true` колонки `variant` записываются через shredded Parquet encoding для ускорения запросов. Каждый data file самостоятельно определяет layout по буферизированным строкам, поэтому разные файлы одного snapshot могут shred разные поля |
| `write.parquet.variant-inference-buffer-size` | 100 | Число строк для schema inference при variant shredding; большее значение даёт более репрезентативную выборку ценой памяти |
| `write.parquet.bloom-filter-enabled.column.col1` | не задано | Указание Parquet создавать Bloom filter для `col1` |
| `write.parquet.bloom-filter-max-bytes` | 1048576 (1 MB) | Максимальный размер bitset Bloom filter |
| `write.parquet.bloom-filter-fpp.column.col1` | 0.01 | Вероятность false positive Bloom filter для `col1`, должна быть > 0 и < 1 |
| `write.parquet.bloom-filter-ndv.column.col1` | не задано | Ожидаемое число distinct values для Bloom filter `col1`, должно быть > 0 |
| `write.parquet.bloom-filter-adaptive-enabled` | false | Включает adaptive sizing Bloom filter: выбирается минимальный candidate filter, удовлетворяющий фактическому NDV при заданном FPP и ограничении `write.parquet.bloom-filter-max-bytes`, вместо постоянного выделения max buffer. Игнорируется, если для колонки явно задан NDV |
| `write.parquet.stats-enabled.column.col1` | не задано | Собирать ли Parquet column statistics для `col1` |
| `write.parquet.dict-encoding-enabled.column.col1` | не задано | Использовать ли dictionary encoding Parquet для `col1` |
| `write.avro.compression-codec` | gzip | Avro codec: `gzip` (deflate level 9), `zstd`, `snappy`, `uncompressed` |
| `write.avro.compression-level` | null | Уровень сжатия Avro |
| `write.orc.stripe-size-bytes` | 67108864 (64 MB) | Размер ORC stripe по умолчанию |
| `write.orc.block-size-bytes` | 268435456 (256 MB) | Размер filesystem block для ORC files |
| `write.orc.compression-codec` | zlib | ORC codec: `zstd`, `lz4`, `lzo`, `zlib`, `snappy`, `none` |
| `write.orc.compression-strategy` | speed | Стратегия ORC compression: `speed` или `compression` |
| `write.orc.bloom.filter.columns` | не задано | Список имён колонок через запятую, для которых создаётся Bloom filter |
| `write.orc.bloom.filter.fpp` | 0.05 | Вероятность false positive Bloom filter, > 0 и < 1 |
| `write.location-provider.impl` | null | Необязательная собственная реализация `LocationProvider` |
| `write.metadata.compression-codec` | none | Codec сжатия metadata: `none` или `gzip` |
| `write.metadata.metrics.max-inferred-column-defaults` | 100 | Максимум колонок, для которых автоматически собираются metrics. Колонки выбираются pre-order обходом schema: сначала top-level, затем поля первого nested struct и т. д. |
| `write.metadata.metrics.default` | `truncate(16)` | Metrics mode по умолчанию для всех колонок: `none`, `counts`, `truncate(length)` или `full` |
| `write.metadata.metrics.column.col1` | не задано | Metrics mode для отдельной `col1` |
| `write.target-file-size-bytes` | 536870912 (512 MB) | Целевой размер генерируемых data files |
| `write.delete.target-file-size-bytes` | 67108864 (64 MB) | Целевой размер delete files |
| `write.distribution-mode` | не задан; зависит от engine | Распределение данных при записи: `none` — без shuffle; `hash` — hash по partition key; `range` — range по partition key либо sort key при наличии SortOrder |
| `write.delete.distribution-mode` | не задано | Распределение данных для delete |
| `write.update.distribution-mode` | не задано | Распределение данных для update |
| `write.merge.distribution-mode` | не задано | Распределение данных для merge |
| `write.wap.enabled` | false | Включает Write-Audit-Publish (WAP) |
| `write.summary.partition-limit` | 0 | Добавляет partition-level summary stats в snapshot summary, если число изменённых партиций меньше лимита |
| `write.metadata.delete-after-commit.enabled` | false | Удалять ли самый старый **отслеживаемый** version metadata file после каждого commit; см. [[maintenance#Удаление старых metadata files]] |
| `write.metadata.previous-versions-max` | 100 | Максимальное число предыдущих version metadata files, сохраняемых в tracking |
| `write.spark.fanout.enabled` | false | Включает Spark fanout writer, не требующий кластеризации данных, но потребляющий больше памяти |
| `write.object-storage.enabled` | false | Включает object-storage location provider, добавляющий hash-компонент в пути файлов |
| `write.object-storage.partitioned-paths` | true | Включать partition values в путь файла |
| `write.data.path` | table location + `/data` | Базовый путь data files |
| `write.metadata.path` | table location + `/metadata` | Базовый путь metadata files |
| `write.delete.mode` | copy-on-write | Режим delete: `copy-on-write` или `merge-on-read` (v2+) |
| `write.delete.isolation-level` | serializable | Isolation level для delete: `serializable` или `snapshot` |
| `write.update.mode` | copy-on-write | Режим update: `copy-on-write` или `merge-on-read` (v2+) |
| `write.update.isolation-level` | serializable | Isolation level для update |
| `write.merge.mode` | copy-on-write | Режим merge: `copy-on-write` или `merge-on-read` (v2+) |
| `write.merge.isolation-level` | serializable | Isolation level для merge |
| `write.delete.granularity` | partition | Гранулярность генерируемых delete files: `partition` или `file` |

Примечания к metrics mode:

1. `none` — metrics не сохраняются.
2. `counts` — сохраняются только count metrics (`value_counts`, `null_value_counts`, `nan_value_counts`).
3. `truncate(length)` — сохраняются counts и усечённые границы (`lower_bounds`, `upper_bounds`). Усечение применяется только к string/binary; остальные типы сохраняются без изменения.
4. `full` — сохраняются все metrics, включая полные `lower_bounds` и `upper_bounds`.

### Свойства шифрования

| Property | Default | Описание |
| --- | --- | --- |
| `encryption.key-id` | не задано | ID master key таблицы |
| `encryption.data-key-length` | 16 bytes | Длина ключей шифрования файлов таблицы; допустимо 16, 24 или 32 bytes |

Подробнее: [[encryption|Шифрование]].

### Свойства поведения таблицы

| Property | Default | Описание |
| --- | --- | --- |
| `commit.retry.num-retries` | 4 | Число retries commit до ошибки |
| `commit.retry.min-wait-ms` | 100 | Минимальная задержка перед retry, мс |
| `commit.retry.max-wait-ms` | 60000 (1 min) | Максимальная задержка перед retry, мс |
| `commit.retry.total-timeout-ms` | 1800000 (30 min) | Общий timeout commit retries, мс |
| `commit.status-check.num-retries` | 3 | Число проверок, был ли commit успешен после потери соединения, прежде чем вернуть unknown commit state |
| `commit.status-check.min-wait-ms` | 1000 (1s) | Минимальная пауза между status-check |
| `commit.status-check.max-wait-ms` | 60000 (1 min) | Максимальная пауза между status-check |
| `commit.status-check.total-timeout-ms` | 1800000 (30 min) | Общий timeout для определения статуса commit |
| `commit.manifest.target-size-bytes` | 8388608 (8 MB) | Target size при merge manifest files |
| `commit.manifest.min-count-to-merge` | 100 | Минимальное количество manifests до автоматического merge |
| `commit.manifest-merge.enabled` | true | Выполнять ли автоматический merge manifests при записи |
| `history.expire.max-snapshot-age-ms` | 432000000 (5 days) | Default максимального возраста snapshots при expiration для таблицы и branches |
| `history.expire.min-snapshots-to-keep` | 1 | Минимальное число сохраняемых snapshots таблицы/branch |
| `history.expire.max-ref-age-ms` | `Long.MAX_VALUE` (forever) | Максимальный возраст snapshot references, кроме `main`; `main` никогда не истекает |
| `gc.enabled` | true | Разрешает garbage-collection операции: expiration snapshots и удаление orphan files |

### Зарезервированные свойства таблицы

Reserved table properties используются только при создании/обновлении таблицы и не сохраняются в table metadata.

| Property | Default | Описание |
| --- | --- | --- |
| `format-version` | 2 | Версия table format согласно Iceberg Spec; default 2 начиная с Iceberg 1.4.0 |

### Информационные свойства

Informational properties добавляют контекст к таблице и полезны для документации, discovery и интеграции с внешними инструментами. Они не влияют на read/write behavior и semantics запросов.

| Property | Default | Описание |
| --- | --- | --- |
| `comment` | не задано | Описание таблицы: её бизнес-смысл и контекст использования |

### Флаги совместимости

| Property | Default | Описание |
| --- | --- | --- |
| `compatibility.snapshot-id-inheritance.enabled` | false | Разрешает commit snapshots без явных snapshot IDs; для format version > 1 фактически всегда true |
