---
title: "Go Modules Reference"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/ref/mod.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Go Modules Reference

## Введение {#introduction}

Modules — механизм, с помощью которого Go управляет dependencies.

Этот документ — подробное reference-руководство по module system Go. Введение в создание Go-проектов см. в [[../code|How to Write Go Code]]. Информацию об использовании modules, миграции проектов на modules и других темах см. в серии публикаций, начинающейся с [Using Go Modules](https://go.dev/blog/using-go-modules).

## Modules, packages и versions {#modules-overview}

**Module** — коллекция packages, которые выпускаются, versioned и распространяются вместе. Modules могут загружаться непосредственно из version control repositories или с module proxy servers.

Module идентифицируется [module path](#module-path), который объявляется в [`go.mod` file](#go-mod-file) вместе с информацией о dependencies module. **Module root directory** — directory, содержащий `go.mod`. **Main module** — module, содержащий directory, из которого вызвана command `go`.

Каждый **package** внутри module — коллекция source files в одной directory, компилируемых вместе. **Package path** — module path, объединённый с subdirectory package относительно module root. Например, module `"golang.org/x/net"` содержит package в directory `"html"`; path этого package — `"golang.org/x/net/html"`.

### Module paths {#module-path}

**Module path** — каноническое имя module, объявляемое directive [`module`](#go-mod-file-module) в [`go.mod`](#go-mod-file). Module path служит prefix для package paths внутри module.

Module path должен описывать и назначение module, и то, где его искать. Обычно он состоит из repository root path, directory внутри repository — обычно пустой — и major version suffix, только для major version 2 и выше.

- **Repository root path** — часть module path, соответствующая root directory version-control repository, где разрабатывается module. Большинство modules определяются в root repository, поэтому обычно repository root path совпадает со всем module path. Например, `golang.org/x/net` — repository root path одноимённого module. Как command `go` находит repository через HTTP requests, производные от module path, описано в [Finding a repository for a module path](#vcs-find).
- Если module определён не в root repository, **module subdirectory** — часть module path, называющая эту directory без major version suffix. Она также служит prefix для semantic-version tags. Например, module `golang.org/x/tools/gopls` находится в subdirectory `gopls` repository с root path `golang.org/x/tools`, поэтому его module subdirectory — `gopls`. См. [Mapping versions to commits](#vcs-version) и [Module directories within a repository](#vcs-dir).
- Если module выпускается с major version 2 или выше, module path должен оканчиваться [major version suffix](#major-version-suffixes), например `/v2`. Suffix может быть частью physical subdirectory name, а может и не быть. Например, module `golang.org/x/repo/sub/v2` может находиться в `/sub` или `/sub/v2` repository `golang.org/x/repo`.

Если другие modules могут зависеть от module, эти правила необходимо соблюдать, чтобы command `go` могла найти и загрузить module. На допустимые characters module paths также действуют [lexical restrictions](#go-mod-file-ident).

Module, который никогда не будет загружаться как dependency другого module, может использовать любой valid package path, однако следует избегать collisions с paths dependencies и standard library. Standard library использует package paths без точки в первом path element, и command `go` не пытается разрешать такие paths через network servers. Paths `example` и `test` зарезервированы для users: standard library не будет их использовать, поэтому они подходят для self-contained modules, например tutorials, example code и tests.

### Versions {#versions}

**Version** идентифицирует immutable snapshot module и может быть [release](#glos-release-version) или [pre-release](#glos-pre-release-version). Каждая version начинается с `v`, после которого идёт semantic version. Формат, interpretation и comparison определены [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

Semantic version состоит из трёх неотрицательных integers — major, minor и patch — разделённых точками. После patch version может идти optional pre-release string с hyphen. После pre-release string или patch version может идти build metadata string, начинающаяся с plus. Например, `v0.0.0`, `v1.12.134`, `v8.0.5-pre` и `v2.0.9+meta` — valid versions.

Каждая часть version указывает на stability и compatibility:

- **Major version** увеличивается, а minor и patch устанавливаются в zero после backwards-incompatible изменения public interface или documented functionality module, например удаления package.
- **Minor version** увеличивается, а patch устанавливается в zero после backwards-compatible изменения, например добавления function.
- **Patch version** увеличивается после изменения, не затрагивающего public interface, например bug fix или optimization.
- Pre-release suffix означает unstable pre-release; такие versions сортируются раньше соответствующего release: `v1.2.3-pre` раньше `v1.2.3`.
- Build metadata suffix игнорируется при comparison versions. Command `go` принимает versions с build metadata и преобразует их в pseudo-versions, чтобы сохранить total ordering. Special suffix `+incompatible` обозначает version major 2+ из repository, выпущенную до миграции на modules. Special suffix `+dirty` добавляется к version information binary, если binary собран Go toolchain 1.24+ внутри valid local VCS repository с uncommitted working-tree changes.

Version считается unstable, если major version равна 0 или присутствует pre-release suffix. На unstable versions compatibility requirements не распространяются. Например, `v0.2.0` может быть несовместима с `v0.1.0`, а `v1.5.0-beta` — с `v1.5.0`.

Go может обращаться к modules в VCS через tags, branches или revisions, не соответствующие этим conventions. Однако в main module command `go` автоматически преобразует revision names в canonical versions и удаляет build metadata suffixes, кроме `+incompatible`. Результатом может быть [pseudo-version](#pseudo-versions). Например:

```bash
go get golang.org/x/net@daa7c041
```

может преобразовать commit hash `daa7c041` в `v0.0.0-20191109021931-daa7c04131f5`. Вне main module требуются canonical versions; non-canonical version вроде `master` в `go.mod` вызывает error.

### Pseudo-versions {#pseudo-versions}

**Pseudo-version** — специальным образом отформатированная [pre-release version](#glos-pre-release-version), кодирующая информацию о конкретной revision VCS. Например: `v0.0.0-20191109021931-daa7c04131f5`.

Pseudo-versions могут ссылаться на revisions, для которых отсутствуют semantic-version tags, например на commits development branch до выпуска tag.

Каждая pseudo-version содержит три части:

- base version prefix (`vX.0.0` или `vX.Y.Z-0`), полученный из semantic-version tag, предшествующего revision, либо `vX.0.0`, если такого tag нет;
- timestamp `yyyymmddhhmmss` в UTC; для Git используется commit time, не author time;
- revision identifier: 12-character prefix commit hash либо zero-padded Subversion revision number.

В зависимости от base version используются ровно три формы:

```text
vX.0.0-yyyymmddhhmmss-abcdefabcdef
vX.Y.Z-pre.0.yyyymmddhhmmss-abcdefabcdef
vX.Y.(Z+1)-0.yyyymmddhhmmss-abcdefabcdef
```

Первая применяется, когда known base version отсутствует. Во всех случаях major `X` должен соответствовать major-version suffix module path. Вторая применяется, если base является pre-release вроде `vX.Y.Z-pre`. Третья — если base является release вроде `vX.Y.Z`; например для base `v1.2.3` pseudo-version может быть `v1.2.4-0.20191109021931-daa7c04131f5`.

Один commit может иметь более одной pseudo-version с разными base versions, например если более низкий tag появился после записи pseudo-version. Формы обеспечивают два свойства: pseudo-version с известной base сортируется выше base и ниже следующего tagged version, а pseudo-versions с одинаковым base prefix сортируются chronologically.

Command `go` проверяет pseudo-version, чтобы module author сохранял контроль над ordering: если указан base version, соответствующий semantic-version tag должен быть ancestor revision; timestamp должен совпадать с timestamp revision; revision должна быть ancestor хотя бы одной branch или tag repository. Это предотвращает обход MVS искусственно высокой pseudo-version, flooding proxies бесконечными variants и ссылки на unapproved changes или pull requests.

Pseudo-version не нужно писать вручную. Многие commands принимают commit hash или branch и автоматически преобразуют их в pseudo-version либо tagged version:

```bash
go get example.com/mod@master
go list -m -json example.com/mod@abcd1234
```

### Major version suffixes {#major-version-suffixes}

Начиная с major version 2 module paths обязаны иметь **major version suffix** вроде `/v2`, соответствующий major version. Например, module `example.com/mod` в `v1.0.0` должен иметь path `example.com/mod/v2` в `v2.0.0`.

Major version suffixes реализуют [import compatibility rule](https://research.swtch.com/vgo-import):

> Если старый package и новый package имеют один и тот же import path, новый package должен быть backwards compatible со старым.

Новая major version по определению может содержать incompatible changes, поэтому начиная с `v2` packages должны получать новые import paths. Так как module path — prefix package import paths, suffix module path обеспечивает отдельные import paths для несовместимых major versions.

Suffixes не допускаются для `v0` и `v1`: `v0` нестабильна и не имеет compatibility guarantee, а `v1` обычно служит обязательством compatibility относительно последней `v0`, а не указанием incompatible changes.

Special case: paths, начинающиеся с `gopkg.in/`, всегда имеют major version suffix даже для `v0` и `v1`, причём suffix начинается с точки, а не slash, например `gopkg.in/yaml.v2`.

Suffixes позволяют нескольким major versions одного module сосуществовать в одной build. Это важно, например, при diamond dependency problem. Разные incompatible major versions имеют разные module paths и рассматриваются как отдельные modules.

Многие проекты выпускали `v2+` до modules без major version suffix. Такие versions обозначаются build tag `+incompatible`, например `v2.0.0+incompatible`. См. [Compatibility with non-module repositories](#non-module-compat).

### Resolving a package to a module {#resolve-pkg-mod}

Когда command `go` загружает package по package path, она должна определить module, который предоставляет этот package.

Сначала command `go` ищет в [build list](#glos-build-list) modules, paths которых являются prefixes package path. Например, для package `example.com/a/b`, если в build list есть module `example.com/a`, command проверит directory `b` этого module. Directory считается package, если содержит хотя бы один `.go` file; build constraints на этом этапе не применяются. Если package предоставляет ровно один module build list, используется он. Если не предоставляет ни один или предоставляют два и более, возникает error. Flag `-mod=mod` разрешает command искать новые modules для missing packages и обновлять `go.mod`/`go.sum`; `go get` и `go mod tidy` делают это автоматически.

При поиске нового module command учитывает `GOPROXY`, `GOPRIVATE` и `GONOPROXY`. Для каждого source в `GOPROXY` запрашивается latest version каждого module path, который потенциально может предоставить package, то есть каждого prefix package path. Каждый успешно найденный module скачивается, и проверяется наличие package. Если package найден в нескольких modules, используется module с самым длинным path. Если modules найдены, но package в них отсутствует, сообщается error. Если modules не найдены, command переходит к следующему source `GOPROXY`.

Например, при поиске `golang.org/x/net/html` и `GOPROXY=https://corp.example.com,https://proxy.golang.org` могут параллельно запрашиваться latest versions:

```text
golang.org/x/net/html
golang.org/x/net
golang.org/x
golang.org
```

сначала у `corp.example.com`, затем — если все requests завершились 404/410 — у `proxy.golang.org`.

После нахождения подходящего module command добавляет `require` с его path и version в `go.mod` main module, чтобы при будущих builds использовался тот же module/version. Если найденный package не импортируется package main module, requirement получает `// indirect`.

## `go.mod` files {#go-mod-file}

Module определяется UTF-8 text file `go.mod` в module root. File line-oriented: каждая line содержит одну directive — keyword и arguments.

```text
module example.com/my/thing

go 1.23.0

require example.com/other/thing v1.0.2
require example.com/new/thing/v2 v2.3.4
exclude example.com/old/thing v1.2.3
replace example.com/bad/thing v1.4.5 => example.com/good/thing v1.4.5
retract [v1.9.0, v1.9.5]
```

Одинаковый leading keyword соседних lines можно вынести в block, подобно Go imports:

```text
require (
    example.com/new/thing/v2 v2.3.4
    example.com/old/thing v1.2.3
)
```

`go.mod` задуман human-readable и machine-writable. `go get` может upgrade/downgrade dependencies, commands, загружающие module graph, могут автоматически обновлять `go.mod`, `go mod edit` выполняет low-level edits, а package [`golang.org/x/mod/modfile`](https://pkg.go.dev/golang.org/x/mod/modfile) позволяет выполнять те же операции программно.

`go.mod` обязателен для main module и replacement module, заданного local file path. Module без явного `go.mod` всё ещё может быть dependency или replacement по module path/version; см. [Compatibility with non-module repositories](#non-module-compat).

### Lexical elements {#go-mod-file-lexical}

Parser разбивает `go.mod` на whitespace, comments, punctuation, keywords, identifiers и strings.

Whitespace: space U+0020, tab U+0009, carriage return U+000D и newline U+000A. Всё, кроме newline, служит только разделителем tokens; newline — significant token.

Comments начинаются с `//` и продолжаются до end of line. `/* */` comments запрещены.

Punctuation tokens: `(`, `)` и `=>`.

Keywords различают directives. Grammar ниже включает `module`, `go`, `tool`, `ignore`, `require`, `exclude`, `replace`, `retract`; поддерживаемые Go versions также распознают описанные ниже `toolchain` и `godebug` directives.

Identifiers — sequences non-whitespace characters, например module paths или semantic versions.

Strings бывают interpreted (`"..."`) и raw (между grave accents). В interpreted string backslash вместе со следующим character образует escape sequence; `\"` не завершает string. Unquoted value interpreted string заменяет каждый escape sequence character'ом после backslash: например `\"` становится `"`, а `\n` — `n`. В raw string backslashes специального значения не имеют.

Identifiers и strings взаимозаменяемы в grammar `go.mod`.

### Module paths and versions {#go-mod-file-ident}

Большинство identifiers/strings в `go.mod` — module paths или versions.

Module path обязан удовлетворять ограничениям:

- состоит из одного или нескольких non-empty path elements, разделённых `/`, и не начинается/заканчивается slash;
- каждый element содержит ASCII letters, ASCII digits и ограниченную ASCII punctuation `-`, `.`, `_`, `~`;
- element не начинается и не заканчивается точкой;
- prefix element до первой точки не должен быть Windows reserved file name независимо от case (`CON`, `com1`, `NuL` и т. п.);
- тот же prefix не должен заканчиваться tilde и одной или несколькими digits, например `EXAMPL~1.COM`.

Если path должен загружаться network — например в `require` без replacement или справа в non-local `replace` — действуют дополнительные требования: leading path element, обычно domain, содержит только lowercase ASCII letters, digits, dots и hyphens, имеет хотя бы одну dot и не начинается hyphen; final element вида `/vN`, где `N` выглядит numeric, не может иметь leading zero, быть `/v1` или содержать dots. Для `gopkg.in/` вместо этого действуют conventions самого сервиса.

Versions в `go.mod` могут быть canonical или non-canonical. Canonical version начинается с `v` и следует Semantic Versioning 2.0.0. Большинство других identifiers/strings допустимы как non-canonical version, но только в `go.mod` main module; command `go` при automatic update старается заменить их canonical equivalents. В `require`, `replace`, `exclude` final path element должен быть совместим с major version.

### Grammar {#go-mod-file-grammar}

Syntax `go.mod` задаётся EBNF:

```ebnf
GoMod = { Directive } .
Directive = ModuleDirective |
            GoDirective |
            ToolDirective |
            IgnoreDirective |
            RequireDirective |
            ExcludeDirective |
            ReplaceDirective |
            RetractDirective .
```

Newlines, identifiers и strings обозначаются `newline`, `ident`, `string`. Module paths и versions — `ModulePath`, `Version`:

```ebnf
ModulePath = ident | string . /* see restrictions above */
Version = ident | string .    /* see restrictions above */
```

### `module` directive {#go-mod-file-module}

`module` определяет path main module. В `go.mod` должна быть ровно одна `module` directive.

```ebnf
ModuleDirective = "module" ( ModulePath | "(" newline ModulePath newline ")" ) newline .
```

```text
module golang.org/x/net
```

#### Deprecation {#go-mod-file-module-deprecation}

Module можно пометить deprecated block comment'ов, содержащим `Deprecated:` — case-sensitive — в начале paragraph. Message начинается после colon и продолжается до end of paragraph. Comments могут находиться непосредственно перед `module` либо после неё на той же line.

```text
// Deprecated: use example.com/mod/v2 instead.
module example.com/mod
```

Начиная с Go 1.17 `go list -m -u` проверяет deprecation всех modules build list, а `go get` — modules, нужные packages из command line. Для получения deprecation command загружает `go.mod` version, соответствующей `@latest`, без учёта retractions/exclusions; из того же file загружается список retracted versions.

Author может добавить comment и выпустить новую version, а в более высокой version изменить или удалить message. Deprecation относится ко всем minor versions одного module; major versions с отдельными module paths рассматриваются отдельно. Для отдельных minor/patch versions обычно подходит `retract`.

### `go` directive {#go-mod-file-go}

`go` указывает version Go, semantics которой предполагает module. Version должна быть valid Go version, например `1.14`, `1.21rc1`, `1.23.0`.

Directive задаёт minimum Go version для использования module. До Go 1.21 она была advisory; начиная с Go 1.21 toolchains отказываются использовать modules, объявляющие более новую version. Она также участвует в выборе toolchain.

Directive ограничивает language features packages module: compiler отвергает features, появившиеся после указанной version. При попытке старого compiler собрать package с newer syntax diagnostic указывает, что module написан для более новой Go version.

Она также меняет behavior command `go`:

- с `go 1.14` может автоматически включаться vendoring при согласованном `vendor/modules.txt`;
- с `go 1.16` pattern `all` соответствует только packages, transitively imported packages/tests main module; ранее включались также tests dependencies и дальше;
- с `go 1.17` `go.mod` содержит explicit `require` для каждого module, предоставляющего package transitively imported main module package/test; indirect requirements обычно выделяются в отдельный block; это включает graph pruning и lazy loading; `go mod vendor` не помещает `go.mod`/`go.sum` dependencies в vendor и записывает их Go versions в `vendor/modules.txt`;
- с `go 1.21` line объявляет обязательный minimum Go, должна быть не ниже `go` всех dependencies, command больше не пытается поддерживать previous older version и аккуратнее сохраняет `go.mod` checksums в `go.sum`.

В file допускается максимум одна `go` directive. Большинство commands добавляют её с current Go version, если line отсутствует. Если directive отсутствует, предполагается `go 1.16`.

```ebnf
GoDirective = "go" GoVersion newline .
GoVersion = string | ident .  /* valid release version; see above */
```

```text
go 1.23.0
```

### `toolchain` directive {#go-mod-file-toolchain}

`toolchain` объявляет suggested Go toolchain для main module. Suggested version не может быть ниже required version из `go`. Directive действует только когда module является main и default toolchain старее suggested.

Для reproducibility command `go` записывает собственное toolchain name в `toolchain` line всякий раз, когда обновляет `go` version в `go.mod`, обычно во время `go get`.

```ebnf
ToolchainDirective = "toolchain" ToolchainName newline .
ToolchainName = string | ident .  /* valid toolchain name */
```

```text
toolchain go1.21.0
```

Подробнее: [[../toolchain|Go toolchains]].

### `godebug` directive {#go-mod-file-godebug}

`godebug` задаёт одну GODEBUG setting, применяемую, когда module является main. Lines может быть несколько и их можно группировать. Указывать несуществующий GODEBUG key в main module — error. Effect `godebug key=value` эквивалентен тому, как если бы каждый compiling main package содержал `//go:debug key=value`.

```ebnf
GodebugDirective = "godebug" ( GodebugSpec | "(" newline { GodebugSpec } ")" newline ) .
GodebugSpec = GodebugKey "=" GodebugValue newline.
GodebugKey = GodebugChar { GodebugChar }.
GodebugValue = GodebugChar { GodebugChar }.
GodebugChar = any non-space character except , " ` ' (comma and quotes).
```

```text
godebug default=go1.21
godebug (
	panicnil=1
	asynctimerchan=0
)
```

Подробнее: [[../godebug|GODEBUG]].

### `require` directive {#go-mod-file-require}

`require` объявляет minimum required version dependency. Для каждой required module version command `go` загружает её `go.mod`, включает requirements и затем применяет MVS для build list.

Command автоматически добавляет `// indirect` некоторым requirements. Comment означает, что никакой package required module не imported directly package main module.

Если `go` ≤1.16, indirect requirement добавляется, когда selected version выше version, уже implied transitively другими dependencies — например после explicit upgrade, удаления другой dependency или из-за dependency без корректного requirement. При `go 1.17+` indirect requirement добавляется для каждого module, предоставляющего package, imported даже indirect package/test main module либо переданного `go get`; это обеспечивает graph pruning и lazy loading.

```ebnf
RequireDirective = "require" ( RequireSpec | "(" newline { RequireSpec } ")" newline ) .
RequireSpec = ModulePath Version newline .
```

```text
require golang.org/x/net v1.2.3

require (
    golang.org/x/crypto v1.4.5 // indirect
    golang.org/x/text v1.6.7
)
```

### `tool` directive {#go-mod-file-tool}

Начиная с Go 1.24 `tool` добавляет package как dependency current module и делает его доступным через `go tool`, когда current working directory находится в module либо workspace, содержащем module. Если tool package находится вне current module, нужен `require`, задающий version.

Meta-pattern `tool` разрешается в список tools из current `go.mod`, а в workspace mode — в union tools всех modules workspace.

```ebnf
ToolDirective = "tool" ( ToolSpec | "(" newline { ToolSpec } ")" newline ) .
ToolSpec = ModulePath newline .
```

```text
tool golang.org/x/tools/cmd/stringer

tool (
    example.com/module/cmd/a
    example.com/module/cmd/b
)
```

### `ignore` directive {#go-mod-file-ignore}

`ignore` заставляет command `go` игнорировать slash-separated directory paths и всё recursively contained при matching package patterns.

Если path начинается `./`, он interpreted относительно module root; указанная directory и всё внутри исключаются. Иначе игнорируется directory с таким path на любой depth module и всё её содержимое.

```ebnf
IgnoreDirective = "ignore" ( IgnoreSpec | "(" newline { IgnoreSpec } ")" newline ) .
IgnoreSpec = RelativeFilePath newline .
RelativeFilePath = /* slash-separated relative file path */ .
```

```text
ignore ./node_modules

ignore (
    static
    content/html
    ./third_party/javascript
)
```

### `exclude` directive {#go-mod-file-exclude}

`exclude` запрещает command `go` загружать конкретную module version.

Начиная с Go 1.16, если version из `require` любого `go.mod` исключена `exclude` main module, requirement игнорируется; `go get`/`go mod tidy` могут добавить requirement на более высокую version. До Go 1.16 command выбирала next higher non-excluded version из available versions — release/pre-release, но не pseudo-version — что могло быть nondeterministic.

`exclude` действует только в `go.mod` main module и игнорируется в dependencies.

```ebnf
ExcludeDirective = "exclude" ( ExcludeSpec | "(" newline { ExcludeSpec } ")" newline ) .
ExcludeSpec = ModulePath Version newline .
```

```text
exclude golang.org/x/net v1.2.3

exclude (
    golang.org/x/crypto v1.4.5
    golang.org/x/text v1.6.7
)
```

### `replace` directive {#go-mod-file-replace}

`replace` заменяет contents конкретной version module либо всех versions содержимым из другого места. Replacement задаётся другим module path/version или platform-specific file path.

Version слева ограничивает replacement только этой version; без version заменяются все versions. Local path справа должен быть absolute или начинаться `./`/`../`, указывать module root с `go.mod`, а replacement version в таком случае опускается. Non-local path справа обязан быть valid module path и иметь version; та же replacement module version не должна одновременно присутствовать в build list.

Если replacement module имеет `go.mod`, его `module` directive должна совпадать с заменяемым module path. `replace` из dependencies игнорируются. В workspace с несколькими main modules применяются их `go.mod`; conflicting replacements запрещены и должны быть устранены или overridden через `go.work`.

`replace` сам по себе не добавляет module в graph: нужна `require` edge из main module или dependency.

```ebnf
ReplaceDirective = "replace" ( ReplaceSpec | "(" newline { ReplaceSpec } ")" newline ) .
ReplaceSpec = ModulePath [ Version ] "=>" FilePath newline
            | ModulePath [ Version ] "=>" ModulePath Version newline .
FilePath = /* platform-specific relative or absolute file path */
```

```text
replace golang.org/x/net v1.2.3 => example.com/fork/net v1.4.5

replace (
    golang.org/x/net v1.2.3 => example.com/fork/net v1.4.5
    golang.org/x/net => example.com/fork/net v1.4.5
    golang.org/x/net v1.2.3 => ./fork/net
    golang.org/x/net => ./fork/net
)
```

### `retract` directive {#go-mod-file-retract}

`retract` указывает, что version или closed range versions module не должны использоваться как dependencies, например из-за premature publication или серьёзной ошибки. Retracted versions должны оставаться доступными в repositories/proxies, чтобы не ломать existing builds.

Users не будут автоматически upgrade'иться к retracted version через `go get`, `go mod tidy` и другие commands. Existing builds продолжают работать; warnings показываются, например, `go list -m -u` и `go get`.

Чтобы retract version, author добавляет directive и публикует новую higher release/pre-release, так чтобы `@latest` до применения retractions указывал на неё. Command читает retractions из version, которую показывает `go list -m -retracted $modpath@latest`. Retracted versions скрыты из `go list -m -versions` без `-retracted` и исключаются из queries `@>=...`, `@latest`.

Version с retractions может retract саму себя. Если highest version retracts itself, `@latest` после исключения retracted versions может разрешиться в lower version.

```text
retract (
    v1.0.0 // Published accidentally.
    v1.0.1 // Contains retractions only.
)
```

После этого `@latest` может выбрать, например, `v0.9.5`.

Single version эквивалентна interval с одинаковыми bounds; range записывается `[low, high]`. У каждой directive рекомендуется rationale comment, непосредственно перед line или после неё; comment над block применяется к entries без собственных comments.

```ebnf
RetractDirective = "retract" ( RetractSpec | "(" newline { RetractSpec } ")" newline ) .
RetractSpec = ( Version | "[" Version "," Version "]" ) newline .
```

Examples:

```text
retract v1.0.0
retract [v1.0.0, v1.9.9]
retract (
    v1.0.0
    [v1.0.0, v1.9.9]
)
```

Возврат к unversioned state после premature `v1.0.0`:

```text
retract [v0.0.0, v1.0.1] // assuming v1.0.1 contains this retraction.
```

Удаление всех pseudo- и tagged versions до `v0.15.2`:

```text
retract [v0.0.0-0, v0.15.2]  // assuming v0.15.2 contains this retraction.
```

Directive добавлена в Go 1.16; Go 1.15 и ниже сообщают error для неё в main `go.mod` и игнорируют её в dependencies.

### Automatic updates {#go-mod-file-updates}

Большинство commands сообщают error, если `go.mod` неполон или не соответствует reality. `go get` и `go mod tidy` исправляют большинство проблем; `-mod=mod` у module-aware commands разрешает автоматически исправлять `go.mod`/`go.sum`.

Например, при non-canonical requirements вроде `v1` или branch `dev`, excluded version и redundant indirect requirements update может: преобразовать `v1` в `v1.0.0`, branch `dev` — в pseudo-version, заменить excluded version next available, удалить redundant/misleading requirements или сохранить их как direct requirements, если packages main module их import. В конце file приводится к canonical formatting; command не переписывает `go.mod`, если требовалось лишь formatting.

Поскольку module graph задаёт meaning imports, commands, загружающие packages, используют `go.mod` и могут требовать его update: `go build`, `go get`, `go install`, `go list`, `go test`, `go mod tidy`.

В Go 1.15 и ниже `-mod=mod` был default. Начиная с Go 1.16 default behavior эквивалентно `-mod=readonly`: если нужны изменения, command сообщает error и предлагает fix.

## Minimal version selection (MVS) {#minimal-version-selection}

Go использует algorithm **Minimal Version Selection (MVS)** для выбора module versions build. Подробное описание: [Minimal Version Selection](https://research.swtch.com/vgo-mvs) Russ Cox.

Conceptually MVS работает на directed graph modules, заданном `go.mod`. Vertex — module version. Edge — minimum required dependency version из `require`. Graph модифицируется `exclude`/`replace` main module(s) и `replace` workspace. Output — **build list**, то есть module versions для build.

MVS начинает с main modules — special vertices без version — и traverses graph, отслеживая highest required version каждого module path. Highest encountered versions образуют build list: это минимальные versions, удовлетворяющие всем requirements.

Build list можно посмотреть `go list -m all`. В отличие от некоторых dependency managers, он не сохраняется lock file: MVS deterministic, а появление новых dependency versions само по себе не меняет build list, поэтому list вычисляется в начале каждой module-aware command.

Например, main требует A 1.2 и B 1.2; A 1.2 требует C 1.3, B 1.2 — C 1.4; обе C требуют D 1.2. MVS загрузит соответствующие `go.mod` и выберет A 1.2, B 1.2, C 1.4, D 1.2. Более высокие available B/D не выбираются, потому что никто их не требует.

### Replacement {#mvs-replace}

Contents module, включая `go.mod`, могут заменяться `replace` main `go.mod` или workspace `go.work`. Replacement может относиться к одной version или всем versions. Так как replacement module может иметь другие dependencies, replacement изменяет module graph.

Если, например, C 1.4 заменена R, а R требует D 1.3 вместо D 1.2, build list будет содержать C 1.4 как replaced module и D 1.3.

### Exclusion {#mvs-exclude}

`exclude` main module исключает конкретную version и изменяет graph. Requirement на исключённую version перенаправляется к следующей higher version. Например, если C 1.3 исключена, requirement A 1.2 → C 1.3 обрабатывается как requirement на C 1.4.

### Upgrades {#mvs-upgrade}

`go get` может upgrade набор modules. Для upgrade command перед MVS добавляет edges от visited versions к upgraded versions. Это может добавить/remove indirect dependencies. Чтобы сохранить upgrades, command обновляет `require` main `go.mod`, включая `// indirect` requirements на transitive modules, если без них selected versions были бы ниже.

### Downgrade {#mvs-downgrade}

`go get` также downgrade modules. Для downgrade versions выше target удаляются из graph, а вместе с ними versions других modules, зависящие от удалённых versions. Requirement main module меняется на предыдущую version, если она есть, иначе удаляется.

`go get module@none` удаляет dependency целиком как специальный downgrade: из graph удаляются все versions named module.

## Module graph pruning {#graph-pruning}

Если main module имеет `go 1.17+`, module graph включает только immediate requirements каждого dependency module, который сам указывает `go 1.17+`, если только эта dependency version не требуется transitively другим module с `go 1.16` или ниже. Transitive dependencies modules `go 1.17+` **pruned** из graph.

Так как `go 1.17` `go.mod` содержит `require` для каждого dependency, нужного для build package/test module, pruned graph содержит всё, что нужно `go build`/`go test` для packages dependencies, явно required main module. Module, не нужный ни одному package/test, не может влиять на runtime behavior packages и поэтому его pruned dependencies только создавали бы interference между unrelated modules.

Modules, requirements которых pruned, всё равно присутствуют в module graph и выводятся `go list -m all`; selected versions известны. Packages из них можно загрузить, например как test transitive dependencies. Но command не всегда может определить satisfied dependencies такого module, поэтому arguments `go build`/`go test` не могут напрямую включать packages module с pruned requirements. `go get` может promote module в explicit dependency.

Так как Go 1.16 и ниже pruning не поддерживали, для module с `go 1.16-` включается полный transitive closure, в том числе dependencies `go 1.17+`.

`go.sum`, записанный `go mod tidy`, по default включает checksums, необходимые Go version на одну ниже version из `go` directive. Поэтому `go 1.17` module включает sums полного graph, загружаемого Go 1.16, а `go 1.18` — только sums pruned graph Go 1.17. `-compat` позволяет изменить эту version.

### Lazy module loading {#lazy-loading}

Более полные requirements, добавленные для pruning, позволяют optimization **lazy module loading**. Для main module `go 1.17+` command не загружает полный graph до тех пор, пока это не понадобится: начинает с `go.mod` main module и пытается загрузить packages, используя только его requirements.

Если imported package — например dependency test package вне main module — среди них не найден, оставшаяся часть graph загружается on demand. Если все imports найдены без graph, затем загружаются только `go.mod` modules, содержащих эти packages, и их requirements сверяются с main module на local consistency. Inconsistency возможна после VCS merge, manual edit или local filesystem replacements.

Design details: [lazy module loading proposal](https://go.googlesource.com/proposal/+/master/design/36460-lazy-module-loading.md).

## Workspaces {#workspaces}

**Workspace** — collection modules on disk, используемых как main modules при MVS.

Workspace может быть объявлен [`go.work`](#go-work-file), содержащим relative paths module directories. Без `go.work` workspace состоит из одного module, содержащего current directory.

Большинство `go` subcommands, работающих с modules, действуют на set текущего workspace. `go mod init`, `go mod why`, `go mod edit`, `go mod tidy`, `go mod vendor` и `go get` всегда работают с одним main module.

Workspace context определяется сначала `GOWORK`. `GOWORK=off` включает single-module context. Если variable пустая/unset, command ищет `go.work` в current directory и successive parents. Если file найден — используется его workspace, иначе единственный containing module. Если `GOWORK` задаёт path существующего file с suffix `.work`, workspace mode включается; любое другое non-empty value — error. `go env GOWORK` показывает используемый `go.work` либо empty вне workspace mode.

### `go.work` files {#go-work-file}

`go.work` — UTF-8 line-oriented file. Каждая line содержит directive.

```text
go 1.23.0

use ./my/first/thing
use ./my/second/thing

replace example.com/bad/thing v1.4.5 => example.com/good/thing v1.4.5
```

Keywords можно factor в blocks:

```text
use (
    ./my/first/thing
    ./my/second/thing
)
```

`go work init`, `go work use`, `go work edit` управляют file; package `golang.org/x/mod/modfile` позволяет делать это программно. Command поддерживает `go.work.sum`, где записывает hashes workspace dependencies, отсутствующие в collective `go.sum` workspace modules.

Обычно commit `go.work` в VCS не рекомендуется: checked-in file может override developer workspace из parent directory и вызвать confusion; CI может выбрать/test не те dependency versions, которые увидит внешний consumer module. Однако commit может быть уместен, если modules repository разрабатываются исключительно вместе; тогда authors всё равно должны корректно test/release individual modules.

### Lexical elements {#go-work-file-lexical}

Lexical elements `go.work` определяются так же, как [`go.mod`](#go-mod-file-lexical).

### Grammar {#go-work-file-grammar}

```ebnf
GoWork = { Directive } .
Directive = GoDirective |
            ToolchainDirective |
            UseDirective |
            ReplaceDirective .
```

```ebnf
ModulePath = ident | string . /* see restrictions above */
Version = ident | string .    /* see restrictions above */
```

### `go` directive {#go-work-file-go}

Valid `go.work` обязан содержать `go` directive. Она задаёт Go toolchain version, для semantics которой предназначен file; future toolchains интерпретируют format по указанной version. В file максимум одна directive.

```ebnf
GoDirective = "go" GoVersion newline .
GoVersion = string | ident .  /* valid release version; see above */
```

```text
go 1.23.0
```

### `toolchain` directive {#go-work-file-toolchain}

Объявляет suggested toolchain workspace и действует, если default toolchain старее suggested.

```ebnf
ToolchainDirective = "toolchain" ToolchainName newline .
ToolchainName = string | ident .  /* valid toolchain name */
```

```text
toolchain go1.21.0
```

### `godebug` directive {#go-work-file-godebug}

`godebug` задаёт GODEBUG setting для workspace с тем же syntax/effect, что в `go.mod`. Когда workspace используется, `godebug` directives из `go.mod` игнорируются.

### `use` directive {#go-work-file-use}

`use` добавляет module on disk в set main modules workspace. Argument — relative path directory, содержащей `go.mod`. `use` не добавляет автоматически nested modules; для них нужны отдельные directives.

```ebnf
UseDirective = "use" ( UseSpec | "(" newline { UseSpec } ")" newline ) .
UseSpec = FilePath newline .
FilePath = /* platform-specific relative or absolute file path */
```

```text
use ./mymod  // example.com/mymod

use (
    ../othermod
    ./subdir/thirdmod
)
```

### `replace` directive {#go-work-file-replace}

Workspace `replace` аналогичен `go.mod`: заменяет one/all versions module. Wildcard replace в `go.work` overrides version-specific replace в `go.mod`; workspace replacements override replacements того же module/version во всех workspace modules.

```ebnf
ReplaceDirective = "replace" ( ReplaceSpec | "(" newline { ReplaceSpec } ")" newline ) .
ReplaceSpec = ModulePath [ Version ] "=>" FilePath newline
            | ModulePath [ Version ] "=>" ModulePath Version newline .
FilePath = /* platform-specific relative or absolute file path */
```

```text
replace golang.org/x/net v1.2.3 => example.com/fork/net v1.4.5

replace (
    golang.org/x/net v1.2.3 => example.com/fork/net v1.4.5
    golang.org/x/net => example.com/fork/net v1.4.5
    golang.org/x/net v1.2.3 => ./fork/net
    golang.org/x/net => ./fork/net
)
```

## Compatibility with non-module repositories {#non-module-compat}

Для плавного перехода от GOPATH к modules command `go` умеет загружать и build packages в module-aware mode из repositories без `go.mod`.

При direct download module command находит repository URL, maps version в revision и извлекает archive. Если module path совпадает repository root path и root repository не содержит `go.mod`, command synthesizes `go.mod` в module cache только с `module` directive. Так как synthetic file не содержит `require`, downstream modules могут потребовать дополнительных `// indirect` requirements для deterministic builds.

При download через proxy `go.mod` загружается отдельно; proxy должен предоставить synthetic `go.mod`, если original отсутствует.

### `+incompatible` versions {#incompatible-versions}

Module major version 2+ должен иметь matching suffix module path, но до появления modules многие repositories уже имели tags `v2+`. Для compatibility command добавляет suffix `+incompatible` к versions major 2+, у которых нет `go.mod`. Это означает, что version относится к тому же module path, что более ранние major versions, и command может автоматически upgrade к higher `+incompatible`, даже если build сломается.

```text
require example.com/m v4.1.2+incompatible
```

`v4.1.2+incompatible` соответствует repository tag `v4.1.2`; module должен быть в repository root, `go.mod` должен отсутствовать. Repository может иметь lower majors вроде `v1.5.2`.

После миграции repository, уже имевшего `v2+`, обычно следует выпустить новую major version с correct path, например `example.com/m/v5` и `v5.0.0`, обновив imports.

`+incompatible` не должен быть частью repository tag; tag `v4.1.2+incompatible` игнорируется. Suffix может встречаться и в pseudo-version, например `v2.0.1-20200722182040-012345abcdef+incompatible`.

### Minimal module compatibility {#minimal-module-compatibility}

Major-version suffix создаёт tension с GOPATH mode: module-mode package может импортироваться как `example.com/repo/v2/sub`, в то время как repository без physical `/v2` directory в GOPATH лежит в `$GOPATH/src/example.com/repo/sub`.

Чтобы packages, migrated to modules, могли импортировать друг друга и в GOPATH mode без major-version subdirectory, **minimal module compatibility** добавлена в Go 1.11 и backported в Go 1.9.7/1.10.3.

При resolution import `$modpath/$vn/$dir` в GOPATH mode, где `$modpath` — valid module path, `$vn` — major version suffix, `$dir` optional subdirectory, import может быть redirected к `$GOPATH[d]/src/$modpath/$dir`, если package с suffix отсутствует в relevant vendor/GOPATH, рядом с importer есть `go.mod`, physical `$modpath/$vn` не существует ни в одном GOPATH root, а `$GOPATH[d]/src/$modpath/go.mod` объявляет path `$modpath/$vn`.

## Module-aware commands {#mod-commands}

Большинство `go` commands работают в module-aware или GOPATH mode. В module-aware mode dependencies определяются `go.mod` и обычно читаются из module cache; в GOPATH mode modules игнорируются, а dependencies ищутся в `vendor`/GOPATH.

Начиная с Go 1.16 module-aware mode default независимо от наличия `go.mod`. `GO111MODULE` управляет mode:

- `off`: игнорировать `go.mod`, использовать GOPATH mode;
- `on` или unset: module-aware mode даже без `go.mod`; не все commands работают вне module;
- `auto`: module-aware только при наличии `go.mod` в current/parent; в Go 1.15 и ниже это был default. `go mod` subcommands и `go install` с version query всё равно используют module-aware mode.

В module-aware mode `GOPATH` больше не определяет imports, но по-прежнему хранит downloaded modules в `$GOPATH/pkg/mod` и installed commands в `$GOPATH/bin`, если `GOBIN` не задан.

### Build commands {#build-commands}

Module-aware являются все commands, загружающие package information: `go build`, `go fix`, `go generate`, `go install`, `go list`, `go run`, `go test`, `go vet`.

Общие flags:

- `-mod=mod`: игнорировать vendor и автоматически update `go.mod`;
- `-mod=readonly`: игнорировать vendor и error, если `go.mod` требует update;
- `-mod=vendor`: использовать vendor без network/module cache;
- default: при `go 1.14+` и наличии vendor используется vendor, иначе readonly; `go get` отвергает `-mod`, поскольку управляет dependencies только как `mod`;
- `-modcacherw`: новые module-cache directories делаются read-write вместо read-only; `go clean -modcache` умеет удалять cache без этого flag;
- `-modfile=file.mod`: читать/write alternate `.mod`; настоящий `go.mod` всё равно нужен для определения root, но не читается; соответствующий alternate sum file получается заменой `.mod` на `.sum`.

### Vendoring {#vendoring}

`go mod vendor` строит `vendor` в main module root и копирует packages, нужные builds/tests main module. Packages, импортируемые только tests packages вне main module, не включаются. Build constraints кроме `ignore` при построении vendor не учитываются.

Создаётся `vendor/modules.txt` со списком packages/module versions. При enabled vendoring file служит источником module version information для `go list -m` и `go version -m`; command проверяет его consistency с `go.mod`.

При `go 1.14+` consistent root `vendor` используется автоматически; явно включить можно `-mod=vendor`, выключить — `-mod=readonly`/`-mod=mod`. В vendor mode build commands не используют network/cache. `go mod download`, `go mod tidy`, `go get` продолжают работать с modules/cache как обычно. Vendor directories dependencies и other locations игнорируются и не включаются в module zip.

### `go get` {#go-get}

Usage:

```text
go get [-d] [-t] [-u] [-tool] [build flags] [packages]
```

Examples:

```bash
# Upgrade a specific module.
go get golang.org/x/net

# Upgrade modules that provide packages imported by packages in the main module.
go get -u ./...

# Upgrade or downgrade to a specific version of a module.
go get golang.org/x/text@v0.3.2

# Update to the commit on the module's master branch.
go get golang.org/x/text@master

# Remove a dependency on a module and downgrade modules that require it.
go get golang.org/x/text@none

# Upgrade the minimum required Go version for the main module.
go get go

# Upgrade the suggested Go toolchain, leaving the minimum Go version alone.
go get toolchain

# Upgrade to the latest patch release of the suggested Go toolchain.
go get toolchain@patch
```

`go get` обновляет dependencies main module в `go.mod`. Arguments могут быть packages, patterns или module paths. Package обновляет providing module; pattern сначала expands; module без root package обновляет module, но не package. Без arguments command действует как для `.` и может сочетаться с `-u`.

Каждый argument может иметь `@query`: exact version, prefix, branch/tag, revision, `latest`, `upgrade`, `patch`, `none`. Без suffix используется `@upgrade`.

После resolution command добавляет/изменяет/удаляет `require`, чтобы удерживать desired versions. Requirements — minimum versions и могут повышаться из-за других dependencies. Upgrade одного module может поднять transitive modules; downgrade/remove может понизить/remove modules, которые требуют более высокую version. `@none` — special downgrade. Если package main module всё ещё imported из removed module, следующая build может снова добавить requirement. Несовместимые simultaneous requested versions вызывают error.

После selection command проверяет newly selected modules и modules command-line packages на retraction/deprecation и показывает warnings. `go list -m -u all` проверяет весь build list.

Flags pinned source описывает так:

- `-d`: не build/install, только dependency management; использование `go get` без `-d` для installation deprecated с Go 1.17, а с Go 1.18 `-d` всегда effectively enabled;
- `-u`: upgrade modules, предоставляющие direct/indirect imports named packages, до latest, если уже не selected более высокая pre-release;
- `-u=patch`: upgrade только до latest patch текущей major/minor;
- `-t`: учитывать test dependencies named packages; с `-u` обновляет и их;
- `-insecure`: deprecated; вместо него используется `GOINSECURE`;
- `-tool`: добавить matching `tool` line для packages; с `@none` удалить.

Начиная с Go 1.16 для build/install programs рекомендуется `go install`; `go get` сфокусирован на управлении requirements.

### `go install` {#go-install}

Usage:

```text
go install [build flags] [packages]
```

Examples:

```bash
go install golang.org/x/tools/gopls@latest
go install golang.org/x/tools/gopls@v0.6.4
go install golang.org/x/tools/gopls
go install ./cmd/...
```

Command builds/installs named packages. Executables идут в `GOBIN`, default `$GOPATH/bin` или `$HOME/go/bin`; executables в `$GOROOT` — в `$GOROOT/bin`/`$GOTOOLDIR`. Non-executable packages только build/cache.

С Go 1.16 arguments с version suffix (`@latest`, `@v1.0.0`) строятся module-aware с игнорированием current/parent `go.mod`, что позволяет install executable без изменения main module. При наличии version suffix действуют ограничения: arguments должны быть package paths/patterns, а не standard/meta patterns или filesystem paths; suffix у всех один; все packages — из одного module на одной version; package paths должны быть `main`; main module отсутствует; module target не может содержать `replace`/`exclude`, которые меняли бы interpretation как main; не должен требовать higher version самого себя; vendor не используется.

Go 1.15 и ниже version queries у `go install` не поддерживали. Без suffix command использует module/GOPATH context обычным образом. В module-aware context `go install tool` может install все tools current module.

### `go tool` {#go-tool}

```text
go tool [-n] command [args...]
```

```bash
go tool golang.org/x/tools/cmd/stringer
go tool stringer
```

В module mode `go tool` может build/run tools из `tool` directives. Command можно указать full package path или default binary name — last path component без major suffix — если оно unique среди installed tools.

### `go list -m` {#go-list-m}

```text
go list -m [-u] [-retracted] [-versions] [list flags] [modules]
```

```bash
go list -m all
go list -m -versions example.com/m
go list -m -json example.com/m@latest
```

`-m` переключает `go list` с packages на modules. Arguments: modules, patterns с `...`, version queries или `all`, совпадающий со всем build list. Без arguments выводится main module.

При module listing format template применяется к `Module`:

```go
type Module struct {
    Path       string
    Version    string
    Versions   []string
    Replace    *Module
    Time       *time.Time
    Update     *Module
    Main       bool
    Indirect   bool
    Dir        string
    GoMod      string
    GoVersion  string
    Retracted  []string
    Deprecated string
    Error      *ModuleError
}

type ModuleError struct {
    Err string
}
```

Default output — path, version и replacement. Если module replaced, `Replace` описывает replacement, а `Dir` указывает source replacement, не replaced source.

`-u` добавляет available upgrade information и сведения о retraction/deprecation selected version. `-versions` заполняет ordered list known versions; retracted скрыты без `-retracted`. `-retracted` также разрешает retracted versions в version queries и нужен, например, чтобы увидеть highest version независимо от retraction.

Template function `module` принимает path/query и возвращает `Module`; при error поле `Error` non-nil.

### `go mod download` {#go-mod-download}

```text
go mod download [-x] [-json] [-reuse=old.json] [modules]
```

```bash
go mod download
go mod download golang.org/x/mod@v0.2.0
```

Загружает named modules в module cache. Arguments могут быть paths/patterns dependencies main module или `path@query`; без arguments — все dependencies main module. Обычно command `go` скачивает modules automatically, поэтому `download` нужен в основном для prefill cache или подготовки data module proxy.

Без `-json` stdout empty; progress/errors идут stderr. `-json` печатает objects вида:

```go
type Module struct {
    Path     string
    Query    string
    Version  string
    Error    string
    Info     string
    GoMod    string
    Zip      string
    Dir      string
    Sum      string
    GoModSum string
    Origin   any
    Reuse    bool
}
```

`-x` печатает executed commands. `-reuse=old.json` принимает previous `go mod download -json`; command может доказать, что module unchanged, не redownload его и выставить `Reuse=true`. Normal module cache уже обеспечивает такой reuse, flag полезен там, где cache не сохраняется.

### `go mod edit` {#go-mod-edit}

```text
go mod edit [editing flags] [-fmt|-print|-json] [go.mod]
```

Examples:

```bash
go mod edit -replace example.com/a@v1.0.0=./a
go mod edit -dropreplace example.com/a@v1.0.0
go mod edit -go=1.14 -require=example.com/m@v1.0.0 -print
go mod edit -fmt
go mod edit -print tools.mod
go mod edit -json
```

Это low-level CLI для tools/scripts; command читает только один `go.mod` и не получает metadata других modules. Default target — main `go.mod`, но file можно указать явно.

Editing flags выполняются по порядку и могут повторяться: `-module`, `-go=version`, `-require=path@version`, `-droprequire=path`, `-exclude`, `-dropexclude`, `-replace=old[@v]=new[@v]`, `-dropreplace`, `-retract`, `-dropretract`, `-tool`, `-droptool`. `-require` не решает graph constraints, поэтому users обычно должны предпочитать `go get`; `-tool` не добавляет required dependencies, поэтому для users предпочтителен `go get -tool`.

Output flags: `-fmt` — только format; `-print` — stdout вместо write; `-json` — JSON representation. JSON соответствует структурам:

```go
type Module struct {
    Path    string
    Version string
}

type GoMod struct {
    Module  ModPath
    Go      string
    Require []Require
    Exclude []Module
    Replace []Replace
    Retract []Retract
}

type ModPath struct {
    Path       string
    Deprecated string
}

type Require struct {
    Path     string
    Version  string
    Indirect bool
}

type Replace struct {
    Old Module
    New Module
}

type Retract struct {
    Low       string
    High      string
    Rationale string
}

type Tool struct {
    Path string
}
```

Это представляет только сам `go.mod`; для полного build list используется `go list -m -json all`. Package `golang.org/x/mod/modfile` позволяет parse/edit/format file программно.

### `go mod graph` {#go-mod-graph}

```text
go mod graph [-go=version]
```

Печатает module requirement graph с применёнными replacements, по edge на line:

```text
example.com/main example.com/a@v1.1.0
example.com/main example.com/b@v1.2.0
example.com/a@v1.1.0 example.com/b@v1.1.1
example.com/a@v1.1.0 example.com/c@v1.3.0
example.com/b@v1.1.0 example.com/c@v1.1.0
example.com/b@v1.2.0 example.com/c@v1.2.0
```

Каждый vertex — specific module version, edge — minimum requirement. Main module не имеет `@version`. `-go=version` просит загрузить graph по semantics данной Go version, а не `go` directive main module.

### `go mod init` {#go-mod-init}

```text
go mod init [module-path]
```

```bash
go mod init
go mod init example.com/m
```

Создаёт новый `go.mod` в current directory; существовать заранее он не должен. Optional argument — module path. Без него command пытается infer path по import comments `.go` files и current directory, если та находится в GOPATH.

### `go mod tidy` {#go-mod-tidy}

```text
go mod tidy [-e] [-v] [-x] [-diff] [-go=version] [-compat=version]
```

`tidy` синхронизирует `go.mod` с source: добавляет missing requirements для build packages/dependencies, удаляет modules, не предоставляющие relevant packages, добавляет missing `go.sum` entries и удаляет ненужные.

`-e` (Go 1.16+) продолжает работу после package-loading errors; `-v` показывает removed modules; `-x` — executed commands; `-diff` не modifies files, а печатает unified diff и exits non-zero, если diff непустой.

`tidy` рекурсивно загружает все packages main module, все tools и imports, включая imports tests — даже tests в других modules. Он действует так, будто включены все build tags, чтобы учесть platform/custom-tag files, кроме `ignore`; directories `testdata`, names с `.`/`_` не рассматриваются без explicit imports.

После loading для каждого module, предоставляющего package set, должен существовать `require` main `go.mod` — либо, при `go 1.16-`, transitive requirement другого required module. Missing modules добавляются на `latest`, irrelevant requirements удаляются. `// indirect` comments также корректируются.

`-go` меняет `go` directive и соответственно pruning/lazy-loading/indirect requirements. Default `tidy` проверяет, что selected versions не изменятся при graph semantics Go version непосредственно перед version из `go`; `-compat` задаёт проверяемую compatibility version явно.

### `go mod vendor` {#go-mod-vendor}

```text
go mod vendor [-e] [-v] [-o]
```

Строит `vendor` main module root с copies всех packages, нужных builds/tests main module; tests packages вне main module не тянут свои-only imports. Build constraints кроме `ignore` не учитываются.

Создаётся `vendor/modules.txt` с packages и versions. Existing `vendor` удаляется перед reconstruction: local changes делать не следует. Integrity можно проверить повторным `go mod vendor` и отсутствием diff.

`-e` продолжает после loading errors, `-v` печатает vendored modules/packages, `-o` (Go 1.18+) выводит tree в указанную absolute или module-relative directory вместо `vendor`.

### `go mod verify` {#go-mod-verify}

```text
go mod verify
```

Проверяет, что dependencies main module в module cache не изменены после download. Для каждого module build list hash `.zip` и extracted directory сравнивается с hash, записанным при первоначальной загрузке. При успехе печатается `all modules verified`, иначе перечисляются changed modules и exit status non-zero.

Это отличается от обычной `go.sum` verification: module-aware commands сверяют downloaded content с `go.sum`/checksum DB. `go mod verify` проверяет изменения **после** download против cache-recorded hashes. Она не скачивает отсутствующий content и не использует `go.sum` для проверки cached module contents, но может download `go.mod` для MVS и verify эти files через `go.sum`, добавляя missing entries.

### `go mod why` {#go-mod-why}

```text
go mod why [-m] [-vendor] packages...
```

Показывает shortest path import graph от main module к каждому target package. Output — stanzas с `# target`, затем package path chain; для ненужного target — parenthesized note.

```text
$ go mod why golang.org/x/text/language golang.org/x/text/encoding
# golang.org/x/text/language
rsc.io/quote
rsc.io/sampler
golang.org/x/text/language

# golang.org/x/text/encoding
(main module does not need package golang.org/x/text/encoding)
```

`-m` трактует arguments как modules, но всё равно исследует package graph, не graph `go mod graph`. `-vendor` игнорирует imports tests packages вне main module; после Go 1.16 для modules `go 1.16+` effect отсутствует, поскольку `all` уже совпадает с set `go mod vendor`.

### `go version -m` {#go-version-m}

```text
go version [-m] [-v] [file ...]
```

Examples:

```bash
go version
go version ~/go/bin/gopls
go version -m ~/go/bin/gopls
go version -m ~/go/bin/
```

`go version` сообщает Go version, которой собран каждый named executable. Без files — собственную version. Directory обходится recursively; `-v` также сообщает unrecognized files.

`-m` печатает embedded module version information. Example:

```text
/home/jrgopher/go/bin/goimports: go1.14.3
        path    golang.org/x/tools/cmd/goimports
        mod     golang.org/x/tools      v0.0.0-20200518203908-8018eb2c26ba      h1:0Lcy64USfQQL6GAJma8BdHCgeofcchQj+Z7j0SXYAzU=
        dep     golang.org/x/mod        v0.2.0          h1:KU7oHjnv3XNWfa5COkzUifxZmxp1TyI7ImMXqFxLwvQ=
        dep     golang.org/x/xerrors    v0.0.0-20191204190536-9bdfabe68543      h1:E7g+9GITq07hpfrRu66IVDexMakfv52eLZ2CXBWiKr4=
```

`path` — main package path; `mod` — module main package с path/version/sum, при main module version `(devel)` и sum absent; `dep` — linked dependency module; `=>` — replacement предыдущего module: local directory только path, module replacement — path/version/sum; replaced original sum отсутствует. Format table может измениться. Те же данные доступны через `runtime/debug.ReadBuildInfo`.

### `go clean -modcache` {#go-clean-modcache}

```text
go clean [-modcache]
```

`-modcache` удаляет весь module cache, включая unpacked source dependencies. Это обычно лучший способ удаления cache: files/directories default read-only для защиты authenticated content, из-за чего обычный `rm -r` может fail.

`-modcacherw` у build/module-aware commands делает новые cache directories writable; его можно установить глобально через `GOFLAGS`:

```bash
go env -w GOFLAGS=-modcacherw
```

Flag следует использовать осторожно; `go mod verify` обнаруживает изменения cached files.

### Version queries {#version-queries}

Многие commands принимают version query после `@`:

```bash
go get example.com/m@latest
go mod download example.com/m@master
go list -m -json example.com/m@e3702bed2
```

Query может быть exact semantic version (`v1.2.3`); version prefix (`v1`, `v1.2`) выбирающий highest matching; comparison (`<v1.2.3`, `>=v1.5.6`) выбирающий nearest available version — lowest для `>`/`>=`, highest для `<`/`<=`; VCS revision/tag/branch, преобразуемые в tagged или pseudo-version; `latest`; `upgrade`; `patch`.

`latest` выбирает highest release; если releases нет — highest pre-release; если tags нет — pseudo-version tip default branch. `upgrade` похож на latest, но сохраняет currently required higher version, например pre-release. `patch` выбирает latest с теми же major/minor; без current requirement эквивалентен latest, хотя с Go 1.16 `go get @patch` требует current version.

Кроме exact named versions/revisions queries работают по versions `go list -m -versions`, то есть tagged versions без pseudo-versions. Excluded versions и retracted versions latest module игнорируются, кроме explicit `-retracted` scenarios.

Release versions предпочитаются pre-release. Например, при `v1.2.2` и `v1.2.3-pre` `latest` выберет `v1.2.2`; query `<v1.2.4` тоже выберет release `v1.2.2`, хотя pre-release numerically ближе. Если tagged versions отсутствуют, `latest`/`upgrade`/`patch` используют pseudo-version tip default branch; другие queries error.

### Module commands outside a module {#commands-outside}

Module-aware commands обычно выполняются в context main `go.mod`, но часть может работать без него.

| Command | Behavior без `go.mod` |
| --- | --- |
| `go build`, `go doc`, `go fix`, `go fmt`, `go generate`, `go install`, `go list`, `go run`, `go test`, `go vet` | Можно загружать/import/build только standard library packages и `.go` files, явно указанные command line. Packages других modules нельзя build: негде записать requirements для deterministic build. |
| `go get` | Pinned source описывает build/install как обычно, но main module отсутствует, поэтому `replace` и `exclude` не применяются. |
| `go list -m` | Для большинства arguments нужны explicit version queries, кроме `-versions`. |
| `go mod download` | Для большинства arguments нужны explicit version queries. |
| `go mod edit` | Нужен explicit file argument. |
| `go mod graph`, `go mod tidy`, `go mod vendor`, `go mod verify`, `go mod why` | Требуют `go.mod` и error без него. |

### `go work init` {#go-work-init}

```text
go work init [moddirs]
```

Создаёт новый `go.work` в current directory. Optional paths добавляются как `use`; без них создаётся empty workspace. В file также записывается current Go version.

### `go work edit` {#go-work-edit}

```text
go work edit [editing flags] [go.work]
```

Low-level editing для tools/scripts; читает только `go.work`, не lookup modules. Без file ищет `go.work` в current/parents.

Editing flags применяются по порядку и повторяемы: `-fmt`, `-use=path`, `-dropuse=path`, `-replace=old[@v]=new[@v]`, `-dropreplace`, `-go=version`. Output flags `-print` и `-json` печатают результат вместо write.

JSON соответствует:

```go
type Module struct {
    Path    string
    Version string
}

type GoWork struct {
    Go        string
    Directory []Directory
    Replace   []Replace
}

type Use struct {
    Path       string
    ModulePath string
}

type Replace struct {
    Old Module
    New Module
}
```

### `go work use` {#go-work-use}

```text
go work use [-r] [moddirs]
```

Добавляет directories в `go.work`; для existing on-disk module добавляет `use`, для отсутствующего path удаляет соответствующую directive. `-r` recursively ищет modules в argument directories и действует так, будто каждый найденный directory был отдельным argument.

### `go work sync` {#go-work-sync}

```text
go work sync
```

Sync'ит workspace build list обратно в workspace modules. Build list вычисляется MVS по всем transitive dependencies workspace. Затем `go.mod` каждого `use` module переписывается так, чтобы relevant dependency versions были upgrade'нуты до workspace build list. MVS гарантирует, что workspace version каждого module не ниже version individual module.

## Module proxies {#module-proxy}

### `GOPROXY` protocol {#goproxy-protocol}

**Module proxy** — HTTP server, отвечающий на описанные ниже `GET` paths. Query parameters и специальные headers не нужны, поэтому proxy может быть обычным static file server, включая `file://`.

Успех — HTTP 200. Redirects 3xx follow. 4xx/5xx — errors; 404 и 410 означают, что module/version отсутствует на этом proxy, но может быть найден в другом source. Error responses должны быть `text/plain` с charset `utf-8` или `us-ascii`.

`GOPROXY` — ordered list proxy URLs и keywords `direct`/`off`. Separators важны: comma позволяет fallback только после 404/410; pipe — после **любой** error, включая timeout. Это позволяет proxy работать gatekeeper: например, отвечать 403 на unapproved modules и не допускать fallback.

Paths case-encoded: uppercase letter заменяется `!` + lowercase, поэтому `example.com/M` и `example.com/m` различимы на case-insensitive filesystem.

Proxy должен поддерживать:

| Path | Ответ |
| --- | --- |
| `$base/$module/@v/list` | Known versions, одна per line; pseudo-versions не включаются. |
| `$base/$module/@v/$version.info` | JSON metadata `{Version string, Time time.Time}`. Version canonical; Time — creation/commit time. |
| `$base/$module/@v/$version.mod` | `go.mod` указанной version. Если source не имеет `go.mod`, proxy возвращает synthetic file. |
| `$base/$module/@v/$version.zip` | Module zip с content данной version. |
| `$base/$module/@latest` | JSON как `.info` для latest version, если proxy не может получить список через `@v/list`, например для pseudo-version-only repository. |

`$version` в `.info`, `.mod`, `.zip` должен быть valid canonical version. `@latest` должен выбирать latest по правилам version query. Если известны suitable release/pre-release versions из `@v/list`, clients могут не запрашивать `@latest`.

Proxy должен отвечать immutable content для `.mod`/`.zip`: после публикации конкретной version content не меняется. Это важно для authenticated/repeatable builds.

### Communicating with proxies {#communicating-with-proxies}

Для download конкретного module version command сначала получает `.info`; затем `.mod`, чтобы построить graph; `.zip` загружается, когда требуется package source. Content проверяется через `go.sum`/checksum database перед использованием.

При package-to-module resolution command может запрашивать `@v/list`/`@latest` для нескольких prefixes package path. Requests к одному proxy могут выполняться concurrently.

Proxy может mirror modules из VCS либо другого proxy. Local module cache directory `cache/download` соответствует GOPROXY layout и может быть обслужен static HTTP server или `file://` proxy.

### Serving modules directly from a proxy {#serving-from-proxy}

Custom module path может через `<meta name="go-import">` указать VCS value `mod` и URL proxy. Тогда command использует GOPROXY protocol непосредственно по указанному URL, даже если module path обычно потребовал бы VCS discovery.

## Version control systems {#vcs}

Когда proxy не используется или configuration требует direct access, command `go` скачивает source через VCS.

### Finding a repository for a module path {#vcs-find}

Если module path содержит VCS qualifier (`.bzr`, `.fossil`, `.git`, `.hg`, `.svn`) в конце path component, command использует всё до qualifier как repository URL. Например, `example.com/foo.git/bar` означает Git repository `example.com/foo` и module в `bar`. Protocol выбирается по возможностям VCS tool.

Без qualifier command отправляет GET к URL module path с `?go-get=1`, предпочитая HTTPS; HTTP fallback допустим только при `GOINSECURE`:

```text
https://golang.org/x/mod?go-get=1
http://golang.org/x/mod?go-get=1
```

Redirects follow; response status сам по себе игнорируется. Server должен вернуть HTML `<head>` с ранним tag:

```html
<meta name="go-import" content="root-path vcs repo-url [subdirectory]">
```

`root-path` — repository root path либо, при наличии `subdirectory` и Go 1.25+, path, соответствующий этой subdirectory. Он обязан быть exact/prefix requested module path; при non-exact prefix выполняется дополнительный request для verification tags.

`vcs` — supported VCS либо keyword `mod`, означающий GOPROXY protocol. `repo-url` содержит scheme и не содержит `.vcs` qualifier; insecure schemes допускаются только при `GOINSECURE`. Optional `subdirectory` задаёт repository subdirectory, соответствующую `root-path`, и распознаётся только Go 1.25+.

Supported VCS:

| Name | Command | Default GOVCS | Secure schemes |
| --- | --- | --- | --- |
| Bazaar | `bzr` | Private only | `https`, `bzr+ssh` |
| Fossil | `fossil` | Private only | `https` |
| Git | `git` | Public and private | `https`, `git+ssh`, `ssh` |
| Mercurial | `hg` | Public and private | `https`, `ssh` |
| Subversion | `svn` | Private only | `https`, `svn+ssh` |

Например, `golang.org/x/mod?go-get=1` может вернуть:

```html
<meta name="go-import" content="golang.org/x/mod git https://go.googlesource.com/mod">
```

GitHub и другие popular hosts обычно отвечают на такие queries автоматически. После нахождения repository command clone/fetch минимально нужные данные; конкретные VCS commands могут меняться. Для Git обычно можно list versions без download commits и fetch commit без ancestors, хотя иногда ancestors нужны.

### Mapping versions to commits {#vcs-version}

Canonical version вроде `v1.2.3`, `v2.4.0-beta`, `v3.0.0+incompatible` должна соответствовать semantic-version tag repository.

Если module находится в repository root или major-version subdirectory root, tag равен version, например `v0.3.2`. Если module subdirectory non-empty, tag prefix'ится subdirectory и slash: `golang.org/x/tools/gopls` в `gopls` использует tag `gopls/v0.4.0`.

Major number tag должен совпадать с module path suffix. Tag `v2+` может относиться к module без suffix только если `go.mod` отсутствует и module расположен в repository root; такая version получает `+incompatible`, но suffix не должен присутствовать в самом tag.

После создания tag не следует удалять или перемещать: versions authenticated, изменение может привести к security error; content deleted tags может оставаться cached proxies.

### Mapping pseudo-versions to commits {#vcs-pseudo}

Последние 12 characters pseudo-version обычно идентифицируют revision: Git/Mercurial commit hash prefix, Subversion zero-padded revision. Перед checkout command проверяет timestamp и, при наличии base version, что corresponding semantic tag является ancestor commit.

### Mapping branches and commits to versions {#vcs-branch}

Version query может ссылаться на branch/tag/revision. Command преобразует её в canonical version для MVS. Если revision tagged одной или несколькими valid semantic versions, используется highest valid tag, совместимый с target module path. Иначе генерируется pseudo-version, base которой строится от highest valid ancestor tag, если он есть.

### Module directories within a repository {#vcs-dir}

После checkout revision command находит module root. Module path состоит из repository root path, module subdirectory и optional major suffix.

Обычно root module path равен repository root. Для nested module `example.com/monorepo/foo/bar` в repository `example.com/monorepo`, `go.mod` должен находиться в `foo/bar`. Для `/v2` module `go.mod` может быть в `foo/bar` или `foo/bar/v2`. Major-version subdirectories позволяют вести несколько majors в одной branch и полезны для GOPATH compatibility.

После нахождения root command создаёт `.zip` directory contents и извлекает его в cache. Zip не включает vendor directories и nested modules — subdirectories с собственным `go.mod`. Поэтому module не должен ссылаться на files вне own directory/nested modules; например `//go:embed` pattern не может match nested module. Это можно сознательно использовать, чтобы исключить большие testdata files, поместив там отдельный `go.mod`, хотя это может снизить coverage users.

### Special case for LICENSE files {#vcs-license}

Если module не в repository root и в module root нет file ровно `LICENSE`, command при создании zip копирует `LICENSE` repository root, если он есть в той же revision. Special case относится только к имени `LICENSE`, без `.txt` и других extensions, поскольку расширение правила сломало бы existing cryptographic sums. Symlinks в zip не включаются; при необходимости authors могут копировать license files в each module subdirectory.

### Controlling version control tools with `GOVCS` {#vcs-govcs}

Direct VCS execution — потенциальная attack surface. Default command разрешает public downloads только через Git и Mercurial, а private modules — через любой known VCS. Public/private определяется `GOPRIVATE`. Proxy downloads через GOPROXY protocol этим ограничениям не подчиняются.

`GOVCS` задаётся comma-separated rules `pattern:vcslist`; `vcslist` — pipe-separated commands либо `all`/`off`. Pattern — glob `path.Match`, совпадающий с leading elements module/import path. Первое matching rule применяется. Даже `off` не запрещает `mod` scheme proxy origin.

```text
GOVCS=github.com:git,evil.com:off,*:git|hg
```

Здесь GitHub — только Git, `evil.com` — никакого VCS, остальные — Git/Mercurial. Special patterns `public` и `private` используют `GOPRIVATE`. Default эквивалентен:

```text
public:git|hg,private:all
```

Разрешить всё:

```text
GOVCS=*:all
```

Запретить весь VCS direct access:

```text
GOVCS=*:off
```

`go env -w` сохраняет setting. `GOVCS` появилась в Go 1.16; earlier Go могли запускать любой known VCS для любого module.

## Module zip files {#zip-files}

Module versions распространяются как `.zip`. Обычно users не взаимодействуют с ними напрямую: command создаёт/скачивает/extract автоматически. `go mod download` получает zip в cache; `golang.org/x/mod/zip` позволяет работать с ними программно.

### File path and size constraints {#zip-path-size-constraints}

Ограничения обеспечивают safe/cross-platform extraction:

- module zip ≤500 MiB; суммарный uncompressed content ≤500 MiB; `go.mod` ≤16 MiB; `LICENSE` ≤16 MiB;
- каждый file path начинается `$module@$version/`, где module path/version valid, version canonical и compatible с major suffix;
- modes, timestamps и прочая metadata игнорируются;
- empty directories могут присутствовать, но не extract; command их не создаёт в zip;
- symbolic links и irregular files игнорируются;
- directories named `vendor` исключаются;
- contents nested module directories с `go.mod` исключаются;
- никакие два paths не могут быть equal по Unicode case-folding (`strings.EqualFold`);
- top-level `go.mod` optional; если есть, имя строго lowercase `go.mod`; files с именем `go.mod` в других directories не допускаются;
- file/directory names допускают Unicode letters, ASCII digits, ASCII space и punctuation `!#$%&()+,-.=@[]^_{}~`; package paths имеют более строгие правила;
- base name до первой dot не может быть Windows reserved name независимо от case.

## Private modules {#private-modules}

Go умеет получать modules из private proxies/VCS, но обычно требуется configuration. Relevant variables: `GOPROXY`, `GOPRIVATE`, `GONOPROXY`, `GONOSUMDB`, `GOINSECURE`. Их можно задавать environment или сохранять `go env -w`.

### Private proxy serving all modules {#private-module-proxy-all}

Central private proxy, обслуживающий public и private modules, даёт maximum administrative control и minimum client configuration:

```text
GOPROXY=https://proxy.corp.example.com
GONOSUMDB=corp.example.com
```

Command использует только corporate proxy и не обращается к другим proxies/VCS. `GONOSUMDB` запрещает public checksum DB для corporate prefix. Proxy обычно нужен read access к private VCS и Internet для public modules. Minimal implementation может обслуживать module-cache layout и заполнять его `go mod download`.

### Private proxy serving private modules {#private-module-proxy-private}

Proxy может обслуживать только private modules с fallback на public sources:

```text
GOPROXY=https://proxy.corp.example.com,https://proxy.golang.org,direct
GONOSUMDB=corp.example.com
```

Fallback после corporate proxy происходит только на 404/410 из-за comma. Любой другой status, например 403 для disallowed license/vulnerability, terminal и позволяет proxy контролировать public-module policy даже без hosting этих modules.

### Direct access to private modules {#private-module-proxy-direct}

Без private proxy можно настроить direct VCS:

```text
GOPRIVATE=corp.example.com
```

Default `GOPROXY=https://proxy.golang.org,direct` сохраняется, но paths matching `GOPRIVATE` не отправляются public proxy/checksum DB и скачиваются direct.

Для custom paths может требоваться internal HTTP server, отвечающий на `https://corp.example.com/mod?go-get=1`. Это можно избежать VCS suffix в path, например `corp.example.com/repo.git/mod`, позволяющим определить repository root напрямую.

Developers нужен read access к repositories; VCS лучше configure без interactive prompts. При вызове Git command `go` default устанавливает `GIT_TERMINAL_PROMPT=0`, но уважает explicit settings.

### Passing credentials to private proxies {#private-module-proxy-auth}

Proxy authentication поддерживает HTTP Basic и headers, предоставленные `GOAUTH`.

Credentials можно хранить в `.netrc`:

```text
machine proxy.corp.example.com
login jrgopher
password hunter2
```

`NETRC` задаёт file; default `$HOME/.netrc` на Unix-like и `%USERPROFILE%\_netrc` на Windows. Fields разделяются whitespace, поэтому whitespace нельзя включать username/password; machine — host, не full URL, поэтому разные credentials для paths одного host через `.netrc` невозможны.

С Go 1.24 `GOAUTH` может использовать `.netrc`, запускать `git credential fill` в указанной working directory или custom command. Custom command способен возвращать arbitrary HTTP headers, например Bearer token, scoped к URL prefixes. Protocol: `go help goauth`. Credentials `GOAUTH`, включая default `netrc`, применяются только к HTTPS.

Credentials можно включить прямо в `GOPROXY` URL:

```text
GOPROXY=https://jrgopher:hunter2@proxy.corp.example.com
```

Это требует осторожности: environment variables могут попасть в shell history/logs.

### Passing credentials to private repositories {#private-module-repo-auth}

При direct module download authentication выполняет VCS tool, например Git, поэтому credentials настраиваются в `.gitconfig`/tool-specific config. Command предпочитает HTTPS, если scheme не был задан при repository lookup; для GitHub предполагается HTTPS.

Например, HTTPS можно rewrite на SSH:

```gitconfig
[url "git@github.com:"]
    insteadOf = https://github.com/
```

### Privacy {#private-module-privacy}

Default:

```text
GOPROXY=https://proxy.golang.org,direct
```

Поэтому module path сначала отправляется public proxy Google. PII command не посылает, но full requested module path виден proxy. После 404/410 command может обратиться direct VCS.

`GOPRIVATE`/`GONOPROXY` задают glob prefixes, которые не следует запрашивать у proxy:

```text
GOPRIVATE=*.corp.example.com,*.research.example.com
```

`GOPRIVATE` — default для `GONOPROXY` и `GONOSUMDB`. Matching `GONOPROXY` path fetch direct.

Если trusted private proxy обслуживает **все** modules, `GONOPROXY` не нужен:

```text
GOPROXY=https://proxy.corp.example.com
GONOSUMDB=*.corp.example.com,*.research.example.com
```

Если trusted proxy обслуживает только private modules, не следует устанавливать `GONOPROXY`, но proxy обязан корректно использовать status codes:

```text
GOPROXY=https://proxy.corp.example.com,https://proxy.golang.org
GONOSUMDB=*.corp.example.com,*.research.example.com
```

Typo вроде:

```bash
go mod download corp.example.com/secret-product/typo@latest
```

может раскрыть private path public proxy, если private proxy ответит 404/410 и произойдёт fallback. Другой error status остановит fallback.

Checksum DB также получает full module path. `GOSUMDB` default `sum.golang.org`. `GONOSUMDB`/`GOPRIVATE` предотвращают запросы private prefixes; proxy может mirror checksum DB. `GOSUMDB=off` полностью отключает DB, но тогда новые modules без existing `go.sum` authentication не получают global verification.

## Module cache {#module-cache}

Module cache хранит downloaded module files отдельно от build cache. Default `$GOPATH/pkg/mod`, override `GOMODCACHE`. Maximum size отсутствует и automatic cleanup нет. Cache может безопасно shared несколькими projects/processes.

Source files/directories default read-only, чтобы не допустить accidental modification. Удалять cache следует `go clean -modcache`; `-modcacherw` создаёт новые directories writable ценой большего риска. `go mod verify` обнаруживает modifications dependencies.

Основные paths:

| Path | Назначение |
| --- | --- |
| `$module@$version/` | Extracted contents module zip; может не иметь `go.mod`, если original его не имел. |
| `cache/download/` | Files from proxies/VCS в GOPROXY-compatible layout; directory можно serving как proxy. |
| `cache/download/$module/@v/list` | Cached known-version list; может меняться, поэтому command обычно refetch. |
| `cache/download/$module/@v/$version.info` | JSON metadata. |
| `cache/download/$module/@v/$version.mod` | `go.mod` version, synthetic если original отсутствует. |
| `cache/download/$module/@v/$version.zip` | Module archive. |
| `cache/download/$module/@v/$version.ziphash` | Hash file contents; не hash zip bytes/metadata. |
| `cache/download/sumdb/` | Data checksum database. |
| `cache/vcs/` | Directly cloned VCS repositories; names — hex hashes repo type/URL; Git clones обычно bare/shallow. |

Uppercase in module paths/versions escaping'ятся exclamation mark, например `Azure` → `!azure`, чтобы избежать case-insensitive collisions.

## Authenticating modules {#authenticating}

Когда command скачивает module zip или `go.mod` в cache, она вычисляет cryptographic hash и сравнивает с known value. Несовпадение — security error; downloaded file удаляется.

Для `go.mod` hash строится по file content; для zip — по names/contents внутри archive в deterministic order, независимо от file order, compression, alignment и metadata. Details: [`golang.org/x/mod/sumdb/dirhash`](https://pkg.go.dev/golang.org/x/mod/sumdb/dirhash).

Hash сравнивается с main module `go.sum`. При mismatch command сообщает security error. Если line отсутствует, hash обычно проверяется checksum database, после чего добавляется `go.sum` и content — cache. Для private modules (`GOPRIVATE`/`GONOSUMDB`) или `GOSUMDB=off` hash принимается без checksum-DB verification.

Cache shared projects, но command при access сверяет hashes с **main module** `go.sum`, не доверяя sums других modules. Zip hashes дороги, поэтому используются precomputed `.ziphash`. `go mod verify` отдельно проверяет, что cached zip/extracted dirs не изменены.

### `go.sum` files {#go-sum-files}

`go.sum` рядом с `go.mod` содержит cryptographic hashes direct/indirect dependencies. Он может быть пуст/отсутствовать, если dependencies нет или все replacement local.

Каждая line имеет три fields: module path, version и hash. Version с `/go.mod` означает hash только `go.mod`; без suffix — files module zip. Hash field — algorithm и base64 digest через `:`, сейчас поддержан `h1` (SHA-256); future algorithm мог бы называться `h2`.

`go.sum` может содержать hashes нескольких versions одного module, поскольку MVS иногда загружает несколько `go.mod` для selection. Он также может сохранять versions, уже не required. `go mod tidy` добавляет missing и удаляет unnecessary hashes.

### Checksum database {#checksum-database}

Checksum DB — global source `go.sum` lines для public modules и защищает от misbehavior proxy/origin. Она обеспечивает глобальную consistency: конкретная version не может незаметно менять bits.

Default service [sum.golang.org](https://sum.golang.org), operated by Google, представляет Transparent Log / Merkle Tree на базе Trillian. Independent auditors могут verify append-only consistency.

Protocol включает endpoints:

| Path | Назначение |
| --- | --- |
| `$base/latest` | Signed encoded latest tree description: tree size и root hash. |
| `$base/lookup/$module@$version` | Log record number, `go.sum` data и signed tree description containing record. |
| `$base/tile/$H/$L/$K[.p/$W]` | Log tile; optional partial width `$W`; client falls back full tile, если partial absent. |
| `$base/tile/$H/data/$K[.p/$W]` | Record data для leaf hashes corresponding tile. |

`$module`/`$version` case-encoded через `!` + lowercase. При lookup module, ещё не present log, DB может fetch origin перед response. Client обязан аутентифицировать lookup data against signed tree hash и собственную timeline signed hashes; выполняются inclusion и consistency proofs. Signed tree hashes/tiles cached local.

Command не обязана connect DB directly: module proxy может mirror checksum protocol.

`GOSUMDB` задаёт database name и optional public key/URL:

```text
GOSUMDB="sum.golang.org"
GOSUMDB="sum.golang.org+<publickey>"
GOSUMDB="sum.golang.org+<publickey> https://sum.golang.org"
```

Command знает public key `sum.golang.org` и alias `sum.golang.google.cn` для mainland China; другие databases требуют explicit key. URL default `https://` + name. Default `GOSUMDB=sum.golang.org`. `GOSUMDB=off` отключает DB; pinned source также упоминает deprecated `go get -insecure` как отключавший consultation DB. Для selective bypass лучше `GOPRIVATE`/`GONOSUMDB`.

## Environment variables {#environment-variables}

Ниже перечислены module-related variables; полный список — `go help environment`.

| Variable | Значение |
| --- | --- |
| `GO111MODULE` | `off` — GOPATH mode; `on`/unset — module-aware; `auto` — module-aware при найденном `go.mod`, что было default до Go 1.16. |
| `GOMODCACHE` | Directory module cache; default `$GOPATH/pkg/mod`. |
| `GOINSECURE` | Comma-separated glob module prefixes, разрешённых для insecure direct fetch. Не отключает checksum DB; для этого используются `GOPRIVATE`/`GONOSUMDB`. |
| `GONOPROXY` | Prefixes, всегда скачиваемые direct, не через proxy; default `GOPRIVATE`. |
| `GONOSUMDB` | Prefixes, не проверяемые public checksum DB; default `GOPRIVATE`. |
| `GOPATH` | В GOPATH mode — roots source; в module mode first `$GOPATH/pkg/mod` default cache. Default `$HOME/go`. |
| `GOPRIVATE` | Prefixes private modules; default для `GONOPROXY`/`GONOSUMDB`, также определяет private для `GOVCS`. |
| `GOPROXY` | Ordered proxy URLs separated comma/pipe; comma fallback только 404/410, pipe — any error. Schemes `https`, `http`, `file`; no scheme → HTTPS. Keywords `off`, `direct`. Default `https://proxy.golang.org,direct`. File proxy: `GOPROXY=file://$(go env GOMODCACHE)/cache/download`. |
| `GOSUMDB` | Checksum DB name + optional public key/URL; default `sum.golang.org`, `off` disables. |
| `GOVCS` | Allowed VCS rules. Default `public:git|hg,private:all`. |
| `GOWORK` | Path `.work` file для workspace; `off` disables; empty → search parents. |

## Glossary {#glossary}

<a id="glos-build-constraint"></a>
**build constraint:** условие, определяющее, используется ли Go source file при compilation package. Может задаваться suffix filename (`foo_linux_amd64.go`) или build-constraint comments.

<a id="glos-build-list"></a>
**build list:** module versions, используемые build command (`go build`, `go list`, `go test`). Определяется main `go.mod` и transitively required `go.mod` посредством MVS. Включает versions всех modules graph, не только relevant конкретной command.

<a id="glos-canonical-version"></a>
**canonical version:** корректно отформатированная version без build metadata, кроме `+incompatible`; `v1.2.3` canonical, `v1.2.3+meta` — нет.

<a id="glos-current-module"></a>
**current module:** synonym [main module](#glos-main-module).

<a id="glos-deprecated-module"></a>
**deprecated module:** module, больше не поддерживаемый authors. Major versions считаются distinct modules. Marked deprecation comment в latest `go.mod`.

<a id="glos-direct-dependency"></a>
**direct dependency:** package, path которого присутствует в `import` declaration source/test main module, либо module, содержащий такой package.

<a id="glos-direct-mode"></a>
**direct mode:** configuration, заставляющая command скачивать module непосредственно из VCS вместо proxy. `GOPROXY=direct` — для всех; `GOPRIVATE`/`GONOPROXY` — для matching paths.

<a id="glos-go-mod-file"></a>
**`go.mod` file:** file, определяющий module path, requirements и metadata в module root.

<a id="glos-go-work-file"></a>
**`go.work` file:** file, определяющий set modules workspace.

<a id="glos-import-path"></a>
**import path:** string, используемая для import package в source; synonym package path.

<a id="glos-indirect-dependency"></a>
**indirect dependency:** package transitively imported package/test main module, но не появляющийся в imports main module, либо module graph, не предоставляющий directly imported package main module.

<a id="glos-lazy-module-loading"></a>
**lazy module loading:** изменение Go 1.17, избегающее загрузки полного module graph для commands, которым он не нужен, в modules `go 1.17+`.

<a id="glos-main-module"></a>
**main module:** module, в context которого invoked `go`; определяется `go.mod` current/parent directory.

<a id="glos-major-version"></a>
**major version:** первое число semantic version (`1` в `v1.2.3`); incompatible release увеличивает major и сбрасывает minor/patch в 0; major 0 unstable.

<a id="glos-major-version-subdirectory"></a>
**major version subdirectory:** repository subdirectory, совпадающая major suffix, где может определяться module, например `v2` для `example.com/mod/v2`.

<a id="glos-major-version-suffix"></a>
**major version suffix:** suffix module path, совпадающий major version, например `/v2`; обязателен с `v2.0.0`, запрещён раньше, кроме special `gopkg.in` rules.

<a id="glos-minimal-version-selection"></a>
**minimal version selection (MVS):** algorithm выбора versions всех modules build.

<a id="glos-minor-version"></a>
**minor version:** второе число (`2` в `v1.2.3`); backwards-compatible feature release увеличивает minor и сбрасывает patch.

<a id="glos-module"></a>
**module:** collection packages, released, versioned и distributed together.

<a id="glos-module-cache"></a>
**module cache:** local downloaded-module directory, default `GOPATH/pkg/mod`.

<a id="glos-module-graph"></a>
**module graph:** directed graph requirements rooted at main module(s); vertices modules, edges `require` versions с учётом main `replace`/`exclude`.

<a id="glos-module-graph-pruning"></a>
**module graph pruning:** Go 1.17 change, уменьшающее graph за счёт omission transitive dependencies modules `go 1.17+`.

<a id="glos-module-path"></a>
**module path:** path, идентифицирующий module и служащий prefix package import paths, например `golang.org/x/net`.

<a id="glos-module-proxy"></a>
**module proxy:** web server, реализующий GOPROXY protocol для version metadata, `go.mod` и zip files.

<a id="glos-module-root-directory"></a>
**module root directory:** directory, содержащая `go.mod`, определяющий module.

<a id="glos-module-subdirectory"></a>
**module subdirectory:** часть module path после repository root path, указывающая subdirectory module; при non-empty также prefix semantic-version tags; major suffix не входит.

<a id="glos-package"></a>
**package:** source files одной directory, compiled together; см. [[../spec#Packages|Specification: Packages]].

<a id="glos-package-path"></a>
**package path:** unique path package = module path + subdirectory, например `golang.org/x/net/html`; synonym import path.

<a id="glos-patch-version"></a>
**patch version:** третье число (`3` в `v1.2.3`); увеличивается, если public interface не меняется.

<a id="glos-pre-release-version"></a>
**pre-release version:** version с hyphen и identifiers после patch, например `v1.2.3-beta4`; unstable и сортируется до corresponding release.

<a id="glos-pseudo-version"></a>
**pseudo-version:** version, кодирующая VCS revision identifier и timestamp, например `v0.0.0-20191109021931-daa7c04131f5`.

<a id="glos-release-version"></a>
**release version:** version без pre-release suffix, например `v1.2.3`.

<a id="glos-repository-root-path"></a>
**repository root path:** portion module path, соответствующая VCS repository root directory.

<a id="glos-retracted-version"></a>
**retracted version:** version, на которую не следует зависеть из-за premature publication или серьёзной проблемы; помечается `retract`.

<a id="glos-semantic-version-tag"></a>
**semantic version tag:** repository tag, mapping version к конкретной revision.

<a id="glos-selected-version"></a>
**selected version:** version module, выбранная MVS; highest version module path, найденная graph.

<a id="glos-vendor-directory"></a>
**vendor directory:** directory `vendor` с copies packages других modules, необходимых main module; поддерживается `go mod vendor`.

<a id="glos-version"></a>
**version:** identifier immutable snapshot module: `v` + semantic version.

<a id="glos-workspace"></a>
**workspace:** collection modules on disk, используемых как main modules при MVS.
