---
title: Отчётность по метрикам
tags: [apache-iceberg, concepts, metrics, observability]
source_project: apache/iceberg
source_file: docs/docs/metrics-reporting.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/metrics-reporting.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Отчётность по метрикам

Начиная с Iceberg 1.1.0 доступны API `MetricsReporter` и `MetricsReport`. Они позволяют описывать разные типы отчётов о метриках и подключать заменяемые реализации доставки этих отчётов.

## Типы отчётов

### ScanReport

`ScanReport` содержит метрики, собранные во время scan planning конкретной таблицы. Помимо общей информации — например snapshot ID и имени таблицы — он включает:

- общую длительность scan planning;
- количество data/delete files в результате;
- количество просканированных/пропущенных data/delete manifests;
- количество просканированных/пропущенных data/delete files;
- количество просканированных equality/positional delete files.

### CommitReport

`CommitReport` содержит метрики, собранные после commit изменений таблицы, то есть после создания snapshot. Помимо snapshot ID и имени таблицы, отчёт включает:

- общую длительность;
- число попыток, потребовавшихся для успешного commit;
- число добавленных/удалённых data/delete files;
- число добавленных/удалённых equality/positional delete files;
- число добавленных/удалённых equality/positional deletes.

## Доступные MetricsReporter

### `LoggingMetricsReporter`

Это reporter по умолчанию, если другой не настроен. Он пишет результаты в log. Пример `ScanReport`:

```text
INFO org.apache.iceberg.metrics.LoggingMetricsReporter - Received metrics report:
ScanReport{
    tableName=scan-planning-with-eq-and-pos-delete-files,
    snapshotId=2,
    filter=ref(name="data") == "(hash-27fa7cc0)",
    schemaId=0,
    projectedFieldIds=[1, 2],
    projectedFieldNames=[id, data],
    scanMetrics=ScanMetricsResult{
        totalPlanningDuration=TimerResult{timeUnit=NANOSECONDS, totalDuration=PT0.026569404S, count=1},
        resultDataFiles=CounterResult{unit=COUNT, value=1},
        resultDeleteFiles=CounterResult{unit=COUNT, value=2},
        totalDataManifests=CounterResult{unit=COUNT, value=1},
        totalDeleteManifests=CounterResult{unit=COUNT, value=1},
        scannedDataManifests=CounterResult{unit=COUNT, value=1},
        skippedDataManifests=CounterResult{unit=COUNT, value=0},
        totalFileSizeInBytes=CounterResult{unit=BYTES, value=10},
        totalDeleteFileSizeInBytes=CounterResult{unit=BYTES, value=20},
        skippedDataFiles=CounterResult{unit=COUNT, value=0},
        skippedDeleteFiles=CounterResult{unit=COUNT, value=0},
        scannedDeleteManifests=CounterResult{unit=COUNT, value=1},
        skippedDeleteManifests=CounterResult{unit=COUNT, value=0},
        indexedDeleteFiles=CounterResult{unit=COUNT, value=2},
        equalityDeleteFiles=CounterResult{unit=COUNT, value=1},
        positionalDeleteFiles=CounterResult{unit=COUNT, value=1}},
    metadata={iceberg-version=Apache Iceberg 1.4.0-SNAPSHOT}}
```

Пример `CommitReport`:

```text
INFO org.apache.iceberg.metrics.LoggingMetricsReporter - Received metrics report:
CommitReport{
    tableName=scan-planning-with-eq-and-pos-delete-files,
    snapshotId=1,
    sequenceNumber=1,
    operation=append,
    commitMetrics=CommitMetricsResult{
        totalDuration=TimerResult{timeUnit=NANOSECONDS, totalDuration=PT0.098429626S, count=1},
        attempts=CounterResult{unit=COUNT, value=1},
        addedDataFiles=CounterResult{unit=COUNT, value=1},
        totalDataFiles=CounterResult{unit=COUNT, value=1},
        totalDeleteFiles=CounterResult{unit=COUNT, value=0},
        addedRecords=CounterResult{unit=COUNT, value=1},
        totalRecords=CounterResult{unit=COUNT, value=1},
        addedFilesSizeInBytes=CounterResult{unit=BYTES, value=10},
        totalFilesSizeInBytes=CounterResult{unit=BYTES, value=10},
        totalPositionalDeletes=CounterResult{unit=COUNT, value=0},
        totalEqualityDeletes=CounterResult{unit=COUNT, value=0}}}
```

### `RESTMetricsReporter`

При использовании `RESTCatalog` это reporter по умолчанию. Он отправляет metrics на REST server в endpoint `/v1/{prefix}/namespaces/{namespace}/tables/{table}/metrics`, определённый REST OpenAPI spec.

Отправкой metrics через REST управляет property `rest-metrics-reporting-enabled`, default `true`.

## Собственный Metrics Reporter

Реализация API `MetricsReporter` даёт полный контроль над входящими экземплярами `MetricsReport`. Например, отчёты можно отправлять в Prometheus endpoint или другую observability-платформу.

```java
public class InMemoryMetricsReporter implements MetricsReporter {

  private List<MetricsReport> metricsReports = Lists.newArrayList();

  @Override
  public void report(MetricsReport report) {
    metricsReports.add(report);
  }

  public List<MetricsReport> reports() {
    return metricsReports;
  }
}
```

## Регистрация собственного Metrics Reporter

### Через конфигурацию Catalog

Catalog property [[catalog-properties|`metrics-reporter-impl`]] принимает fully qualified class name реализации `MetricsReporter`, например:

```text
metrics-reporter-impl=org.apache.iceberg.metrics.InMemoryMetricsReporter
```

### Через Java API во время Scan planning

Независимо от reporter, зарегистрированного на уровне catalog, дополнительные reporters можно передать конкретному `TableScan`:

```java
TableScan tableScan =
    table
        .newScan()
        .metricsReporter(customReporterOne)
        .metricsReporter(customReporterTwo);

try (CloseableIterable<FileScanTask> fileScanTasks = tableScan.planFiles()) {
  // ...
}
```
