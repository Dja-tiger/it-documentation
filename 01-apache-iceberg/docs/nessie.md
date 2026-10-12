---
title: "Nessie"
tags: [apache-iceberg, catalogs, nessie, branching]
source_project: apache/iceberg
source_file: docs/docs/nessie.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/nessie.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Iceberg Nessie Integration

Iceberg интегрируется с Nessie через module `iceberg-nessie`.

Nessie добавляет поверх Iceberg:

- multi-table transactions;
- git-like operations: branches, tags, commits;
- metastore capabilities, похожие на Hive.

Nessie требует отдельный server.

## Включение Nessie Catalog

Module `iceberg-nessie` bundled в Spark/Flink runtimes начиная с Iceberg 0.11.0.

Spark 3.5 example:

```shell
spark-sql --packages \
org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:{{ icebergVersion }}
```

## Spark SQL Extensions

Для управления Nessie repository через SQL используются Nessie extensions:

```shell
bin/spark-sql \
  --packages "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:{{ icebergVersion }},org.projectnessie.nessie-integrations:nessie-spark-extensions-3.5_2.12:{{ nessieVersion }}" \
  --conf spark.sql.extensions="org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions,org.projectnessie.spark.extensions.NessieSparkSessionExtensions" \
  --conf <other settings>
```

## Nessie Catalog

Required properties:

- `warehouse` — path хранения tables;
- `uri` — base URI Nessie server, например `http://localhost:19120/api/v2`;
- `ref` — optional branch/tag.

Java:

```java
Map<String, String> options = new HashMap<>();
options.put("warehouse", "/path/to/warehouse");
options.put("ref", "main");
options.put("uri", "https://localhost:19120/api/v2");
Catalog nessieCatalog = CatalogUtil.loadCatalog(
    "org.apache.iceberg.nessie.NessieCatalog",
    "nessie",
    options,
    hadoopConfig);
```

Spark:

```java
conf.set("spark.sql.catalog.nessie.warehouse", "/path/to/warehouse");
conf.set("spark.sql.catalog.nessie.uri", "http://localhost:19120/api/v2");
conf.set("spark.sql.catalog.nessie.ref", "main");
conf.set("spark.sql.catalog.nessie.type", "nessie");
conf.set("spark.sql.catalog.nessie", "org.apache.iceberg.spark.SparkCatalog");
conf.set(
    "spark.sql.extensions",
    "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions,org.projectnessie.spark.extensions.NessieSparkSessionExtensions");
```

Flink Python:

```python
import os
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment

env = StreamExecutionEnvironment.get_execution_environment()
iceberg_flink_runtime_jar = os.path.join(
    os.getcwd(), "iceberg-flink-runtime-{{ icebergVersion }}.jar")
env.add_jars("file://{}".format(iceberg_flink_runtime_jar))
table_env = StreamTableEnvironment.create(env)

table_env.execute_sql("create catalog nessie_catalog with ("
                      "'type'='iceberg', "
                      "'catalog-impl'='org.apache.iceberg.nessie.NessieCatalog', "
                      "'uri'='http://localhost:19120/api/v2', "
                      "'ref'='main', "
                      "'warehouse'='/path/to/warehouse')")
```

Имя `nessie` не специальное: catalog может называться как угодно. Важны implementation/type и required settings.

Один Nessie catalog даёт доступ ко всему repository. Можно создавать/удалять/merge branches и делать commits. Iceberg table идентифицируется namespace произвольной глубины + table name, например `data.base.name.table`. Nessie namespaces должны быть явно созданы.

Каждая Iceberg transaction становится одним Nessie commit. Один Nessie commit способен включать произвольное число actions/tables, но текущая Iceberg integration ограничивает transaction semantics доступным набором single-table transactions.

Merge, commit log, diff и другие repository operations выполняются через Nessie client/CLI либо Nessie SQL extensions.

## Nessie и Iceberg

Для большинства Iceberg operations Nessie ведёт себя как обычный catalog: организует tables и атомарно commit changes. Дополнительно история Iceberg transactions становится Nessie commit history, которую можно list/merge/cherry-pick между branches.

### Loosely coupled transactions

Можно создать branch, выполнить на нём набор operations и затем атомарно merge branch в main. Downstream consumers увидят несколько изменений одновременно.

Это **не настоящий multi-table database transaction**: каждая операция branch остаётся отдельной Iceberg transaction/Nessie commit. Merge только делает последовательность commits одновременно видимой в target branch, подобно fast-forward в git.

Плюс модели в том, что несколько приложений могут независимо изменять branch, а затем весь набор изменений публикуется downstream одновременно.

### Эксперименты

Большие изменения — schema evolution, partition evolution — можно сначала выполнить в отдельном branch, протестировать correctness/performance и лишь затем merge. Если experiment неудачен, branch удаляется без влияния на main.

> [!danger]
> Regular Iceberg table maintenance при Nessie сложнее обычного. Перед [[maintenance|maintenance operations]] обязательно изучите Nessie Management Services, чтобы не удалить files, всё ещё reachable из других Nessie references.

## Future improvements

Основное направление — полноценные Iceberg multi-table transactions: изменения нескольких Iceberg tables в одной transaction с соответствующими isolation semantics.
