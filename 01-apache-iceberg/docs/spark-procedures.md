---
title: "Spark Procedures"
tags: [apache-iceberg, spark, procedures, maintenance]
source_project: apache/iceberg
source_file: docs/docs/spark-procedures.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/spark-procedures.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Spark Procedures

Сначала настройте [[spark-configuration|Spark catalogs]]. В Spark 3.x stored procedures доступны только при подключённых Iceberg SQL extensions. В Spark 4.0 procedures поддерживаются native Spark и не требуют Iceberg SQL extensions, но являются **case-sensitive**.

## Использование

Procedures вызываются через любой настроенный Iceberg catalog командой `call`. Все находятся в namespace `system`.

Аргументы можно передавать по имени (рекомендуется) или позиционно. Смешивать оба способа нельзя.

### Named arguments

Именованные arguments разрешено передавать в любом порядке; optional можно пропускать:

```sql
call catalog_name.system.procedure_name(arg_name_2 => arg_2, arg_name_1 => arg_1);
```

### Positional arguments

Позиционно можно пропустить только optional arguments в конце:

```sql
call catalog_name.system.procedure_name(arg_1, arg_2, ... arg_n);
```

## Управление snapshots

### `rollback_to_snapshot`

Откатывает таблицу к заданному snapshot ID. Для rollback по времени используйте `rollback_to_timestamp`.

> [!info]
> Procedure инвалидирует cached Spark plans, ссылающиеся на таблицу.

| Argument | Required | Type | Описание |
| --- | --- | --- | --- |
| `table` | ✔ | string | Таблица |
| `snapshot_id` | ✔ | long | Snapshot ID для rollback |

Output:

| Field | Type | Описание |
| --- | --- | --- |
| `previous_snapshot_id` | long | Current snapshot до rollback |
| `current_snapshot_id` | long | Новый current snapshot |

```sql
call catalog_name.system.rollback_to_snapshot('db.sample', 1);
```

### `rollback_to_timestamp`

Откатывает к snapshot, который был current в указанный момент.

| Argument | Required | Type | Описание |
| --- | --- | --- | --- |
| `table` | ✔ | string | Таблица |
| `timestamp` | ✔ | timestamp | Момент rollback |

Output: `previous_snapshot_id`, `current_snapshot_id`.

```sql
call catalog_name.system.rollback_to_timestamp('db.sample', timestamp '2021-06-30 00:00:00.000');
```

### `set_current_snapshot`

Назначает current snapshot. В отличие от rollback, выбранный snapshot не обязан быть ancestor текущего state.

| Argument | Required | Type | Описание |
| --- | --- | --- | --- |
| `table` | ✔ | string | Таблица |
| `snapshot_id` | — | long | Snapshot ID |
| `ref` | — | string | Branch/tag reference |

Нужно передать ровно один из `snapshot_id` или `ref`.

```sql
call catalog_name.system.set_current_snapshot('db.sample', 1);
call catalog_name.system.set_current_snapshot(table => 'db.sample', ref => 's1');
```

### `cherrypick_snapshot`

Cherry-pick переносит изменения существующего snapshot в current table state, создавая новый snapshot и не изменяя original. Поддерживаются только append и dynamic overwrite snapshots.

| Argument | Required | Type |
| --- | --- | --- |
| `table` | ✔ | string |
| `snapshot_id` | ✔ | long |

Output: `source_snapshot_id`, `current_snapshot_id`.

```sql
call catalog_name.system.cherrypick_snapshot('my_table', 1);
call catalog_name.system.cherrypick_snapshot(snapshot_id => 1, table => 'my_table');
```

### `publish_changes`

Публикует изменения staged WAP ID в current table state. Создаёт новый snapshot на основе staged snapshot. Успешно публикуются только append/dynamic overwrite snapshots. Если найдено несколько snapshots с одним `wap_id`, procedure завершается ошибкой.

| Argument | Required | Type |
| --- | --- | --- |
| `table` | ✔ | string |
| `wap_id` | ✔ | string |

Output: `source_snapshot_id`, `current_snapshot_id`.

