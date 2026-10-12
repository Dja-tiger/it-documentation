---
title: "Нумерация версий Go modules"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/modules/version-numbers.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Нумерация версий Go modules

Каждая часть version number Go module сообщает пользователям о стабильности и backward compatibility. При выпуске новой версии номер должен отражать характер изменений относительно предыдущего release.

Go modules используют semantic versioning.

| Стадия | Пример | Что означает |
|---|---|---|
| В разработке | pseudo-version или `v0.x.x` | Module нестабилен; backward compatibility не гарантируется. |
| Major | `v1.x.x`, `v2.x.x` | Для нового major возможны backward-incompatible public API changes. |
| Minor | `vx.4.x` | Backward-compatible public API changes. |
| Patch | `vx.x.1` | Исправления без изменения public API/контракта release. |
| Pre-release | `vx.x.x-beta.2` | Alpha/beta/RC-подобный milestone без гарантии стабильности. |

## Версия в разработке

До стабильного `v1` module может иметь pseudo-version или version `v0.x.x`.

### Pseudo-version

Когда commit не имеет semantic version tag, Go tools могут сгенерировать pseudo-version для записи в `go.mod`.

> [!important]
> Не формируйте pseudo-version вручную. Позвольте Go tools вычислять её.

Пример:

```text
v0.0.0-20170915032832-14c0d48ead0c
```

Форма:

```text
baseVersionPrefix-timestamp-revisionIdentifier
```

Компоненты:

- `baseVersionPrefix` — производен от предшествующего semantic version tag либо от `vX.0.0`, если подходящего tag нет;
- `timestamp` — UTC-время создания revision в формате `yymmddhhmmss`; для Git используется commit time, а не author time;
- `revisionIdentifier` — обычно первые 12 символов commit hash; в Subversion — zero-padded revision number.

Pseudo-version полезна, когда client должен зависеть от конкретного ещё не tagged commit.

### v0

`v0.x.x` является формальным semantic version, но не обещает стабильность или backward compatibility. Breaking changes между v0 releases допустимы, а переход с v0 на v1 также может потребовать адаптации client code.

## Pre-release

Пример:

```text
v1.2.3-beta.2
```

Pre-release identifier добавляется после `major.minor.patch` через `-`. Такой release не даёт гарантий стабильности.

## Minor version

Minor release означает backward-compatible изменения public API:

```text
v1.4.0
```

Это могут быть новые functions, methods, struct fields, types либо изменения dependencies, которые не требуют изменения существующего client code.

## Patch version

Patch release предназначен для небольших исправлений, не меняющих public API:

```text
v1.4.1
```

Пользователь должен иметь возможность перейти на patch без изменения своего кода.

## Major version

Major release означает возможные backward-incompatible public API changes.

`v1+` сообщает, что module считается стабильным, кроме явно обозначенных pre-release versions.

Major increment выше v1 следует делать только при необходимости, потому что он создаёт значительную миграционную стоимость для пользователей.

Для v2 и выше major version входит в module path:

```text
module example.com/mymodule/v2
```

Это означает, что новый major рассматривается dependency management как новый module с отдельным module path. Imports пользователя также меняются:

```go
import "example.com/mymodule/v2/package"
```

Подробный workflow — [[major-version|Разработка major-version update]].
