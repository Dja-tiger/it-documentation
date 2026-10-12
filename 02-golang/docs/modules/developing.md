---
title: "Разработка и публикация модулей"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/modules/developing.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Разработка и публикация модулей

Связанные packages можно объединять в modules, а затем публиковать их для использования другими разработчиками. Здесь дан обзор жизненного цикла разработки и публикации Go modules.

Для разработки, публикации и использования modules применяются:

- **workflow разработки и публикации**, в котором module со временем получает новые versions;
- **design practices**, помогающие пользователям понимать API и безопасно переходить на новые versions;
- **децентрализованная модель публикации**: module остаётся в вашем repository и публикуется через version tag, а не загружается в обязательный централизованный registry;
- **pkg.go.dev** — поисковая система packages и браузер документации;
- **соглашение о version numbering**, основанное на semantic versioning и передающее ожидания по стабильности и backward compatibility;
- **Go tools** для загрузки source code, управления dependencies и обновления versions.

Если задача состоит только в использовании чужих packages, см. [[managing-dependencies|Управление зависимостями]]. Для первого практического знакомства — [[../tutorial/create-module|Create a Go module]].

## Workflow разработки и публикации

Для module, предназначенного другим разработчикам, рекомендуется следующий общий процесс:

1. Спроектировать и реализовать packages, входящие в module.
2. Закоммитить код в repository с соблюдением соглашений, позволяющих Go tools получать source code.
3. Опубликовать module, чтобы его можно было обнаружить и использовать.
4. Выпускать последующие versions, используя version numbering, которое сообщает о стабильности и backward compatibility.

Подробный end-to-end процесс описан в [[release-workflow|Module release and versioning workflow]].

## Проектирование и разработка

Module легче находить и использовать, если его functions и packages образуют логически целостную систему. При проектировании public API старайтесь держать функциональность сфокусированной и ограниченной ясной ответственностью.

Проектирование с учётом backward compatibility уменьшает стоимость upgrades для пользователей. Изменения API стоит строить так, чтобы по возможности не требовать major-version release.

До публикации module его можно использовать локально через директиву `replace`. Это удобно, когда client code и новый module разрабатываются параллельно, но module ещё недоступен через `go get`.

## Децентрализованная публикация

В Go module публикуется путём установки version tag на код в repository. Обязательный централизованный upload-сервис не требуется. Go tools могут получить source code:

- непосредственно из repository, найденного по module path;
- через module proxy.

После импорта package пользователь может применить `go get`, чтобы разрешить dependency. Go tools используют module path и version tag для поиска и скачивания нужной версии.

Соглашения по repository и tags подробно описаны в [[managing-source|Управление исходным кодом module]]. Пошаговая публикация — в [[publishing|Публикация module]].

## Обнаружение packages

После публикации и первого получения module через Go ecosystem он становится видим на [pkg.go.dev](https://pkg.go.dev/). Там разработчики могут искать packages и читать документацию.

Чтобы использовать module, разработчик импортирует один из его packages, после чего Go tools разрешают и скачивают dependency.

## Versioning

При развитии module версии назначаются по semantic versioning. Номер версии сообщает:

- считается ли module стабильным;
- гарантируется ли backward compatibility;
- является ли release pre-release;
- содержит ли release breaking changes.

Version number публикуется repository tag'ом. Правила подробно описаны в [[version-numbers|Module version numbering]]. Для breaking major update см. [[major-version|Разработка major-version update]].
