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

Эта страница является подробным reference manual для module system Go.

Для знакомства с базовыми concepts modules сначала можно прочитать [[../tutorial/create-module|Tutorial: создание Go module]], а для повседневного dependency workflow — [[managing-dependencies|Управление dependencies]]. Эта страница описывает нормативное и operational behavior module-aware команды `go`: module paths и versions, `go.mod`/`go.work`, Minimal Version Selection, module proxies, VCS resolution, authentication, checksum database, private modules и environment variables.

## Modules, packages и versions {#modules-overview}

**Module** — коллекция packages, которые version'ятся, публикуются и распространяются вместе. Module определяется file `go.mod` в module root directory.

Каждый module имеет **module path**, объявленный `module` directive в `go.mod`. Module path является canonical name module и prefix import paths packages внутри него.

Package в module с path:

```text
example.com/my/module
```

и directory:

```text
foo/bar
```

имеет package path:

```text
example.com/my/module/foo/bar
```

Module публикуется как последовательность immutable versions. Каждая version обычно соответствует semantic version tag repository. При отсутствии suitable tag Go может использовать pseudo-version, derived из revision и timestamp.

При выполнении command внутри module module называется **main module**. Его `go.mod` определяет direct requirements, replacements, exclusions и другие module settings. Все modules, выбранные для конкретного build, образуют **build list**.

## Module paths {#module-path}

Module path не только идентифицирует module, но обычно также сообщает Go tool, где искать source.

Типичный module path:

```text
github.com/user/project
```

Module path состоит концептуально из:

1. **repository root path** — часть, соответствующая root VCS repository;
2. optional **module subdirectory** — если module находится ниже repository root;
3. optional **major version suffix** — `/v2`, `/v3` и т. д. для major versions `v2+`.

Например:

```text
example.com/monorepo/foo/bar/v2
```

может означать repository root `example.com/monorepo`, module subdirectory `foo/bar` и major suffix `/v2`.

Module path должен удовлетворять lexical restrictions Go module system. Paths case-sensitive, но при storage/proxy encoding uppercase letters escape'ятся, чтобы paths оставались однозначными на case-insensitive filesystems.

### Major version suffixes {#major-version-suffixes}

Для major versions `v0` и `v1` module path обычно не содержит major suffix:

```text
example.com/mod
```

Начиная с `v2`, suffix является частью module identity:

```text
example.com/mod/v2
example.com/mod/v3
```

Следовательно, `example.com/mod` и `example.com/mod/v2` — разные modules и могут одновременно присутствовать в одном build.

Для `gopkg.in` исторически поддерживается форма `.v2`, `.v3` и т. п.; module system учитывает эту convention как special compatibility case.

## Versions {#versions}

Go module versions используют semantic versioning в canonical form:

```text
vMAJOR.MINOR.PATCH
```

Примеры:

```text
v1.2.3
v0.8.0
v2.0.1
```

Pre-release suffix допустим:

```text
v1.2.3-beta.1
```

Build metadata обычно не участвует в canonical module version; special suffix `+incompatible` используется для compatibility с некоторыми non-module repositories.

Ordering соответствует semantic versioning:

- major сравнивается первым;
- затем minor;
- затем patch;
- pre-release сортируется перед соответствующим release.

`v0` считается unstable line. `v1+` предполагает semantic compatibility внутри major version.

### Pseudo-versions {#pseudo-versions}

Если revision не имеет suitable semantic version tag, Go может представить его pseudo-version.

Пример:

```text
v0.0.0-20191109021931-daa7c04131f5
```

или, если есть предыдущая tagged version:

```text
v1.3.2-0.20191109021931-daa7c04131f5
```

Pseudo-version включает:

- base version prefix;
- UTC timestamp revision;
- revision identifier, например 12-character Git commit prefix.

Go проверяет, что timestamp совпадает с commit time и что base version действительно соответствует appropriate ancestor tag. Это не позволяет arbitrary pseudo-version искусственно изменить ordering versions.

Не создавайте pseudo-versions вручную: Go tools генерируют их автоматически.

## Resolving a package to a module {#resolve-pkg-mod}

Когда imported package не предоставляется ни одним module текущего build list, `go` command должен найти module, который этот package предоставляет.

Для package:

```text
golang.org/x/net/html
```

Go рассматривает possible module path prefixes, например:

```text
golang.org/x/net/html
golang.org/x/net
golang.org/x
golang.org
```

Для каждого candidate определяется latest suitable version. Module source загружается, и Go проверяет наличие package directory. Если package предоставляют несколько candidates, выбирается module с **наиболее длинным module path**.

При успешном resolution requirement добавляется в `go.mod`, если command разрешено его изменять.

## `go.mod` files {#go-mod-file}

File `go.mod` определяет module path, Go language/toolchain requirements и module graph edges.

Пример:

```text
module example.com/mymodule

go 1.27

toolchain go1.27.1

require (
    example.com/a v1.2.3
    example.com/b v0.9.0
)

replace example.com/a => ../a
```

`go.mod` line-oriented. Comments используют syntax `//`.

### Lexical elements {#go-mod-file-lexical}

Identifiers вроде directive names состоят из non-whitespace tokens. Strings при необходимости могут быть quoted. Module paths и versions имеют дополнительные restrictions, обеспечивающие portability и unambiguous proxy/filesystem representation.

Go module path/version escaping используется в proxy URLs и module cache. Uppercase letters encode'ятся как `!` + lowercase letter, например:

```text
example.com/Azure
```

становится:

```text
example.com/!azure
```

### Grammar {#go-mod-file-grammar}

