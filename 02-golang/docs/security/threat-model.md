---
title: "Go Threat Model"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/security/threat-model.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Go Threat Model

Если package documentation не задаёт отдельный threat model, для standard library/toolchain предполагается этот общий model.

## Build safety

Сборка Go code предполагается безопасной и не должна иметь неожиданных side effects вроде исполнения attacker code.

## Runtime execution

Запуск malicious code сам по себе не считается vulnerability Go. Пользователь считается ответственным за решение выполнить program.

## Memory safety

При отсутствии `unsafe` runtime/language должны обеспечивать memory safety в рамках documented model.

## Trust boundaries

APIs, разумно ожидающие arbitrary user input, должны быть hardened против panic и произвольного resource exhaustion.

Garbage input, который просто даёт unexpected output, не обязательно является security issue.

## Environment control

Local OS/system считается trusted. Attacks, требующие уже скомпрометированного filesystem, arbitrary environment variables/PATH control либо process memory access, вне threat model.

## Packages с отдельной security model

Отдельные security notes/models имеют, среди прочих:

- `encoding/json`;
- `encoding/json/v2`;
- `encoding/json/jsontext`;
- `encoding/gob`;
- `html/template`;
- `image`;
- `debug/pe`, `debug/macho`, `debug/dwarf`, `debug/plan9obj`, `debug/elf`.

При использовании этих packages их package-level security model имеет приоритет над general assumptions.
