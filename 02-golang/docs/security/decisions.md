---
title: "Go Security Decisions"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/decisions.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Go Security Decisions

## Обзор {#overview}

Этот документ содержит решения Go Security team по различным часто сообщаемым issues. В основном он служит reference для случаев, которые team **не считает vulnerability**.

Список не является исчерпывающим.

## Общие принципы {#principles}

Не каждый bug является vulnerability.

Практически для любого bug можно придумать hypothetical scenario, в котором он приводит к vulnerability.

Например, представим bug в image decoder, из-за которого некоторые inputs decode'ятся неправильно. Теперь представим hypothetical system, принимающую фотографии бумажных cheques и выполняющую bank transfers для их оплаты. Если system содержит gateway, который validates request, и backend, который выполняет transfer, parser differential между image decoders gateway и backend может привести к тому, что gateway пропустит malicious operation в backend.

Классифицировать image misparsing bug как vulnerability только на основании такого scenario бесполезно. Warning users о «vulnerability» такого рода создаёт шум, поскольку почти никто из users реально не затронут.

Такое использование термина даже вредит security: users привыкают считать reports в основном бессмысленными и начинают их игнорировать.

Этот example также объясняет, почему Go team не назначает severity labels security issues. Для hypothetical cheque processor issue может быть high severity, но для большинства users это вообще не issue.

Общий принцип: одной лишь возможности построить hypothetical scenario, где bug приводит к security issue, недостаточно, чтобы сам bug обрабатывался как security issue.

## Vulnerabilities {#vulns}

### Remote Code Execution {#rce}

Scenario, позволяющий attacker выполнять code там, где code execution не ожидается, является PRIVATE-track vulnerability.

Это правило имеет priority над всеми остальными decisions.

Оно не относится к functions, назначение которых — выполнять code.

В scope:

- parse function исполняет code на malicious input;
- malicious request заставляет HTTP server исполнять code.

Не в scope:

- command `go test` запускает tests. Запуск `go test` над attacker-controlled tests не входит в threat model.

### Panics {#panics}

Panic при processing attacker-controlled input может быть vulnerability.

Panic в server, который должен обрабатывать attacker-controlled requests, например `net/http` server, обычно является PRIVATE-track vulnerability.

Panic в client, например `net/http` client, обычно является PUBLIC-track vulnerability.

Panic в parse function package, работающего с plausibly malicious input, например `archive/zip` или `image/png`, обычно является PUBLIC-track vulnerability.

Input, вызывающий panic из-за своего естественного размера, например очень большое image, обычно не классифицируется как vulnerability.

Invalid inputs для functions, которые явно не предназначены для parsing potentially malicious data, находятся вне threat model и обычно не рассматриваются как security bugs.

Например, image **parsers** должны защищаться от invalid inputs, но panic в image **encoder** может быть bug, не являясь vulnerability.

Panic в deprecated function не считается vulnerability; см. decision по [deprecated APIs](#deprecated).

### Excessive resource consumption {#quadratic}

Excessive CPU или memory consumption, например function с runtime `O(n²)` относительно input size, обычно рассматривается так же, как panic.

### Сборка malicious code {#malicious-build}

Сборка attacker-controlled program должна быть безопасной, даже если запуск такой program небезопасен.

Например, предполагается, что untrusted code можно безопасно **собрать**, после чего запускать его в sandbox.

При этом Go team настоятельно рекомендует считать это defense-in-depth measure и выполнять сам build untrusted code также в unprivileged sandbox environment.

**Data exfiltration не входит в threat model.** Сборка attacker-controlled program может создать output, содержащий contents arbitrary local files.

**Execution malicious code также не входит в threat model.** Запущенная malicious program очевидно может выполнять malicious actions.

Vulnerability, обычно PRIVATE track:

- malicious module заставляет `go build` выполнить arbitrary code.

Не обрабатываются как security issues:

- `go build` выводит error, содержащий text arbitrary local file;
- compiled executable содержит contents arbitrary local file;
- malicious program может повредить runtime state и выполнить arbitrary code;
- compilation bug позволяет obfuscate malicious code.

## Non-Vulnerabilities {#non-vuln}

### Attacker-controlled environment {#attacker-control}

Если attack требует, чтобы attacker уже контролировал environment, в котором работает program, это не vulnerability.

Сюда, среди прочего, относятся возможности:

- добавлять programs в `$PATH`;
- задавать arbitrary environment variables.

### Deprecated APIs {#deprecated}

Порог, при котором bug deprecated API считается security issue, выше, чем для supported API.

В частности, panic или excessive resource consumption в deprecated API **никогда** не обрабатываются как vulnerability.

Users, которым требуется security hardening, должны использовать supported APIs.

### `image`, `x/image`: большие images {#large-image}

Parsing большого image может потребовать большой объём memory.

Например, 65536×65536 image с 32-bit color требует 16 GiB для хранения uncompressed.

Многие image compression formats способны сжать большое простое image до очень маленького file size. Поэтому decoding маленького file может выделить огромное количество memory.

Users, parsing'ящие untrusted images, должны проверять image size до decoding, например через [`image.DecodeConfig`](https://pkg.go.dev/image#DecodeConfig).

Go team не считает vulnerability ситуацию, когда image parsing function корректно decodes очень большое, хорошо сжатое image.

### `net/http`: redirects {#http-redirect}

HTTP client package `net/http` обрабатывает redirects и содержит security-relevant behavior.

Например, он удаляет header `Authorization` при redirect на domain, который не является subdomain или exact match initial request domain.

Header stripping — defense-in-depth measure, защищающая от ситуации, когда misconfigured или compromised server случайно пересылает client request с sensitive headers на untrusted destination.

Сам по себе failure удалить headers при redirect не позволяет attacker получить credentials из headers. Но его можно объединить с другими vulnerabilities, например open redirect на server, и добиться такого результата.

Изменение HTTP client behavior имеет высокий risk сломать existing users, зависящих от текущего поведения.

Например, current same-origin policy client разрешает subdomains: redirect с `example.com` на `www.example.com` сохраняет headers, тогда как WHATWG Fetch standard этого не делает.

Возможно, align client со standard полезно, но делать это в security release скорее причинит existing users проблемы, чем исправит реальные vulnerabilities.

Поскольку redirect sanitization является defense-in-depth, а изменение behavior рискованно, **все аспекты HTTP client redirects считаются вне security bug process**.