`go.mod` состоит из directives, каждая из которых может быть single-line либо grouped block:

```text
require example.com/a v1.2.3
```

эквивалентно:

```text
require (
    example.com/a v1.2.3
)
```

Supported directives включают `module`, `go`, `toolchain`, `godebug`, `require`, `tool`, `ignore`, `exclude`, `replace`, `retract`.

### `module` directive {#go-mod-file-module}

```text
module module-path
```

Объявляет module path. В одном `go.mod` допускается одна `module` directive.

Для `v2+` major suffix должен соответствовать version line module.

#### Deprecation comment {#go-mod-file-module-deprecation}

Module можно пометить deprecated comment непосредственно перед `module` directive. Convention:

```text
// Deprecated: use example.com/newmod instead.
module example.com/oldmod
```

Go tools могут показывать это сообщение users. Deprecation определяется по latest version module.

### `go` directive {#go-mod-file-go}

```text
go 1.27
```

Задаёт minimum Go language/toolchain version, assumptions которой использует module.

Начиная с Go 1.21 эта requirement mandatory: toolchain старее указанной version откажется использовать module. `go` version main module также должна быть не ниже `go` versions dependencies.

Directive влияет не только на language features, но и на module semantics конкретных releases — vendoring, graph pruning, lazy loading и другие behavior changes.

### `toolchain` directive {#go-mod-file-toolchain}

```text
toolchain go1.27.1
```

Предлагает toolchain для работы с main module. Если default toolchain старее suggested toolchain и automatic switching разрешён, command может переключиться на него.

Special value:

```text
toolchain default
```

запрещает automatic upgrade beyond default toolchain.

### `godebug` directive {#go-mod-file-godebug}

```text
godebug asynctimerchan=0
```

или block:

```text
godebug (
    default=go1.21
    panicnil=1
)
```

Задаёт default GODEBUG behavior для main packages/tests текущего module. Не влияет на module, когда он используется как dependency.

### `require` directive {#go-mod-file-require}

```text
require example.com/mod v1.2.3
```

Добавляет edge module graph: текущий module требует указанную minimum version dependency.

`// indirect` comment указывает, что module не предоставляет package, directly imported main module, но нужен graph/build.

Начиная с Go 1.17 `go.mod` main module обычно включает explicit requirements для modules, предоставляющих transitively imported packages/tests main module, что позволяет graph pruning и lazy loading.

### `tool` directive {#go-mod-file-tool}

```text
tool example.com/tools/cmd/gen
```

Объявляет Go package как developer tool dependency. Module, содержащий tool, также должен участвовать в module graph через `require`.

Tool запускается:

```bash
go tool gen
```

либо full package path, если short name ambiguous.

### `ignore` directive {#go-mod-file-ignore}

```text
ignore ./node_modules
```

или:

```text
ignore generated
```

Исключает matching directories main module из package pattern matching, например `./...`.

### `exclude` directive {#go-mod-file-exclude}

```text
exclude example.com/mod v1.2.3
```

Запрещает конкретную version module при MVS для current main module. `exclude` dependencies игнорируются; действует только configuration main module/workspace.

### `replace` directive {#go-mod-file-replace}

```text
replace example.com/mod => ../mod
```

или:

```text
replace example.com/mod v1.2.3 => example.com/fork/mod v1.2.4-fixed
```

Replacement может target'ить:

- local directory;
- другой module path/version;
- другую version того же module.

`replace` не добавляет module в graph сам по себе: module должен быть required каким-либо graph edge.

`replace` directives dependency modules игнорируются; effective replacements задаются main module или workspace.

### `retract` directive {#go-mod-file-retract}

```text
retract v1.2.0 // contains a severe bug
```

или range:

```text
retract [v1.0.0, v1.0.5]
```

Retracted versions не выбираются автоматически большинством module commands, но остаются downloadable для repeatable builds existing users.

Retractions читаются из `go.mod` latest available version module, поэтому после добавления retraction обычно публикуется новая higher version.

## Automatic updates to `go.mod` {#go-mod-file-updates}

Go commands могут автоматически изменять `go.mod`/`go.sum`, когда:

- добавляются packages/modules;
- selected versions меняются;
- `go mod tidy` синхронизирует dependencies;
- Go version/toolchain requirements должны быть обновлены в соответствии с command semantics.

Если command работает в read-only mode, необходимые изменения вместо записи становятся error.

## Minimal version selection (MVS) {#minimal-version-selection}

MVS определяет selected version каждого module path в build list.

Основная идея: из всех minimum requirements для одного module path выбирается **наибольшая** version, встречающаяся в module graph.

Например, если:

```text
M requires A v1.0.0
M requires B v1.0.0
A v1.0.0 requires C v1.1.0
B v1.0.0 requires C v1.2.0
```

selected version C будет:

```text
C v1.2.0
```

MVS отличается от алгоритмов, автоматически выбирающих latest version: если graph требует C v1.2.0 и доступна C v1.9.0, C v1.9.0 сама по себе не будет выбрана без requirement/upgrade command.

Это делает builds более predictable и уменьшает accidental upgrades.

### Upgrades {#minimal-version-selection-upgrade}

`go get module@version` может добавить/повысить root requirement. После этого MVS пересчитывает graph, и transitive modules при необходимости тоже повышаются, чтобы удовлетворить requirements новой version.

### Downgrades {#minimal-version-selection-downgrade}

Если requested downgrade несовместим с requirements других selected modules, Go может downgrade'ить и эти modules либо удалить dependencies, чтобы получить graph, удовлетворяющий target maximum.

