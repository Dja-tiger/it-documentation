---
title: "Нумерация versions modules"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/modules/version-numbers.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Нумерация versions modules

Developer module использует каждую часть version number, чтобы сообщить stability и backward compatibility. Для каждого release version number отражает nature изменений относительно предыдущего release.

Если ваш code использует external modules, version numbers помогают оценивать stability dependency при upgrade. Если вы разрабатываете собственный module, version number передаёт другим developers expectations о stability и compatibility.

**См. также:**

- управление external dependencies: [[managing-dependencies|Управление dependencies]];
- публикация собственной version: [[publishing|Публикация module]].

Published module использует semantic versioning.

Например:

```text
v1.4.0-beta.2
```

В этом числе:

- `1` — major;
- `4` — minor;
- `0` — patch;
- `beta.2` — optional pre-release identifier.

| Stage | Example | Что сообщает users |
| --- | --- | --- |
| [[#In development|In development]] | automatic pseudo-version / `v0.x.x` | Module ещё развивается и нестабилен; backward compatibility/stability не гарантируются. |
| [[#Major version|Major]] | `v1.x.x` | Public API может содержать backward-incompatible changes относительно предыдущих major versions. |
| [[#Minor version|Minor]] | `vx.4.x` | Backward-compatible public API changes; compatibility и stability гарантируются в рамках major. |
| [[#Patch version|Patch]] | `vx.x.1` | Changes не затрагивают public API или dependencies; compatibility и stability сохраняются. |
| [[#Pre-release version|Pre-release]] | `vx.x.x-beta.2` | Alpha/beta milestone без stability guarantees. |

## In development {#in-development}

Module всё ещё развивается и считается **unstable**. Backward compatibility и stability не гарантируются.

Version может иметь одну из форм.

### Pseudo-version number {#pseudo}

Пример:

```text
v0.0.0-20170915032832-14c0d48ead0c
```

Если module ещё не tagged в repository, Go tools создают pseudo-version, используемую, например, в `go.mod` consumer code.

> [!important]
> Всегда позволяйте Go tools генерировать pseudo-version автоматически. Не создавайте её вручную.

Pseudo-version полезна, когда consumer должен использовать конкретный commit, который ещё не получил semantic version tag.

Форма:

```text
baseVersionPrefix-timestamp-revisionIdentifier
```

Части:

- **baseVersionPrefix** — `vX.0.0` или `vX.Y.Z-0`, derived из предшествующего semantic version tag либо `vX.0.0`, если tag отсутствует;
- **timestamp** — UTC creation time revision в формате `yymmddhhmmss`. В Git используется commit time, а не author time;
- **revisionIdentifier** — 12-character prefix commit hash, а для Subversion — zero-padded revision number.

### v0 number {#v0}

Пример:

```text
v0.x.x
```

Module с v0 использует формальное semantic version number из major/minor/patch частей и optional pre-release identifier.

Хотя v0 может использоваться в production, она не даёт guarantees stability или backward compatibility.

Кроме того, v1+ разрешено нарушать compatibility с v0. Поэтому developer consumer code отвечает за adaptation к incompatible changes до выпуска v1.

## Pre-release version {#pre-release}

Pre-release сообщает о milestone вроде alpha/beta и не даёт guarantees stability.

Пример:

```text
vx.x.x-beta.2
```

Pre-release identifier можно добавить к любой `major.minor.patch` combination через `-identifier`.

## Minor version {#minor}

Minor version сообщает о backward-compatible changes public API.

Пример:

```text
vx.4.x
```

Public API меняется, но client code предыдущих minor versions не должен ломаться.

Такая version может включать:

- changes dependencies самого module;
- новые functions;
- новые methods;
- новые struct fields;
- новые types.

Users могут воспользоваться новой functionality, но им не требуется менять существующий code только из-за upgrade minor version.

## Patch version {#patch}

Patch version сообщает о changes, не затрагивающих public API или dependencies.

Пример:

```text
vx.x.1
```

Обычно это небольшие изменения вроде bug fixes. Consumer code может безопасно upgrade'иться без изменений.

## Major version {#major}

Major version сообщает о backward-incompatible changes public API и не гарантирует compatibility с предыдущими majors.

Пример:

```text
v1.x.x
```

v1 и выше означает, что module считается stable для использования, за исключением pre-release versions.

Поскольку v0 stability guarantees не даёт, developer, обновляющий dependency с v0 на v1, отвечает за adaptation к возможным breaking changes.

Maintainer должен увеличивать major выше v1 только когда это необходимо: major upgrade создаёт существенный disruption для users. Это включает:

- backward-incompatible public API changes;
- необходимость менять package paths во всех imports нового major.

Major version выше v1 также получает новый module path, потому что major number добавляется в path:

```text
module example.com/mymodule/v2
```

а release version будет, например:

```text
v2.0.0
```

Новая major version считается новым module с отдельной history с точки зрения dependency management.

Подробнее:

- [[major-version|Разработка major version update]];
- [[release-workflow|Module release and versioning workflow]];
- [[gomod-ref|go.mod reference]].
