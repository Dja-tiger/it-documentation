# Сверка структуры с Iceberg 1.12.0

Проверено страниц навигации: **42**.

Это автоматическая сверка, а не подтверждение полноты перевода. Разное число блоков может означать объединение примеров. Несовпадение кода может быть следствием регистра SQL или перевода комментариев. Отсутствие ключа требует проверки исходного контекста.

SHA-256 исходников и переводов, номера несовпавших блоков и отсутствующие ключи сохранены в [JSON](source-parity.json).

| Страница | Заголовки: источник / перевод | Код: источник / перевод | Блоки без совпадения | Отсутствующие ключи таблиц |
| --- | --- | --- | --- | --- |
| [api.md](../docs/api.md) | 15 / 14 | 13 / 13 | 0 | — |
| [aws.md](../docs/aws.md) | 53 / 61 | 25 / 50 | 20 | — |
| [branching.md](../docs/branching.md) | 7 / 7 | 14 / 14 | 0 | — |
| [catalog-properties.md](../docs/catalog-properties.md) | 7 / 7 | 0 / 2 | 0 | — |
| [configuration.md](../docs/configuration.md) | 9 / 9 | 0 / 0 | 0 | — |
| [custom-catalog.md](../docs/custom-catalog.md) | 6 / 6 | 6 / 7 | 6 | — |
| [dell.md](../docs/dell.md) | 6 / 6 | 3 / 3 | 0 | — |
| [delta-lake-migration.md](../docs/delta-lake-migration.md) | 10 / 9 | 2 / 3 | 2 | — |
| [encryption.md](../docs/encryption.md) | 5 / 5 | 6 / 6 | 1 | — |
| [evolution.md](../docs/evolution.md) | 5 / 6 | 2 / 2 | 0 | — |
| [fileio.md](../docs/fileio.md) | 4 / 4 | 0 / 0 | 0 | — |
| [flink-configuration.md](../docs/flink-configuration.md) | 8 / 8 | 7 / 7 | 6 | — |
| [flink-connector.md](../docs/flink-connector.md) | 6 / 6 | 6 / 7 | 6 | — |
| [flink-ddl.md](../docs/flink-ddl.md) | 21 / 21 | 21 / 22 | 19 | — |
| [flink-maintenance.md](../docs/flink-maintenance.md) | 44 / 49 | 17 / 17 | 10 | — |
| [flink-queries.md](../docs/flink-queries.md) | 28 / 25 | 26 / 23 | 25 | — |
| [flink-writes.md](../docs/flink-writes.md) | 37 / 36 | 18 / 18 | 13 | — |
| [flink.md](../docs/flink.md) | 14 / 12 | 22 / 21 | 15 | — |
| [hive-migration.md](../docs/hive-migration.md) | 5 / 5 | 3 / 3 | 3 | — |
| [hive.md](../docs/hive.md) | 50 / 50 | 55 / 55 | 55 | — |
| [index.md](../docs/index.md) | 4 / 6 | 0 / 0 | 0 | — |
| [java-api-quickstart.md](../docs/java-api-quickstart.md) | 18 / 18 | 16 / 16 | 1 | — |
| [jdbc.md](../docs/jdbc.md) | 6 / 5 | 2 / 2 | 0 | — |
| [kafka-connect.md](../docs/kafka-connect.md) | 46 / 31 | 19 / 24 | 10 | — |
| [maintenance.md](../docs/maintenance.md) | 15 / 15 | 11 / 11 | 0 | — |
| [metrics-reporting.md](../docs/metrics-reporting.md) | 11 / 11 | 4 / 5 | 2 | — |
| [nessie.md](../docs/nessie.md) | 10 / 8 | 4 / 5 | 3 | — |
| [partitioning.md](../docs/partitioning.md) | 6 / 6 | 3 / 3 | 0 | — |
| [performance.md](../docs/performance.md) | 4 / 4 | 0 / 0 | 0 | — |
| [reliability.md](../docs/reliability.md) | 5 / 5 | 0 / 0 | 0 | — |
| [rest-catalog.md](../docs/rest-catalog.md) | 11 / 11 | 2 / 2 | 1 | — |
| [rest-protocol.md](../docs/rest-protocol.md) | 12 / 12 | 0 / 0 | 0 | — |
| [schemas.md](../docs/schemas.md) | 1 / 1 | 0 / 0 | 0 | — |
| [spark-configuration.md](../docs/spark-configuration.md) | 13 / 13 | 12 / 12 | 5 | `snapshot-property._custom-key_`, `spark.sql.catalog._catalog-name_.cache-enabled`, `spark.sql.catalog._catalog-name_.cache.expiration-interval-ms`, `spark.sql.catalog._catalog-name_.catalog-impl`, `spark.sql.catalog._catalog-name_.default-namespace`, `spark.sql.catalog._catalog-name_.io-impl`, `spark.sql.catalog._catalog-name_.metrics-reporter-impl`, `spark.sql.catalog._catalog-name_.type`, `spark.sql.catalog._catalog-name_.uri`, `spark.sql.catalog._catalog-name_.use-nullable-query-schema`, `spark.sql.catalog._catalog-name_.warehouse` |
| [spark-ddl.md](../docs/spark-ddl.md) | 40 / 36 | 62 / 55 | 62 | — |
| [spark-getting-started.md](../docs/spark-getting-started.md) | 10 / 10 | 10 / 10 | 8 | — |
| [spark-procedures.md](../docs/spark-procedures.md) | 100 / 38 | 58 / 40 | 56 | — |
| [spark-queries.md](../docs/spark-queries.md) | 26 / 26 | 37 / 37 | 35 | — |
| [spark-structured-streaming.md](../docs/spark-structured-streaming.md) | 11 / 11 | 6 / 6 | 2 | — |
| [spark-writes.md](../docs/spark-writes.md) | 26 / 22 | 27 / 27 | 19 | — |
| [table-migration.md](../docs/table-migration.md) | 6 / 6 | 0 / 0 | 0 | — |
| [view-configuration.md](../docs/view-configuration.md) | 3 / 3 | 0 / 0 | 0 | — |

Повторить из корня репозитория:

```sh
python3 01-apache-iceberg/_meta/source-parity.py \
  --source-root /tmp/iceberg-source-1.12.0 --download --write
```

Для повторной сверки по загруженным исходникам уберите `--download`. Источники загружаются по фиксированному tag; их контрольные суммы позволяют обнаружить изменение содержимого.
