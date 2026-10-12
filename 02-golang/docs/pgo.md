---
title: "Profile-guided optimization (PGO)"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/pgo.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Profile-guided optimization

Начиная с Go 1.20 compiler поддерживает Profile-Guided Optimization (PGO), также называемую Feedback-Directed Optimization (FDO), для дополнительной optimization builds.

Содержание:

- [Обзор](#overview)
- [Сбор profiles](#collecting-profiles)
- [Сборка с PGO](#building)
- [Примечания](#notes)
- [FAQ](#faq)
- [Appendix: alternative profile sources](#alternative-sources)

## Обзор {#overview}

Profile-guided optimization — compiler optimization technique, которая передаёт information из representative runs application обратно compiler следующего build. Compiler использует profile, чтобы принимать более informed optimization decisions.

Например, compiler может более aggressively inline functions, которые profile показывает как часто вызываемые.

Go compiler использует **CPU pprof profiles** как PGO input, например profiles из [`runtime/pprof`](https://pkg.go.dev/runtime/pprof) или [`net/http/pprof`](https://pkg.go.dev/net/http/pprof).

По состоянию на Go 1.22 benchmarks representative set Go programs показывали, что build с PGO улучшает performance примерно на **2–14%**. Ожидается, что gains со временем будут расти по мере добавления новых PGO-aware optimizations.

## Сбор profiles {#collecting-profiles}

Go compiler ожидает CPU pprof profile.

Profiles, generated Go runtime — например через `runtime/pprof` и `net/http/pprof` — можно использовать напрямую.

Profiles из других systems иногда можно использовать после conversion; requirements описаны в [appendix](#alternative-sources).

Для best results profile должен быть **representative реального production behavior** application.

Unrepresentative profile, скорее всего, даст мало или вообще не даст improvement в production. Поэтому primary recommended approach — собирать profiles непосредственно из production environment.

Типичный workflow:

1. Build и release initial binary **без PGO**.
2. Collect profiles from production.
3. При следующем release build latest source с production profile.
4. Вернуться к step 2.

Go PGO в целом устойчив к skew между profiled version application и version, которая собирается с profile, а также к profiles, собранным с уже optimized binaries. Именно это делает iterative lifecycle возможным.

Подробнее — [AutoFDO](#autofdo).

Если собирать profile в production трудно или невозможно, например command-line tool распространяется конечным users, можно использовать representative benchmark.

Но representative benchmarks сложно строить и поддерживать representative по мере evolution application.

Особенно важно: **microbenchmarks обычно плохие candidates для PGO profiling**, потому что покрывают лишь малую часть application и поэтому дают маленький benefit для whole-program optimization.

## Сборка с PGO {#building}

Standard approach — хранить pprof CPU profile под name:

```text
default.pgo
```

в directory main package profiled binary.

По default `go build` автоматически обнаруживает `default.pgo` и включает PGO.

Profiles рекомендуется commit'ить прямо в source repository, потому что они являются build input, важным и для reproducibility, и для performance. Хранение рядом с source убирает дополнительные steps получения profile перед build.

Для более сложных scenarios используется flag `go build -pgo`.

Default:

```text
-pgo=auto
```

что реализует behavior `default.pgo` выше.

Полностью отключить PGO:

```bash
go build -pgo=off
```

Если `default.pgo` использовать нельзя, можно явно передать path:

```bash
go build -pgo=/tmp/foo.pprof
```

> [!note]
> Path, переданный `-pgo`, применяется ко **всем** main packages одного invocation.
>
> Например:
>
> ```bash
> go build -pgo=/tmp/foo.pprof ./cmd/foo ./cmd/bar
> ```
>
> применяет `foo.pprof` и к `foo`, и к `bar`, что обычно нежелательно. Разные binaries чаще всего требуют разных profiles и отдельных `go build` invocations.

> [!note]
> До Go 1.21 default был `-pgo=off`; PGO требовалось включать явно.

## Примечания {#notes}

### Сбор representative production profiles

Production environment — лучший source representative profiles.

Самый простой способ начать — подключить `net/http/pprof` и получить:

```text
/debug/pprof/profile?seconds=30
```

с произвольной instance service.

Это хороший старт, но single 30-second profile может быть unrepresentative:

- instance может быть idle именно в момент profiling, хотя обычно busy;
- traffic patterns могут меняться в течение day;
- instance может выполнять long-running operations, например 5 min operation A, затем 5 min operation B; 30-second profile, скорее всего, захватит только один operation type;
- load distribution между instances может быть uneven.

Более robust strategy — собирать multiple profiles в разные moments и с разных instances, уменьшая влияние variation individual profiles.

После этого profiles можно [merge](#merging-profiles).

Многие organizations используют continuous profiling services, автоматически sampling fleet; такие systems подходят как source для PGO profiles.

### Merge profiles {#merging-profiles}

`pprof` умеет объединять profiles:

```bash
go tool pprof -proto a.pprof b.pprof > merged.pprof
```

Merge фактически является straightforward sum samples inputs независимо от wall duration.

Поэтому для profiles коротких slices long-running service обычно нужно использовать одинаковую duration, например по 30 seconds.

Иначе longer profiles будут overrepresented.

### AutoFDO {#autofdo}

Go PGO разработан для workflow в стиле [AutoFDO](https://research.google/pubs/pub45290/).

Повторим lifecycle:

1. Build/release initial binary без PGO.
2. Collect profiles из production.
3. Build latest source с profile.
4. GOTO 2.

Здесь важны два свойства.

**Source stability.** Development продолжается постоянно, поэтому source profiled binary обычно немного отличается от latest source следующего build. Go PGO пытается быть устойчивым к такому skew.

**Iterative stability.** После первого iteration profiled binary уже PGO-optimized предыдущим profile. Go PGO должен оставаться стабильным и в closed loop.

Source stability достигается heuristics, сопоставляющими samples profile с compiling source.

Например, добавление новых functions обычно не ломает mapping существующего code. Если changed code сопоставить не удаётся, degradation graceful: конкретная function теряет часть optimization opportunities, но PGO benefit в целом распределён по многим functions.

Iterative stability означает отсутствие performance oscillation между successive PGO builds: fast → slow → fast.

Теоретически hot function можно так сильно ускорить PGO, что в следующем profile она перестанет быть hot и optimization исчезнет, после чего function снова станет slow. Go compiler intentionally применяет conservative PGO optimizations, чтобы избегать значительной variance.

Если наблюдается такая instability, upstream просит [создать issue](https://go.dev/issue/new).

Source и iterative stability вместе позволяют не требовать обязательный two-stage build:

```text
unoptimized canary -> profile -> final production build
```

если только не требуется абсолютно peak performance.

### Source stability и refactoring {#source-stability}

Go PGO best-effort сопоставляет samples старого profile с current source.

Основной mechanism — line offsets внутри functions, например «call на 5-й line function `foo`».

Изменения, которые обычно **не ломают** matching:

- changes в file вне hot function;
- добавление/change code выше или ниже function;
- перемещение function в другой file того же package — compiler игнорирует source filename.

Изменения, которые **могут ломать** matching:

- edits внутри hot function, меняющие line offsets;
- rename function и/или receiver type methods;
- move function в другой package, меняющий symbol name.

Если profile относительно fresh, обычно affected лишь небольшой subset hot functions.

Но degradation постепенно accumulates, потому что source редко refactor'ится обратно в прежнее состояние. Поэтому profiles важно регулярно обновлять.

Large refactor, который массово renames functions или перемещает их между packages, может заметно ухудшить matching до появления нового profile.

Теоретически для rote renames старый profile можно переписать, заменив symbol names. Package [`github.com/google/pprof/profile`](https://pkg.go.dev/github.com/google/pprof/profile) содержит primitives для такой rewrite, но на момент upstream document готового off-the-shelf tool нет.

### Performance нового code

Новый code или code path, включённый feature flag, отсутствует в старом profile.

Поэтому первый release не получает для него PGO optimizations. После rollout соберите новый profile.

При оценке initial rollout учитывайте, что он не обязательно отражает steady-state performance будущих PGO builds.

## FAQ {#faq}

### Можно ли PGO optimize standard library packages?

Да.

PGO применяется ко **всей program**. Все packages rebuild'ятся с учётом profile, включая standard library.

### Можно ли optimize packages dependent modules?

Да.

PGO применяется ко всей program, включая dependency packages. Поэтому unique way, которым ваша application использует dependency, влияет на optimizations этой dependency.

### Может ли unrepresentative profile сделать program медленнее, чем без PGO?

Не должен.

Unrepresentative profile может направить optimizations в cold code и дать мало benefit, но hot code не должен стать медленнее именно из-за PGO.

Если PGO стабильно ухудшает performance относительно `-pgo=off`, upstream просит [создать issue](https://go.dev/issue/new).

### Можно ли использовать один profile для разных `GOOS/GOARCH` builds?

Да.

Profile format equivalent между OS/architecture configurations. Например, profile `linux/arm64` можно использовать для `windows/amd64` build.

Но применяются source-stability caveats. Platform-specific code, который отличается между configurations, не будет match'иться.

Например, internals file handling package `os` различаются между Linux и Windows, поэтому Windows equivalents hot Linux functions не получат PGO optimizations из Linux-only samples.

Profiles разных platforms можно merge'ить.

### Что делать, если один binary используется для разных workload types?

Однозначного выбора нет.

Пример: database binary используется read-heavy в одном service и write-heavy в другом.

Три options:

1. **Отдельный binary/profile для каждого workload.** Лучший performance для каждого scenario, но больше operational complexity.
2. **Один binary с profile самого важного workload.** Максимизирует benefit приоритетного workload; shared code часто улучшит и остальные.
3. **Merge profiles всех workloads**, weighted по total footprint. Обычно даёт умеренный improvement всем workloads при одном common binary.

### Как PGO влияет на build time?

PGO обычно заметно увеличивает package build times.

Главная причина: profile влияет на все packages binary, поэтому first use нового profile требует rebuild всего dependency graph.

Как и обычные builds, результаты cache'ятся, поэтому subsequent incremental builds с тем же profile не требуют полного rebuild.

Если build time растёт аномально сильно, upstream просит file issue.

### Как PGO влияет на binary size?

PGO может слегка увеличивать binary из-за дополнительного function inlining.

## Appendix: alternative profile sources {#alternative-sources}

CPU profiles из Go runtime уже имеют правильный format для PGO.

Organizations могут предпочитать другие tools, например Linux `perf`, или иметь existing fleet-wide continuous profiling systems.

Alternative profile можно использовать после conversion в [pprof format](https://github.com/google/pprof/tree/main/proto), если выполнены requirements:

- один sample index должен иметь type/unit `samples`/`count` или `cpu`/`nanoseconds`;
- samples должны представлять CPU time в sample location;
- profile должен быть symbolized: `Function.name` заполнен;
- samples должны содержать stack frames **inlined functions**, иначе Go не сможет поддерживать iterative stability;
- `Function.start_line` должен быть заполнен — это line, содержащая keyword `func`; compiler использует:

```text
Location.Line.line - Function.start_line
```

для вычисления line offsets samples.

Многие existing pprof converters не заполняют `Function.start_line`.

> [!note]
> До Go 1.21 DWARF metadata не содержала function start lines (`DW_AT_decl_line`), что может усложнять conversion external profiles.

Дополнительная информация о compatibility third-party tools: [PGO Tools](https://go.dev/wiki/PGO-Tools).