### Removing module requirements {#minimal-version-selection-removal}

`go get module@none` удаляет requirement. Если другие modules требуют удаляемый module/version, команда может также downgrade/remove их, чтобы resulting graph больше его не содержал.

## Module graph pruning {#graph-pruning}

Начиная с Go 1.17 modules могут использовать **graph pruning**.

Если dependency module объявляет `go 1.17` или выше, его `go.mod` содержит explicit requirements на modules, предоставляющие packages, transitively imported packages/tests этого dependency. Это позволяет main module не загружать полные transitive graphs таких modules.

Для module с `go 1.17+` `go.mod` main module содержит requirement на каждый module, предоставляющий package transitively imported package/test main module.

Dependencies с `go` version ниже 1.17 не имеют этих guarantees, поэтому их transitive `go.mod` graphs могут потребоваться целиком.

Pruning уменьшает network/file reads и ускоряет commands в больших graphs.

### Pruned module graph {#pruned-module-graph}

Graph включает:

- all requirements main module;
- requirements unpruned dependency modules;
- достаточную информацию о pruned modules, чтобы selected versions остаются корректными.

### Module graph loading {#module-graph-loading}

Go загружает `go.mod` files по необходимости. Некоторые commands требуют full graph, другие могут работать с partial information.

## Lazy module loading {#lazy-loading}

Также начиная с Go 1.17, когда module graph pruning применим, многие commands загружают requirements **lazy**.

Вместо чтения `go.mod` каждого module upfront Go начинает с packages, реально relevant command, и расширяет graph только когда требуется выяснить provider package или проверить selected version.

Lazy loading не изменяет MVS result; оно уменьшает работу, необходимую для его получения в конкретной операции.

## Workspaces {#workspaces}

Workspace позволяет работать с несколькими modules как с main modules одновременно.

Workspace определяется `go.work` file и особенно полезен, когда несколько locally checked-out modules разрабатываются совместно.

Tutorial: [[../tutorial/workspaces|Multi-module workspaces]].

### `go.work` files {#go-work-file}

Пример:

```text
go 1.27

use (
    ./module-a
    ./module-b
)

replace example.com/shared => ../shared
```

Workspace file поддерживает directives `go`, `toolchain`, `godebug`, `use`, `replace`.

#### `go` directive {#go-work-file-go}

Задаёт Go version workspace semantics и должна быть не ниже `go` versions всех workspace modules.

#### `toolchain` directive {#go-work-file-toolchain}

Suggested toolchain для workspace mode аналогично `go.mod`.

#### `godebug` directive {#go-work-file-godebug}

Задаёт workspace-level defaults для main packages, overriding defaults modules согласно GODEBUG rules.

#### `use` directive {#go-work-file-use}

```text
use ./module-a
```

Каждый `use` path указывает directory, содержащий `go.mod`. Module из этого directory становится main module workspace.

#### `replace` directive {#go-work-file-replace}

Workspace replacement применяется ко всем workspace modules и override'ит conflicting module-level replacements. Conflicting replacements между workspace modules должны быть разрешены workspace `replace`.

### Starting a workspace {#workspaces-starting}

Создать workspace:

```bash
go work init ./module-a ./module-b
```

Добавить module:

```bash
go work use ./module-c
```

При установленном `GOWORK` либо найденном parent `go.work` command входит в workspace mode.

`GOWORK=off` принудительно выключает workspace mode:

```bash
GOWORK=off go build .
```

### Workspace commands {#workspaces-commands}

Основные commands:

```text
go work edit
go work init
go work sync
go work use
```

`go work sync` синхронизирует selected versions workspace build list с individual `go.mod` files workspace modules, сохраняя MVS consistency.

## Vendoring {#vendoring}

Main module может хранить copies packages dependencies в directory `vendor`.

Создать/update vendor tree:

```bash
go mod vendor
```

`vendor/modules.txt` описывает vendored modules/packages и metadata, включая explicit requirements и Go versions в современных releases.

Если main module имеет `go` version с automatic vendoring semantics и `vendor/modules.txt` согласован с `go.mod`, build commands могут автоматически использовать vendor directory без `-mod=vendor`.

Dependencies' own vendor directories не используются.

Module zip files также исключают vendor directories.

## Module-aware commands {#mod-commands}

Большинство `go` commands учитывают module/workspace mode.

### `go get` {#go-get}

`go get` изменяет dependencies main module: добавляет, upgrade'ит, downgrade'ит или удаляет module requirements.

Examples:

```bash
go get example.com/mod@v1.2.3
go get example.com/mod@latest
go get example.com/mod@none
```

Package arguments resolve'ятся к modules. Version queries могут указывать semantic version, branch, tag, revision, `latest`, `upgrade`, `patch` и другие supported query forms.

Modern `go get` управляет dependencies; installation executables конкретной version выполняется через:

```bash
go install example.com/cmd@version
```

### `go install` {#go-install}

С version suffix `@version` `go install` строит и устанавливает executable package вне dependency graph current module.

Например:

```bash
go install golang.org/x/tools/gopls@latest
```

Package должен быть `main`, а module/version resolution следует специальным restrictions, чтобы build был reproducible и не зависел от current main module replacements.

### `go list -m` {#go-list-m}

Показывает modules вместо packages.

Examples:

```bash
go list -m all
go list -m -u all
go list -m -versions example.com/mod
```

`-json` возвращает structured module metadata. `-retracted` включает retracted versions, когда применимо.

### Version queries {#version-queries}

Query после `@` может быть:

