---
title: Шифрование
tags: [apache-iceberg, concepts, encryption, kms]
source_project: apache/iceberg
source_file: docs/docs/encryption.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/encryption.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Шифрование

Шифрование Iceberg-таблиц защищает конфиденциальность и целостность данных в недоверенном storage. Файлы `data`, `delete`, `manifest` и `manifest list` шифруются и защищаются от модификации перед отправкой в storage backend.

`metadata.json` не содержит пользовательских данных или статистики, поэтому не шифруется.

В Iceberg 1.12.0 шифрование поддерживается в Hive и REST catalogs для таблиц с Parquet и Avro.

Для включения шифрования нужны два параметра:

1. Catalog property, задающий KMS (Key Management Service): либо `encryption.kms-type` для встроенных KMS clients (`aws`, `azure`, `gcp`), либо `encryption.kms-impl` с class path собственного KMS client.
2. Table property `encryption.key-id`, задающий ID master key, используемого для шифрования и расшифрования таблицы. Master keys хранятся и управляются KMS.

Подробности внутреннего устройства см. в [[#Приложение: внутреннее устройство]].

## Пример

```sh
spark-sql --packages org.apache.iceberg:iceberg-spark-runtime-{{ sparkVersionMajor }}:{{ icebergVersion }}\
    --conf spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions \
    --conf spark.sql.catalog.spark_catalog=org.apache.iceberg.spark.SparkSessionCatalog \
    --conf spark.sql.catalog.spark_catalog.type=hive \
    --conf spark.sql.catalog.local=org.apache.iceberg.spark.SparkCatalog \
    --conf spark.sql.catalog.local.type=hive \
    --conf spark.sql.catalog.local.encryption.kms-type=aws
```

```sql
CREATE TABLE local.db.table (id bigint, data string) USING iceberg
TBLPROPERTIES ('encryption.key-id'='<master-key-id>');
```

Вставленные данные будут шифроваться автоматически:

```sql
INSERT INTO local.db.table VALUES (1, 'a'), (2, 'b'), (3, 'c');
```

Проверить шифрование data, manifest и manifest-list files можно через:

```sh
hexdump -C <path/to/file> | more
```

Parquet files должны начинаться с magic string `PARE` (режим PARquet Encrypted footer), а manifest/list files — с `AGS1` (AES GCM Stream v1).

При чтении данные расшифровываются автоматически:

```sql
SELECT * FROM local.db.table;
```

## Требования безопасности к catalog

1. Catalog обязан гарантировать, что property `encryption.key-id` не изменяется и не удаляется на протяжении жизни таблицы.
2. Если `metadata.json` хранится без защиты в storage, подверженном tampering, реализация catalog не должна слепо доверять прочитанным metadata:
   - metadata можно хранить в отдельном доверенном object store;
   - `metadata.json` можно размещать в tamper-proof storage;
   - можно использовать checksums для проверки целостности, при этом сами checksums должны находиться в отдельном доверенном storage.

## Клиенты управления ключами

Iceberg включает clients для AWS, GCP и Azure KMS. Для другой системы можно реализовать интерфейс `org.apache.iceberg.encryption.KeyManagementClient`.

Основные методы интерфейса:

```java
  /**
   * Initialize the KMS client with given properties.
   *
   * @param properties kms client properties (taken from catalog properties)
   */
  void initialize(Map<String, String> properties);

  /**
   * Wrap a secret key, using a wrapping/master key which is stored in KMS and referenced by an ID.
   * Wrapping means encryption of the secret key with the master key, and adding optional
   * KMS-specific metadata that allows the KMS to decrypt the secret key in an unwrapping call.
   *
   * @param key a secret key being wrapped
   * @param wrappingKeyId a key ID that represents a wrapping key stored in KMS
   * @return wrapped key material
   */
  ByteBuffer wrapKey(ByteBuffer key, String wrappingKeyId);

  /**
   * Unwrap a secret key, using a wrapping/master key which is stored in KMS and referenced by an ID.
   *
   * @param wrappedKey wrapped key material (encrypted key and optional KMS metadata, returned by
   *     the wrapKey method)
   * @param wrappingKeyId a key ID that represents a wrapping key stored in KMS
   * @return raw key bytes
   */
  ByteBuffer unwrapKey(ByteBuffer wrappedKey, String wrappingKeyId);
```

## Приложение: внутреннее устройство

Стандартный encryption manager Iceberg генерирует для каждого data/delete file отдельный encryption key и уникальный file ID (`AAD prefix`). Генерация выполняется на worker nodes с использованием cryptographically secure random generator. Для Parquet параметры передаются в механизм Parquet Modular Encryption; для Avro — в AES GCM Stream.

Родительский manifest file хранит encryption key и AAD prefix каждого data/delete file в поле `key_metadata`. Для Avro data tables туда также добавляется длина data file. Сам manifest file шифруется AES GCM Stream с собственными encryption key и AAD prefix, генерируемыми на driver nodes.

Родительский manifest list file хранит encryption key, AAD prefix и длину каждого manifest file в поле `key_metadata`. Manifest list также шифруется AES GCM Stream с ключом и AAD prefix, сгенерированными стандартным encryption manager.

Ключ manifest list, AAD prefix и длина файла упаковываются в объект key metadata. Этот объект сериализуется и шифруется с помощью Key Encryption Key (KEK), причём timestamp создания KEK используется как AES-GCM AAD. KEK и уникальный `KEK_ID` генерируются secure random generator. Для каждого snapshot `KEK_ID` ключа, шифрующего metadata manifest list, хранится в поле `key-id` структуры snapshot. Зашифрованные key metadata manifest list находятся в списке `encryption-keys` table metadata.

KEK шифруется master key таблицы через KMS client, а результат хранится в `encryption-keys`. KEK переиспользуется в течение срока, допустимого NIST SP 800-57, после чего выполняется rotation: создаются новые KEK/KEK_ID для новых объектов manifest-list key metadata. Предыдущие KEK сохраняются, поскольку они нужны существующим snapshots.
