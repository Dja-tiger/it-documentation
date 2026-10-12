---
title: "REST Catalog"
tags: [apache-iceberg, catalogs, rest, authentication]
source_project: apache/iceberg
source_file: docs/docs/rest-catalog.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/rest-catalog.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Iceberg REST Catalog

Iceberg REST catalog — любой catalog service, реализующий Iceberg REST Catalog API specification. Вместо catalog-specific client для каждого engine/language логика catalog размещается за HTTP API, и один REST client может работать с любым compliant server.

Эта страница описывает подключение engines. Концепции protocol — [[rest-protocol|REST Catalog Protocol]].

Для локального тестирования Apache публикует Docker image `apache/iceberg-rest-fixture`, реализующий REST API поверх in-memory catalog.

## Примеры

### Spark

```shell
spark-sql --packages org.apache.iceberg:iceberg-spark-runtime-{{ sparkVersionMajor }}:{{ icebergVersion }} \
    --conf spark.sql.catalog.my_catalog=org.apache.iceberg.spark.SparkCatalog \
    --conf spark.sql.catalog.my_catalog.type=rest \
    --conf spark.sql.catalog.my_catalog.uri=https://catalog-service/api/catalog \
    --conf spark.sql.catalog.my_catalog.warehouse=my_warehouse \
    --conf spark.sql.catalog.my_catalog.rest.auth.type=oauth2 \
    --conf spark.sql.catalog.my_catalog.credential=<client_id>:<client_secret>
```

### Flink

```sql
create catalog prod with (
  'type'='iceberg',
  'catalog-type'='rest',
  'uri'='https://catalog-service/api/catalog'
);
```

## Configuration

Минимально необходим `uri`. Общие properties вроде `warehouse` и `io-impl` также применяются. Server может менять client configuration через endpoint discovery.

| Property | Default | Описание |
| --- | --- | --- |
| `snapshot-loading-mode` | `ALL` | `ALL` — загрузить все snapshots; `REFS` — только referenced snapshots |
| `rest-metrics-reporting-enabled` | true | Отправлять metrics REST server |
| `view-endpoints-supported` | false | Backward compatibility со старыми servers, у которых есть view endpoints, но нет `endpoints` в ConfigResponse |
| `rest-page-size` | null | Page size listing namespaces/tables/resources |
| `namespace-separator` | `%1F` | Separator уровней namespace в REST calls |
| `scan-planning-mode` | `client` | `client` или `server`; server может override per-table |
| `rest-scan-planning.poll-timeout-ms` | 300000 | Max async server-side planning polling time |
| `rest-scan-planning.poll-num-retries` | 10 | Дополнительные poll attempts после первого fetch; `0` = один fetch |
| `rest.client.max-retries` | 5 | HTTP retries с exponential backoff |
| `rest.client.max-connections` | 100 | Max total HTTP pool; JVM system property с тем же именем имеет приоритет |
| `rest.client.connections-per-route` | 100 | Max pooled connections per route |
| `rest.client.connection-timeout-ms` | null | Connection timeout; иначе default HTTP library |
| `rest.client.socket-timeout-ms` | null | Socket timeout |
| `rest.client.user-agent` | null | Custom `User-Agent` |
| `rest.client.proxy.hostname` | null | HTTP proxy hostname; используется только вместе с port |
| `rest.client.proxy.port` | null | HTTP proxy port |
| `rest.client.proxy.username` | null | Basic proxy auth username; нужен вместе с password |
| `rest.client.proxy.password` | null | Basic proxy auth password |
| `rest.client.tls.configurer-impl` | null | Custom `org.apache.iceberg.rest.auth.TLSConfigurer` для SSLContext, hostname verifier, protocols/ciphers. Нужен no-arg constructor |

### Table cache properties

Freshness-aware table loading использует отдельный cache, не общий catalog cache.

| Property | Default | Описание |
| --- | --- | --- |
| `rest-table-cache.expire-after-write-ms` | 300000 (5 min) | TTL cached table entries |
| `rest-table-cache.max-entries` | 100 | Max entries |

## Authentication

Поддерживаемые mechanisms: `none`, `basic`, `oauth2`, `sigv4`, `google`.

### REST auth properties

| Property | Default | Описание |
| --- | --- | --- |
| `rest.auth.type` | `none` | Mechanism: `none`, `basic`, `oauth2`, `sigv4`, `google` |
| `rest.auth.basic.username` | null | Username при Basic; required |
| `rest.auth.basic.password` | null | Password при Basic; required |
| `rest.auth.sigv4.delegate-auth-type` | `oauth2` | Auth type после SigV4 signing |

### OAuth2

| Property | Default | Описание |
| --- | --- | --- |
| `token` | null | Bearer token; нужен `token` или `credential` |
| `credential` | null | `client_id:client_secret` для client credentials flow |
| `oauth2-server-uri` | `v1/oauth/tokens` | Token endpoint; задайте явно, если OAuth server не REST catalog |
| `token-expires-in-ms` | 3600000 | Когда token считается expired |
| `token-refresh-enabled` | true | Auto refresh при известной expiration metadata |
| `token-exchange-enabled` | true | Использовать token exchange; false позволяет fallback на client credentials |
| `scope` | `catalog` | OAuth scope |
| `audience` | null | Optional audience |
| `resource` | null | Optional resource |

> [!danger]
> `credential` и `token` — secrets. Engines могут выводить catalog config в UI/logs. Spark, например, показывает settings в Environment tab и пишет event logs. Проверьте redaction и при необходимости расширьте `spark.redaction.regex`.

### SigV4

| Property | Default | Описание |
| --- | --- | --- |
| `rest.signing-region` | null | AWS region для SigV4 |
| `rest.signing-name` | `execute-api` | Service name для signing |
| `rest.access-key-id` | null | Static access key |
| `rest.secret-access-key` | null | Static secret |
| `rest.session-token` | null | Static session token |
| `client.credentials-provider` | null | Custom AWS credentials provider вместо default chain |
| `client.assume-role.arn` | required by user | ARN role для assume-role |
| `client.assume-role.region` | required by user | Region AWS clients кроме STS |
| `client.assume-role.external-id` | null | Optional external ID |
| `client.assume-role.timeout-sec` | 1 hour | Session timeout assume role |

Если заданы `rest.access-key-id` + `rest.secret-access-key` (+ optional session token), они имеют приоритет над default chain и `client.credentials-provider`.

`client.credentials-provider` должен иметь static `create()` или `create(Map<String,String>)`.

Если заданы assume-role ARN/region, Iceberg использует default credential chain для assume role. Assume-role не применяется, если заданы static REST credentials или custom provider.

### Google authentication

| Property | Default | Описание |
| --- | --- | --- |
| `gcp.auth.credentials-path` | ADC | Path service-account JSON |
| `gcp.auth.credentials-json` | ADC | JSON string service-account credential |
| `gcp.auth.scopes` | `https://www.googleapis.com/auth/cloud-platform` | Comma-separated OAuth scopes |
