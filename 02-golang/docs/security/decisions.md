---
title: "Go Security Decisions"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/decisions.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Go Security Decisions

Справочник классификационных решений Go Security Team. Главная идея: **не каждый bug — vulnerability**. Возможность придумать гипотетическую систему, где любой bug становится security-sensitive, недостаточна для security classification; иначе reports превращаются в шум.

Severity также context-dependent, поэтому Go team не считает generic severity score универсальной характеристикой.

## Что считается vulnerability

### Remote Code Execution

Unexpected attacker-triggered code execution — PRIVATE-track vulnerability и имеет приоритет над другими classification rules.

В scope:

- parser исполняет код из malicious input;
- malicious HTTP request приводит к execution кода server process.

Не в scope: команда, назначение которой изначально состоит в выполнении attacker-controlled code/tests, например запуск `go test` над malicious test source.

### Panics

Panic на attacker-controlled input может быть vulnerability.

Обычно:

- server API, ожидающий untrusted requests → PRIVATE;
- client API → PUBLIC;
- parser plausible malicious formats (`archive/zip`, `image/png`) → PUBLIC.

Panic только из-за естественно огромного valid input обычно не vulnerability. Invalid input в API, не предназначенный для parsing untrusted data, обычно также вне security process.

Deprecated API имеет более высокий bar; panic/resource exhaustion там policy не считает vulnerability.

### Excessive resource consumption

Pathological CPU/memory growth (например `O(n²)` на attacker-controlled input) обычно оценивается примерно как panic/DoS.

### Build safety

Сборка untrusted Go code должна быть безопасной как defense-in-depth: build не должен неожиданно исполнять attacker code.

Security issue: malicious module заставляет `go build` выполнить arbitrary code.

Не security issue в этой threat model:

- build error раскрывает text local file;
- output binary содержит local file contents;
- запущенная malicious program ломает runtime state;
- compiler bug только помогает obfuscation malicious code.

Build untrusted code всё равно рекомендуется выполнять в unprivileged sandbox.

## Что обычно не считается vulnerability

### Attacker уже управляет environment

Если attack требует control OS/filesystem/PATH/environment variables/memory process, это вне модели: local system считается trusted boundary.

### Deprecated APIs

Panic или excessive resource consumption в deprecated API не обрабатываются как vulnerability. Security-hardening users должны переходить на supported APIs.

### Large images

Хорошо сжатое огромное изображение может потребовать огромный uncompressed buffer. Это естественное свойство input, не vulnerability само по себе. При untrusted images сначала проверяйте dimensions через `image.DecodeConfig` и применяйте application limits.

### `net/http` redirects

HTTP client stripping sensitive headers при redirects — defense-in-depth. Поведение same-origin/subdomain имеет compatibility implications, а сам open redirect обычно находится на server side. Поэтому Go policy выводит детали redirect sanitization из security bug process, чтобы не ломать users risky emergency changes.
