---
title: "Разработка и публикация modules"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/modules/developing.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Разработка и публикация modules

Связанные packages можно объединять в modules, а затем публиковать modules для использования другими developers. Эта страница даёт обзор разработки и публикации modules.

Для разработки, публикации и использования modules применяются:

- **Workflow**, по которому module разрабатывается и публикуется, а затем получает новые versions. См. [[#Workflow разработки и публикации modules]].
- **Design practices**, помогающие users понять module и стабильно обновляться на новые versions. См. [[#Design и development]].
- **Децентрализованная система публикации** modules и получения их source code. Module остаётся в собственном repository и публикуется через version number. См. [[#Децентрализованная публикация]].
- **Package search engine и documentation browser** [pkg.go.dev](https://pkg.go.dev/), где developers могут найти module. См. [[#Package discovery]].
- **Convention нумерации versions**, передающая expectations о stability и backward compatibility. См. [[#Versioning]].
- **Go tools**, упрощающие управление dependencies: получение source module, upgrades и другое. См. [[managing-dependencies|Управление dependencies]].

**См. также:**

- Если нужно только использовать packages, разработанные другими, переходите к [[managing-dependencies|Управление dependencies]].
- Для tutorial с основами module development см. [[../tutorial/create-module|Создание Go module]].

## Workflow разработки и публикации modules {#workflow}

Если module будет использоваться другими developers, соблюдайте conventions, упрощающие его использование.

Подробный end-to-end процесс описан в [[release-workflow|Module release and versioning workflow]]. На высоком уровне:

1. Спроектируйте и реализуйте packages, входящие в module.
2. Commit'ьте code в repository, соблюдая conventions, делающие source доступным через Go tools.
3. Опубликуйте module, чтобы developers могли его обнаружить.
4. Со временем выпускайте новые versions, используя version numbering convention, которая сообщает stability и backward compatibility.

## Design и development {#design}

Module проще найти и использовать, если его functions и packages образуют связное целое. При проектировании public API старайтесь сохранять functionality сфокусированной и самостоятельной.

Проектирование с учётом backward compatibility помогает users обновляться с минимальными изменениями client code. Существуют techniques, позволяющие избегать releases, нарушающих compatibility. Подробнее: [Keeping your modules compatible](https://go.dev/blog/module-compatibility).

До публикации module можно использовать его через local filesystem с `replace` directive. Это удобно, когда client code разрабатывается одновременно с unpublished module. Подробнее см. [[release-workflow#Разработка против unpublished module|Module release and versioning workflow]].

## Децентрализованная публикация {#decentralized}

В Go module публикуется путём tagging source code в repository. Не нужно загружать module в центральный service: Go tools могут скачать source напрямую из repository — location определяется module path, который фактически является URL без scheme — либо через proxy server.

После import package users применяют Go tools, включая `go get`, чтобы скачать code module для compilation.

Эта модель требует conventions, по которым Go tools от имени developer могут найти module source. Go tools используют:

- module path;
- module version number/tag;
- repository location.

Подробнее о source/publishing conventions см. [[managing-source|Управление source module]].

Пошаговая публикация: [[publishing|Публикация module]].

## Package discovery {#discovery}

После публикации module и его первого получения через Go tools module становится видимым на [pkg.go.dev](https://pkg.go.dev/). Там developers могут найти package через search и прочитать documentation.

Чтобы начать использовать module, developer импортирует его packages и запускает `go get`, скачивая source code для compilation.

Подробнее о поиске и использовании modules см. [[managing-dependencies|Управление dependencies]].

## Versioning {#versioning}

По мере развития module versions получают numbers, основанные на semantic versioning. Version number сообщает users:

- насколько release стабилен;
- можно ли ожидать backward compatibility;
- насколько рискован upgrade.

Version указывается tag'ом source code в repository.

Разработка major update: [[major-version|Разработка major version update]].

Правила semantic versioning Go modules: [[version-numbers|Нумерация versions modules]].
