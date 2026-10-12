# Самостоятельное изучение Go

Этот каталог — **learning layer** поверх уже переведённой официальной документации в `../docs/`.

Он не заменяет документацию и не пересказывает её. Его задача — дать порядок изучения, практику, проверку понимания и последовательность проектов.

```text
официальная документация
        ↓
русский reference в ../docs/
        ↓
learning roadmap
        ↓
практика и эксперименты
        ↓
проверка знаний
        ↓
мини-проекты
        ↓
production-oriented Data Engineering service
```

## С чего начать

1. Прочитать [[study-rules|правила обучения и критерий mastery]].
2. Открыть [[roadmap|Roadmap]] и начать с Stage 1.
3. Отмечать фактический прогресс в [[progress|Progress]].
4. Для каждой темы сначала читать указанные официальные материалы, затем выполнять упражнения.
5. Переходить дальше только после практической проверки из stage-файла.

## Навигация

- [[roadmap|Roadmap]] — порядок тем и checkpoint’ы.
- [[progress|Progress]] — детальный checklist.
- [[study-rules|Методика обучения]] — mastery и повторение Day 0/1/3/7/14.
- [[standard-library|Минимальный маршрут по standard library]].
- [[projects/README|Последовательность проектов]].
- `stages/` — что читать, понимать, ломать и писать на каждом этапе.
- `practice/` — задания без готовых решений.

## Для кого построен маршрут

Маршрут рассчитан на инженера с сильной базой в SQL, PostgreSQL/Greenplum, ETL/ELT, Kafka, Linux, API и production systems, но без системного опыта Go.

Поэтому здесь не объясняются заново общие инженерные идеи вроде транзакции, HTTP или worker pool. Фокус — на том, **как эти идеи выражаются в Go**, какие guarantees даёт язык/runtime и какие ошибки типичны именно для Go.

## Источники истины

- Переведённые материалы: `../docs/`.
- Нормативная семантика языка: [[../docs/spec|Go 1.27 Specification]].
- Standard library API: [pkg.go.dev/std](https://pkg.go.dev/std).
- Интерактивная практика core language: [A Tour of Go](https://go.dev/tour/).

Specification используется как reference в ранних stages и читается системно только ближе к концу маршрута.

> [!important]
> Baseline курса — **Go 1.27.1**. Learning layer не меняет upstream refs, metadata и translated documentation.
