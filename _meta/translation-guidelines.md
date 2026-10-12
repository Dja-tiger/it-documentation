# Правила перевода

## Источник истины

Используются только официальный сайт проекта, официальный репозиторий и документация конкретного release/tag.

Для Apache Iceberg текущий baseline — `apache-iceberg-1.12.0`.

## Соответствие upstream

Один upstream Markdown-файл соответствует одному Markdown-файлу перевода. Имя файла сохраняется без изменения.

Пример:

```text
docs/docs/spark-queries.md
→
01-apache-iceberg/docs/spark-queries.md
```

## YAML frontmatter

Каждая страница содержит источник, release и статус перевода:

```yaml
---
title: "..."
tags:
  - apache-iceberg
source_project: apache/iceberg
source_file: docs/docs/example.md
source_ref: apache-iceberg-1.12.0
source_url: https://github.com/apache/iceberg/...
translation_status: translated
translated_at: 2026-10-12
---
```

## Что переводится

Переводятся заголовки, описательный текст, пояснения, предупреждения и подписи.

Не переводятся SQL, Java/Python/Scala-код, API identifiers, имена классов и методов, имена параметров и property keys, shell-команды, пути файлов и URL.

Если русский эквивалент может исказить инженерный смысл, английский термин сохраняется и при первом употреблении поясняется: `snapshot (снимок состояния таблицы)`, `manifest file`, `metadata file`, `optimistic concurrency control`.

## Obsidian

Для внутренней навигации используются WikiLinks. Иерархия официальной документации отражается в `MOC.md`, при этом один upstream-файл не дублируется физически в нескольких каталогах.

## Обновление версии

После нового release:

1. определить новый tag;
2. сравнить `docs/mkdocs.yml`;
3. найти добавленные/удалённые страницы;
4. сравнить изменённые upstream-файлы;
5. пометить затронутые переводы `outdated`;
6. обновлять перевод отдельными коммитами.

Рекомендуемый формат коммитов:

```text
docs(iceberg): translate partitioning for 1.12.0
docs(iceberg): sync spark queries with 1.12.1
docs(iceberg): add catalog page from upstream
```

## Лицензирование

Apache Iceberg распространяется по Apache License 2.0. Переведённые файлы являются изменёнными производными материалами и содержат ссылку на оригинал и уведомление о модификации.
