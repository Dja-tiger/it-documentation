---
title: Схемы
tags: [apache-iceberg, concepts, schema, data-types]
source_project: apache/iceberg
source_file: docs/docs/schemas.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/blob/apache-iceberg-1.12.0/docs/docs/schemas.md
translation_status: translated
translated_at: 2026-10-12
---
<!-- Apache Iceberg documentation, Apache License 2.0. Russian translation modified from the original. -->

# Схемы

Iceberg-таблицы поддерживают следующие типы:

| Тип | Описание | Примечания |
| --- | --- | --- |
| **`boolean`** | `true` или `false` | |
| **`int`** | 32-битное знаковое целое | Можно расширить до `long` |
| **`long`** | 64-битное знаковое целое | |
| **`float`** | 32-битное IEEE 754 число с плавающей точкой | Можно расширить до `double` |
| **`double`** | 64-битное IEEE 754 число с плавающей точкой | |
| **`decimal(P,S)`** | Decimal с фиксированной точкой; precision P, scale S | Scale фиксирован, precision не более 38 |
| **`date`** | Календарная дата без времени и часового пояса | |
| **`time`** | Время суток без даты и часового пояса | Хранится в микросекундах |
| **`timestamp`** | Timestamp без часового пояса | Хранится в микросекундах |
| **`timestamptz`** | Timestamp с часовым поясом | Хранится в микросекундах |
| **`timestamp_ns`** | Timestamp без часового пояса, точность до наносекунд | Хранится в наносекундах; добавлен в v3 |
| **`timestamptz_ns`** | Timestamp с часовым поясом, точность до наносекунд | Хранится в наносекундах; добавлен в v3 |
| **`string`** | Символьная последовательность произвольной длины | UTF-8 |
| **`uuid`** | Universally Unique Identifier | |
| **`fixed(L)`** | Массив байт фиксированной длины L | |
| **`binary`** | Массив байт произвольной длины | |
| **`variant`** | Полуструктурированные данные, подобные JSON | Добавлен в v3 |
| **`geometry(C)`** | Геопространственные объекты с параметром CRS | Линейная интерполяция рёбер; добавлен в v3 |
| **`geography(C, A)`** | Геопространственные объекты с CRS и алгоритмом обработки рёбер | Нелинейная интерполяция рёбер; добавлен в v3 |
| **`unknown`** | Placeholder для колонок с ещё не определённым типом | Должен быть optional; добавлен в v3 |
| **`struct<...>`** | Запись с именованными полями любого типа | |
| **`list<E>`** | Список элементов любого типа | |
| **`map<K, V>`** | Map с ключами и значениями любых типов | |

Iceberg отслеживает каждое поле схемы таблицы по ID, который никогда не переиспользуется в этой таблице. Подробнее см. [[evolution#Корректность|гарантии корректности]].
