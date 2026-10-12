---
title: "Tutorial: поиск уязвимых dependencies через govulncheck"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/govulncheck.md"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Поиск и исправление уязвимых dependencies через `govulncheck`

`govulncheck` — low-noise security tool для Go. Он не ограничивается вопросом «есть ли у module известная vulnerability»: tool анализирует dependency graph и call graph, чтобы понять, вызывает ли ваш код vulnerable symbols прямо или косвенно.

Это помогает отделять реально reachable vulnerabilities от informational findings.

## Что будет сделано

1. Создать sample module с intentionally vulnerable dependency.
2. Установить и запустить `govulncheck`.
3. Оценить findings по reachability/impact.
4. Обновить dependency до fixed version.
5. Повторить scan.

## Sample module

```bash
mkdir vuln-tutorial
cd vuln-tutorial
go mod init vuln.tutorial
```

`main.go`:

```go
package main

import (
    "fmt"
    "os"

    "golang.org/x/text/language"
)

func main() {
    for _, arg := range os.Args[1:] {
        tag, err := language.Parse(arg)
        if err != nil {
            fmt.Printf("%s: error: %v\n", arg, err)
        } else if tag == language.Und {
            fmt.Printf("%s: undefined\n", arg)
        } else {
            fmt.Printf("%s: tag %s\n", arg, tag)
        }
    }
}
```

Подтяните dependencies:

```bash
go mod tidy
```

Tutorial намеренно понижает `golang.org/x/text` до vulnerable version:

```bash
go get golang.org/x/text@v0.3.5
```

`go.mod`:

```text
module vuln.tutorial

go 1.20

require golang.org/x/text v0.3.5
```

## Установка и запуск `govulncheck`

```bash
go install golang.org/x/vuln/cmd/govulncheck@latest
```

Scan current module:

```bash
govulncheck ./...
```

Tutorial output показывает два findings для `golang.org/x/text@v0.3.5`:

- `GO-2021-0113` — reachable: application вызывает `language.Parse`, уязвимый symbol достижим;
- `GO-2022-1059` — informational: vulnerability существует в imported module, но call stacks из application к vulnerable symbols не найдены.

Именно reachability делает `govulncheck` менее шумным, чем простой CVE/module-version matching.

## Как читать finding

Typical finding включает:

- Go vulnerability ID;
- описание impact;
- ссылку на подробности;
- module/package;
- найденную version;
- first fixed version;
- call stacks из вашего source до vulnerable symbol, если vulnerability reachable.

Пример смысловой структуры:

```text
Vulnerability: GO-2021-0113
Module:        golang.org/x/text
Found in:      v0.3.5
Fixed in:      v0.3.7
Reachable:     yes
Call stack:    main -> language.Parse
```

## Оценка vulnerability

Не все findings имеют одинаковый priority.

Для каждого finding:

1. Прочитайте impact и условия exploitation.
2. Проверьте reachability.
3. Определите, может ли vulnerable path получать untrusted input.
4. Учитывайте deployment/environment mitigations.
5. Найдите fixed version.

В tutorial `GO-2021-0113` релевантна, потому что `Parse` вызывается напрямую и предполагается обработка untrusted input; возможен denial of service.

`GO-2022-1059` для конкретного sample не reachable, поэтому ниже priority. Однако она находится в том же module и исправлена в более новой version, так что можно устранить обе одним upgrade.

## Варианты remediation

### 1. Upgrade dependency

Предпочтительный вариант, когда fixed version доступна и совместима.

### 2. Перестать использовать vulnerable symbol

Если upgrade невозможен, можно удалить/заменить call path на безопасный API/implementation.

## Upgrade

Tutorial обновляет dependency до version, закрывающей оба findings:

```bash
go get golang.org/x/text@v0.3.8
```

После этого повторите:

```bash
govulncheck ./...
```

Ожидаемый результат tutorial:

```text
No vulnerabilities found.
```

## Практический workflow

`govulncheck` имеет смысл запускать регулярно:

- локально перед release;
- в CI;
- после dependency updates;
- при появлении нового security advisory;
- при обновлении Go toolchain/standard library.

Security scan не заменяет patch policy, SBOM/dependency inventory и threat modeling, но позволяет сфокусироваться на vulnerabilities, которые действительно достигаются вашим Go code.
