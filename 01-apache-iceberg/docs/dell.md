---
title: "Dell ECS"
tags: [apache-iceberg, storage, dell, ecs, s3]
source_project: apache/iceberg
source_file: docs/docs/dell.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/dell.md
translation_status: reviewed
translated_at: 2026-10-12
reviewed_at: 2026-10-26
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Интеграция Iceberg с Dell

## Интеграция Dell ECS

Iceberg можно использовать с Dell Enterprise Object Storage (ECS) через ECS catalog начиная с версии 0.15.0.

Подробнее о продукте: [Dell ECS](https://www.dell.com/en-us/dt/storage/ecs/index.htm).

### Параметры

Для использования Dell ECS с Iceberg требуются следующие параметры:

| Имя | Описание |
| --- | --- |
| `ecs.s3.endpoint` | Endpoint сервиса ECS S3 |
| `ecs.s3.access-key-id` | Имя пользователя ECS |
| `ecs.s3.secret-access-key` | Секретный ключ S3 |
| `warehouse` | Расположение данных и метаданных |

Warehouse должен использовать следующие форматы:

| Пример | Описание |
| --- | --- |
| `ecs://bucket-a` | Использовать весь bucket для данных |
| `ecs://bucket-a/` | Использовать весь bucket; завершающий `/` игнорируется |
| `ecs://bucket-a/namespace-a` | Использовать prefix для доступа только к данным указанного namespace |

Iceberg runtime JAR выпускается для разных версий Spark и Flink. Выбирайте соответствующую версию.

Хотя JAR [клиента Dell ECS](https://github.com/EMCECS/ecs-object-client-java) обратно совместим, Dell EMC рекомендует использовать последнюю версию клиента.

> [!note]
> Примечание к переводу: ниже сохранены исторические версии из исходной страницы Iceberg 1.12.0. Это примеры upstream, а не проверенная комбинация для текущей установки. Воспроизводимая учебная среда с Iceberg 1.12.0 описана в [[../labs/README|лабораторной]]; интеграция Dell ECS там не проверяется.

### Spark

Чтобы использовать Dell ECS catalog со Spark 3.5.0, создайте Spark session следующим образом:

```bash
ICEBERG_VERSION=1.4.2
SPARK_VERSION=3.5_2.12
ECS_CLIENT_VERSION=3.3.2

DEPENDENCIES="org.apache.iceberg:iceberg-spark-runtime-${SPARK_VERSION}:${ICEBERG_VERSION},\
org.apache.iceberg:iceberg-dell:${ICEBERG_VERSION},\
com.emc.ecs:object-client-bundle:${ECS_CLIENT_VERSION}"

spark-sql --packages ${DEPENDENCIES} \
    --conf spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions \
    --conf spark.sql.catalog.my_catalog=org.apache.iceberg.spark.SparkCatalog \
    --conf spark.sql.catalog.my_catalog.warehouse=ecs://bucket-a/namespace-a \
    --conf spark.sql.catalog.my_catalog.catalog-impl=org.apache.iceberg.dell.ecs.EcsCatalog \
    --conf spark.sql.catalog.my_catalog.ecs.s3.endpoint=http://10.x.x.x:9020 \
    --conf spark.sql.catalog.my_catalog.ecs.s3.access-key-id=<Your-ecs-s3-access-key> \
    --conf spark.sql.catalog.my_catalog.ecs.s3.secret-access-key=<Your-ecs-s3-secret-access-key>
```

После этого обращайтесь к данным ECS через `my_catalog`. Команды `SHOW NAMESPACES IN my_catalog` и `SHOW TABLES IN my_catalog` возвращают namespaces и таблицы каталога.

Особенность работы с каталогом:

1. `SparkSession.catalog` не обращается к стороннему каталогу Spark ни в Python, ни в Scala. Поэтому для перечисления таблиц и namespaces используйте SQL DDL.

### Flink

Для использования Dell ECS catalog во Flink сначала создайте окружение Flink:

```bash
# HADOOP_HOME is your hadoop root directory after unpack the binary package.
export HADOOP_CLASSPATH=`$HADOOP_HOME/bin/hadoop classpath`

# download Iceberg dependency
MAVEN_URL=https://repo1.maven.org/maven2
ICEBERG_VERSION=0.15.0
FLINK_VERSION=1.14
wget ${MAVEN_URL}/org/apache/iceberg/iceberg-flink-runtime-${FLINK_VERSION}/${ICEBERG_VERSION}/iceberg-flink-runtime-${FLINK_VERSION}-${ICEBERG_VERSION}.jar
wget ${MAVEN_URL}/org/apache/iceberg/iceberg-dell/${ICEBERG_VERSION}/iceberg-dell-${ICEBERG_VERSION}.jar

# download ECS object client
ECS_CLIENT_VERSION=3.3.2
wget ${MAVEN_URL}/com/emc/ecs/object-client-bundle/${ECS_CLIENT_VERSION}/object-client-bundle-${ECS_CLIENT_VERSION}.jar

# open the SQL client.
/path/to/bin/sql-client.sh embedded \
    -j iceberg-flink-runtime-${FLINK_VERSION}-${ICEBERG_VERSION}.jar \
    -j iceberg-dell-${ICEBERG_VERSION}.jar \
    -j object-client-bundle-${ECS_CLIENT_VERSION}.jar \
    shell
```

Затем создайте каталог `my_catalog` через Flink SQL:

```SQL
CREATE CATALOG my_catalog WITH (
    'type'='iceberg',
    'warehouse' = 'ecs://bucket-a/namespace-a',
    'catalog-impl'='org.apache.iceberg.dell.ecs.EcsCatalog',
    'ecs.s3.endpoint' = 'http://10.x.x.x:9020',
    'ecs.s3.access-key-id' = '<Your-ecs-s3-access-key>',
    'ecs.s3.secret-access-key' = '<Your-ecs-s3-secret-access-key>');
```

После этого команды `USE CATALOG my_catalog`, `SHOW DATABASES` и `SHOW TABLES` позволяют переключиться на каталог и получить список namespaces и таблиц.

### Ограничения

При работе с каталогом Dell ECS учитывайте следующие ограничения:

1. Команды `RENAME` поддерживаются без дополнительных защитных механизмов. Перед переименованием таблицы необходимо убедиться, что все commits в исходную таблицу завершены.
2. `RENAME` переименовывает только таблицу и не перемещает data files. В результате данные таблицы могут находиться за пределами настроенного warehouse.
3. Операции compare-and-swap (CAS), используемые при commit таблицы, основаны на checksum объекта. Существует очень малая вероятность конфликта контрольных сумм.
