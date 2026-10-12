# Stage 11 — Security и hardening

## Цель

Применить Go security tooling и threat-model thinking к уже существующему service, не сводя security к «запустить scanner».

## Перед началом

Production-shaped HTTP/DB application с dependencies.

## Прочитать

1. [[../../docs/security/index|Безопасность Go]].
2. [[../../docs/security/best-practices|Security Best Practices]].
3. [[../../docs/tutorial/govulncheck|govulncheck tutorial]].
4. [[../../docs/security/vuln/index|Go Vulnerability Management]].
5. [[../../docs/security/threat-model|Go Threat Model]].
6. Повторить [[../../docs/security/fuzz/index|Fuzzing]] и [[../../docs/race-detector|Race Detector]] как security-relevant tools.
7. Reference по необходимости: [[../../docs/security/policy|Security Policy]], [[../../docs/security/decisions|Security Decisions]], [[../../docs/security/vuln/database|Vulnerability DB]], [[../../docs/security/vuln/editor|IDE scanning]].
8. [[../../docs/security/fips140|FIPS 140-3]] — optional, только если появится соответствующее compliance требование.

## Что необходимо понять

- [ ] vulnerability version presence ≠ reachable vulnerable symbol.
- [ ] `govulncheck` source analysis использует reachability/call graph.
- [ ] dependency update требует tests/review, а не механического latest.
- [ ] fuzzing ищет adversarial/edge inputs по invariants.
- [ ] race может нарушить security boundary.
- [ ] `go vet` — baseline analyzer, не security proof.
- [ ] untrusted HTTP/JSON/file input имеет explicit limits.
- [ ] path/SQL identifiers/URLs/config values проходят appropriate validation/allowlisting.
- [ ] secrets/logging/errors формируют отдельный trust boundary.

## Что НЕ нужно пока изучать

- Go Security Team disclosure process в деталях;
- CVE CNA administration;
- FIPS implementation internals без business requirement;
- cryptographic primitive implementation.

## Практика

- [[../practice/12-security|Security hardening]].

## Эксперименты

- подключить intentionally vulnerable tutorial dependency только в isolated sample и сравнить module finding vs reachable finding;
- пропустить malformed JSON/file payload через fuzz target;
- в toy endpoint убрать input size limit и описать DoS path;
- сравнить user-controlled SQL value parameterization и dynamic identifier allowlist.

## Проверка себя

1. Чем `govulncheck` полезнее простого списка CVE dependencies?
2. Почему «не reachable сейчас» не равно «можно никогда не обновлять»?
3. Какие inputs pricing service считаются untrusted?
4. Где resource exhaustion является частью threat model?
5. Какие проверки должны выполняться в CI, а какие требуют design review?
6. Когда custom crypto — плохая идея?

## Практическая проверка

Составить короткий threat model `pricing-api`: assets, trust boundaries, untrusted inputs, resource limits, dependency risks, SQL/JSON handling, secrets, logs. Затем внедрить automated `go vet`, `go test -race`, targeted fuzz и `govulncheck` gate.

## Критерий завершения

Я могу перейти дальше, если способен:

- объяснить reachable vulnerability path;
- сформулировать resource/input boundaries;
- использовать Go-native security tooling;
- превратить fuzz/race findings в regression tests;
- отличать tool finding от реального risk assessment.

## Следующий этап

[[12-performance|Stage 12 — Performance and diagnostics]].
