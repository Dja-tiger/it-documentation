---
title: "Руководство по участию в разработке Go"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/contribute.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Руководство по участию в разработке Go

Проект Go приветствует всех участников.

Этот документ помогает пройти процесс внесения изменений в проект Go. Он немного отличается от процессов, используемых во многих других open-source проектах. Предполагается, что вы уже знакомы с основами Git и Go.

Помимо этой страницы сообщество Go поддерживает wiki-страницу [CodeReview](https://go.dev/wiki/CodeReview). По мере освоения review process можно дополнять и саму wiki.

Front end `gccgo` расположен отдельно; для него см. официальную страницу [Contributing to gccgo](https://go.dev/doc/gccgo_contribute.html).

## Как стать contributor

### Обзор

Первый шаг — зарегистрироваться как contributor Go и настроить окружение.

Необходимая последовательность:

1. **Шаг 0.** Выберите один Google Account, который будете использовать для contributions в Go. Используйте его на всех следующих шагах и настройте `git` так, чтобы commits создавались с e-mail этого account.
2. **Шаг 1.** [Подпишите и отправьте](https://cla.developers.google.com/clas) CLA (Contributor License Agreement).
3. **Шаг 2.** Настройте authentication credentials для Go Git repository. Откройте [go.googlesource.com](https://go.googlesource.com), нажмите **Generate Password** в правом верхнем меню и следуйте инструкциям.
4. **Шаг 3.** Зарегистрируйтесь в Gerrit — code review tool команды Go — открыв [страницу входа Gerrit](https://go-review.googlesource.com/login/). CLA и Gerrit registration выполняются для account один раз.
5. **Шаг 4.** Установите `git-codereview`:

```bash
go install golang.org/x/review/git-codereview@latest
```

Есть автоматический tool, который проводит через эти шаги:

```bash
go install golang.org/x/tools/cmd/go-contrib-init@latest
cd /code/to/edit
go-contrib-init
```

Остальная часть этого раздела подробнее объясняет перечисленные действия. Если они уже выполнены вручную или через tool, переходите к [[#Перед внесением изменений в код]].

### Шаг 0. Выберите Google Account

Contribution в Go отправляется через Google Account с конкретным e-mail address. На всех этапах и для последующих contributions необходимо использовать один и тот же account.

Возможно, потребуется выбрать между личным и корпоративным адресом. Выбор зависит от того, кому принадлежат copyright rights на код, который вы будете писать и отправлять. Перед выбором корпоративного account это может потребоваться обсудить с работодателем.

Google Account может быть:

- Gmail account;
- account организации Google Workspace / G Suite;
- account, связанный с внешним e-mail address.

Например, если нужно использовать существующий корпоративный e-mail, который не управляется через Google Workspace, можно [создать Google Account для существующего e-mail](https://accounts.google.com/SignUpWithoutGmail).

Git также должен создавать commits с выбранным e-mail. Настройку можно задать глобально для всех repositories или локально для конкретного repository.

Проверить текущую конфигурацию:

```bash
git config --global user.email  # global config
git config user.email           # local config
```

Изменить адрес:

```bash
git config --global user.email name@example.com
git config user.email name@example.com
```

### Шаг 1. Contributor License Agreement

Перед первой отправкой change в Go project необходимо оформить один из двух CLA. Какой именно CLA нужен, зависит от владельца copyright на работу.

- Если copyright holder — вы сами, необходимо принять [Individual Contributor License Agreement](https://developers.google.com/open-source/cla/individual). Его можно оформить online.
- Если copyright holder — ваша организация, организация должна принять [Corporate Contributor License Agreement](https://developers.google.com/open-source/cla/corporate).

Проверить уже подписанные agreements и подписать новые можно на сайте [Google Developers Contributor License Agreements](https://cla.developers.google.com/clas?pli=1&authuser=1).

Если copyright holder уже подписал соответствующее соглашение для другого Google open-source project, повторно оформлять его не требуется.

Если copyright holder отправляемого кода изменился — например, вы начали делать contributions от имени новой компании — сообщите об этом в mailing list [`golang-dev`](mailto:golang-dev@googlegroups.com), чтобы maintainers могли убедиться, что оформлено правильное agreement.

### Шаг 2. Настройте Git authentication

Основной Go repository находится на [go.googlesource.com](https://go.googlesource.com) — Git server, размещённом Google.

Web authentication выполняется через Google Account, но локальный `git` также необходимо настроить для доступа к server.

1. Откройте [go.googlesource.com](https://go.googlesource.com) и нажмите **Generate Password** в правом верхнем меню. Будет выполнено перенаправление на `accounts.google.com` для входа.
2. После входа откроется страница **Configure Git** с персонализированным script. При локальном выполнении script настраивает Git для хранения уникального authentication key. Этот key имеет пару на server аналогично SSH keys.
3. Скопируйте и выполните script в terminal, чтобы сохранить secret authentication token в `.gitcookies`. В Windows при использовании `cmd` следуйте отдельной инструкции в жёлтом блоке страницы; в остальных случаях используйте обычный script.

### Шаг 3. Создайте Gerrit account

Gerrit — open-source tool, который maintainers Go используют для обсуждения и review code submissions.

Для регистрации откройте [go-review.googlesource.com/login/](https://go-review.googlesource.com/login/) и один раз войдите через тот же Google Account, который использовался на предыдущих шагах.

### Шаг 4. Установите git-codereview

Любое изменение Go должно пройти review независимо от автора. Custom Git command `git-codereview` упрощает отправку изменений в Gerrit.

Установка:

```bash
go install golang.org/x/review/git-codereview@latest
```

Убедитесь, что executable доступен через shell `PATH`, чтобы команда `git` могла его найти.

Проверка:

```bash
git codereview help
```

Команда должна вывести help text. Если вместо этого появляется ошибка, убедитесь, что `$GOPATH/bin` входит в `$PATH`.

В Windows при использовании git-bash необходимо, чтобы `git-codereview.exe` находился в Git exec-path. Узнать каталог можно командой:

```bash
git --exec-path
```

После этого создайте symbolic link либо скопируйте executable из `$GOPATH/bin` в этот каталог.

## Перед внесением изменений в код

Проект приветствует code patches, но значимые изменения следует обсудить **до** начала реализации. Рекомендуется обозначить намерение внести contribution в issue tracker: создать [новый issue](https://go.dev/issue/new) или заявить о работе над [существующим issue](https://go.dev/issues).

### Куда вносить изменения

Go project состоит из основного repository [go](https://go.googlesource.com/go), содержащего исходный код языка Go, а также множества repositories `golang.org/x/...`, содержащих tools и infrastructure проекта.

Например:

- [`golang.org/x/pkgsite`](https://go.googlesource.com/pkgsite) — код [pkg.go.dev](https://pkg.go.dev);
- [`golang.org/x/playground`](https://go.googlesource.com/playground) — Go Playground;
- [`golang.org/x/tools`](https://go.googlesource.com/tools) — различные Go tools, включая language server [gopls](https://go.dev/s/gopls).

Полный список `golang.org/x/...` repositories доступен на [go.googlesource.com](https://go.googlesource.com).

### Проверьте issue tracker

Независимо от того, уже знаете вы, что хотите исправить, или только ищете задачу, первый источник — [Go issue tracker](https://github.com/golang/go/issues).

Issues triage'ятся, классифицируются и получают workflow labels.

Большинство `golang.org/x/...` repositories также используют основной Go issue tracker. Некоторые repositories ведут issues отдельно, поэтому перед работой проверьте tracker конкретного repository.

Основные workflow labels:

- **NeedsInvestigation** — проблема ещё не полностью понята; требуется анализ root cause.
- **NeedsDecision** — проблема в основном понятна, но команда Go ещё не определила лучший способ её решения. Лучше дождаться решения до написания кода. Если issue долго не двигается, допустимо напомнить maintainers в comments.
- **NeedsFix** — проблема полностью понята и можно писать исправление.

Примеры GitHub searches:

- [issues, требующие investigation](https://github.com/golang/go/issues?q=is%3Aissue+is%3Aopen+label%3ANeedsInvestigation): `is:issue is:open label:NeedsInvestigation`;
- [issues, требующие fix](https://github.com/golang/go/issues?q=is%3Aissue+is%3Aopen+label%3ANeedsFix): `is:issue is:open label:NeedsFix`;
- [NeedsFix с уже предложенным change](https://github.com/golang/go/issues?q=is%3Aissue+is%3Aopen+label%3ANeedsFix+%28%22golang.org%2Fcl%22+OR+%22go.dev%2Fcl%22%29): `is:issue is:open label:NeedsFix ("golang.org/cl" OR "go.dev/cl")`;
- [NeedsFix без предложенного change](https://github.com/golang/go/issues?q=is%3Aissue+is%3Aopen+label%3ANeedsFix+NOT+%22golang.org%2Fcl%22+NOT+%22go.dev%2Fcl%22): `is:issue is:open label:NeedsFix NOT "golang.org/cl" NOT "go.dev/cl"`.

### Для новой проблемы откройте issue

Кроме совсем тривиальных изменений, любой contribution должен быть связан с существующим issue. Можно открыть новый issue и обсудить план.

Это позволяет:

- проверить design;
- избежать дублирования работы;
- убедиться, что идея соответствует целям языка и tools;
- проверить высокоуровневое решение до написания кода.

Code review tool не предназначен для high-level design discussion.

Основной Go repository следует [шестимесячному development cycle](https://go.dev/wiki/Go-Release-Cycle). Вторая половина цикла — трёхмесячный feature freeze, во время которого принимаются только bug fixes и documentation updates. Новые contributions можно отправлять и во время freeze, но они не будут merge'иться до его окончания.

Freeze распространяется на основной repository и на код `golang.org/x/...`, необходимый для сборки binaries релиза. Список vendored packages можно посмотреть для [standard library](https://github.com/golang/go/blob/master/src/vendor/modules.txt) и [`go` command](https://github.com/golang/go/blob/master/src/cmd/vendor/modules.txt).

Значимые изменения языка, libraries или tools — включая API changes в main repository и `golang.org/x`, а также command-line changes команды `go` — должны пройти [change proposal process](https://go.dev/s/proposal-process) до принятия.

Sensitive security-related issues следует отправлять **только** на [security@golang.org](mailto:security@golang.org).

## Отправка изменения через Gerrit

Для review рекомендуется Gerrit. У него есть learning curve для пользователей, привыкших только к GitHub workflow, но это основной workflow contributors Go и наиболее полно поддерживаемый процесс.

Подробнее об интерфейсе и возможностях см. [Gerrit documentation](https://gerrit-review.googlesource.com/Documentation/index.html), в частности [Review UI Overview](https://gerrit-review.googlesource.com/Documentation/user-review-ui.html) и [Basic Gerrit Walkthrough — For GitHub Users](https://gerrit-review.googlesource.com/Documentation/intro-gerrit-walkthrough-github.html).

### Обзор процесса Gerrit

**Шаг 1. Clone source code и один раз убедитесь, что исходное состояние успешно собирается и проходит tests.**

Для main Go repository:

```bash
git clone https://go.googlesource.com/go
cd go/src
./all.bash
```

Для repository `golang.org/x/...`, например `tools`:

```bash
git clone https://go.googlesource.com/tools
cd tools
go test ./...
```

**Шаг 2. Подготовьте change в новой branch, созданной от `master`.** Для commit используйте `git codereview change`: tool создаёт или amend'ит один commit в branch.

```text
git checkout -b mybranch
[edit files...]
git add [files...]
git codereview change
[edit again...]
git add [files...]
git codereview change
[etc.]
```

**Шаг 3. Протестируйте изменения.** Запустите tests изменённого package или повторно весь suite.

В main Go repository:

```bash
./all.bash
```

В `golang.org/x/...` repository:

```bash
go test ./...
```

**Шаг 4. Отправьте change на review в Gerrit.** Несмотря на название, `mail` не отправляет e-mail напрямую:

```bash
git codereview mail
```

**Шаг 5. После review внесите правки в тот же единственный commit и отправьте его снова:**

```text
[edit files...]
git add [files...]
git codereview change
git codereview mail
```

Ниже шаги рассмотрены подробнее.

### Шаг 1. Clone source code

Помимо свежей Go installation необходима локальная копия source из правильного repository.

Go source можно разместить в любом месте файловой системы, но **вне `GOPATH`**. Default `GOPATH` — каталог `go` в home directory.

Clone выполняется с `go.googlesource.com`, а не с GitHub.

Main repository:

```bash
git clone https://go.googlesource.com/go
cd go
```

Пример `golang.org/x/...` repository:

```bash
git clone https://go.googlesource.com/tools
cd tools
```

### Шаг 2. Подготовьте change в новой branch

Каждый Go change должен находиться в отдельной branch, созданной от `master`.

Обычные Git commands используются для создания branch и staging:

```text
git checkout -b mybranch
[edit files...]
git add [files...]
```

Вместо `git commit` используйте:

```bash
git codereview change
```

Откроется `$EDITOR`, где редактируется commit description.

`git codereview change` автоматически добавит уникальную строку `Change-Id` в нижнюю часть commit message. Gerrit использует её, чтобы связывать последовательные uploads одного и того же change.

Не изменяйте и не удаляйте `Change-Id`.

Пример:

```text
Change-Id: I2fbdbffb3aab626c4b6f56348861b7909e3e8990
```

Tool также проверяет, что source code обработан `go fmt`, а commit message соответствует [[#Хорошие commit messages|рекомендуемому формату]].

Если файлы нужно изменить ещё раз, добавьте изменения в staging и снова выполните `git codereview change`. Каждый последующий запуск amend'ит существующий commit, сохраняя `Change-Id`.

В каждой branch должен оставаться один commit. Если случайно созданы дополнительные commits, используйте `git rebase`, чтобы squash'ить их в один.

### Шаг 3. Протестируйте изменения

Перед отправкой review необходимо запустить tests **для всего дерева**, чтобы изменение не сломало другие packages или programs.

#### Main Go repository

Для package стандартной библиотеки tests package должны проходить:

```bash
go test
```

Короткий test suite всего tree:

```bash
cd go/src
./all.bash
```

В Windows используется `all.bat`.

Успешный запуск заканчивается строкой:

```text
ALL TESTS PASSED
```

`make.bash` можно использовать вместо `all.bash`, если требуется только собрать compiler и standard library без полного test suite. После сборки Go tool будет установлен как `bin/go` под directory clone.

Для ускоренной разработки см. [[#Быстрая проверка изменений]].

#### Repositories golang.org/x/...

Запустите tests всего repository, например для `tools`:

```bash
cd tools
go test ./...
```

Если есть сомнения в текущем build status, проверьте [Build Dashboard](https://build.golang.org). Ошибки также могут обнаружить TryBots в code review.

Некоторые repositories имеют собственную testing infrastructure. Например, это относится к `golang.org/x/vscode-go`. Всегда проверяйте documentation конкретного repository; обычно нужные команды указаны в root `README`.

### Шаг 4. Отправьте change на review

После подготовки и полного тестирования:

```bash
git codereview mail
```

`mail` не отправляет e-mail непосредственно — команда отправляет change в Gerrit.

Gerrit назначит change number и URL. Output выглядит примерно так:

```text
remote: New Changes:
remote:   https://go-review.googlesource.com/99999 math: improved Sin, Cos and Tan precision for very large arguments
```

При ошибке см. [[#Устранение ошибок mail]].

Если change связан с открытым GitHub issue и commit message оформлен по рекомендуемому формату, bot через несколько минут добавит в issue ссылку на Gerrit change.

### Шаг 5. Исправьте change после review

Maintainers Go review'ят код в Gerrit; notifications приходят по e-mail. Comments можно просматривать и отвечать на них в Gerrit либо [по e-mail](https://gerrit-review.googlesource.com/Documentation/intro-user.html#reply-by-email).

Для revision используйте ту же branch:

```bash
git codereview change
# сохраните commit description
git codereview mail
```

Если description менять не требуется, просто сохраните и закройте editor. Не изменяйте `Change-Id`.

И здесь branch должна содержать один commit. Случайно созданные дополнительные commits squash'ятся через `git rebase`.

## Отправка изменения через GitHub

Хотя Gerrit workflow рекомендуется и лучше поддерживается, contributors, привыкшие к [GitHub flow](https://guides.github.com/introduction/flow/), могут использовать привычный pull request process.

Maintainers Go всё равно проводят review в Gerrit. Tool [GerritBot](https://go.dev/wiki/GerritBot) синхронизирует GitHub pull requests с Gerrit.

Откройте GitHub pull request обычным способом. GerritBot создаст соответствующий Gerrit change list (CL) и добавит ссылку в PR. Обновления PR синхронизируются с CL. Comments из Gerrit также публикуются в pull request, поэтому GitHub notifications продолжают работать.

Следует учитывать:

- Для ответа reviewers, включая отметку feedback как **Done**, нужен [Gerrit account](https://go-review.googlesource.com/login/). Полезно заранее познакомиться с Gerrit: просматривать [open CLs](https://go-review.googlesource.com/q/status:open+-is:wip), подписываться на интересные CLs через star или review'ить чужие изменения.
- Для обновления PR просто push'ьте код в branch. Допустимы как дополнительные commits, так и rebase + force-push.
- При принятии PR все commits будут squash'ены. Final commit description составляется из PR title + description; descriptions отдельных commits будут отброшены.
- Дополнительные детали см. в [GerritBot FAQ](https://go.dev/wiki/GerritBot#frequently-asked-questions).

## Хорошие commit messages

Commit messages Go следуют определённым conventions.

Пример:

```text
math: improve Sin, Cos and Tan precision for very large arguments

The existing implementation has poor numerical properties for
large arguments, so use the McGillicutty algorithm to improve
accuracy above 1e10.

The algorithm is described at https://wikipedia.org/wiki/McGillicutty_Algorithm

Fixes #159
```

### Первая строка

Первая строка change description обычно представляет собой короткое однострочное summary, предварённое именем основного затронутого package.

Удобное правило: текст должен естественно завершать фразу:

> This change modifies Go to _____.

Следовательно, summary не начинается с заглавной буквы, не является полноценным предложением и описывает фактический результат изменения.

После первой строки оставьте пустую строку.

### Основной текст

Остальная часть description раскрывает context и объясняет, что делает изменение.

Пишите полноценными предложениями с правильной punctuation — так же, как комментарии в Go source. Не используйте HTML, Markdown или другой markup. Строки рекомендуется переносить примерно на 72 columns.

Дополнительные рекомендации см. в [Commit messages](https://go.dev/wiki/CommitMessage).

Добавляйте релевантные данные, например benchmark results для performance changes. Tool [`benchstat`](https://pkg.go.dev/golang.org/x/perf/cmd/benchstat) традиционно используется для форматирования benchmark data в descriptions.

### Ссылки на issues

Специальная запись:

```text
Fixes #12345
```

связывает change с issue `12345` в Go issue tracker. После применения change tracker автоматически пометит issue как fixed.

Если change является только частью решения:

```text
Updates #12345
```

Это добавит в issue comment со ссылкой на Gerrit change, но не закроет issue после merge.

Для changes в `golang.org/x/...` repository используйте fully-qualified GitHub syntax, чтобы ссылка указывала на issue main repository, а не x/repository:

```text
Fixes golang/go#159
```

## Процесс review

### Типичные ошибки начинающих contributors

После отправки change в Gerrit его обычно triage'ят в течение нескольких дней. Первоначальный review для новых contributors часто сосредоточен на базовом оформлении и типичных ошибках.

К ним относятся:

- Commit message не соответствует рекомендуемому формату.
- Нет связанного GitHub issue. Подавляющее большинство changes требует issue, где описан bug/feature и достигнут consensus до реализации. Gerrit review обсуждает implementation, а не целесообразность high-level change. Без issue обычно принимаются только тривиальные/cosmetic changes.
- Change отправлен во время feature freeze. Maintainer может оставить отметку вроде `R=go1.12`, означающую, что review будет продолжен в следующем development window. Если вы заранее знаете, что timing неподходящий, такой comment можно добавить самостоятельно.

### Trybots

После первоначального просмотра maintainers запускают TryBots — cluster servers, выполняющий полный test suite на нескольких architectures.

Большинство runs завершается за несколько минут, после чего Gerrit получает ссылку на results.

При failure откройте logs конкретных platforms, выясните причину, исправьте patch и upload'ьте новую version. Maintainers запустят TryBots повторно.

Иногда сам tree временно broken на отдельных platforms. Если failure не выглядит связанным с patch:

1. проверьте [Build Dashboard](https://build.golang.org) — воспроизводится ли failure в соседних recent commits;
2. можно оставить Gerrit comment, что failure, вероятно, unrelated;
3. поискать error в GitHub issues или среди недавно обновлённых [`watchflakes` issues](https://github.com/golang/go/issues?q=is%3Aissue%20watchflakes%20sort%3Aupdated-desc);
4. если change основан на старом commit, попробовать `git rebase` на latest `master`.

### Reviews

Сообщество Go ценит подробный review.

Каждый review comment следует воспринимать как отдельный ticket: его нужно «закрыть», либо реализовав предложение, либо обоснованно объяснив reviewer, почему выбран другой вариант.

После обновления change пройдите по всем comments и ответьте на каждый:

- **Done** — предложение реализовано;
- **Reply** — объяснение, почему предложение не реализовано либо что сделано вместо него.

Несколько review rounds — нормальная практика даже для опытных contributors. Новый round может содержать новые comments, после чего reviewer снова ждёт updated change.

### Voting conventions

При приближении к решению reviewers выставляют Code-Review votes.

- **+2** — change одобрен для merge. Такой vote могут ставить только Go maintainers / approvers.
- **+1** — change выглядит хорошо, но либо нужны небольшие изменения до approval, либо reviewer не является maintainer и не может дать +2, но поддерживает approval.

Для submission необходим Code-Review `+2` от maintainer.

Maintainers также могут поставить **Hold +1**, если change пока нельзя submit'ить, например пока не завершён proposal review нового API.

Для submission не должно оставаться ни одного Hold `+1` от maintainer.

Кроме того, для supply-chain security и compliance в change должны участвовать два Google employees — либо как uploader, либо как reviewers с Code-Review не ниже `+1`.

### Submission одобренного change

Когда change готов, maintainer выполняет submit, добавляя его как commit в Gerrit repository.

Approval и submission разделены: maintainer может одобрить change, но не submit'ить его сразу, например из-за временного freeze tree.

При submission change попадает в repository. Change description содержит ссылку на code review, а review обновляется ссылкой на repository commit.

Поскольку integration использует Git **Cherry Pick**, commit hash после submit изменяется.

Если change уже несколько дней approved, но не submitted, допустимо оставить Gerrit comment с просьбой выполнить submission.

### Дополнительная информация

Дополнительные сведения о review process находятся на wiki [CodeReview](https://go.dev/wiki/CodeReview).

## Прочие темы

Следующие разделы относятся к рабочим деталям вокруг issue/edit/review/submit process.

### Gopls

При работе с main Go repository и использовании `gopls` команда `go`, запускаемая `gopls`, должна соответствовать версии source code, с которой ведётся работа.

`go` command можно собрать через `make.bash`, а directory `bin` добавить в `PATH`.

Дополнительные детали: [Gopls: Advanced topics](https://go.dev/gopls/advanced). Полная документация Gopls: [go.dev/gopls](https://go.dev/gopls).

### Copyright headers

Files в Go repository не содержат списков author names, чтобы не создавать clutter и не поддерживать такие списки вручную. Имя contributor сохраняется в change log.

Новые files должны использовать стандартный copyright header:

```go
// Copyright {{now.UTC.Year}} The Go Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.
```

Copyright year соответствует году добавления file. При изменении существующего file год copyright обновлять не нужно.

### Устранение ошибок mail

Самая частая причина failure `git codereview mail` — e-mail в commit не совпадает с e-mail account, использованным при регистрации.

Пример ошибки:

```text
remote: Processing changes: refs: 1, done
remote:
remote: ERROR:  In commit ab13517fa29487dcf8b0d48916c51639426c5ee9
remote: ERROR:  author email address XXXXXXXXXXXXXXXXXXX
remote: ERROR:  does not match your user account.
```

Настройте правильный e-mail локально для repository:

```bash
git config user.email email@address.com
```

Измените author текущего commit:

```bash
git commit --amend --author="Author Name <email@address.com>"
```

Затем повторите:

```bash
git codereview mail
```

### Быстрая проверка изменений

Запуск `all.bash` после каждого локального изменения слишком тяжёлый. Хотя перед отправкой change полный запуск настоятельно рекомендуется, в обычном development cycle можно rebuild/test только нужную часть.

- `make.bash` rebuild'ит Go toolchain без полного test suite.
- `run.bash` запускает весь test suite без rebuild toolchain.
- `all.bash` концептуально соответствует `make.bash`, затем `run.bash`.

Пусть directory clone Go repository называется `$GOROOT`. `go`, собранный `$GOROOT/src/make.bash`, будет установлен как:

```text
$GOROOT/bin/go
```

Если compiler был изменён и требуется проверить его на собственном project:

```bash
cd <MYPROJECTDIR>
$GOROOT/bin/go test
```

Если изменяется standard library, обычно compiler rebuild не нужен. Достаточно запустить tests изменённого package, используя обычную Go version либо compiler из clone, если новый library code требует более свежего языка:

```text
cd $GOROOT/src/crypto/sha1
[make changes...]
$GOROOT/bin/go test .
```

Если изменяется сам compiler, можно rebuild только internal `compile` tool:

```text
cd $GOROOT/src
[make changes...]
$GOROOT/bin/go install cmd/compile
$GOROOT/bin/go build [something...]
$GOROOT/bin/go run [something...]
$GOROOT/bin/go test [something...]
```

Тот же принцип действует для других internal tools Go toolchain, например `asm`, `cover`, `link`: rebuild через `go install cmd/<TOOL>`, затем тестируйте с собранным Go binary.

Помимо per-package tests существует top-level test suite в `$GOROOT/test`, содержащий black-box и regression tests. Он запускается `all.bash`, но его можно запустить вручную:

```bash
$GOROOT/bin/go test cmd/internal/testdir
```

### Выбор reviewer / CC

Если в предшествующем обсуждении явно не указано обратное, reviewer лучше не назначать вручную.

Все changes автоматически CC'ятся в mailing list [golang-codereviews@googlegroups.com](https://groups.google.com/group/golang-codereviews). Для самого первого change возможна moderation delay для защиты от spam.

Reviewer или другие interested parties можно указать options `-r` и `-cc`. Обе принимают comma-separated e-mail addresses:

```bash
git codereview mail -r joe@golang.org -cc mabel@example.com,math-nuts@swtch.com
```

### Синхронизация client

Пока вы работали, в repository могли появиться новые changes. Обновить local branch:

```bash
git codereview sync
```

Внутри команда выполняет `git pull -r`.

### Review чужого кода

Reviewers могут предлагать изменения напрямую. Gerrit предоставляет команды, позволяющие импортировать чужой change для локального review/testing.

На странице CL откройте меню `⋮`, выберите **Download patch** и подходящую команду для вашего Git workflow. Она будет похожа на:

```bash
git fetch https://go.googlesource.com/review refs/changes/21/13245/1 && git checkout FETCH_HEAD
```

Чтобы вернуться, checkout'ните branch, на которой работали ранее.

### Git aliases

`git-codereview` можно запускать напрямую:

```bash
git codereview sync
```

Для удобства можно создать aliases, чтобы использовать:

```bash
git sync
```

Subcommands `git-codereview` подобраны так, чтобы не конфликтовать с native Git commands.

Добавьте в Git config, обычно `~/.gitconfig`:

```ini
[alias]
	change = codereview change
	gofmt = codereview gofmt
	mail = codereview mail
	pending = codereview pending
	submit = codereview submit
	sync = codereview sync
```

### Несколько зависимых changes

Опытные contributors могут складывать связанные commits в одной branch. Gerrit поддерживает dependency chain: каждый change всё равно должен быть отдельно approved и submitted, но dependencies видны reviewers.

Для группы dependent changes оставьте каждый change отдельным commit в одной branch и выполните:

```bash
git codereview mail HEAD
```

В этом случае `HEAD` следует указать явно, хотя для одиночного change это обычно не требуется.

Подробнее см. [git-codereview — Multiple Commit Work Branches](https://pkg.go.dev/golang.org/x/review/git-codereview#hdr-Multiple_Commit_Work_Branches).

### Minor Releases

Если требуется change для release branch с целью backport, см. wiki [Minor Releases](https://go.dev/wiki/MinorReleases).
