---
title: "Security Best Practices for Go Developers"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/best-practices.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Security Best Practices for Go Developers

[[index|Назад к Go Security]]

Эта страница содержит best practices для Go developers, которые хотят уделять приоритетное внимание security своих projects. От automated testing через fuzzing до простой проверки race conditions — эти рекомендации помогают сделать codebase более безопасной и надёжной.

## Проверяйте source code и binaries на vulnerabilities

Регулярное scanning code и binaries помогает обнаруживать potential security risks на раннем этапе.

Для этого можно использовать [`govulncheck`](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck), работающий на основе [Go vulnerability database](https://pkg.go.dev). Tool сканирует code на known vulnerabilities и анализирует, какие из них действительно затрагивают application.

Начать можно с [[../tutorial/govulncheck|govulncheck tutorial]].

`govulncheck` можно интегрировать в CI/CD flows.

Go team предоставляет [GitHub Action for govulncheck](https://github.com/marketplace/actions/golang-govulncheck-action) в GitHub Marketplace.

Также `govulncheck` поддерживает flag `-json`, упрощающий integration vulnerability scanning с другими CI/CD systems.

Vulnerabilities можно проверять и прямо в code editor через [[vuln/editor|Go extension for Visual Studio Code]]. Для начала доступен [tutorial](https://go.dev/doc/tutorial/govulncheck-ide).

## Поддерживайте Go version и dependencies актуальными

Использование [актуальной Go version](https://go.dev/doc/install) предоставляет latest language features, performance improvements и fixes известных security vulnerabilities.

Актуальная Go version также улучшает compatibility с newer versions dependencies и помогает избегать integration issues.

[Go release history](https://go.dev/doc/devel/release) показывает changes между releases.

Go team выпускает point releases на протяжении release cycle для исправления security bugs. Обновляйтесь до latest minor Go version, чтобы получать latest security fixes.

Поддерживать актуальными third-party dependencies также важно для software security, performance и compliance с latest standards Go ecosystem.

Однако бездумное обновление до latest versions [тоже может быть рискованным](https://research.swtch.com/npm-colors): можно получить новые bugs, incompatible changes или даже malicious code.

Поэтому dependencies следует обновлять ради security patches и improvements, но каждое update нужно внимательно review'ить и test'ировать.

## Используйте fuzzing для поиска edge-case exploits

[[fuzz/index|Fuzzing]] — вид automated testing, использующий coverage guidance для изменения random inputs и прохождения разных code paths с целью найти potential vulnerabilities, например:

- SQL injections;
- buffer overflows;
- denial of service;
- cross-site scripting attacks.

Fuzzing часто достигает edge cases, которые programmers пропускают или считают слишком маловероятными для manual tests.

Начать можно с [[../tutorial/fuzz|tutorial по fuzzing]].

## Проверяйте race conditions через Go race detector

Race condition возникает, когда две или более [goroutines](https://go.dev/tour/concurrency/1) одновременно обращаются к одному resource и хотя бы одно обращение является write.

Это может приводить к unpredictable и трудно диагностируемым problems.

Используйте встроенный [[../race-detector|race detector]], чтобы находить potential race conditions и повышать safety/reliability concurrent programs.

Race detector обнаруживает только races, которые действительно происходят во время runtime, поэтому не найдёт races в code paths, которые не выполняются.

Чтобы использовать detector, добавьте `-race` при tests или build application, например:

```text
go test -race
```

Code будет compiled с включённым race detector. Если detector обнаружит data race, он [выведет report](https://go.dev/doc/articles/race_detector#report-format), содержащий stack traces conflicting accesses и stacks мест создания участвующих goroutines.

## Используйте Vet для анализа suspicious constructs

Команда [`go vet`](https://pkg.go.dev/cmd/vet) анализирует source code и отмечает potential issues, которые могут не быть syntax errors, но способны привести к problems во время runtime.

Среди них suspicious constructs вроде unreachable code, unused variables и распространённых ошибок вокруг goroutines.

Раннее обнаружение таких issues помогает поддерживать code quality, сокращать debugging time и повышать software reliability.

Запуск для project:

```text
go vet ./...
```

## Подпишитесь на golang-announce для уведомлений о security releases

Go releases, содержащие security fixes, заранее анонсируются в low-volume mailing list [golang-announce@googlegroups.com](https://groups.google.com/group/golang-announce).

Если вам важно знать о готовящихся security fixes самого Go, подпишитесь на этот list.
