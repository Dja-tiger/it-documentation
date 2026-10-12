---
title: "JDBC Catalog"
tags: [apache-iceberg, catalogs, jdbc]
source_project: apache/iceberg
source_file: docs/docs/jdbc.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/jdbc.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Iceberg JDBC Integration

## JDBC Catalog

Iceberg может использовать таблицу в relational database для управления Iceberg tables через JDBC.

Database должна поддерживать **atomic transactions**, чтобы JDBC catalog мог гарантировать atomic Iceberg commits и serializable isolation чтения.

### Конфигурация

Поскольку разные databases/providers используют разные connection settings, JDBC catalog разрешает произвольные `jdbc.*` properties:

| Property | Default | Описание |
| --- | --- | --- |
| `uri` | — | JDBC connection string |
| `jdbc.<property_key>` | — | Любые key/value JDBC connection properties |

### Spark example

MySQL:

```shell
spark-sql --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:{{ icebergVersion }} \
    --conf spark.sql.catalog.my_catalog=org.apache.iceberg.spark.SparkCatalog \
    --conf spark.sql.catalog.my_catalog.warehouse=s3://my-bucket/my/key/prefix \
    --conf spark.sql.catalog.my_catalog.type=jdbc \
    --conf spark.sql.catalog.my_catalog.uri=jdbc:mysql://test.1234567890.us-west-2.rds.amazonaws.com:3306/default \
    --conf spark.sql.catalog.my_catalog.jdbc.verifyServerCertificate=true \
    --conf spark.sql.catalog.my_catalog.jdbc.useSSL=true \
    --conf spark.sql.catalog.my_catalog.jdbc.user=admin \
    --conf spark.sql.catalog.my_catalog.jdbc.password=pass
```

### Java API

```java
Class.forName("com.mysql.cj.jdbc.Driver"); // ensure JDBC driver is at runtime classpath
Map<String, String> properties = new HashMap<>();
properties.put(CatalogProperties.CATALOG_IMPL, JdbcCatalog.class.getName());
properties.put(CatalogProperties.URI, "jdbc:mysql://localhost:3306/test");
properties.put(JdbcCatalog.PROPERTY_PREFIX + "user", "admin");
properties.put(JdbcCatalog.PROPERTY_PREFIX + "password", "pass");
properties.put(CatalogProperties.WAREHOUSE_LOCATION, "s3://warehouse/path");
Configuration hadoopConf = new Configuration(); // configs if you use HadoopFileIO
JdbcCatalog catalog = CatalogUtil.buildIcebergCatalog("test_jdbc_catalog", properties, hadoopConf);
```
