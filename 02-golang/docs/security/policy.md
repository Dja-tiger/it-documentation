---
title: "Go Security Policy"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/policy.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Go Security Policy

## Обзор

Этот документ объясняет process Go Security team для обработки полученных reports и то, какого ответа можно ожидать.

## Reporting security bug

Все security bugs в Go distribution следует отправлять по email на [security@golang.org](mailto:security@golang.org). Письмо доставляется Go Security team.

Используйте subject:

```text
Vulnerability: {package name}: {one-line summary}
```

Не отправляйте attachments без строгой необходимости, чтобы message не была помечена как spam.

При желании укажите preferred attribution. Если будет опубликован CVE, attribution будет добавлена в него.

Reports должны быть краткими и содержать:

- описание найденной issue;
- способ, которым, по вашему мнению, issue можно exploit'ить;
- небольшой reproduction test case или program.

Перед отправкой полезно проверить [[decisions|список решений по часто сообщаемым категориям issues]].

Email будет acknowledged в течение 7 days. Если reply не пришёл, повторно напишите Go Security team на `security@golang.org`. Убедитесь, что в message присутствует слово **vulnerability**.

Если ещё через 3 days acknowledgement нет, письмо могло попасть в spam. В таком случае [создайте report здесь](https://g.co/vulnz), выберите:

> I want to report a technical security or an abuse risk related bug in a Google product (SQLi, XSS, etc.)

и укажите `Go` как affected product.

Issue будет исправлена или раскрыта публично не позднее чем через 90 days после initial acknowledgement.

Emails с security reports сохраняются indefinitely для tracking remediation status и правильной attribution discoveries.

### LLM-generated reports

Не отправляйте LLM-generated reports без proper curation.

Современные LLM хорошо находят реальные и важные security bugs, но также хорошо находят imaginary issues или реальные issues, которые [[decisions#non-vuln|не являются security bugs]]. LLM output часто verbose, скрывает важную information среди irrelevant text и содержит громкие, но необоснованные claims.

Для LLM-generated reports ценность заключается в **curation**.

Если отправить десятки possible security issues и ожидать, что Go Security team сама найдёт одну значимую среди остальных, это перекладывает curation на team и мешает цели делать Go безопаснее.

Поэтому attribution даётся только reporters, у которых существенная доля reports оказывается реальными findings.

Жёсткого numeric threshold нет. В качестве general guideline: если большинство reports не признаются security issues и team не считает curation полезной, attribution за последующие discoveries предоставляться не будет.

Конкретный threshold для «most» и формальное определение «curation» намеренно не задаются. Цель правила — всегда признавать good-faith reporters, которые реально создают value, и не поощрять indiscriminate forwarding больших объёмов LLM output.

## Tracks

В зависимости от nature issue Go Security team относит её к одному из tracks:

- `PUBLIC`;
- `PRIVATE`;
- `URGENT`.

Все security issues получают CVE numbers.

Go Security team не назначает традиционные fine-grained severity labels вроде `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, потому что severity сильно зависит от того, как user использует affected API/functionality.

По той же причине при выпуске CVE Go team не назначает CVSS scores и не считает этот scoring system подходящим для Go.

Third parties, например MITRE или NIST через NVD, могут назначать CVSS scores, но Go team не endorses эти scores как точное отражение impact.

Например, impact resource exhaustion issue в `encoding/json` parser зависит от того, что parsing'ится:

- trusted JSON files из local filesystem — impact, вероятно, low;
- arbitrary untrusted JSON из HTTP request body — impact может быть значительно выше.

При этом tracks всё же дают signal о perceived severity и breadth issue.

Issue с medium-to-significant impact для многих users обычно относится к `PRIVATE`, а issue с negligible/minor impact или затрагивающая небольшую subset users — к `PUBLIC`.

### PUBLIC

Issues `PUBLIC` track:

- затрагивают niche configurations;
- имеют очень ограниченный impact;
- либо уже широко известны.

PUBLIC issues получают label [`Proposal-Security`](https://github.com/golang/go/labels/Proposal-Security), обсуждаются через [Go proposal review process](https://go.googlesource.com/proposal/+/master/README.md#proposal-review), **исправляются публично** и backport'ятся в следующие scheduled [minor releases](https://go.dev/wiki/MinorReleases), которые обычно выходят примерно monthly.

Release announcement содержит details issues, но отдельного pre-announcement нет.

Examples прошлых PUBLIC issues:

- [#44916](https://go.dev/issue/44916): `archive/zip`: panic при `Reader.Open`;
- [#44913](https://go.dev/issue/44913): `encoding/xml`: infinite loop при `xml.NewTokenDecoder` с custom `TokenReader`;
- [#43786](https://go.dev/issue/43786): `crypto/elliptic`: incorrect operations на P-224 curve;
- [#40928](https://go.dev/issue/40928): `net/http/cgi`, `net/http/fcgi`: XSS при отсутствии `Content-Type`;
- [#40618](https://go.dev/issue/40618): `encoding/binary`: `ReadUvarint`/`ReadVarint` могут читать unlimited bytes из invalid inputs;
- [#36834](https://go.dev/issue/36834): `crypto/x509`: certificate validation bypass в Windows 10.

### PRIVATE

Issues `PRIVATE` track — violations committed security properties.

PRIVATE issues **исправляются в следующем scheduled minor release** и остаются private до этого момента.

За 3–7 days до release в `golang-announce` отправляется pre-announcement, сообщающий:

- что upcoming releases содержат один или несколько security fixes;
- затрагивают ли issues standard library, toolchain или оба;
- reserved CVE IDs каждого fix.

Для issues, присутствующих в major version release candidate, используется тот же process: fix включается в следующий scheduled RC.

Examples прошлых PRIVATE issues:

- [#53416](https://go.dev/issue/53416): `path/filepath`: stack exhaustion в `Glob`;
- [#53616](https://go.dev/issue/53616): `go/parser`: stack exhaustion во всех `Parse*` functions;
- [#54658](https://go.dev/issue/54658): `net/http`: handling server errors после GOAWAY;
- [#56284](https://go.dev/issue/56284): `syscall`, `os/exec`: unsanitized NUL в environment variables.

### URGENT

Issues `URGENT` track угрожают integrity Go ecosystem либо активно exploit'ятся в wild с severe damage.

Недавних examples нет, но к этому классу относились бы:

- remote code execution в `net/http`;
- practical key recovery в `crypto/tls`.

URGENT issues исправляются private и **вызывают immediate dedicated security release**, возможно без pre-announcement.

## Existing issues, оказавшиеся security-related

Если вы считаете, что [существующая issue](https://go.dev/issue) security-related, отправьте email на [security@golang.org](mailto:security@golang.org).

Укажите issue ID и кратко объясните, почему её следует обрабатывать по этой security policy.

## Disclosure process

Go project использует следующий process:

1. После получения security report назначается primary handler, который координирует fix и release process.
2. Issue подтверждается и определяется список affected software.
3. Code audit'ится для поиска возможных аналогичных problems.
4. Если после консультации с submitter решено, что требуется CVE number, primary handler получает его.
5. Fixes готовятся для двух последних major releases и `head/master`; fixes для двух последних releases также merge'ятся в `head/master`.
6. В день применения fixes announcements отправляются в [golang-announce](https://groups.google.com/group/golang-announce), [golang-dev](https://groups.google.com/group/golang-dev) и [golang-nuts](https://groups.google.com/group/golang-nuts).

Process может занимать время, особенно если нужна coordination с maintainers других projects. Team старается обработать bug максимально быстро, но соблюдение процесса необходимо для consistent disclosure.

Security issues с CVE публикуются под product `Golang` на [CVEDetails](https://www.cvedetails.com/vulnerability-list/vendor_id-14185/Golang.html), а также в [National Vulnerability Database](https://web.nvd.nist.gov/view/vuln/search).

## Получение security updates

Лучший способ получать security announcements — подписаться на [golang-announce](https://groups.google.com/forum/#!forum/golang-announce).

Messages, относящиеся к security issue, имеют prefix:

```text
[security]
```

## Comments по policy

Предложения по улучшению policy можно обсуждать через [Go issue tracker](https://go.dev/issue/new).