- exact canonical version;
- version prefix, например `@v1.2`;
- revision/tag/branch identifier;
- `latest`;
- `upgrade`;
- `patch`;
- comparison query вроде `@>=v1.2.3` в contexts, где поддерживается.

Go преобразует branch/revision query в canonical version или pseudo-version для MVS.

`latest` предпочитает highest release version, затем highest pre-release, затем newest pseudo-version, если tagged versions отсутствуют.

### `go mod download` {#go-mod-download}

Загружает modules в local module cache:

```bash
go mod download
```

С explicit arguments:

```bash
go mod download example.com/mod@v1.2.3
```

`-json` показывает paths downloaded `.info`, `.mod`, `.zip`, extracted directory, sums и errors.

### `go mod edit` {#go-mod-edit}

Programmatic editing `go.mod` без понимания higher-level dependency intent.

Поддерживает flags для изменения directives, например:

```bash
go mod edit -module=example.com/new

go mod edit -go=1.27

go mod edit -require=example.com/mod@v1.2.3

go mod edit -replace=example.com/mod=../mod
```

`-json` печатает parsed structure.

### `go mod graph` {#go-mod-graph}

Печатает module requirement graph как edges:

```text
module@version dependency@version
```

Полезно для диагностики, почему определённая module version участвует в MVS.

### `go mod init` {#go-mod-init}

Создаёт новый `go.mod`:

```bash
go mod init example.com/mymodule
```

Если module path не указан, command в некоторых repository layouts может попытаться вывести его из VCS/import metadata, но explicit path предпочтительнее.

### `go mod tidy` {#go-mod-tidy}

Гарантирует, что `go.mod` содержит requirements, необходимые packages/tests main module, и не содержит unnecessary requirements. Также синхронизирует `go.sum`.

`tidy` рассматривает packages во всех build tags, кроме `ignore`, и включает test dependencies так, чтобы module metadata было достаточным across supported build configurations.

Flags позволяют, среди прочего, проверить необходимость изменений или target Go compatibility semantics.

### `go mod vendor` {#go-mod-vendor}

Создаёт `vendor` tree из packages, необходимых main module packages/tests, и `vendor/modules.txt`.

`-o` может указывать другой output directory в supported versions, но automatic vendoring ожидает directory `vendor` в main module root.

### `go mod verify` {#go-mod-verify}

Проверяет, что downloaded module `.zip` files и extracted directories в cache не изменены относительно recorded hashes.

```bash
go mod verify
```

### `go mod why` {#go-mod-why}

Показывает shortest import path chain от main module к указанным packages либо modules (`-m`).

Useful для ответа, почему dependency присутствует:

```bash
go mod why -m example.com/mod
```

### `go version -m` {#go-version-m}

Показывает embedded module/version/build information Go binary:

```bash
go version -m ./mybinary
```

### `go clean -modcache` {#go-clean-modcache}

Удаляет весь module cache:

```bash
go clean -modcache
```

Это предпочтительный способ очистки cache, особенно когда extracted files read-only.

## Workspace commands {#go-work-commands}

### `go work init` {#go-work-init}

Создаёт `go.work`, optionally сразу добавляя modules:

```bash
go work init ./a ./b
```

### `go work edit` {#go-work-edit}

Programmatic editing `go.work`, включая `use`, `replace`, `go`, `toolchain` directives и JSON output.

### `go work use` {#go-work-use}

Добавляет/удаляет module directories в `use` set. С `-r` recursively ищет modules под directory.

```bash
go work use -r ./services
```

### `go work sync` {#go-work-sync}

Синхронизирует workspace build list обратно в requirements individual workspace modules.

## Module proxies {#module-proxy}

Module proxy — HTTP server, реализующий `GOPROXY` protocol. Proxy может:

- cache public modules;
- enforce policy;
- обслуживать private modules;
- изолировать clients от VCS servers;
- обеспечивать repeatable availability immutable module versions.

Default:

```text
GOPROXY=https://proxy.golang.org,direct
```

Go сначала обращается к public proxy, затем при `404`/`410` использует direct VCS.

### `GOPROXY` protocol {#goproxy-protocol}

Пусть `$base` — proxy base URL, `$module` — escaped module path, `$version` — escaped version.

Proxy endpoints:

| Path | Назначение |
| --- | --- |
| `$base/$module/@v/list` | Список известных tagged versions, по одной на строку; pseudo-versions не включаются. |
| `$base/$module/@v/$version.info` | JSON metadata `{Version, Time}`. `Version` обязательна и canonical; `Time` optional RFC3339 creation time. Endpoint также может resolve'ить branch/revision query в canonical version. |
| `$base/$module/@v/$version.mod` | Original `go.mod`; если у source version его не было, synthetic `go.mod` только с `module` directive. |
| `$base/$module/@v/$version.zip` | Module source archive в canonical module zip format. |
| `$base/$module/@latest` | Optional metadata latest version, когда list пуст/не подходит. |

При latest resolution Go предпочитает:

1. semantically highest release;
2. highest pre-release;
3. chronologically newest pseudo-version.

Successful `.mod` и `.zip` content для одной version должен быть immutable: он cryptographically authenticated.

Go cache proxy content в:

```text
$GOPATH/pkg/mod/cache/download
```

Layout cache соответствует URL space `GOPROXY`, поэтому этот directory можно даже обслуживать как static file proxy.

### Communicating with proxies {#communicating-with-proxies}

Go обращается к proxy только за data, отсутствующими в module cache.

Typical `go build` flow:

1. вычислить build list, читая `go.mod` и выполняя MVS;
2. загрузить packages command line и imports;
3. если package не предоставляется build list, найти module provider, добавить latest suitable requirement и пересчитать;
4. build packages после resolution.