```sql
call catalog_name.system.publish_changes('my_table', 'wap_id_1');
call catalog_name.system.publish_changes(wap_id => 'wap_id_2', table => 'my_table');
```

### `fast_forward`

Fast-forward одного branch к latest snapshot другого.

| Argument | Required | Type | Описание |
| --- | --- | --- | --- |
| `table` | ✔ | string | Таблица |
| `branch` | ✔ | string | Branch, который будет продвинут |
| `to` | ✔ | string | Source branch |

Output: `branch_updated`, `previous_ref`, `updated_ref`.

```sql
call catalog_name.system.fast_forward('my_table', 'main', 'audit-branch');
```

## Управление metadata

Большинство [[maintenance|maintenance actions]] доступны как procedures.

### `expire_snapshots`

Каждая write/update/delete/upsert/compaction создаёт snapshot. `expire_snapshots` удаляет старые snapshots и файлы, которые нужны **только** им. Файлы, на которые ссылается хотя бы один non-expired snapshot, не удаляются.

| Argument | Required | Type | Default / описание |
| --- | --- | --- | --- |
| `table` | ✔ | string | Таблица |
| `older_than` | — | timestamp | 5 дней назад; удалить snapshots старше |
| `retain_last` | — | int | 1; минимум ancestor snapshots независимо от возраста |
| `max_concurrent_deletes` | — | int | Размер thread pool delete actions; default без pool |
| `stream_results` | — | boolean | false; при true deletion files передаются driver по RDD partitions — рекомендуется для предотвращения driver OOM |
| `snapshot_ids` | — | array<long> | Явные snapshot IDs для expiration |
| `clean_expired_metadata` | — | boolean | Удалять неиспользуемые specs/schemas и другие metadata |

