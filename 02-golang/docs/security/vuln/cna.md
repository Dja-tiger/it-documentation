---
title: "Go CNA Policy"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/vuln/cna.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Go CNA Policy

Go CNA — CVE Numbering Authority, sub-CNA Google CNA. Она назначает CVE IDs и публикует CVE Records для public vulnerabilities в определённом Go ecosystem scope.

## Scope

Включены:

- Go project standard library;
- Go sub-repositories (`golang.org/x/...`);
- public vulnerabilities importable Go modules, если module не входит в scope другой CNA.

Исключены application-only/non-importable packages, например обычный `package main` executable. Такие reports могут исключаться из Go vulnerability database как `NOT_IMPORTABLE`.

Undisclosed vulnerabilities Go project отправляются по [[../policy|Go Security Policy]].

## Запрос CVE для уже public vulnerability

Official vuln database reporting form может одновременно запросить CVE ID для существующей **PUBLIC** vulnerability Go ecosystem.

> [!danger]
> Эта form создаёт **public issue**. Никогда не используйте её для undisclosed vulnerability. Private report отправляется через security policy channel.

Public считается issue, который уже disclosed, либо находится в package, который вы maintain, и вы готовы немедленно disclosed его публично.