Для graph Go может отдельно запрашивать маленькие `.mod` files, не скачивая большие `.zip` archives.

Example:

```bash
curl https://proxy.golang.org/golang.org/x/mod/@v/v0.2.0.mod
```

Source package загружается через `.zip` endpoint:

```bash
curl -O https://proxy.golang.org/golang.org/x/mod/@v/v0.2.0.zip
```

`.mod` и `.zip` requests отдельны специально: module graph может требовать много `go.mod` files без необходимости source всех modules.

При поиске new module provider Go запрашивает latest versions всех possible path prefixes, затем выбирает candidate с longest module path, реально содержащий package.

После `.mod`/`.zip` download Go вычисляет cryptographic hash, сравнивает его с `go.sum` или checksum database и при mismatch выдаёт security error.

### Serving modules directly from a proxy {#serving-from-proxy}

Custom module path discovery через `?go-get=1` может вернуть `go-import` meta tag с VCS type `mod`:

```html
<meta name="go-import" content="example.com/gopher mod https://modproxy.example.com">
```

Тогда Go использует указанную URL как `GOPROXY` base и скачивает `.info`, `.mod`, `.zip` через proxy protocol.

Modules, обслуживаемые таким образом, не доступны старому GOPATH-mode `go get`.

## Version control systems {#vcs}

В direct mode Go загружает module source непосредственно из VCS repository.

Поддерживаются:

- Git;
- Subversion;
- Mercurial;
- Bazaar;
- Fossil.

Соответствующий VCS tool должен находиться в `PATH`.

Чтобы использовать direct mode для specific modules, настройте `GOPRIVATE`/`GONOPROXY`; для всех modules:

```text
GOPROXY=direct
```

### Finding a repository for a module path {#vcs-find}

Если path содержит VCS qualifier `.git`, `.hg`, `.svn`, `.bzr`, `.fossil` в конце path component, prefix до qualifier определяет repository URL.

Например:

```text
example.com/foo.git/bar
```

указывает repository `example.com/foo.git`, а module — subdirectory `bar`.

Если qualifier отсутствует, Go делает request:

```text
https://module-path?go-get=1
```

и ищет `<meta name="go-import">`:

```html
<meta name="go-import" content="root-path vcs repo-url [subdirectory]">
```

Fields:

- `root-path` — repository root path либо path соответствующий declared `subdirectory`;
- `vcs` — VCS identifier или `mod`;
- `repo-url` — repository URL со scheme;
- `subdirectory` — optional repository subdirectory, поддерживаемый в этой форме Go 1.25+.

Если `root-path` — strict prefix requested path, Go делает дополнительный request для prefix и проверяет, что metadata согласована.

`GOINSECURE` может разрешить HTTP/insecure protocols specific module prefixes.

VCS support/default security:

| VCS | Command | Default GOVCS | Secure schemes |
| --- | --- | --- | --- |
| Bazaar | `bzr` | private only | `https`, `bzr+ssh` |
| Fossil | `fossil` | private only | `https` |
| Git | `git` | public/private | `https`, `git+ssh`, `ssh` |
| Mercurial | `hg` | public/private | `https`, `ssh` |
| Subversion | `svn` | private only | `https`, `svn+ssh` |

Popular hosting platforms вроде GitHub уже отвечают на `?go-get=1`; custom configuration обычно не нужна.

### Mapping versions to commits {#vcs-version}

Canonical semantic module version сопоставляется repository tag.

Если module в repository root (или major version subdirectory), tag обычно равен version:

```text
v1.2.3
```

Если module находится в subdirectory `gopls`, tag prefixed subdirectory:

```text
gopls/v0.4.0
```

Major version tag должен соответствовать major suffix module path.

Tag после публикации нельзя переставлять или удалять как normal workflow: immutable versions authenticated, и clients могут получить checksum/security errors. Даже удалённый tag content может оставаться cached module proxies.

### Mapping pseudo-versions to commits {#vcs-pseudo}

Последние 12 characters pseudo-version обычно кодируют revision prefix. Go проверяет timestamp и base ancestor tag перед checkout.

### Mapping branches and commits to versions {#vcs-branch}

Version query:

```bash
go get example.com/mod@master
```

или commit hash преобразуется в canonical semantic version, если revision tagged, иначе в pseudo-version. Если revision имеет несколько valid tags, выбирается highest suitable semantic version для target module path.

### Module directories within a repository {#vcs-dir}

После checkout Go ищет module root.

Если module path = repository root path, module root = repository root.

Если module path содержит subdirectory, `go.mod` должен находиться в corresponding subdirectory.

Для `/v2+` module `go.mod` может находиться:

- в base module subdirectory;
- либо в major version subdirectory, например `v2`.

Major version subdirectories позволяют разрабатывать несколько majors в одной branch и сохраняют directory/import compatibility для старых GOPATH-era tools.

Создавая module zip, Go исключает:

- vendor directories;
- nested modules, то есть subdirectories с собственным `go.mod`.

Поэтому `//go:embed` не должен ссылаться на files nested module.

### Special case for `LICENSE` files {#vcs-license}

Если module находится в subdirectory и в module root нет `LICENSE`, Go при создании zip копирует `LICENSE` repository root, если он существует в той же revision.

Special case действует только для exact filename `LICENSE` без extension.

Symlinks не входят в module zip, поэтому symlink на root license не является portable substitute; при необходимости license file следует копировать.

### Controlling VCS with `GOVCS` {#vcs-govcs}

