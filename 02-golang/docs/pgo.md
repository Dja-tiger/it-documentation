---
title: "Profile-guided optimization (PGO)"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/pgo.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Profile-guided optimization

Начиная с Go 1.20 compiler поддерживает Profile-Guided Optimization (PGO), также называемую Feedback-Directed Optimization (FDO).

Идея: CPU profile representative execution передаётся compiler следующего build, чтобы compiler знал реальные hot paths и принимал более точные optimization decisions — например, aggressive inlining hot calls.

Go использует **CPU pprof profiles** как PGO input.

В upstream guide зафиксировано: representative benchmarks Go programs для Go 1.22 показывали примерно **2–14%** performance improvement; конкретный выигрыш workload-specific и меняется с развитием compiler.

## Collecting profiles

Подходящие sources:

- `runtime/pprof`;
- `net/http/pprof`;
- converted external profiles, если они соответствуют pprof requirements.

Наиболее важное условие — profile должен быть **representative production behavior**.

Unrepresentative profile обычно даёт мало пользы. Microbenchmarks чаще всего плохой source, потому что покрывают узкий subset application.

### Recommended iterative workflow

1. Build/release initial binary без PGO или с предыдущим profile.
2. Collect CPU profiles production.
3. При следующем release build latest source с collected profile.
4. Release optimized binary.
5. Collect profiles уже с него.
6. Repeat.

Go PGO специально разработан устойчивым к небольшому skew между profiled source и source следующего build, а также к profiles, собранным с уже PGO-optimized binaries.

## Building with PGO

Standard convention — положить CPU profile с именем:

```text
default.pgo
```

в directory main package.

Default `go build` обнаруживает его при `-pgo=auto`.

Официальный guide рекомендует хранить profile рядом с source в repository, потому что profile является build input, влияющим на performance/reproducibility.

Явный profile:

```bash
go build -pgo=/tmp/service.pprof ./cmd/service
```

Отключить:

```bash
go build -pgo=off ./cmd/service
```

> [!warning]
> Один explicit `-pgo=/path/profile` применяется ко **всем** main packages в конкретном `go build`. Если собираются разные binaries, обычно каждому нужен свой representative profile и отдельный build invocation.

До Go 1.21 default был `-pgo=off`; в modern Go auto mode — standard workflow.

## Representative production profiles

Простой старт для HTTP service:

```text
/debug/pprof/profile?seconds=30
```

Но один 30-second profile одной instance может быть biased:

- instance временно idle;
- traffic mix меняется по времени суток;
- long-running operations не помещаются в sample window;
- load balancer неравномерно распределяет request types.

Лучше собирать multiple profiles:

- в разные моменты времени;
- с разных replicas;
- с одинаковой duration;
- с representative traffic.

Continuous profiling systems хорошо подходят как production profile source.

## Merge profiles

```bash
go tool pprof -proto a.pprof b.pprof > merged.pprof
```

Merge фактически суммирует samples и не нормализует их по wall duration. Поэтому profiles, представляющие равные sampling windows, должны иметь одинаковую duration; иначе длинный profile получает больший weight.

Для разных workloads weighting должен отражать desired production importance/footprint.

## AutoFDO properties

### Source stability

Profile от немного старой source revision всё ещё полезен.

Compiler сопоставляет samples с current source heuristically. Многие changes не ломают matching:

- изменения вне hot function;
- добавление других functions;
- перемещение function в другой file того же package.

Могут ломать matching:

- significant edits внутри hot function, меняющие line offsets;
- function/type rename;
- move function в другой package.

Если конкретный function не сопоставлен, degradation graceful: теряется PGO optimization этой части, но другие hot functions продолжают получать benefits.

Profile skew накапливается, поэтому profiles нужно обновлять регулярно, особенно после крупного refactoring.

### Iterative stability

В теории PGO могла бы создать oscillation: function hot → optimized → перестала hot → не optimized next build → снова hot. Go compiler использует conservative optimization approach, чтобы избегать такой instability.

Именно source + iterative stability позволяют не строить каждый release обязательным двух-stage pipeline `unoptimized canary -> profile -> final build`.

## Новый код

Новый code path отсутствует в old profile, поэтому первый release после feature introduction не получает full PGO benefits для этого path. После rollout соберите новый profile — steady-state performance следующего build может быть лучше.

## Standard library

PGO применяется ко **всей program**, включая standard library packages, которые rebuild'ятся с учетом profile.

## Dependencies

То же относится к packages dependent modules. Unique usage dependency вашей application влияет на оптимизации этой dependency.

## Может ли плохой profile сделать хуже?

Design goal Go — unrepresentative profile не должен делать hot production path медленнее, чем no-PGO build. Он просто может оптимизировать cold code и дать минимальный benefit. Если observed performance регрессирует именно из-за PGO, upstream просит filing issue.

## Cross-platform profiles

Profile format совместим между `GOOS/GOARCH`, поэтому profile `linux/arm64` можно применять к `windows/amd64` build.

Но source/platform-specific code может не match, например internals `os` package для Linux/Windows. Platform-independent application code обычно всё равно сопоставляется.

Можно merge profiles разных architectures/platforms, учитывая workload weighting.

## Один binary, разные workloads

Например database binary используется read-heavy и write-heavy services.

Варианты:

1. **Отдельный build/profile на workload** — лучший peak performance, больше operational complexity.
2. **Один profile самого важного workload** — maximal benefit для приоритетного сценария, common code всё равно может улучшить остальные.
3. **Merged fleet profile** — умеренные benefits для всех, один binary.

## Build time

PGO увеличивает build time. Profile влияет на весь dependency graph, поэтому first build с новым profile может rebuild'ить все packages.

Build cache применяется как обычно; повторные incremental builds с тем же profile не обязаны rebuild'ить всё.

## Binary size

PGO может немного увеличить binary из-за дополнительного inlining.

## Alternative profile sources

External profile можно использовать, если он converted в pprof format и содержит необходимые данные.

Requirements:

- sample index типа/unit `samples/count` или `cpu/nanoseconds`;
- samples отражают CPU time в locations;
- profile symbolized (`Function.name` заполнен);
- samples содержат frames для **inlined functions**, иначе iterative stability страдает;
- `Function.start_line` заполнен — compiler использует его для line offsets.

До Go 1.21 DWARF мог не содержать function start lines, что затрудняло conversion external profiles.

## Production practice

PGO стоит рассматривать как часть build supply chain:

- profile — versioned build input;
- source profile должен быть доверенным и representative;
- CI должен уметь reproducibly выбрать конкретный profile;
- после крупных refactors профиль обновляется;
- improvement проверяется benchmarks/load tests, а не предполагается.
