---
title: "Dell ECS"
tags: [apache-iceberg, storage, dell, ecs, s3]
source_project: apache/iceberg
source_file: docs/docs/dell.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/dell.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Dell

Iceberg поддерживает Dell Enterprise Cloud Storage (ECS) через `DellClientFactories` и `EcsFileIO`.

## Dell ECS FileIO

`EcsFileIO` реализует Iceberg `FileIO` поверх Dell ECS Object Storage SDK.

Подключение зависит от compute engine, но общая модель одинакова: задаётся `io-impl=org.apache.iceberg.dell.ecs.EcsFileIO` и ECS connection properties.

Основные properties:

| Property | Описание |
| --- | --- |
| `ecs.s3.endpoint` | ECS S3-compatible endpoint |
| `ecs.s3.access-key-id` | Access key |
| `ecs.s3.secret-access-key` | Secret key |

Пример Spark catalog:

```shell
spark-sql \
  --conf spark.sql.catalog.my_catalog=org.apache.iceberg.spark.SparkCatalog \
  --conf spark.sql.catalog.my_catalog.type=hadoop \
  --conf spark.sql.catalog.my_catalog.warehouse=s3://bucket/warehouse \
  --conf spark.sql.catalog.my_catalog.io-impl=org.apache.iceberg.dell.ecs.EcsFileIO \
  --conf spark.sql.catalog.my_catalog.ecs.s3.endpoint=https://ecs.example.com:9021 \
  --conf spark.sql.catalog.my_catalog.ecs.s3.access-key-id=<access-key> \
  --conf spark.sql.catalog.my_catalog.ecs.s3.secret-access-key=<secret-key>
```

## Custom client factory

Для организаций, которым нужен собственный способ credentials/client configuration, Iceberg позволяет подключить custom `DellClientFactory` через соответствующие catalog properties.

Factory получает catalog properties и создаёт ECS clients, поэтому здесь можно реализовать интеграцию с internal secret store, credential rotation, custom TLS/proxy и другими environment-specific requirements.

## URI и совместимость

ECS работает через S3-compatible object API. Iceberg metadata содержит absolute file paths, поэтому при смене endpoint/authority следует внимательно учитывать path compatibility при orphan cleanup и migration — это особенно важно для [[maintenance#Удаление orphan files|RemoveOrphanFiles]].
