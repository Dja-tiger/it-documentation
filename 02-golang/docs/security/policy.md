---
title: "Go Security Policy"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/policy.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Go Security Policy

Документ описывает процесс Go Security Team для обработки security reports.

## Как сообщить vulnerability

Security bugs Go distribution отправляются на:

```text
security@golang.org
```

Рекомендованный subject:

```text
Vulnerability: {package name}: {one-line summary}
```

Не прикладывайте attachments без необходимости, чтобы письмо не попало в spam. Укажите preferred attribution, если хотите, чтобы оно попало в CVE.

Хороший report содержит:

- краткое описание issue;
- realistic exploitation path;
- маленький reproducible test/program;
- affected package/version/environment.

Сначала полезно проверить [[decisions|список classification decisions]], чтобы не отправлять категории, которые Go team сознательно не считает vulnerabilities.

Security team ожидает acknowledgement в течение **7 дней**. Если ответа нет, следует повторно написать на security address. Если ещё через 3 дня acknowledgement нет, policy предлагает fallback через Google vulnerability-report channel и указать Go как affected product.

Issue должно быть исправлено или раскрыто публично не позднее **90 дней** после initial acknowledgement.

Security-report emails сохраняются для tracking remediation и attribution.

## LLM-generated reports

Не отправляйте необработанный массовый LLM output.

LLMs способны находить реальные bugs, но также генерируют ложные/не-security findings, чрезмерно длинные explanations и необоснованные severity claims. Ценность reporter'а — в **curation**: подтвердить issue, удалить noise, показать exploitability и reproduction.

Go team прямо предупреждает: массовая пересылка uncurated LLM findings перекладывает triage на security team и мешает основной задаче. Attribution может не предоставляться reporter'ам, у которых большинство submissions не являются полезными security findings.

## Tracks

Go не назначает собственные CRITICAL/HIGH/MEDIUM/LOW или CVSS. Impact сильно зависит от use context. Например parser resource exhaustion почти безвреден для trusted local config и критичен для untrusted HTTP body.

Все security issues получают CVE, но обрабатываются по трём tracks.

### PUBLIC

Для niche configurations, очень ограниченного impact либо уже широко известной проблемы.

- обсуждается через публичный proposal/security process;
- исправляется публично;
- backport идёт в следующий scheduled minor release (примерно monthly cadence);
- release announcement описывает issue;
- отдельного pre-announcement нет.

### PRIVATE

Нарушение заявленных security properties со значимым impact.

- fix готовится private;
- попадает в следующий scheduled minor release;
- за 3–7 дней отправляется pre-announcement в `golang-announce`;
- pre-announcement сообщает область (stdlib/toolchain) и reserved CVE IDs;
- аналогичный процесс применяется к affected release candidates.

### URGENT

Threat ecosystem integrity либо active exploitation с severe damage.

Examples класса: practical remote code execution в `net/http`, key recovery в `crypto/tls`.

- fix private;
- немедленный dedicated security release;
- pre-announcement может отсутствовать.

## Existing public issue оказался security-sensitive

Не раскрывайте дополнительные exploit details в public issue. Напишите на `security@golang.org`, укажите issue ID и почему он должен обрабатываться по security policy.

## Disclosure process

1. Report получает primary handler.
2. Подтверждается issue и affected software.
3. Выполняется audit похожих issues.
4. При необходимости резервируется/назначается CVE.
5. Fixes готовятся для двух последних major Go releases и current development head.
6. В disclosure date fixes публикуются, а announcements отправляются в `golang-announce`, `golang-dev`, `golang-nuts`.

Cross-project coordination может увеличить фактическую сложность подготовки, но process должен оставаться последовательным.

## Получение security updates

Основной channel — mailing list `golang-announce`; security messages имеют prefix `[security]`.

Предложения по policy можно обсуждать через Go issue tracker.
