---
title: "Go CNA Policy"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/vuln/cna.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Go CNA Policy

[[index|Назад к Go Vulnerability Management]]

## Обзор

Go CNA — [CVE Numbering Authority](https://www.cve.org/ProgramOrganization/CNAs), которая назначает [CVE IDs](https://www.cve.org/ResourcesSupport/Glossary?activeTerm=glossaryCVEID) и публикует [CVE Records](https://www.cve.org/ResourcesSupport/Glossary?activeTerm=glossaryRecord) для public vulnerabilities в Go ecosystem.

Go CNA является sub-CNA Google CNA.

## Scope

Go CNA покрывает:

- vulnerabilities в Go project — [standard library](https://pkg.go.dev/std) и [sub-repositories](https://pkg.go.dev/golang.org/x);
- public vulnerabilities в importable Go modules, которые ещё не покрываются другой CNA.

Scope намеренно исключает vulnerabilities в applications или packages, написанных на Go, но не importable другими modules, например code в `package main`.

Подробнее об excluded reports см. [[database#excluded-reports|Go Vulnerability Database — Excluded Reports]].

Чтобы сообщить potential new vulnerability в Go project, используйте [[../policy|Go Security Policy]].

## Запрос CVE ID для public vulnerability

> [!important]
> Form ниже создаёт **public issue** в issue tracker и поэтому **не должна** использоваться для reporting undisclosed vulnerabilities в Go. Для undisclosed issues следуйте [[../policy|Security Policy]].

Чтобы запросить CVE ID для существующей **PUBLIC** vulnerability в Go ecosystem, [отправьте request через эту form](https://go.dev/s/vulndb-report-new).

Vulnerability считается public, если она:

- уже была disclosed publicly;
- либо существует в package, который вы maintain'ите, и вы готовы disclose её публично.