Если `older_than`/`retain_last` не заданы, используются [[configuration#Свойства поведения таблицы|table expiration properties]]. Snapshots, удерживаемые branch/tag, не удаляются. Default branch/tag не истекают; policy можно задать `history.expire.max-ref-age-ms`. `main` не истекает никогда.

Output counts:

- `deleted_data_files_count`;
- `deleted_position_delete_files_count`;
- `deleted_equality_delete_files_count`;
- `deleted_manifest_files_count`;
- `deleted_manifest_lists_count`;
- `deleted_statistics_files_count`.

```sql
call hive_prod.system.expire_snapshots('db.sample', timestamp '2021-06-30 00:00:00.000', 100);
```

```sql
call hive_prod.system.expire_snapshots(table => 'db.sample', snapshot_ids => array(123));
```

### `remove_orphan_files`

Удаляет files, которые не упоминаются ни в одном metadata file таблицы.

| Argument | Required | Type | Default / описание |
| --- | --- | --- | --- |
| `table` | ✔ | string | Таблица |
| `older_than` | — | timestamp | 3 дня назад |
| `location` | — | string | Table location |
| `dry_run` | — | boolean | false; только показать candidates |
| `max_concurrent_deletes` | — | int | Thread pool delete operations |
| `stream_results` | — | boolean | false; при true stream partitions driver и return sample до 20 000 paths |
| `file_list_view` | — | string | Dataset со списком files вместо directory listing |
| `equal_schemes` | — | map<string,string> | default `map('s3a,s3n','s3')` |
| `equal_authorities` | — | map<string,string> | Эквивалентные filesystem authorities |
| `prefix_mismatch_mode` | — | string | `ERROR` default, `IGNORE`, `DELETE` |
| `prefix_listing` | — | boolean | false; использовать `SupportsPrefixOperations`; FileIO должен его поддерживать |

Output: `orphan_file_location`.

Dry run:

```sql
call catalog_name.system.remove_orphan_files(table => 'db.sample', dry_run => true);
```

Ограничить location:

```sql
call catalog_name.system.remove_orphan_files(table => 'db.sample', location => 'tablelocation/data');
```

Использовать view со списком файлов:

```java
Dataset<Row> compareToFileList =
    spark
        .createDataFrame(allFiles, FilePathLastModifiedRecord.class)
        .withColumnRenamed("filePath", "file_path")
        .withColumnRenamed("lastModified", "last_modified");
String fileListViewName = "files_view";
compareToFileList.createOrReplaceTempView(fileListViewName);
```

```sql
call catalog_name.system.remove_orphan_files(table => 'db.sample', file_list_view => 'files_view');
```

Prefix mismatch:

```sql
call catalog_name.system.remove_orphan_files(table => 'db.sample', prefix_mismatch_mode => 'IGNORE');
call catalog_name.system.remove_orphan_files(table => 'db.sample', prefix_mismatch_mode => 'DELETE');
call catalog_name.system.remove_orphan_files(table => 'db.sample', equal_schemes => map('file', 'file1'));
call catalog_name.system.remove_orphan_files(table => 'db.sample', equal_authorities => map('ns1', 'ns2'));
call catalog_name.system.remove_orphan_files(table => 'db.sample', prefix_listing => true);
```

> [!danger]
> Для production orphan cleanup используйте безопасный retention window и сначала `dry_run`. Несовпадающие схемы/authorities путей могут привести к неверной классификации файлов; см. также [[maintenance#Удаление orphan files]].

### `rewrite_data_files`

Параллельно compact data files. Маленькие files увеличивают manifests и file-open overhead; слишком большие можно split в target size.

| Argument | Required | Type | Описание |
| --- | --- | --- | --- |
| `table` | ✔ | string | Таблица |
| `strategy` | — | string | `binpack` (default) или `sort` |
| `sort_order` | — | string | `zorder(c1,c2)`, `hilbert(c1,c2)` или comma-separated `ColumnName ASC/DESC NULLS FIRST/LAST`; default table sort order |
| `options` | — | map<string,string> | Action options |
| `where` | — | string | Predicate; выбираются все files, которые **могут** содержать matching data |

#### General options

| Name | Default | Описание |
| --- | --- | --- |
| `max-concurrent-file-group-rewrites` | 5 | Одновременно переписываемые file groups |
| `partial-progress.enabled` | false | Commit groups до завершения всей rewrite |
| `partial-progress.max-commits` | 10 | Максимум commits при partial progress |
| `partial-progress.max-failed-commits` | `partial-progress.max-commits` | Допустимые failed commits |
| `use-starting-sequence-number` | true | Использовать sequence number snapshot на момент начала compaction, а не нового snapshot |
| `rewrite-job-order` | none | `bytes-asc`, `bytes-desc`, `files-asc`, `files-desc`, `none` |
| `target-file-size-bytes` | 512 MB | Target output file size |
| `min-file-size-bytes` | 75% target | Files меньше всегда candidates |
| `max-file-size-bytes` | 180% target | Files больше всегда candidates |
| `min-input-files` | 5 | Group с >= N files rewrite независимо от других criteria; минимум два files |
| `rewrite-all` | false | Rewrite всех supplied files |
| `max-file-group-size-bytes` | 100 GB | Максимальный объём одной file group |
| `max-file-group-input-files` | `Long.MAX_VALUE` | Максимум input files на group. Если ниже `min-input-files` при `rewrite-all=false`, file-count trigger недостижим; остаются size/delete triggers |
| `delete-file-threshold` | `Integer.MAX_VALUE` | Минимум deletes, связанных с data file, чтобы сделать его candidate |
| `delete-ratio-threshold` | 0.3 | Минимальная доля deletes для candidate |
| `output-spec-id` | current spec | Output partition spec; data реорганизуются под него |
| `remove-dangling-deletes` | false | После rewrite убрать dangling position/equality delete files отдельным commit |
| `max-files-to-rewrite` | null | Верхний лимит eligible files |
| `cache-delete-files` | false | Executor cache delete files; полезно, когда один delete file применяется к многим data files |

> [!info]
> Dangling delete files здесь определяются только по data sequence numbers. Это не проверка семантической неприменимости global equality delete или отдельных position deletes.

#### Sort strategy

| Name | Default | Описание |
| --- | --- | --- |
| `compression-factor` | 1.0 | Корректирует оценку output data относительно compressed on-disk input; >1 создаёт больше output files, <1 меньше |
| `shuffle-partitions-per-file` | 1 | Shuffle partitions на output file; Iceberg coalesce sorted partitions обратно в один sorted file |

ZOrder options:

| Name | Default | Описание |
| --- | --- | --- |
| `var-length-contribution` | 8 | Bytes variable-length String/Binary, участвующие в key |
| `max-output-size` | `Integer.MAX_VALUE` | Bytes, interleaved алгоритмом ZOrder |

Hilbert использует general + sort options, собственных нет. Каждая primitive column даёт полную ширину 8 bytes, поэтому `var-length-contribution`/`max-output-size` не применяются. `hilbert()`, `zorder()` и plain sort columns нельзя смешивать в одном `sort_order`.

Output:

- `rewritten_data_files_count`;
- `added_data_files_count`;
- `rewritten_bytes_count`;
- `failed_data_files_count` (при partial progress);
- `removed_delete_files_count`.

Examples:

```sql
call catalog_name.system.rewrite_data_files('db.sample');
```

```sql
call catalog_name.system.rewrite_data_files(
  table => 'db.sample', strategy => 'sort',
  sort_order => 'id DESC NULLS LAST,name ASC NULLS FIRST');
```

```sql
call catalog_name.system.rewrite_data_files(table => 'db.sample', strategy => 'sort', sort_order => 'zorder(c1,c2)');
call catalog_name.system.rewrite_data_files(table => 'db.sample', strategy => 'sort', sort_order => 'hilbert(c1,c2)');
```

```sql
call catalog_name.system.rewrite_data_files(
  table => 'db.sample',
  options => map('min-input-files', '2', 'remove-dangling-deletes', 'true'));
```

```sql
call catalog_name.system.rewrite_data_files(table => 'db.sample', where => 'id = 3 and name = "foo"');
```

### `rewrite_manifests`

Переписывает manifests для оптимизации scan planning. Data files внутри manifests сортируются по partition spec fields. Выполняется параллельным Spark job и инвалидирует cached plans.

| Argument | Required | Type | Default / описание |
| --- | --- | --- | --- |
| `table` | ✔ | string | Таблица |
| `use_caching` | — | boolean | false; Spark caching увеличивает executor memory footprint |
| `spec_id` | — | int | current spec ID |
| `sort_by` | — | array<string> | Partition transforms для clustering manifests; default все transforms в spec order |

Output: `rewritten_manifests_count`, `added_manifests_count`.

```sql
call catalog_name.system.rewrite_manifests('db.sample');
call catalog_name.system.rewrite_manifests(table => 'db.sample', spec_id => 1);
call catalog_name.system.rewrite_manifests(table => 'db.sample', sort_by => array('category'));
```

### `rewrite_position_delete_files`

Решает две задачи:

- minor compaction small position delete files;
- фильтрация dangling records, указывающих на уже non-live data files, в selected delete files.

| Argument | Required | Type |
| --- | --- | --- |
| `table` | ✔ | string |
| `options` | — | map<string,string> |
| `where` | — | string |

Options:

| Name | Default |
| --- | --- |
| `max-concurrent-file-group-rewrites` | 5 |
| `partial-progress.enabled` | false |
| `partial-progress.max-commits` | 10 |
| `rewrite-job-order` | none (`bytes-asc/desc`, `files-asc/desc`, `none`) |
| `target-file-size-bytes` | 64 MB (`write.delete.target-file-size-bytes`) |
| `min-file-size-bytes` | 75% target |
| `max-file-size-bytes` | 180% target |
| `min-input-files` | 5 |
| `rewrite-all` | false |
| `max-file-group-size-bytes` | 100 GB |
| `max-file-group-input-files` | `Long.MAX_VALUE` |
| `max-files-to-rewrite` | null |

Output: `rewritten_delete_files_count`, `added_delete_files_count`, `rewritten_bytes_count`, `added_bytes_count`.

```sql
call catalog_name.system.rewrite_position_delete_files('db.sample');
call catalog_name.system.rewrite_position_delete_files(table => 'db.sample', options => map('rewrite-all', 'true'));
call catalog_name.system.rewrite_position_delete_files(table => 'db.sample', options => map('min-input-files','2'));
```

## Миграция таблиц

### `snapshot`

Создаёт lightweight временную Iceberg-копию source table без изменения source. Новая таблица разделяет исходные data files, но новые writes идут в собственный location.

> [!warning]
> Snapshot table не является единственным owner исходных data files, поэтому operations, способные физически удалить shared files (`expire_snapshots`), запрещены. Metadata-only deletes разрешены. Если original Hive table физически удалит shared file, snapshot table будет повреждена.

| Argument | Required | Type | Default |
| --- | --- | --- | --- |
| `source_table` | ✔ | string | Source table |
| `table` | ✔ | string | Новая Iceberg table |
| `location` | — | string | Catalog default |
| `properties` | — | map<string,string> | New table properties |
| `parallelism` | — | int | 1 |
| `ignore_missing_files` | — | boolean | false |

Output: `imported_files_count`.

```sql
call catalog_name.system.snapshot('db.sample', 'db.snap');
call catalog_name.system.snapshot('db.sample', 'db.snap', '/tmp/temptable/');
```

### `migrate`

Заменяет existing table Iceberg-таблицей, используя существующие source data files. Schema, partitioning, properties и location копируются. Поддерживаются Avro, Parquet, ORC; bucketed source не поддерживается, потому что bucketing невозможно сохранить. Files добавляются в Iceberg metadata через name-to-id mapping исходной schema.

Original table по умолчанию сохраняется как `table_BACKUP_`.

| Argument | Required | Type | Default |
| --- | --- | --- | --- |
| `table` | ✔ | string | Таблица |
| `properties` | — | map<string,string> | Properties Iceberg |
| `drop_backup` | — | boolean | false |
| `backup_table_name` | — | string | `table_BACKUP_` |
| `parallelism` | — | int | 1 |
| `ignore_missing_files` | — | boolean | false |

Output: `migrated_files_count`.

```sql
call catalog_name.system.migrate('spark_catalog.db.sample', map('foo', 'bar'));
call catalog_name.system.migrate('db.sample');
```

### `add_files`

Добавляет existing files из Hive/file-based table в существующую Iceberg table, включая выбор partitions. Files не перемещаются; создаются только metadata entries. Schema contents файлов **не валидируются**. После операции Iceberg считает files своими, поэтому последующий `expire_snapshots` может физически их удалить.

> [!warning]
> `add_files` читает Parquet metadata каждого добавляемого file один раз. С tiered storage вроде S3 Intelligent-Tiering это может извлечь archived object и удерживать его на более дорогом tier установленный storage period.

| Argument | Required | Type | Default |
| --- | --- | --- | --- |
| `table` | ✔ | string | Target |
| `source_table` | ✔ | string | Source или `` `file_format`.`path` `` |
| `partition_filter` | — | map<string,string> | Source partitions |
| `check_duplicate_files` | — | boolean | true |
| `parallelism` | — | int | 1 |

Output: `added_files_count`, `changed_partition_count`. Последний может быть `null`, если `compatibility.snapshot-id-inheritance.enabled=true` или format version > 1.

```sql
call spark_catalog.system.add_files(
  table => 'db.tbl',
  source_table => 'db.src_tbl',
  partition_filter => map('part_col_1', 'A')
);
```

```sql
call spark_catalog.system.add_files(
  table => 'db.tbl',
  source_table => '`parquet`.`path/to/table`'
);
```

### `register_table`

Создаёт catalog entry для уже существующего `metadata.json`.

| Argument | Required | Type |
| --- | --- | --- |
| `table` | ✔ | string |
| `metadata_file` | ✔ | string |

> [!danger]
> Регистрация одного и того же `metadata.json` одновременно в нескольких catalogs может привести к потерянным updates, потере данных и corruption. Используйте procedure только когда таблица больше не зарегистрирована в старом catalog либо переносится между catalogs.

Output: `current_snapshot_id`, `total_records_count`, `total_data_files_count`.

```sql
call spark_catalog.system.register_table(
  table => 'db.tbl',
  metadata_file => 'path/to/metadata/file.json'
);
```

## Информация о metadata

### `ancestors_of`

Возвращает live snapshot IDs ancestor chain заданного snapshot или current snapshot.

| Argument | Required | Type |
| --- | --- | --- |
| `table` | ✔ | string |
| `snapshot_id` | — | long |

Если история выглядит так:

```text
A -> B -> C -> D
      \ -> C' -> D'
```

без `snapshot_id` current chain будет `A -> B -> C' -> D'`; при snapshot ID `D` — историческая `A -> B -> C -> D`.

Output: `snapshot_id`, `timestamp`.

```sql
call spark_catalog.system.ancestors_of('db.tbl');
call spark_catalog.system.ancestors_of('db.tbl', 1);
call spark_catalog.system.ancestors_of(snapshot_id => 1, table => 'db.tbl');
```

## Change Data Capture

### `create_changelog_view`

Создаёт view изменений таблицы.

| Argument | Required | Type | Описание |
| --- | --- | --- | --- |
| `table` | ✔ | string | Source |
| `changelog_view` | — | string | Имя view |
| `options` | — | map<string,string> | Spark read options |
| `net_changes` | — | boolean | false; только итоговые изменения; должен быть false при `compute_updates=true` |
| `compute_updates` | — | boolean | default true, если переданы identifier columns, иначе false |
| `identifier_columns` | — | array<string> | Identity columns; если compute true и не переданы, используются current table identifier fields |

Типовые read options:

- `start-snapshot-id` — exclusive;
- `end-snapshot-id` — inclusive, default current;
- `start-timestamp` — exclusive;
- `end-timestamp` — inclusive, default current.

Output: `changelog_view`.

```sql
call spark_catalog.system.create_changelog_view(
  table => 'db.tbl',
  options => map('start-snapshot-id','1','end-snapshot-id', '2')
);
```

```sql
call spark_catalog.system.create_changelog_view(
  table => 'db.tbl',
  options => map('start-timestamp','1678335750489','end-timestamp', '1678992105265'),
  changelog_view => 'my_changelog_view'
);
```

```sql
call spark_catalog.system.create_changelog_view(
  table => 'db.tbl',
  options => map('start-snapshot-id','1','end-snapshot-id', '2'),
  identifier_columns => array('id', 'name')
);
```

```sql
select * from tbl_changes;
select * from tbl_changes where _change_type = 'INSERT' and id = 3 order by _change_ordinal;
```

CDC metadata columns:

- `_change_type`: `INSERT`, `DELETE`, `UPDATE_BEFORE`, `UPDATE_AFTER`;
- `_change_ordinal`: order изменений;
- `_commit_snapshot_id`: snapshot, где произошло изменение.

Пример:

| id | name | _change_type | _change_ordinal | _commit_snapshot_id |
| --- | --- | --- | --- | --- |
| 1 | Alice | INSERT | 0 | 5390529835796506035 |
| 2 | Bob | INSERT | 0 | 5390529835796506035 |
| 1 | Alice | DELETE | 1 | 8764748981452218370 |

#### Net changes

Intermediate changes можно убрать, оставив только net effect:

```sql
call spark_catalog.system.create_changelog_view(
  table => 'db.tbl',
  options => map('end-snapshot-id', '87647489814522183702'),
  net_changes => true
);
```

В примере Alice была inserted и затем deleted, поэтому в net result останется только Bob.

#### Carry-over rows

По умолчанию procedure убирает carry-over rows, которые возникают при copy-on-write row-level operations. Например, file содержит Alice и Bob; удаление Bob требует rewrite file и переноса Alice в новый file. Raw changelog может показать Alice как `DELETE` + `INSERT`, хотя её логическое значение не менялось. Чтобы увидеть такие rows напрямую:

```sql
select * from spark_catalog.db.tbl.changes;
```

#### Pre/post update images

Если включено, пара `DELETE` + `INSERT` с одинаковыми identifier columns преобразуется в `UPDATE_BEFORE` + `UPDATE_AFTER`. Например:

| id | name | _change_type |
| --- | --- | --- |
| 3 | Robert | UPDATE_BEFORE |
| 3 | Dan | UPDATE_AFTER |

## Table Statistics

### `compute_table_stats`

Вычисляет Number of Distinct Values (NDV) в Puffin statistics. Default — все top-level primitive columns current snapshot; можно указать snapshot/columns.

| Argument | Required | Type |
| --- | --- | --- |
| `table` | ✔ | string |
| `snapshot_id` | — | string |
| `columns` | — | array<string> |

Output: `statistics_file`.

```sql
call catalog_name.system.compute_table_stats('my_table');
call catalog_name.system.compute_table_stats(table => 'my_table', snapshot_id => 'snap1');
call catalog_name.system.compute_table_stats(table => 'my_table', snapshot_id => 'snap1', columns => array('col1', 'col2'));
```

## Partition Statistics

### `compute_partition_stats`

Incrementally вычисляет partition stats от последнего snapshot с `PartitionStatisticsFile` до выбранного snapshot (default current), объединяет и регистрирует новый statistics file. Если предыдущего файла нет, выполняется full compute.

| Argument | Required | Type |
| --- | --- | --- |
| `table` | ✔ | string |
| `snapshot_id` | — | string |

Output: `partition_statistics_file`.

```sql
call catalog_name.system.compute_partition_stats('my_table');
call catalog_name.system.compute_partition_stats(table => 'my_table', snapshot_id => 'snap1');
```

## Репликация таблицы

### `rewrite_table_path`

Подготавливает Iceberg table к копированию в новый location: stage копию metadata files, заменяя source prefix на target prefix во всех absolute paths.

> [!info]
> Procedure переписывает metadata и position delete files во staging и создаёт copy plan. Сами files в target location она **не копирует**.

| Argument | Required | Default | Type | Описание |
| --- | --- | --- | --- | --- |
| `table` | ✔ | — | string | Таблица |
| `source_prefix` | ✔ | — | string | Existing prefix |
| `target_prefix` | ✔ | — | string | Replacement |
| `start_version` | — | first metadata.json | string | Первый metadata version |
| `end_version` | — | latest metadata.json | string | Последний metadata version |
| `staging_location` | — | новый каталог под metadata | string | Output staging |
| `create_file_list` | — | true | boolean | Создавать copy-plan file |

#### Modes

- **Full Rewrite** — переписывает все reachable metadata files (`metadata.json`, manifest lists, manifests, position delete files) и возвращает все reachable files.
- **Incremental Rewrite** — при `start_version`/`end_version` обрабатывает только metadata/files, добавленные в этом диапазоне.

Output:

| Field | Type | Описание |
| --- | --- | --- |
| `latest_version` | string | Последний переписанный metadata file |
| `file_list_location` | string | CSV mapping source → target |
| `rewritten_manifest_file_paths_count` | int | Manifests с rewritten paths |
| `rewritten_delete_file_paths_count` | int | Delete files с rewritten paths |

Copy-plan CSV:

```csv
sourcepath/datafile1.parquet,targetpath/datafile1.parquet
sourcepath/datafile2.parquet,targetpath/datafile2.parquet
stagingpath/manifest.avro,targetpath/manifest.avro
```

Full rewrite HDFS → S3:

```sql
call catalog_name.system.rewrite_table_path(
    table => 'db.my_table',
    source_prefix => 'hdfs://nn:8020/path/to/source_table',
    target_prefix => 's3a://bucket/prefix/db.db/my_table'
);
```

Incremental:

```sql
call catalog_name.system.rewrite_table_path(
    table => 'db.my_table',
    source_prefix => 's3a://bucketOne/prefix/db.db/my_table',
    target_prefix => 's3a://bucketTwo/prefix/db.db/my_table',
    start_version => 'v2.metadata.json',
    end_version => 'v20.metadata.json',
    staging_location => 's3a://bucketStaging/my_table'
);
```

После rewrite files можно физически скопировать, например Hadoop DistCp, затем зарегистрировать target через `register_table`.

> [!warning]
> `rewrite_table_path` в этой версии не поддерживает tables с partition statistics files.
