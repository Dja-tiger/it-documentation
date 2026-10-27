---
title: Apache Iceberg — справочник по задачам
tags: [apache-iceberg, reference, moc]
material_type: reference
source_ref: apache-iceberg-1.12.0
---

# Найти инструкцию по задаче

Используйте эту страницу во время работы. Для последовательного изучения есть [учебный маршрут](../learn/README.md), для полного оглавления — [MOC](../MOC.md). Примеры SQL ниже относятся к Spark; для другого движка проверяйте его поддержку и синтаксис.

| Задача | Основная страница | Что уточнить перед выполнением |
| --- | --- | --- |
| Запустить первую таблицу | [Лабораторная](../labs/README.md), [Spark getting started](../docs/spark-getting-started.md) | Версии Spark/Scala/runtime, настройка каталога |
| Создать, переименовать или удалить таблицу | [Spark DDL](../docs/spark-ddl.md) | Разница DROP и PURGE, поддержка операции каталогом |
| Добавить колонку, переименовать поле, расширить тип | [Эволюция](../docs/evolution.md), [DDL](../docs/spark-ddl.md) | Допустимые изменения типов; metadata change не равно преобразованию всех данных |
| Выбрать тип колонки | [Схемы](../docs/schemas.md), [mapping Spark](../docs/spark-getting-started.md) | Поддержка типа движком и format version |
| Выбрать или изменить партиционирование | [Партиционирование](../docs/partitioning.md), [эволюция](../docs/evolution.md), [DDL](../docs/spark-ddl.md) | Типичные фильтры; старые файлы не переразбиваются автоматически |
| Записать данные, выполнить MERGE/UPDATE/DELETE | [Spark writes](../docs/spark-writes.md), [конфигурация](../docs/configuration.md) | Ключ сопоставления, повторы источника, COW/MOR, format version |
| Прочитать прошлую версию | [Spark queries](../docs/spark-queries.md) | Наличие snapshot и его файлов; не путать ID с номером версии |
| Найти файлы, snapshots, manifests и историю | [Metadata tables](../docs/spark-queries.md) | Семантика current/all tables и учёт delete files |
| Откатить ошибочную запись | [Spark procedures](../docs/spark-procedures.md), [snapshots](../learn/02-snapshots.md) | Выбранный предок, влияние на последующие загрузки; DDL отдельно |
| Сохранить контрольную версию или вести audit branch | [Branches и tags](../docs/branching.md) | Retention ссылок, общая схема таблицы |
| Объединить мелкие файлы | [Обслуживание](../docs/maintenance.md), [rewrite_data_files](../docs/spark-procedures.md) | Число и размеры файлов, стратегия, стоимость rewrite |
| Перегруппировать manifests | [Обслуживание](../docs/maintenance.md), [процедуры](../docs/spark-procedures.md) | Не путать metadata rewrite с data compaction |
| Удалить старую историю | [expire_snapshots](../docs/spark-procedures.md), [обслуживание](../docs/maintenance.md) | Retention, branches/tags, нужные downstream snapshots |
| Найти и удалить orphan files | [remove_orphan_files](../docs/spark-procedures.md), [обслуживание](../docs/maintenance.md) | Сначала dry run; длительность writes; соответствие URI |
| Разобрать конфликт writers | [Надёжность](../docs/reliability.md), [конфигурация](../docs/configuration.md), [каталоги](../docs/catalog-properties.md) | Ошибка commit или validation, механизм атомарности каталога |
| Настроить размер файлов и параметры чтения/записи | [Table configuration](../docs/configuration.md), [Spark configuration](../docs/spark-configuration.md) | Table property и session/read/write option могут иметь разный приоритет |
| Подключить REST catalog | [REST catalog](../docs/rest-catalog.md), [протокол](../docs/rest-protocol.md) | URI, authentication, доступ к storage и совместимость клиента |
| Подключить Hive/JDBC/Nessie catalog | [Hive](../docs/hive.md), [JDBC](../docs/jdbc.md), [Nessie](../docs/nessie.md) | Зависимости, backend каталога, механизм commit |
| Подключить S3, Glue или DynamoDB | [AWS](../docs/aws.md), [File I/O](../docs/fileio.md) | Credentials, endpoints, permissions, выбранный catalog/FileIO |
| Настроить Flink | [Flink](../docs/flink.md), [конфигурация](../docs/flink-configuration.md), [writes](../docs/flink-writes.md) | Версия connector, checkpoints, streaming/incremental ограничения |
| Подключить Kafka Connect | [Kafka Connect](../docs/kafka-connect.md) | Delivery guarantees, маршрутизация, schema evolution |
| Перенести Hive/Delta Lake таблицу | [Обзор миграции](../docs/table-migration.md), [Hive](../docs/hive-migration.md), [Delta Lake](../docs/delta-lake-migration.md) | Владение общими файлами, ограничения, проверка данных и план возврата |
| Встроить Iceberg в Java-приложение | [Java quickstart](../docs/java-api-quickstart.md), [API](../docs/api.md), [File I/O](../docs/fileio.md) | Совместимые библиотеки, загрузка таблицы, commit и retries |
| Настроить шифрование или метрики | [Шифрование](../docs/encryption.md), [metrics reporting](../docs/metrics-reporting.md) | Поддержка конкретным FileIO/движком, ключи и получатель метрик |

## Как оценивать ответ справочника

База перевода зафиксирована на **1.12.0**, а не на плавающем `latest`. Проверяйте ограничения версии и движка. Статус `translated` в существующих страницах не является подтверждением построчной сверки; известные расхождения и метод проверки перечислены в [отчёте о полноте](../_meta/review-2026-10-26.md).

Для поиска по содержимому в редакторе используйте имя процедуры или property key: `rewrite_data_files`, `write.target-file-size-bytes`, `commit.retry.num-retries`. Идентификаторы в переводе сохраняются на английском.
