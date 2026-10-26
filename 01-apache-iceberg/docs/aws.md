---
title: "AWS"
tags: [apache-iceberg, aws, s3, glue, dynamodb, storage, catalog]
source_project: apache/iceberg
source_file: docs/docs/aws.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/aws.md
translation_status: in_progress
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Интеграции Iceberg с AWS

Iceberg интегрируется с AWS services через module `iceberg-aws`. Здесь описаны Glue Catalog, DynamoDB Catalog и lock manager, `S3FileIO`, AWS client configuration и основные варианты запуска Iceberg в AWS.

## Включение AWS integration

Module `iceberg-aws` входит в Spark/Flink runtime Iceberg начиная с 0.11.0. AWS clients в runtime **не bundled**, чтобы приложение могло использовать совместимую версию AWS SDK. Iceberg зависит от **AWS SDK v2**.

Можно добавить:

- `software.amazon.awssdk:bundle`;
- либо только нужные clients: Glue, S3, DynamoDB, KMS, STS.

Default AWS clients используют Apache HTTP Client. Он не входит в AWS SDK bundle и должен быть добавлен отдельно. При необходимости можно использовать URL Connection HTTP Client; настройка описана в [[#AWS Client Customization]].

### Spark

```sh
spark-sql --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:{{ icebergVersion }},org.apache.iceberg:iceberg-aws-bundle:{{ icebergVersion }} \
    --conf spark.sql.defaultCatalog=my_catalog \
    --conf spark.sql.catalog.my_catalog=org.apache.iceberg.spark.SparkCatalog \
    --conf spark.sql.catalog.my_catalog.warehouse=s3://my-bucket/my/key/prefix \
    --conf spark.sql.catalog.my_catalog.type=glue \
    --conf spark.sql.catalog.my_catalog.io-impl=org.apache.iceberg.aws.s3.S3FileIO
```

`iceberg-aws-bundle` содержит AWS dependencies, необходимые Iceberg.

### Flink

```sh
ICEBERG_VERSION={{ icebergVersion }}
MAVEN_URL=https://repo1.maven.org/maven2
ICEBERG_MAVEN_URL=$MAVEN_URL/org/apache/iceberg

wget $ICEBERG_MAVEN_URL/iceberg-flink-runtime-{{ flinkVersionMajor }}/$ICEBERG_VERSION/iceberg-flink-runtime-{{ flinkVersionMajor }}-$ICEBERG_VERSION.jar
wget $ICEBERG_MAVEN_URL/iceberg-aws-bundle/$ICEBERG_VERSION/iceberg-aws-bundle-$ICEBERG_VERSION.jar

/path/to/bin/sql-client.sh embedded \
    -j iceberg-flink-runtime-{{ flinkVersionMajor }}-$ICEBERG_VERSION.jar \
    -j iceberg-aws-bundle-$ICEBERG_VERSION.jar \
    shell
```

```sql
create catalog my_catalog with (
  'type'='iceberg',
  'warehouse'='s3://my-bucket/my/key/prefix',
  'catalog-type'='glue',
  'io-impl'='org.apache.iceberg.aws.s3.S3FileIO'
);
```

Preload через `sql-client-defaults.yaml`:

```yaml
catalogs:
  - name: my_catalog
    type: iceberg
    warehouse: s3://my-bucket/my/key/prefix
    catalog-type: glue
    io-impl: org.apache.iceberg.aws.s3.S3FileIO
```

### Hive

Добавьте Iceberg Hive runtime и AWS bundle в Hive classpath либо через CLI:

```text
add jar /my/path/to/iceberg-hive-runtime.jar;
add jar /my/path/to/aws/bundle.jar;
```

```sql
set iceberg.engine.hive.enabled=true;
set hive.vectorized.execution.enabled=false;
set iceberg.catalog.glue.type=glue;
set iceberg.catalog.glue.warehouse=s3://my-bucket/my/key/prefix;

create external table database_a.table_a
stored by 'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler'
tblproperties ('iceberg.catalog'='glue');
```

Те же настройки можно preload через `hive-site.xml`.

# Catalogs

## Glue Catalog

AWS Glue можно использовать как implementation Iceberg `Catalog`.

Соответствия:

- Iceberg namespace → Glue Database;
- Iceberg table → Glue Table;
- версия Iceberg table → Glue TableVersion.

Используйте:

```text
catalog-impl=org.apache.iceberg.aws.glue.GlueCatalog
```

или:

```text
catalog-type=glue
```

### Glue Catalog ID

В каждом AWS account/region существует отдельный Glue metastore. По умолчанию Iceberg использует account и region из default AWS credential/region setup.

Для другого AWS account задайте:

```text
glue.id=<numeric-aws-account-id>
```

Если catalog расположен в другом region, AWS client также должен быть настроен на этот region.

### Skip Archive

По умолчанию `GlueCatalog` **не архивирует** старые Glue TableVersions при каждом update. Это особенно важно для streaming ingestion, где commit frequency высока.

Чтобы сохранять старые Glue versions:

```text
glue.skip-archive=false
```

При высокой частоте commit следите за Glue quotas.

### Skip Name Validation

Glue рекомендует Hive-compatible database/table names. В существующих системах иногда встречаются нестандартные символы; в таком случае validation можно отключить соответствующей Glue catalog property. При этом Iceberg не гарантирует, что downstream systems смогут работать с такими именами.

### Optimistic Locking

Glue Catalog по умолчанию использует optimistic locking. Каждая Glue Table имеет version ID. Iceberg запоминает version при чтении metadata и разрешает update только пока server-side version не изменилась.

Если другой writer успел изменить table:

1. update завершается version mismatch;
2. Iceberg refresh metadata;
3. проверяет commit conflict;
4. если операция совместима — повторяет commit.

Это предотвращает случайное перезаписывание concurrent changes и обеспечивает atomic commits.

> [!important]
> Для Glue optimistic locking используйте AWS SDK **>= 2.17.131**. При более старой версии доступен только in-memory lock; для надёжной atomicity нужен [[#DynamoDB Lock Manager]].

### Warehouse Location

Как и другие catalogs, Glue Catalog требует `warehouse`.

Default `FileIO` — `S3FileIO`, поэтому warehouse обычно находится в S3. Для другого storage можно задать `HadoopFileIO` или custom `FileIO` через `io-impl`.

### Table Location

Default location table `my_ns.my_table`:

```text
<warehouse>/my_ns.db/my_table
```

На уровне namespace prefix можно изменить через `locationUri` соответствующей Glue Database.

На уровне table location задаётся явно:

```sql
create table my_catalog.my_ns.my_table (
    id bigint,
    data string,
    category string
)
using iceberg
options ('location'='s3://my-special-table-bucket')
partitioned by (category);
```

Или, если engine поддерживает `location`:

```sql
create table my_catalog.my_ns.my_table (
    id bigint,
    data string,
    category string
)
using iceberg
location 's3://my-special-table-bucket'
partitioned by (category);
```

## DynamoDB Catalog

Iceberg умеет хранить catalog metadata в DynamoDB.

| Property | Default | Описание |
| --- | --- | --- |
| `dynamodb.table-name` | `iceberg` | DynamoDB table, используемая `DynamoDbCatalog` |

### Внутренняя структура DynamoDB table

| Column | Key | Type | Описание |
| --- | --- | --- | --- |
| `identifier` | partition key | string | Table identifier (`db1.table1`) или `NAMESPACE` для namespace records |
| `namespace` | sort key | string | Namespace; GSI использует namespace как partition key и identifier как sort key |
| `v` | — | string | UUID row version для optimistic locking |
| `updated_at` | — | number | Последнее update, millis |
| `created_at` | — | number | Creation timestamp, millis |
| `p.<property_key>` | — | string | Flattened table/namespace properties, включая `table_type`, `metadata_location`, `previous_metadata_location` |

Преимущества design:

1. table-level partition key уменьшает риск hot partition при интенсивных writes в одном namespace;
2. namespace operations изолированы от table commits;
3. reverse GSI обеспечивает list-table operations без full table scan;
4. UUID version `v` исключает collision concurrent commits в одну millisecond;
5. `renameTable` использует multi-row transaction для idempotency;
6. flattened properties позволяют создавать custom GSI, например по `p.owner`.

## RDS JDBC Catalog

Iceberg JDBC Catalog может использовать AWS RDS/Aurora как relational metadata store. Подробности — [[jdbc|JDBC Catalog]]. Для IAM database authentication используйте стандартный AWS RDS IAM flow.

## Как выбрать catalog в AWS

- Если организация уже использует Glue/Athena/EMR/Redshift/Lake Formation — **Glue Catalog** обычно проще всего.
- Для frequent table updates, streaming ingestion и высокой read/write нагрузки Glue и DynamoDB дают хорошую производительность за счёт optimistic locking.
- Для table-level access control Glue удобнее благодаря IAM resource model; DynamoDB item-level IAM сложнее.
- Если нужны быстрые запросы catalog metadata по arbitrary table properties — DynamoDB позволяет добавить secondary indexes.
- DynamoDB catalog можно асинхронно отражать в Glue через DynamoDB Streams + Lambda.
- Если уже есть RDS/Aurora — JDBC catalog даёт прямую интеграцию.

# DynamoDB Lock Manager

`HadoopCatalog`/`HadoopTables` поверх S3 требуют механизм mutual exclusion для atomic commits, поскольку object storage не предоставляет atomic file replacement semantics как HDFS.

Настройка:

```text
lock-impl=org.apache.iceberg.aws.dynamodb.DynamoDbLockManager
lock.table=<dynamodb-lock-table>
```

Если lock table отсутствует, Iceberg создаёт её с billing mode `PAY_PER_REQUEST`.

Остальные lock timings задаются properties из [[catalog-properties#Lock catalog properties]].

# S3 FileIO

`S3FileIO` — рекомендуемая реализация `FileIO` для Amazon S3. `GlueCatalog` использует её по умолчанию; другие catalogs подключают через:

```text
io-impl=org.apache.iceberg.aws.s3.S3FileIO
```

## Progressive Multipart Upload

`S3FileIO` загружает multipart parts параллельно сразу после готовности и удаляет local temporary part после upload. Это повышает throughput и ограничивает local disk consumption.

| Property | Default | Описание |
| --- | --- | --- |
| `s3.multipart.num-threads` | available processors | Общий pool upload threads для output streams |
| `s3.multipart.part-size-bytes` | 32 MB | Размер part |
| `s3.multipart.threshold` | 1.5 | Порог перехода single PUT → multipart, как multiplier part size |
| `s3.staging-dir` | `java.io.tmpdir` | Каталог temporary files |

## S3 Server-Side Encryption

Поддерживаются:

- **SSE-S3** — S3-managed AES-256 keys;
- **SSE-KMS** — AWS KMS key;
- **DSSE-KMS** — dual-layer KMS encryption;
- **SSE-C** — customer-provided key.

| Property | Default | Описание |
| --- | --- | --- |
| `s3.sse.type` | `none` | `none`, `s3`, `kms`, `dsse-kms`, `custom` |
| `s3.sse.key` | `aws/s3` для KMS/DSSE-KMS, иначе null | KMS Key ID/ARN или base64 AES-256 key для custom |
| `s3.sse.md5` | null | Base64 MD5 digest custom key; обязателен для `custom` |

## S3 Access Control List

`S3FileIO` поддерживает ACL через property:

```text
s3.acl=<acl-value>
```

## Object Store File Layout

Traditional Hive layout концентрирует files под одинаковыми prefixes. S3 масштабирует request throughput по prefixes, поэтому такой layout может вызвать throttling.

`ObjectStoreLocationProvider` добавляет deterministic hash к path и распределяет objects по prefixes.

Включение:

```sql
create table my_catalog.my_ns.my_table (
    id bigint,
    data string,
    category string
)
using iceberg
options (
    'write.object-storage.enabled'=true,
    'write.data.path'='s3://my-table-data-bucket/my_table'
)
partitioned by (category);
```

```sql
insert into my_catalog.my_ns.my_table values (1, 'Pizza', 'orders');
```

Современный layout использует 20-bit base2 hash и разбивает entropy на 4-bit directories глубиной 3, например:

```text
s3://my-table-data-bucket/my_ns.db/my_table/0101/0110/1001/10110010/category=orders/00000-0-...parquet
```

Resolution order сейчас:

1. `write.data.path`;
2. `<tableLocation>/data`.

Legacy:

- до 0.12.0 требовался `write.object-storage.path`;
- в 0.12.0 использовался fallback `write.object-storage.path` → `write.folder-storage.path` → `<tableLocation>/data`;
- legacy properties планируются к удалению в 2.0.0.

Чтобы не включать partition values в object key:

```text
write.object-storage.partitioned-paths=false
```

Тогда final entropy добавляется к filename:

```text
s3://my-table-data-bucket/my_ns.db/my_table/1101/0100/1011/00111010-00000-0-...parquet
```

## S3 Retries

При throttling retries должны давать S3 время автоматически scale prefixes.

| Property | Default | Описание |
| --- | --- | --- |
| `s3.retry.num-retries` | 5 | Число retries; для high-throughput throttled workloads upstream рекомендует начать с 32 |
| `s3.retry.min-wait-ms` | 2 s | Минимальный backoff |
| `s3.retry.max-wait-ms` | 20 s | Максимальный backoff |

## S3 Strong Consistency

С ноября 2020 Amazon S3 предоставляет strong read-after-write/list consistency. Iceberg использует это напрямую и не добавляет redundant consistency waits/checks.

## Hadoop S3A FileSystem

> [!important]
> Для S3 рекомендуется **`S3FileIO`**, а не `S3A FileSystem` (`HadoopFileIO`).

`S3FileIO` пишет `s3://`, но способен читать paths `s3a://` и `s3n://` из существующих manifests, поэтому переход с S3A обычно не требует переписывать metadata.

Если S3A всё же нужен:

1. `warehouse` задайте как `s3a://...`;
2. для `HiveCatalog` задайте `hive.metastore.warehouse.dir` как S3A path;
3. добавьте runtime dependency `hadoop-aws`;
4. настройте S3A согласно документации именно вашей версии Hadoop.

## Проверка checksum при записи

```text
s3.checksum-enabled=true
```

Default `false`.

## S3 Tags

Write tags:

```text
s3.write.tags.<key>=<value>
```

Пример Spark:

```sh
spark-sql \
  --conf spark.sql.catalog.my_catalog=org.apache.iceberg.spark.SparkCatalog \
  --conf spark.sql.catalog.my_catalog.warehouse=s3://my-bucket/my/key/prefix \
  --conf spark.sql.catalog.my_catalog.type=glue \
  --conf spark.sql.catalog.my_catalog.io-impl=org.apache.iceberg.aws.s3.S3FileIO \
  --conf spark.sql.catalog.my_catalog.s3.write.tags.my_key1=my_val1
```

Чтобы вместо hard delete сначала помечать object тегами:

```text
s3.delete-enabled=false
s3.delete.tags.<key>=<value>
```

Objects затем можно удалять S3 Lifecycle policy. Default `s3.delete-enabled=true`.

Thread pool tagging/deletion:

```text
s3.delete.num-threads=<n>
```

Автоматические tags:

```text
s3.write.table-tag-enabled=true
s3.write.namespace-tag-enabled=true
```

Они создают:

```text
iceberg.table=<table-name>
iceberg.namespace=<namespace-name>
```

## S3 Access Points

Bucket можно сопоставить access point ARN:

```text
s3.access-points.<bucket>=arn:aws:s3::<ACCOUNT_ID>:accesspoint/<ACCESS_POINT>
```

Для cross-region ARN:

```text
s3.use-arn-region-enabled=true
```

Это позволяет использовать access points для cross-account/cross-region/multi-region и disaster-recovery architectures.

## S3 Access Grants

После добавления AWS S3 Access Grants plugin:

```text
s3.access-grants.enabled=true
```

Fallback на обычные IAM permissions:

```text
s3.access-grants.fallback-to-iam=true
```

Default fallback — `false`.

## S3 Cross-Region Access

```text
s3.cross-region-access-enabled=true
```

Default `false`, чтобы не платить initial latency определения region bucket.

## S3 Transfer Acceleration

```text
s3.acceleration-enabled=true
```

Transfer Acceleration может ускорить long-distance transfers крупных objects через AWS edge network.

## S3 Analytics Accelerator

AWS open-source Analytics Accelerator for S3 оптимизирует reads аналитических formats. Включение:

```text
s3.analytics-accelerator.enabled=true
```

Default `false`.

Пример:

```sh
spark-sql \
  --conf spark.sql.catalog.my_catalog=org.apache.iceberg.spark.SparkCatalog \
  --conf spark.sql.catalog.my_catalog.warehouse=s3://my-bucket2/my/key/prefix \
  --conf spark.sql.catalog.my_catalog.type=glue \
  --conf spark.sql.catalog.my_catalog.io-impl=org.apache.iceberg.aws.s3.S3FileIO \
  --conf spark.sql.catalog.my_catalog.s3.analytics-accelerator.enabled=true
```

Library работает с CRT-based S3 async client или `S3AsyncClient`; upstream рекомендует CRT client для более эффективного connection pooling и throughput.

### Client configuration

| Property | Default | Описание |
| --- | --- | --- |
| `s3.crt.enabled` | true | Создавать async S3 clients через CRT |
| `s3.crt.max-concurrency` | 500 | Max concurrency CRT client |

### Logical IO configuration

| Property | Default | Описание |
| --- | --- | --- |
| `s3.analytics-accelerator.logicalio.prefetch.footer.enabled` | true | Prefetch footer |
| `s3.analytics-accelerator.logicalio.prefetch.page.index.enabled` | true | Prefetch Parquet page index |
| `s3.analytics-accelerator.logicalio.prefetch.file.metadata.size` | 32 KB | Metadata prefetch regular file |
| `s3.analytics-accelerator.logicalio.prefetch.large.file.metadata.size` | 1 MB | Metadata prefetch large file |
| `s3.analytics-accelerator.logicalio.prefetch.file.page.index.size` | 1 MB | Page-index prefetch regular file |
| `s3.analytics-accelerator.logicalio.prefetch.large.file.page.index.size` | 8 MB | Page-index prefetch large file |
| `s3.analytics-accelerator.logicalio.large.file.size` | 1 GB | Threshold large file |
| `s3.analytics-accelerator.logicalio.small.objects.prefetching.enabled` | true | Prefetch small objects |
| `s3.analytics-accelerator.logicalio.small.object.size.threshold` | 3 MB | Small-object threshold |
| `s3.analytics-accelerator.logicalio.parquet.metadata.store.size` | 45 | Parquet metadata store size |
| `s3.analytics-accelerator.logicalio.max.column.access.store.size` | 15 | Max column-access store |
| `s3.analytics-accelerator.logicalio.parquet.format.selector.regex` | `^.*.(parquet\|par)$` | Regex Parquet files |
| `s3.analytics-accelerator.logicalio.prefetching.mode` | `ROW_GROUP` | `OFF`, `ALL`, `ROW_GROUP`, `COLUMN_BOUND` |

### Physical IO configuration

| Property | Default | Описание |
| --- | --- | --- |
| `s3.analytics-accelerator.physicalio.metadatastore.capacity` | 50 | Metadata store capacity |
| `s3.analytics-accelerator.physicalio.blocksizebytes` | 8 MB | Transfer block size |
| `s3.analytics-accelerator.physicalio.readaheadbytes` | 64 KB | Read-ahead bytes |
| `s3.analytics-accelerator.physicalio.maxrangesizebytes` | 8 MB | Max S3 range size |
| `s3.analytics-accelerator.physicalio.partsizebytes` | 8 MB | Transfer part size |
| `s3.analytics-accelerator.physicalio.sequentialprefetch.base` | 2.0 | Sequential prefetch growth base |
| `s3.analytics-accelerator.physicalio.sequentialprefetch.speed` | 1.0 | Sequential prefetch speed factor |

### Telemetry configuration

| Property | Default | Описание |
| --- | --- | --- |
| `s3.analytics-accelerator.telemetry.level` | `STANDARD` | `CRITICAL`, `STANDARD`, `VERBOSE` |
| `s3.analytics-accelerator.telemetry.std.out.enabled` | false | Stdout telemetry |
| `s3.analytics-accelerator.telemetry.logging.enabled` | true | Logging telemetry |
| `s3.analytics-accelerator.telemetry.aggregations.enabled` | false | Aggregated telemetry |
| `s3.analytics-accelerator.telemetry.aggregations.flush.interval.seconds` | -1 | Flush interval |
| `s3.analytics-accelerator.telemetry.logging.level` | `INFO` | Log level |
| `s3.analytics-accelerator.telemetry.logging.name` | `com.amazon.connector.s3.telemetry` | Logger name |
| `s3.analytics-accelerator.telemetry.format` | `default` | `json` или `default` |

### Object client configuration

| Property | Default | Описание |
| --- | --- | --- |
| `s3.analytics-accelerator.useragentprefix` | null | Prefix `User-Agent` S3 requests |

## S3 Dual-stack

```text
s3.dualstack-enabled=true
```

Dual-stack endpoint разрешается в IPv6, если доступен, иначе используется IPv4.

## S3 endpoint

Для S3-compatible storage можно задать endpoint:

```sh
--conf spark.sql.catalog.hadoop_prod.s3.endpoint=http://10.0.0.1:9000
```

## Delete batch size

S3 `DeleteObjects` поддерживает batch до 1000 keys. Iceberg property:

```text
s3.delete.batch-size=250
```

Default — 250; maximum — 1000.

## Remote signing

При REST catalog client может работать без storage credentials, отправляя S3 requests catalog server для подписи:

```text
s3.remote-signing-enabled=true
```

Это соответствует remote-signing flow из [[rest-protocol#Remote signing]].

# AWS Client Customization

Организации часто имеют собственные credential providers, proxies, retry policies и client setup. Реализацию можно подменить через:

```text
client.factory=<implementation org.apache.iceberg.aws.AwsClientFactory>
```

Default:

```text
org.apache.iceberg.aws.DefaultAwsClientFactory
```

Custom factory должен иметь no-arg constructor.

## Cross-account и cross-region через AssumeRole

Iceberg предоставляет:

```text
org.apache.iceberg.aws.AssumeRoleAwsClientFactory
```

Properties:

| Property | Default | Описание |
| --- | --- | --- |
| `client.assume-role.arn` | required | ARN role |
| `client.assume-role.region` | required | Region Glue/S3/DynamoDB clients |
| `client.assume-role.external-id` | null | External ID, особенно для third-party access |
| `client.assume-role.timeout-sec` | 1 hour | Duration STS role session |

Пример:

```sh
spark-sql --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:{{ icebergVersion }},org.apache.iceberg:iceberg-aws-bundle:{{ icebergVersion }} \
    --conf spark.sql.catalog.my_catalog=org.apache.iceberg.spark.SparkCatalog \
    --conf spark.sql.catalog.my_catalog.warehouse=s3://my-bucket/my/key/prefix \
    --conf spark.sql.catalog.my_catalog.type=glue \
    --conf spark.sql.catalog.my_catalog.client.factory=org.apache.iceberg.aws.AssumeRoleAwsClientFactory \
    --conf spark.sql.catalog.my_catalog.client.assume-role.arn=arn:aws:iam::123456789:role/myRoleToAssume \
    --conf spark.sql.catalog.my_catalog.client.assume-role.region=ap-northeast-1
```

STS client создаётся с default credentials/region, затем assumed credentials используются Glue/S3/DynamoDB clients.

REST catalog с SigV4 authentication также может использовать assume-role settings для signing requests.

## Tenant isolation

Для multi-tenant architecture можно выделить tenant-specific IAM roles/resources и применять `AssumeRoleAwsClientFactory`, чтобы каждый catalog/client работал только с разрешёнными buckets/catalog objects.

## Custom credentials provider

```text
client.credentials-provider=<class>
client.credentials-provider.<key>=<value>
```

Class должен реализовывать `software.amazon.awssdk.auth.credentials.AwsCredentialsProvider` и предоставлять static `create()` либо `create(Map<String,String>)`.

## HTTP Client Configurations

Поддерживаются URL Connection HTTP Client и Apache HTTP Client. Default — **Apache**.

| Property | Default | Описание |
| --- | --- | --- |
| `http-client.type` | `apache` | `urlconnection` или `apache` |
| `http-client.proxy-endpoint` | null | Proxy endpoint |
| `http-client.proxy-use-system-property-values` | enabled | Читать Java system proxy properties |
| `http-client.proxy-use-environment-variable-values` | enabled | Читать `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY` |

### URL Connection HTTP Client

| Property | Default | Описание |
| --- | --- | --- |
| `http-client.urlconnection.socket-timeout-ms` | null | Socket timeout |
| `http-client.urlconnection.connection-timeout-ms` | null | Connection timeout |

Пример:

```sh
--conf spark.sql.catalog.my_catalog.http-client.urlconnection.socket-timeout-ms=80
```

### Apache HTTP Client

| Property | Default | Описание |
| --- | --- | --- |
| `http-client.apache.socket-timeout-ms` | null | Socket timeout |
| `http-client.apache.connection-timeout-ms` | null | Connection timeout |
| `http-client.apache.connection-acquisition-timeout-ms` | null | Pool acquisition timeout |
| `http-client.apache.connection-max-idle-time-ms` | null | Max idle time |
| `http-client.apache.connection-time-to-live-ms` | null | Connection TTL |
| `http-client.apache.expect-continue-enabled` | disabled | HTTP expect-continue |
| `http-client.apache.max-connections` | null | Max connections |
| `http-client.apache.tcp-keep-alive-enabled` | disabled | TCP KeepAlive |
| `http-client.apache.use-idle-connection-reaper-enabled` | enabled | Idle connection reaper |

```sh
--conf spark.sql.catalog.my_catalog.http-client.apache.max-connections=5
```

# IAM permissions

## S3

Минимальный read-only access:

```text
s3:GetObject
```

Read/write обычно требует:

```text
s3:GetObject
s3:PutObject
s3:DeleteObject
```

Дополнительные capabilities (tags, ACL, multipart, Access Grants и т. п.) требуют соответствующих AWS permissions.

## Glue

Catalog management требует как минимум permissions соответствующих operations, например:

```text
glue:GetDatabase
glue:GetDatabases
glue:CreateDatabase
glue:UpdateDatabase
glue:DeleteDatabase
glue:GetTable
glue:GetTables
glue:CreateTable
glue:UpdateTable
glue:DeleteTable
```

# Запуск Iceberg в AWS

## Amazon Athena

Athena умеет serverless читать/писать Iceberg tables и выполнять row-level operations/maintenance для поддерживаемых Iceberg tables в Glue Catalog. Всегда проверяйте текущую версию Iceberg/spec features, поддерживаемую Athena.

## Amazon EMR

EMR предоставляет Spark, Hive, Flink и Trino, поэтому Iceberg можно запускать как обычные engine integrations. Начиная с современных EMR 6.x releases Iceberg dependencies можно устанавливать через native EMR configuration; в более старых releases использовались bootstrap actions/custom jars.

## AWS Glue

AWS Glue jobs дают serverless Spark environment, где Iceberg можно использовать с Glue Catalog и `S3FileIO`. Версия встроенного Iceberg зависит от Glue runtime; при необходимости можно предоставить собственные jars, проверив classpath compatibility.

## Amazon EKS

На EKS можно запускать Spark/Flink/Trino и подключать Iceberg как в любом Kubernetes deployment, используя IAM Roles for Service Accounts/Pod Identity для AWS credentials.

## Amazon Managed Service for Apache Flink

Managed Flink может использовать Iceberg connector/runtime JAR и писать Iceberg tables в S3 через Glue/REST/custom catalog.

## Amazon Redshift

Redshift Spectrum/Redshift Serverless может query Iceberg tables, зарегистрированные в Glue Catalog, в рамках текущей поддержки AWS.

## Amazon Data Firehose

Amazon Data Firehose способен доставлять streaming records непосредственно в Iceberg tables в S3 с routing records по destination tables и поддержкой insert/update/delete semantics в рамках service capabilities. Catalog metadata обычно интегрируется с AWS Glue.

## Связанные страницы

- [[catalog-properties|Catalog properties]]
- [[encryption|Iceberg encryption]]
- [[custom-catalog|Custom Catalog / FileIO / LocationProvider]]
- [[rest-catalog|REST Catalog]]
- [[jdbc|JDBC Catalog]]
- [[maintenance|Maintenance]]
