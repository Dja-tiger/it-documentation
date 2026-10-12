---
title: Протокол REST Catalog
tags: [apache-iceberg, catalogs, rest, protocol]
source_project: apache/iceberg
source_file: docs/docs/rest-protocol.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/rest-protocol.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Протокол REST Catalog

## Обзор

По мере роста экосистемы Iceberg каждому engine и языку требовался свой client для каждой реализации catalog. REST Catalog Protocol решает проблему, перенося catalog logic за общий HTTP API, определённый спецификацией Iceberg REST Catalog API: одна реализация client работает с любым совместимым server.

Поскольку commit logic находится на server, протокол поддерживает возможности, недоступные client-side catalogs: server-side разрешение конфликтов, multi-table commits и безопасный обмен таблицами через credential vending или remote signing.

На этой странице описаны концепции протокола и их использование Java client. Параметры подключения и полный reference client properties приведены в [[rest-catalog|REST Catalog]].

## Обнаружение endpoints и конфигурация от server

При инициализации client вызывает configuration route `GET /v1/config`, передавая настроенный `warehouse` как query parameter, если он задан. Ответ может изменить конфигурацию client тремя способами:

- **`defaults`** — свойства, рекомендуемые server; собственная конфигурация client имеет приоритет;
- **`overrides`** — обязательные свойства server, имеющие приоритет над client configuration. Типичный пример — `prefix`, который client добавляет в последующие пути `/v1/{prefix}/namespaces/...`, позволяя одному server обслуживать несколько catalogs;
- **`endpoints`** — список поддерживаемых server API endpoints. Client использует только функции, endpoints которых объявлены; отсутствие view/scan-planning endpoints означает недоступность функции, а не серию ошибочных запросов.

Если поле `endpoints` отсутствует полностью, client предполагает default-набор namespace/table endpoints. Для старых servers с views, появившихся до endpoint discovery, используется `view-endpoints-supported=true`.

## Commit protocol

В отличие от client-side catalog, REST client не пишет metadata file и не меняет pointer самостоятельно. Для commit он отправляет server список требуемых изменений через `POST /v1/{prefix}/namespaces/{namespace}/tables/{table}` в двух частях:

- **Requirements** описывают условия, которые всё ещё должны быть истинны для текущих table metadata: например, branch должен по-прежнему указывать на snapshot, от которого строилось изменение, или UUID таблицы должен совпадать;
- **Updates** — сами изменения metadata: добавление snapshot, установка branch reference, изменение schema и т. п.

Server валидирует все requirements относительно текущих metadata и, если они выполняются, применяет updates и записывает новые metadata. Если requirement нарушен, commit отклоняется; client refresh таблицу, повторно применяет свои изменения и выполняет retry. Поскольку validation централизована на server, все engines получают одинаковую conflict detection, а server может централизованно разрешать конфликты или отклонять некорректные изменения.

Протокол также определяет optional endpoint для атомарного commit нескольких таблиц: `POST /v1/{prefix}/transactions/commit`, доступный в Java как `RESTCatalog.commitTransaction`. Современные engines обычно commit таблицы отдельно, поэтому это прежде всего Java API feature, и server не обязан её поддерживать.

## Делегирование доступа к storage

REST protocol позволяет catalog server управлять доступом к data table, чтобы clients не требовались собственные долгоживущие storage credentials. Спецификация определяет header `X-Iceberg-Access-Delegation` и два механизма.

### Credential vending

Server возвращает short-lived, table-scoped storage credentials (`storage-credentials`) в load-table response. Client применяет их при создании `FileIO`, поэтому чтение/запись data и metadata files выполняются с выданными credentials. Поскольку credentials ограничены storage prefixes конкретной таблицы, catalog становится единой точкой access control.

Решение о выдаче credentials принимает server. Некоторые servers выдают их только при наличии `X-Iceberg-Access-Delegation`.

Credentials истекают. Endpoint `GET /v1/{prefix}/namespaces/{namespace}/tables/{table}/credentials` позволяет long-running jobs получать свежие credentials. S3 `FileIO` обновляет credentials через этот endpoint, если задан `client.refresh-credentials-endpoint`; server обычно возвращает эту настройку в table configuration.

### Remote signing

При remote signing server вообще не передаёт credentials. Вместо этого client отправляет каждый storage request на signing endpoint catalog, server возвращает подписанный request, и client выполняет его. Signing configuration приходит в load-table response. Для S3 механизм активируется `s3.remote-signing-enabled=true`, что server обычно задаёт в возвращаемой table configuration.

## Server-side scan planning

По умолчанию scan планируется client-side: client читает manifest list/manifests и строит file scan tasks. При server-side planning client отправляет scan description — filter, snapshot, выбранные колонки — server, который возвращает scan tasks. Это позволяет server применять собственные оптимизации, metadata caches и indexes и избавляет client от загрузки metadata files.

Planning асинхронный: client отправляет plan, а server либо сразу возвращает результат, либо plan ID, который client poll до завершения. Большие результаты возвращаются batches plan tasks. Client отменяет ненужный plan и прекращает ожидание после `rest-scan-planning.poll-timeout-ms` (default 5 минут) либо после initial fetch плюс `rest-scan-planning.poll-num-retries` (default 10), в зависимости от того, какой предел будет достигнут раньше.

Режим задаётся catalog property `scan-planning-mode`: `client` (default) или `server`. Server может override режим для конкретной таблицы в load-table response. Server-side planning требует advertised scan-planning endpoints.

## Актуальность metadata и caching

Обычная загрузка таблицы означает получение её полных metadata. REST protocol содержит два механизма уменьшения стоимости.

**Freshness-aware table loading.** Если server возвращает `ETag`, client кэширует загруженную таблицу и отправляет ETag в следующих load через `If-None-Match`. Если таблица не изменилась, server отвечает `304 Not Modified`, и client переиспользует cached table без повторного parsing metadata. Cache ограничен по размеру и времени.

**Lazy snapshot loading.** При `snapshot-loading-mode=REFS` client запрашивает только snapshots, на которые ссылаются branches/tags, а не всю историю таблицы. Остальные snapshots загружаются лениво по мере необходимости, что ускоряет load таблиц с длинной историей.

## Идемпотентные retries commit

Если ответ на commit потерян, например из-за network timeout, слепой retry опасен: первая попытка могла успешно завершиться. Если server сообщает поддержку через `idempotency-key-lifetime` в configuration response, client добавляет уникальный header `Idempotency-Key` к mutating requests. При retry с тем же key server возвращает исходный outcome вместо повторного применения изменения.

## Pagination

Listing endpoints для namespaces, tables и views поддерживают pagination. `rest-page-size` задаёт размер страницы; иначе используется server default.

## Отчётность по метрикам

Если server рекламирует metrics endpoint, client отправляет scan/commit metrics server в дополнение к настроенному `metrics-reporter-impl`. Это даёт operator catalog видимость использования таблиц. Отправку можно отключить через `rest-metrics-reporting-enabled=false`. Состав отчётов описан в [[metrics-reporting|Metrics reporting]].
