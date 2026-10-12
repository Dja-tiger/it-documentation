---
title: "Kafka Connect"
tags: [apache-iceberg, kafka, kafka-connect, sink, cdc]
source_project: apache/iceberg
source_file: docs/docs/kafka-connect.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/kafka-connect.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Kafka Connect

[Kafka Connect](https://kafka.apache.org/documentation/#connect) — распространённый framework для перемещения данных в Apache Kafka и из него через connectors. Например, S3 Sink записывает Kafka data в S3, а Debezium source connectors публикуют CDC-события из relational databases в Kafka.

Архитектура Kafka Connect децентрализованная и распределённая: cluster состоит из worker processes, а connector запускает tasks на этих workers. Deployment полностью управляется configuration, поэтому для запуска connector обычно не требуется писать код.

## Apache Iceberg Sink Connector

Apache Iceberg Sink Connector для Kafka Connect записывает records из Kafka в Iceberg tables.

## Возможности

- централизованная coordination Iceberg commits;
- exactly-once delivery semantics;
- multi-table fan-out;
- автоматическое создание tables и schema evolution;
- mapping field names через Iceberg column mapping;
- variant shredding для Parquet через table property `write.parquet.shred-variants`.

## Установка

Connector ZIP собирается вместе с Iceberg:

```bash
./gradlew -x test -x integrationTest clean build
```

Архив находится в:

```text
./kafka-connect/kafka-connect-runtime/build/distributions
```

Есть две distributions: с bundled Hive Metastore client и без него. Скопируйте нужный archive в Kafka Connect plugins directory на всех nodes.

## Требования

Exactly-once semantics опирается на Kafka KIP-447 и требует Kafka **2.5+**.

## Конфигурация

| Property | Описание |
| --- | --- |
| `iceberg.tables` | Comma-separated список destination tables |
| `iceberg.tables.dynamic-enabled` | `true`: route по имени table из `route-field` вместо static `route-regex`; default `false` |
| `iceberg.tables.route-field` | Поле record для multi-table routing |
| `iceberg.tables.default-commit-branch` | Default target branch; если не задан — `main` |
| `iceberg.tables.default-id-columns` | Default columns, идентифицирующие row (primary key) |
| `iceberg.tables.default-partition-by` | Default partition fields при auto-create |
| `iceberg.tables.auto-create-enabled` | Автоматически создавать destination tables; default `false` |
| `iceberg.tables.evolve-schema-enabled` | Добавлять отсутствующие record fields в schema; default `false` |
| `iceberg.tables.schema-force-optional` | Делать columns optional при create/evolution; default `false`, то есть соблюдать incoming schema |
| `iceberg.tables.schema-case-insensitive` | Искать columns case-insensitive; default `false` |
| `iceberg.tables.auto-create-props.*` | Properties новых auto-created tables |
| `iceberg.tables.write-props.*` | Properties writer initialization; имеют приоритет |
| `iceberg.table.<table-name>.commit-branch` | Branch конкретной table; fallback `iceberg.tables.default-commit-branch` |
| `iceberg.table.<table-name>.id-columns` | PK/id columns конкретной table |
| `iceberg.table.<table-name>.partition-by` | Partition fields конкретной table |
| `iceberg.table.<table-name>.route-regex` | Regex, сопоставляющий `routeField` table |
| `iceberg.control.topic` | Control topic; default `control-iceberg` |
| `iceberg.control.group-id-prefix` | Prefix control consumer group; default `cg-control` |
| `iceberg.control.commit.interval-ms` | Commit interval; default 300000 ms (5 min) |
| `iceberg.control.commit.timeout-ms` | Commit timeout; default 30000 ms |
| `iceberg.control.commit.threads` | Commit threads; default `cores * 2` |
| `iceberg.control.commit.max-consecutive-failures` | Max consecutive failures до остановки coordinator; default `1` |
| `iceberg.coordinator.transactional.prefix` | Prefix transactional ID coordinator producer; default empty |
| `iceberg.catalog` | Catalog name; default `iceberg` |
| `iceberg.catalog.*` | Properties Iceberg catalog initialization |
| `iceberg.hadoop-conf-dir` | Каталог Hadoop config files |
| `iceberg.hadoop.*` | Hadoop configuration overrides |
| `iceberg.kafka.*` | Kafka client properties control topic |

Если `iceberg.tables.dynamic-enabled=false`, property `iceberg.tables` обязателен. Если `true`, обязателен `iceberg.tables.route-field`, содержащий имя target table.

### Kafka configuration

По умолчанию connector пытается использовать Kafka client configuration worker process для control topic. Если получить её нельзя, параметры задаются явно через `iceberg.kafka.*`.

#### Формат сообщений

Kafka Connect converter должен преобразовать message value в `Struct` или `Map`.

### Catalog configuration

`iceberg.catalog.*` передаются catalog initialization. Default distribution включает REST, Glue, DynamoDB, Hadoop, Nessie, JDBC, Hive и BigQuery Metastore catalogs. JDBC drivers в default distribution не входят — их нужно добавить отдельно. Для Hive можно использовать distribution с HMS client.

Для core catalogs:

```text
iceberg.catalog.type=rest|hive|hadoop
```

Для остальных задайте:

```text
iceberg.catalog.catalog-impl=<fully-qualified-class>
```

#### REST example

```json
"iceberg.catalog.type": "rest",
"iceberg.catalog.uri": "https://catalog-service",
"iceberg.catalog.credential": "<credential>",
"iceberg.catalog.warehouse": "<warehouse>"
```

#### Hive example

> [!note]
> Используйте distribution с HMS client либо добавьте HMS client самостоятельно. Для S3 рекомендуется `S3FileIO`, для GCS — `GCSFileIO`; default `HiveCatalog` использует `HadoopFileIO`.

```json
"iceberg.catalog.type": "hive",
"iceberg.catalog.uri": "thrift://hive:9083",
"iceberg.catalog.io-impl": "org.apache.iceberg.aws.s3.S3FileIO",
"iceberg.catalog.warehouse": "s3a://bucket/warehouse",
"iceberg.catalog.client.region": "us-east-1",
"iceberg.catalog.s3.access-key-id": "<AWS access>",
"iceberg.catalog.s3.secret-access-key": "<AWS secret>"
```

#### Glue example

```json
"iceberg.catalog.catalog-impl": "org.apache.iceberg.aws.glue.GlueCatalog",
"iceberg.catalog.warehouse": "s3a://bucket/warehouse",
"iceberg.catalog.io-impl": "org.apache.iceberg.aws.s3.S3FileIO"
```

#### Nessie example

```json
"iceberg.catalog.catalog-impl": "org.apache.iceberg.nessie.NessieCatalog",
"iceberg.catalog.uri": "http://localhost:19120/api/v2",
"iceberg.catalog.ref": "main",
"iceberg.catalog.warehouse": "s3a://bucket/warehouse",
"iceberg.catalog.io-impl": "org.apache.iceberg.aws.s3.S3FileIO"
```

#### BigQuery Metastore example

```json
"iceberg.catalog.catalog-impl": "org.apache.iceberg.gcp.bigquery.BigQueryMetastoreCatalog",
"iceberg.catalog.gcp.bigquery.project-id": "my-project",
"iceberg.catalog.gcp.bigquery.location": "us-east1",
"iceberg.catalog.warehouse": "gs://bucket/warehouse",
"iceberg.catalog.io-impl": "org.apache.iceberg.gcp.gcs.GCSFileIO",
"iceberg.tables.auto-create-props.bq_connection": "projects/my-project/locations/us-east1/connections/my-connection"
```

В зависимости от S3-compatible environment также могут потребоваться `iceberg.catalog.s3.endpoint`, `iceberg.catalog.s3.staging-dir`, `iceberg.catalog.s3.path-style-access`.

### Azure ADLS configuration

Azure Java SDK требует `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET`. В container environment передавайте их как environment variables:

```text
AZURE_CLIENT_ID=e564f687-7b89-4b48-80b8-111111111111
AZURE_TENANT_ID=95f2f365-f5b7-44b1-88a1-111111111111
AZURE_CLIENT_SECRET="XXX"
```

`CLIENT_ID` — Application ID App Registration, `TENANT_ID` — tenant ID, `CLIENT_SECRET` — secret value. App Registration должен иметь role **Storage Blob Data Contributor** на Storage Account.

Connector config:

```json
"iceberg.catalog.type": "rest",
"iceberg.catalog.uri": "https://catalog:8181",
"iceberg.catalog.warehouse": "abfss://storage-container-name@storageaccount.dfs.core.windows.net/warehouse",
"iceberg.catalog.io-impl": "org.apache.iceberg.azure.adlsv2.ADLSFileIO",
"iceberg.catalog.include-credentials": "true"
```

`include-credentials` позволяет передать Azure Java client credentials, чтобы REST catalog предоставил connection information для ADLSv2 client.

### Google GCS configuration

По умолчанию используются Application Default Credentials (ADC):

```json
"iceberg.catalog.type": "rest",
"iceberg.catalog.uri": "https://catalog:8181",
"iceberg.catalog.warehouse": "gs://bucket-name/warehouse",
"iceberg.catalog.io-impl": "org.apache.iceberg.gcp.gcs.GCSFileIO"
```

### Hadoop configuration

Для HDFS/Hive Hadoop config собирается в таком порядке:

1. config files из classpath;
2. files из `iceberg.hadoop-conf-dir`;
3. explicit `iceberg.hadoop.*`.

Приоритет: **sink config > config dir > classpath**.

## Примеры

### Initial setup

#### Source topic

Примеры предполагают существующий topic `events`.

#### Control topic

Если `auto.create.topics.enable=true`, control topic создаётся автоматически. Иначе создайте default `control-iceberg` вручную:

```bash
bin/kafka-topics.sh \
  --command-config command-config.props \
  --bootstrap-server ${CONNECT_BOOTSTRAP_SERVERS} \
  --create \
  --topic control-iceberg \
  --partitions 1
```

> [!note]
> В Confluent Cloud `auto.create.topics.enable` по умолчанию `false`.

### Одна destination table

```sql
create table default.events (
    id string,
    type string,
    ts timestamp,
    payload string
)
partitioned by (hours(ts));
```

Connector:

```json
{
  "name": "events-sink",
  "config": {
    "connector.class": "org.apache.iceberg.connect.IcebergSinkConnector",
    "tasks.max": "2",
    "topics": "events",
    "iceberg.tables": "default.events",
    "iceberg.catalog.type": "rest",
    "iceberg.catalog.uri": "https://localhost",
    "iceberg.catalog.credential": "<credential>",
    "iceberg.catalog.warehouse": "<warehouse name>"
  }
}
```

### Multi-table fan-out: static routing

Records с `type=list` идут в `default.events_list`, с `type=create` — в `default.events_create`, остальные пропускаются.

```sql
create table default.events_list (
    id string,
    type string,
    ts timestamp,
    payload string
)
partitioned by (hours(ts));

create table default.events_create (
    id string,
    type string,
    ts timestamp,
    payload string
)
partitioned by (hours(ts));
```

```json
{
  "name": "events-sink",
  "config": {
    "connector.class": "org.apache.iceberg.connect.IcebergSinkConnector",
    "tasks.max": "2",
    "topics": "events",
    "iceberg.tables": "default.events_list,default.events_create",
    "iceberg.tables.route-field": "type",
    "iceberg.table.default.events_list.route-regex": "list",
    "iceberg.table.default.events_create.route-regex": "create",
    "iceberg.catalog.type": "rest",
    "iceberg.catalog.uri": "https://localhost",
    "iceberg.catalog.credential": "<credential>",
    "iceberg.catalog.warehouse": "<warehouse name>"
  }
}
```

### Multi-table fan-out: dynamic routing

Имя table берётся из поля `db_table`. Если указанной table нет и auto-create выключен, record пропускается. Например `db_table=default.events_list` записывается в `default.events_list`.

```json
{
  "name": "events-sink",
  "config": {
    "connector.class": "org.apache.iceberg.connect.IcebergSinkConnector",
    "tasks.max": "2",
    "topics": "events",
    "iceberg.tables.dynamic-enabled": "true",
    "iceberg.tables.route-field": "db_table",
    "iceberg.catalog.type": "rest",
    "iceberg.catalog.uri": "https://localhost",
    "iceberg.catalog.credential": "<credential>",
    "iceberg.catalog.warehouse": "<warehouse name>"
  }
}
```

## SMTs для Iceberg Sink Connector

Проект содержит Single Message Transforms, полезные для преобразования Kafka data перед sink.

### `CopyValue` — experimental

Копирует значение одного field в новый field.

| Property | Описание |
| --- | --- |
| `source.field` | Source field |
| `target.field` | Target field |

```json
"transforms": "copyId",
"transforms.copyId.type": "org.apache.iceberg.connect.transforms.CopyValue",
"transforms.copyId.source.field": "id",
"transforms.copyId.target.field": "id_copy"
```

### `DmsTransform` — experimental

Преобразует AWS DMS message для CDC sink: fields из `data` поднимаются на top level, добавляются `_cdc.op`, `_cdc.ts`, `_cdc.source`.

Настроек пока нет.

### `DebeziumTransform` — experimental

Преобразует Debezium message для CDC: fields из `before`/`after` поднимаются на top level и добавляются:

- `_cdc.op`;
- `_cdc.ts`;
- `_cdc.offset`;
- `_cdc.source`;
- `_cdc.target`;
- `_cdc.key`.

| Property | Описание |
| --- | --- |
| `cdc.target.pattern` | Pattern target field; default `{db}.{table}` |

### `JsonToMapTransform` — experimental

Преобразует JSON string и выводит schema. Он предназначен для schema-less/inconsistent JSON, где динамические keys иначе вызвали бы бесконтрольное schema evolution и explosion columns.

Вложенные JSON objects превращаются в `Map<String,String>`, а connector создаёт соответствующие Iceberg map columns.

Требования:

- используйте `StringConverter` как `value.converter`, а не `JsonConverter`;
- input strings должны содержать JSON objects `{...}`;
- keys, tombstones и headers не изменяются.

| Property | Default | Описание |
| --- | --- | --- |
| `json.root` | false | При `true` вся JSON object становится single `payload: Map<String,String>` |

Если `json.root=false`, primitive и array fields получают inferred schema, nested objects становятся `Map<String,String>`. Empty arrays/objects исключаются. Mixed-type arrays преобразуются в arrays of strings.

Пример:

```json
{
  "key": 1,
  "array": [1,"two",3],
  "empty_obj": {},
  "nested_obj": {"some_key": ["one", "two"]}
}
```

`json.root=true`:

```text
SinkRecord.schema:
  payload: Optional Map<String, String>

SinkRecord.value:
  payload = Map(
    key = "1",
    array = "[1,\"two\",3]",
    empty_obj = "{}",
    nested_obj = "{\"some_key\":[\"one\",\"two\"]}"
  )
```

`json.root=false`:

```text
SinkRecord.schema:
  key: Optional Int32
  array: Optional Array<String>
  nested_object: Optional Map<String, String>
```

### `KafkaMetadataTransform` — experimental

Добавляет Kafka message metadata: topic, partition, offset, timestamp.

| Property | Default | Описание |
| --- | --- | --- |
| `field_name` | `_kafka_metadata` | Prefix/имя metadata field |
| `nested` | false | true — вложенный Struct; false — prefixed top-level fields |
| `external_field` | none | Постоянная пара `key,value`, например cluster name |

При `nested=true`:

```text
_kafka_metadata.topic
_kafka_metadata.partition
_kafka_metadata.offset
_kafka_metadata.timestamp
```

При `nested=false`:

```text
_kafka_metadata_topic
_kafka_metadata_partition
_kafka_metadata_offset
_kafka_metadata_timestamp
```

### `MongoDebeziumTransform` — experimental

Преобразует Mongo Debezium `before`/`after` BSON strings в typed Structs, ожидаемые `DebeziumTransform`.

Rename columns, не поддерживаемых underlying catalog, пока не поддерживается.

| Property | Values | Описание |
| --- | --- | --- |
| `array_handling_mode` | `array`, `document` | Способ преобразования BSON arrays |

`array` — default: создаёт array datatype; пользователь обязан обеспечить одинаковый type всех элементов каждого array. Это restrictive, но удобно для downstream processing.

`document` — преобразует array в struct of structs, аналогично BSON serialization. Поля называются `_0`, `_1`, `_2`, ... и соответствуют indexes elements.
