---
title: Iceberg — лабораторная на Spark
tags: [apache-iceberg, learning, lab, spark]
material_type: lab
source_ref: apache-iceberg-1.12.0
---

# Одна таблица от создания до обслуживания

Окружение: **Spark 3.5.5 / Scala 2.12 / Java 17 / Iceberg 1.12.0**, format v2, HadoopCatalog, локальные файлы. Нужны работающий Docker, `curl`, Bash и несколько гигабайт свободного места под образ. Первая загрузка образа и JAR требует интернета; Spark работает без сети. Временный warehouse создаётся внутри контейнера и удаляется после завершения.

Используется [официальный образ Spark с Java 17 и Python](https://github.com/apache/spark-docker/blob/master/3.5.5/scala2.12-java17-python3-ubuntu/Dockerfile). В `run.sh` образ закреплён digest, runtime JAR проверяется по SHA-256. Обычный тег `apache/spark:3.5.5` содержит Java 11 и для этой лабораторной не подходит.

## Запуск с автоматическими проверками

Из корня репозитория:

```sh
bash 01-apache-iceberg/labs/run.sh
```

Сценарий [check.py](check.py) печатает SQL, выполняет его и проверяет содержимое таблиц, time travel, изменения схемы и результаты compaction. Успешное завершение: **`ALL ICEBERG LAB CHECKS PASSED`** и код выхода `0`. Ошибка SQL или проверки даёт ненулевой код. Сведения о фактически выполненном запуске находятся в [отчёте](../_meta/review-2026-10-26.md).

Чтобы повторно использовать заранее скачанный JAR, задайте `ICEBERG_LAB_CACHE` — каталог с файлом `iceberg-spark-runtime-3.5_2.12-1.12.0.jar`. Образ остаётся в кэше Docker, временный warehouse — нет.

## Интерактивное повторение

После первого запуска выполните из корня репозитория:

```sh
ICEBERG_CACHE="${ICEBERG_LAB_CACHE:-${TMPDIR:-/tmp}/iceberg-learning-1.12.0}"
docker run --rm -it --hostname localhost --network none \
  --env SPARK_LOCAL_IP=127.0.0.1 \
  --mount "type=bind,src=$ICEBERG_CACHE/iceberg-spark-runtime-3.5_2.12-1.12.0.jar,dst=/opt/iceberg/runtime.jar,readonly" \
  --entrypoint /opt/spark/bin/spark-sql apache/spark:3.5.5-java17-python3 \
  --master 'local[2]' --jars /opt/iceberg/runtime.jar \
  --conf spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions \
  --conf spark.sql.catalog.lab=org.apache.iceberg.spark.SparkCatalog \
  --conf spark.sql.catalog.lab.type=hadoop \
  --conf spark.sql.catalog.lab.warehouse=file:///tmp/iceberg-warehouse \
  --conf spark.sql.session.timeZone=UTC \
  --conf spark.sql.shuffle.partitions=2 \
  --conf spark.ui.enabled=false
```

Каждый новый контейнер начинается с пустого warehouse. Выполняйте SQL из `check.py` по порядку: Python-обёртка `sql("...")` только передаёт строку в Spark. В командах time travel и rollback подставьте snapshot ID **своего** первого INSERT.

## Шаги и ожидаемые результаты

| Шаг | Действия в `check.py` | Проверяемый результат |
| --- | --- | --- |
| 1 | CREATE NAMESPACE, CREATE TABLE, INSERT | Строки `(1, a)`, `(2, b)`; сохранить первый snapshot ID |
| 2 | ADD COLUMN, RENAME COLUMN | Поле `origin` есть; у двух старых строк значение `NULL` |
| 3 | REPLACE PARTITION FIELD, INSERT | Строка 3 записана; в `files` два разных `spec_id` |
| 4 | MERGE с обновлением 2 и вставкой 4 | `(1, a)`, `(2, updated)`, `(3, c)`, `(4, d)` |
| 5 | DELETE строки 1 | Остались 2, 3, 4 |
| 6 | VERSION AS OF первого snapshot | Исторический SELECT возвращает 1 и 2 с исходными значениями |
| 7 | rollback_to_snapshot | Текущие данные снова 1 и 2; поле `origin` осталось в схеме |
| 8 | Просмотр snapshots, history, manifests | Видна сохранённая история и назначение текущего snapshot |
| 9 | Два INSERT в compaction_demo, rewrite_data_files | Число файлов снизилось, четыре строки сохранились |
| 10 | remove_orphan_files с dry_run | Таблица сохранила строки; файлы не удаляются этой процедурой |

Число snapshot ID, имена файлов и время commit различаются между запусками. Проверки используют отношения между состояниями, а не фиксированные случайные значения. Пустой результат orphan dry run допустим.

## Задания для самостоятельного повторения

1. Добавьте третью запись до сохранения первого snapshot. Исправьте ожидаемый исторический результат и объясните, почему он изменился.
2. Добавьте колонку `amount DECIMAL(10,2)` и запишите данные. Переименуйте колонку; проверьте чтение старых строк.
3. Смените партиционирование на часы, сделайте новый INSERT и посмотрите `spec_id`. Объясните, почему старые файлы не стали почасовыми.
4. Выполните rollback, затем новый INSERT. Сравните `snapshots` и `history`: какие сохранённые версии не являются предками текущей?
5. Измените число INSERT в `compaction_demo`. Сравните число файлов до и после, сохранив проверку строк.

## Если запуск не удался

- `Cannot connect to the Docker daemon`: запустите Docker и проверьте `docker info`.
- Таймаут Docker Hub или Maven: повторите загрузку, проверьте сетевой доступ; вычисления ещё не начались.
- `ClassNotFoundException` для Iceberg: проверьте имя runtime и передачу `--jars`; runtime должен соответствовать Spark **3.5** и Scala **2.12**.
- Не хватает памяти: выделите Docker больше памяти и закройте ненужные контейнеры; `local[2]` ограничивает потоки Spark, а не память всей виртуальной машины.

Эта лабораторная проверяет локальный Spark. Она не подтверждает работу S3/MinIO, REST/Hive catalog, Trino, Flink, распределённой отказоустойчивости или производительность под нагрузкой.

Назад: [учебный маршрут](../learn/README.md). Подробности: [Spark DDL](../docs/spark-ddl.md), [запросы](../docs/spark-queries.md), [запись](../docs/spark-writes.md), [процедуры](../docs/spark-procedures.md).