`GOVCS` ограничивает VCS commands, которые Go может запускать при direct fetch.

Default policy эквивалентна:

```text
public:git|hg,private:all
```

General form:

```text
pattern:vcslist,pattern:vcslist
```

Example:

```text
GOVCS=github.com:git,evil.com:off,*:git|hg
```

Special patterns:

- `public` — paths, не matching `GOPRIVATE`;
- `private` — paths matching `GOPRIVATE`.

Values:

- `all` — any known VCS;
- `off` — none;
- `git|hg` — explicit allowlist.

First matching rule wins.

Allow all:

```text
GOVCS=*:all
```

Disable direct VCS entirely:

```text
GOVCS=*:off
```

Restrictions не применяются к module proxy protocol; proxy может безопасно sandbox'ить собственные VCS operations.

## Module zip files {#zip-files}

Module versions распространяются как `.zip` archives. Go автоматически создаёт, загружает и extract'ит их.

Programmatic support: package [`golang.org/x/mod/zip`](https://pkg.go.dev/golang.org/x/mod/zip).

### File path and size constraints {#zip-path-size-constraints}

Constraints обеспечивают safe portable extraction:

- zip file ≤ **500 MiB**;
- total uncompressed files ≤ **500 MiB**;
- `go.mod` ≤ **16 MiB**;
- `LICENSE` ≤ **16 MiB**;
- каждый path начинается `$module@$version/`;
- module path valid, version canonical и compatible с major suffix;
- modes/timestamps/metadata ignored;
- empty directories допустимы, но не extract'ятся;
- symlinks и irregular files игнорируются;
- directories named `vendor` игнорируются;
- nested modules (directories с `go.mod`) исключаются;
- никакие два file paths не могут быть equal under Unicode case folding;
- top-level `go.mod` optional; если есть, имя exact lowercase `go.mod`; другие `go.mod` внутри archive запрещены;
- names ограничены portable set Unicode letters/ASCII digits/space и разрешённой ASCII punctuation;
- basename до first dot не должен быть Windows reserved name независимо от case (`CON`, `NUL`, `COM1` и т. п.).

## Private modules {#private-modules}

Private modules могут храниться в private VCS и proxies.

Relevant variables:

- `GOPROXY` — ordered proxy sources / `direct`;
- `GOPRIVATE` — private module prefix patterns; default для `GONOPROXY` и `GONOSUMDB`;
- `GONOPROXY` — modules, которые нельзя запрашивать через proxies;
- `GONOSUMDB` — modules, которые нельзя проверять public checksum database;
- `GOINSECURE` — modules, для которых direct fetch может использовать insecure protocols.

### Private proxy serving all modules {#private-module-proxy-all}

Если корпоративный proxy обслуживает и private, и public modules:

```text
GOPROXY=https://proxy.corp.example.com
GONOSUMDB=corp.example.com
```

Go обращается только к corporate proxy; checksum database не используется для private prefix.

Proxy сам должен иметь доступ к private VCS и public internet либо собственному upstream source.

### Private proxy serving private modules {#private-module-proxy-private}

Если corporate proxy содержит только private modules:

```text
GOPROXY=https://proxy.corp.example.com,https://proxy.golang.org,direct
GONOSUMDB=corp.example.com
```

Fallback после private proxy происходит только на `404`/`410` при comma separator. Другие statuses, например `403`, terminal и могут использоваться как policy enforcement.

### Direct access to private modules {#private-module-proxy-direct}

Без private proxy:

```text
GOPRIVATE=corp.example.com
```

Default `GOPROXY=https://proxy.golang.org,direct` сохраняется, но modules matching `GOPRIVATE` обходят public proxy/checksum DB и fetch'ятся direct.

Module paths с explicit VCS suffix `.git` могут избежать отдельного `?go-get=1` discovery server.

VCS credentials должны быть configured non-interactively. Go отключает Git terminal prompts по умолчанию через `GIT_TERMINAL_PROMPT=0`, если explicit configuration не говорит иначе.

### Credentials for private proxies {#private-module-proxy-auth}

Proxy authentication поддерживает HTTP basic auth и headers, полученные через `GOAUTH`.

`.netrc` example:

```text
machine proxy.corp.example.com
login jrgopher
password hunter2
```

Location может задаваться `NETRC`; default `$HOME/.netrc` на Unix и `%USERPROFILE%\_netrc` на Windows.

`.netrc` не умеет scopes by URL path и не позволяет whitespace в login/password fields.

Go 1.24+ `GOAUTH` может:

- использовать `.netrc`;
- выполнить `git credential fill` в заданной working directory;
- вызвать custom command, возвращающий arbitrary HTTP headers для HTTPS URL prefixes.

Credentials `GOAUTH` применяются только к HTTPS.

Credentials можно встроить в `GOPROXY` URL:

```text
GOPROXY=https://jrgopher:hunter2@proxy.corp.example.com
```

но это risky: environment variable может попасть в shell history/logs.

### Credentials for private repositories {#private-module-repo-auth}

При direct mode authentication выполняют VCS tools, например Git. Configure `.gitconfig`, credential helpers, `.netrc` и т. п.

Go обычно предпочитает HTTPS URLs. URL rewriting Git может направить GitHub на SSH:

```ini
[url "git@github.com:"]
    insteadOf = https://github.com/
```

### Privacy {#private-module-privacy}

Default:

```text
GOPROXY=https://proxy.golang.org,direct
```

означает, что full module path сначала отправляется public proxy. Это не PII, но private path сам может раскрывать sensitive project names.

Чтобы private prefixes никогда не запрашивались public proxy:

```text
GOPRIVATE=*.corp.example.com,*.research.example.com
```

Если trusted corporate proxy обслуживает **все** modules, не задавайте `GONOPROXY`; вместо этого используйте только corporate `GOPROXY` и `GONOSUMDB` для private prefixes.

Если private proxy обслуживает только private modules, он должен корректно использовать error codes. `404`/`410` разрешают fallback и могут случайно leak'нуть misspelled private module path public proxy. Other error status предотвращает fallback.

Checksum database также получает full module path при lookup. `GONOSUMDB`/`GOPRIVATE` запрещают такие requests для private modules. `GOSUMDB=off` выключает checksum database полностью, но это уменьшает security для всех modules.

## Module cache {#module-cache}

Downloaded modules хранятся отдельно от build cache.

Default:

```text
$GOPATH/pkg/mod
```

Override:

```text
GOMODCACHE=/custom/path
```

Cache:

- shared несколькими Go projects;
- safe для concurrent access;
- не имеет automatic maximum size/cleanup;
- extracted module source обычно read-only, чтобы предотвратить accidental mutation.

Очистка:

```bash
go clean -modcache
```

Flag `-modcacherw` создаёт new cache directories writable, но повышает риск accidental changes.

`go mod verify` обнаруживает изменения downloaded zip/extracted source.

Основные paths:

| Path | Назначение |
| --- | --- |
| `$module@$version/` | Extracted module root. |
| `cache/download/` | Proxy/VCS-derived `.info`, `.mod`, `.zip` content; layout соответствует GOPROXY. |
| `cache/download/$module/@v/list` | Cached known versions list. |
| `cache/download/$module/@v/$version.info` | Version metadata. |
| `cache/download/$module/@v/$version.mod` | `go.mod` или synthetic mod file. |
| `cache/download/$module/@v/$version.zip` | Module archive. |
| `cache/download/$module/@v/$version.ziphash` | Hash contents archive. |
| `cache/download/sumdb/` | Checksum database data. |
| `cache/vcs/` | Cached direct VCS repositories, optimized (например bare/shallow Git where possible). |

Uppercase letters paths escape'ятся через `!` + lowercase, чтобы cache был portable.

## Authenticating modules {#authenticating}

После download `.zip` или `.mod` Go вычисляет cryptographic hash и сравнивает с known value.

Для `go.mod` hash вычисляется из content. Для module zip hash вычисляется deterministically из names и file contents; zip compression/order/metadata на hash не влияют.

Primary local record — `go.sum` main module. Hash mismatch — security error; bad content удаляется и не попадает в module cache.

Если hash отсутствует в `go.sum`, Go обычно проверяет его через global checksum database. Для private modules (`GOPRIVATE`/`GONOSUMDB`) или `GOSUMDB=off` hash принимается без public DB verification и записывается locally.

При чтении shared module cache Go всё равно сравнивает hashes с `go.sum` **current main module**, чтобы project не должен был доверять другим projects на машине.

### `go.sum` files {#go-sum-files}

`go.sum` находится рядом с `go.mod` и содержит cryptographic hashes direct/indirect dependencies.

Line format:

```text
module-path version hash
```

Если version заканчивается `/go.mod`, hash относится только к `go.mod`; иначе — к module zip contents.

Hash format:

```text
h1:<base64-sha256>
```

`go.sum` может содержать hashes нескольких versions одного module, потому что MVS может читать `go.mod` нескольких candidate versions и потому что old versions могут оставаться после upgrades.

`go mod tidy` добавляет missing и удаляет unnecessary sums.

### Checksum database {#checksum-database}

Checksum database — global append-only source `go.sum` lines public modules. Она позволяет clients обнаруживать, если proxy/origin пытается изменить content уже опубликованной version.

Default service:

```text
sum.golang.org
```

Он реализован как transparent log / Merkle tree. Independent auditors могут проверять consistency log.

Основные endpoints:

| Path | Назначение |
| --- | --- |
| `$base/latest` | Signed latest tree head/description. |
| `$base/lookup/$module@$version` | Record number + `go.sum` data + signed tree state. |
| `$base/tile/$H/$L/$K[.p/$W]` | Hash tiles Merkle log; optional partial tile. |
| `$base/tile/$H/data/$K[.p/$W]` | Leaf record data corresponding tile. |

Client:

1. делает `/lookup`;
2. получает module sums и position record;
3. fetch'ит required tiles;
4. выполняет inclusion proof;
5. выполняет consistency proof against previously trusted signed tree heads;
6. только после verification записывает new `go.sum` line.

Signed tree hashes/tiles cache'ятся locally.

Module proxy может mirror'ить checksum database, поэтому client не обязан соединяться с sumdb directly.

`GOSUMDB` forms:

```text
GOSUMDB="sum.golang.org"
GOSUMDB="sum.golang.org+<publickey>"
GOSUMDB="sum.golang.org+<publickey> https://sum.golang.org"
```

Go встроенно знает public key `sum.golang.org`; `sum.golang.google.cn` указывает на ту же database для mainland China. Other databases требуют explicit public key.

Disable:

```text
GOSUMDB=off
```

Предпочтительнее не выключать global verification, а исключать только private modules через `GOPRIVATE`/`GONOSUMDB`.

## Environment variables {#environment-variables}

Module-related variables:

### `GO111MODULE`

- `off` — GOPATH mode;
- `on` или unset — module-aware mode;
- `auto` — module-aware mode только при найденном `go.mod`; это было default в Go 1.15 и ниже.

### `GOMODCACHE`

Directory module cache. Default:

```text
$GOPATH/pkg/mod
```

### `GOINSECURE`

Comma-separated glob patterns module path prefixes, которым direct fetch разрешён через insecure transport. Не отключает checksum validation; для этого используются `GOPRIVATE`/`GONOSUMDB`.

### `GONOPROXY`

Comma-separated glob patterns modules, которые всегда fetch'ятся direct, а не через proxy. Если unset, default = `GOPRIVATE`.

### `GONOSUMDB`

Comma-separated patterns modules, которые не проверяются checksum database. Если unset, default = `GOPRIVATE`.

### `GOPATH`

В GOPATH mode — roots source/code workspace. В module-aware mode первый GOPATH также содержит default module cache `$GOPATH/pkg/mod`. Source main module может находиться где угодно.

Default GOPATH — `go` subdirectory user home.

### `GOPRIVATE`

Comma-separated glob patterns private module prefixes. Default для `GONOPROXY` и `GONOSUMDB`; также определяет public/private classification для `GOVCS`.

### `GOPROXY`

Ordered list proxy URLs, separated commas или pipes.

Comma `,`:

- fallback только после HTTP `404`/`410`.

Pipe `|`:

- fallback после **любой** error, включая timeout/non-HTTP failures.

Supported URL schemes:

- `https`;
- `http`;
- `file`.

Без scheme предполагается HTTPS.

Module cache может выступать file proxy:

```text
GOPROXY=file://$(go env GOMODCACHE)/cache/download
```

Special values:

- `off` — prohibit all module downloads;
- `direct` — direct VCS.

Default:

```text
https://proxy.golang.org,direct
```

### `GOSUMDB`

Checksum database name, optional public key и URL. Default `sum.golang.org`. `off` disables database.

### `GOVCS`

Controls VCS allowlist by path patterns. Default:

```text
public:git|hg,private:all
```

### `GOWORK`

- path to specific `go.work` — enable workspace mode using it;
- `off` — disable workspace mode;
- empty — search current/parent directories for `go.work`.

Example single-module forced build:

```bash
GOWORK=off go build .
```

## Glossary {#glossary}

**build constraint** — условие включения Go source file в package build, заданное filename suffix или build comment.

**build list** — module versions, используемые build command. Определяется requirements main module и transitive module graph через MVS.

**canonical version** — корректно formatted module version без arbitrary build metadata; `+incompatible` — special allowed suffix.

**current module** — synonym main module.

**deprecated module** — module, который authors больше не поддерживают; marked deprecation comment в `go.mod` latest version.

**direct dependency** — package directly imported package/test main module, либо module, предоставляющий такой package.

**direct mode** — configuration, при которой modules загружаются напрямую через VCS (`GOPROXY=direct` или matching `GOPRIVATE`/`GONOPROXY`).

**`go.mod` file** — file module root, определяющий module path, requirements и metadata.

**`go.work` file** — file, определяющий workspace modules и workspace-level replacements/settings.

**import path** — string в Go import declaration; synonym package path.

**indirect dependency** — transitively imported package/module, который не imported напрямую main module, либо graph module, не предоставляющий direct import main module.

**lazy module loading** — Go 1.17+ optimization, избегающая загрузки полного module graph, когда command этого не требует.

**main module** — module, в context которого выполняется `go` command; определяется nearest applicable `go.mod`, либо набором workspace modules.

**major version** — first semantic version number. Breaking release increment'ит major; v0 unstable.

**major version subdirectory** — repository subdirectory, соответствующий major suffix, например `v2`.

**major version suffix** — `/v2`, `/v3` и т. п. в module path; required v2+ и forbidden v0/v1, кроме special conventions вроде gopkg.in.

**minimal version selection (MVS)** — algorithm, выбирающий highest required version каждого module path из graph.

**minor version** — second semantic version number; backward-compatible new functionality increment'ит minor и reset patch.

**module** — collection packages, versioned/released/distributed together.

**module cache** — local storage downloaded modules, default `GOPATH/pkg/mod`.

**module graph** — directed graph module requirements rooted at main module; edges — `require` requirements после effective replacement/exclusion semantics.

**module graph pruning** — Go 1.17+ optimization, позволяющая omitting parts transitive graph modules с adequate explicit requirements.

**module path** — canonical module identifier и prefix package import paths.

**module proxy** — HTTP server implementing GOPROXY protocol.

**module root directory** — directory containing module's `go.mod`.

**module subdirectory** — part module path после repository root path и до major suffix, соответствующая repository subdirectory.

**package** — collection Go source files одного directory, compiled together.

**package path** — unique package identifier: module path + package subdirectory; synonym import path.

**patch version** — third semantic version number; release без public interface changes increment'ит patch.

**pre-release version** — semantic version с suffix после dash, например `v1.2.3-beta.4`; sorts before final release.

**pseudo-version** — version encoding VCS timestamp/revision, например `v0.0.0-20191109021931-daa7c04131f5`.

**release version** — semantic version без pre-release suffix.

**repository root path** — module path prefix, соответствующий VCS repository root.

**retracted version** — published version, которую authors указали не использовать из-за accidental release/severe problem.

**semantic version tag** — VCS tag, mapping semantic module version к revision.

**selected version** — version конкретного module path, выбранная MVS; highest version этого path в effective graph.

**vendor directory** — directory `vendor` с copies dependency packages, создаваемый `go mod vendor`.

**version** — immutable module snapshot identifier вида `v` + semantic version.

**workspace** — collection modules on disk, рассматриваемых как main modules при MVS и выполнении Go commands.
