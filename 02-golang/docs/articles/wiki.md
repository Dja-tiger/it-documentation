---
title: "Writing Web Applications"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/articles/wiki/index.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "reviewed"
---

# Writing Web Applications

## Введение

В этом tutorial рассматриваются:

- создание data structure с methods загрузки и сохранения;
- использование package `net/http` для создания web applications;
- использование package `html/template` для обработки HTML templates;
- использование package `regexp` для validation пользовательского ввода;
- использование closures.

Предполагаются:

- опыт программирования;
- понимание базовых web technologies — HTTP и HTML;
- базовые навыки работы с UNIX/DOS command line.

## Начало работы

Для запуска Go требуется FreeBSD, Linux, macOS или Windows. Символ `$` ниже обозначает command prompt.

Установите Go по [[../install|инструкции по установке]].

Создайте новый directory для tutorial внутри `GOPATH` и перейдите в него:

```text
$ mkdir gowiki
$ cd gowiki
```

Создайте file `wiki.go`, откройте его в editor и добавьте:

```go
package main

import (
    "fmt"
    "os"
)
```

Мы импортируем packages `fmt` и `os` из standard library. Позже, по мере добавления functionality, список imports будет расширяться.

## Data structures

Начнём с data structures. Wiki состоит из набора связанных pages. У каждой page есть title и body — содержимое страницы.

Определим `Page` как struct с двумя fields:

```go
type Page struct {
    Title string
    Body  []byte
}
```

Type `[]byte` означает slice bytes. Подробнее о slices см. официальную статью [Slices: usage and internals](https://go.dev/doc/articles/slices_usage_and_internals.html).

Field `Body` имеет type `[]byte`, а не `string`, потому что именно такой type ожидают I/O libraries, которые будут использованы ниже.

Struct `Page` описывает хранение page data в памяти. Для persistent storage добавим method `save`:

```go
func (p *Page) save() error {
    filename := p.Title + ".txt"
    return os.WriteFile(filename, p.Body, 0600)
}
```

Signature method читается так: это method `save` с receiver `p`, являющимся pointer на `Page`; method не принимает parameters и возвращает value type `error`.

Method сохраняет `Body` page в text file. Для простоты `Title` используется как file name.

`save` возвращает `error`, потому что `os.WriteFile` возвращает error. Это позволяет application обработать ошибку записи. Если всё прошло успешно, `Page.save()` возвращает `nil` — zero value для pointers, interfaces и некоторых других types.

Octal literal `0600`, передаваемый третьим argument в `WriteFile`, означает, что file создаётся с read/write permissions только для текущего пользователя.

Нам потребуется не только сохранять, но и загружать pages. Сначала напишем упрощённую version, игнорирующую error:

```go
func loadPage(title string) *Page {
    filename := title + ".txt"
    body, _ := os.ReadFile(filename)
    return &Page{Title: title, Body: body}
}
```

`loadPage` строит file name из `title`, читает содержимое в variable `body` и возвращает pointer на `Page` literal.

Functions в Go могут возвращать несколько values. `os.ReadFile` возвращает `[]byte` и `error`. Здесь error пока игнорируется с помощью blank identifier `_`.

Но `ReadFile` может вернуть error, например если file не существует. Такие errors игнорировать не следует. Изменим function, чтобы она возвращала `*Page` и `error`:

```go
func loadPage(title string) (*Page, error) {
    filename := title + ".txt"
    body, err := os.ReadFile(filename)
    if err != nil {
        return nil, err
    }
    return &Page{Title: title, Body: body}, nil
}
```

Caller теперь может проверить второй result. Если он `nil`, page успешно загружена. Иначе caller получает `error`, который может обработать.

Теперь у нас есть data structure и возможность сохранять/загружать её из file. Добавим `main`, чтобы проверить code:

```go
func main() {
    p1 := &Page{Title: "TestPage", Body: []byte("This is a sample Page.")}
    p1.save()
    p2, _ := loadPage("TestPage")
    fmt.Println(string(p2.Body))
}
```

После compilation и execution будет создан `TestPage.txt`, содержащий `Body` из `p1`. Затем file будет прочитан в `p2`, а `Body` напечатан.

```text
$ go build wiki.go
$ ./wiki
This is a sample Page.
```

В Windows для запуска program нужно ввести `wiki` без `./`.

## Знакомство с package `net/http`

Ниже полный рабочий пример простого web server:

```go
package main

import (
    "fmt"
    "log"
    "net/http"
)

func handler(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintf(w, "Hi there, I love %s!", r.URL.Path[1:])
}

func main() {
    http.HandleFunc("/", handler)
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

`main` начинается с вызова `http.HandleFunc`, который говорит package `http` обрабатывать все requests к web root `/` с помощью `handler`.

Затем вызывается `http.ListenAndServe` с address `:8080`, то есть server слушает port 8080 на любом interface. Второй argument `nil` пока можно не рассматривать. Function блокируется до завершения program.

`ListenAndServe` всегда возвращает error, поскольку возвращается только при unexpected error. Чтобы записать error в log, вызов оборачивается в `log.Fatal`.

Function `handler` имеет type `http.HandlerFunc` и принимает `http.ResponseWriter` и `*http.Request`.

`http.ResponseWriter` собирает HTTP response server. Записывая в него данные, мы отправляем их HTTP client.

`http.Request` представляет client HTTP request. `r.URL.Path` — path component request URL. Slice expression `[1:]` создаёт sub-slice `Path` с первого character до конца и тем самым убирает leading `/`.

Если запустить server и открыть:

```text
http://localhost:8080/monkeys
```

будет показано:

```text
Hi there, I love monkeys!
```

## Использование `net/http` для wiki pages

Добавьте `net/http` в imports:

```go
import (
    "fmt"
    "os"
    "log"
    "net/http"
)
```

Создадим `viewHandler`, позволяющий просматривать wiki page. Он обрабатывает URLs с prefix `/view/`:

```go
func viewHandler(w http.ResponseWriter, r *http.Request) {
    title := r.URL.Path[len("/view/"):]
    p, _ := loadPage(title)
    fmt.Fprintf(w, "<h1>%s</h1><div>%s</div>", p.Title, p.Body)
}
```

Здесь error из `loadPage` снова игнорируется с `_` только для простоты. Это считается плохой практикой; исправление будет добавлено позже.

Сначала function извлекает title из `r.URL.Path`. Expression `[len("/view/"):]` удаляет leading `/view/`, который не является частью title.

Затем function загружает page, форматирует её простым HTML и пишет result в `w`.

Изменим `main`:

```go
func main() {
    http.HandleFunc("/view/", viewHandler)
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

Создайте `test.txt` со строкой `Hello world`, затем:

```text
$ go build wiki.go
$ ./wiki
```

Открытие `http://localhost:8080/view/test` должно показать page с title `test` и text `Hello world`.

## Редактирование pages

Wiki должна позволять редактировать pages. Добавим два handlers:

- `editHandler` — показывает form редактирования;
- `saveHandler` — сохраняет данные из form.

Сначала зарегистрируем их в `main`:

```go
func main() {
    http.HandleFunc("/view/", viewHandler)
    http.HandleFunc("/edit/", editHandler)
    http.HandleFunc("/save/", saveHandler)
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

`editHandler` загружает page, а если её нет — создаёт пустой `Page`, затем показывает HTML form:

```go
func editHandler(w http.ResponseWriter, r *http.Request) {
    title := r.URL.Path[len("/edit/"):]
    p, err := loadPage(title)
    if err != nil {
        p = &Page{Title: title}
    }
    fmt.Fprintf(w, "<h1>Editing %s</h1>"+
        "<form action=\"/save/%s\" method=\"POST\">"+
        "<textarea name=\"body\">%s</textarea><br>"+
        "<input type=\"submit\" value=\"Save\">"+
        "</form>",
        p.Title, p.Title, p.Body)
}
```

Function работает, но hard-coded HTML неудобен. Есть лучший способ.

## Package `html/template`

`html/template` входит в Go standard library. Он позволяет держать HTML отдельно от Go code и менять layout page без изменения application logic.

Добавьте `html/template` в imports и удалите `fmt`, который больше не нужен:

```go
import (
    "html/template"
    "os"
    "net/http"
)
```

Создайте `edit.html`:

```html
<h1>Editing {{.Title}}</h1>

<form action="/save/{{.Title}}" method="POST">
<div><textarea name="body" rows="20" cols="80">{{printf "%s" .Body}}</textarea></div>
<div><input type="submit" value="Save"></div>
</form>
```

Измените `editHandler`:

```go
func editHandler(w http.ResponseWriter, r *http.Request) {
    title := r.URL.Path[len("/edit/"):]
    p, err := loadPage(title)
    if err != nil {
        p = &Page{Title: title}
    }
    t, _ := template.ParseFiles("edit.html")
    t.Execute(w, p)
}
```

`template.ParseFiles` читает `edit.html` и возвращает `*template.Template`.

`t.Execute` выполняет template, записывая generated HTML в `http.ResponseWriter`. Dotted identifiers `.Title` и `.Body` относятся к `p.Title` и `p.Body`.

Template directives заключаются в double curly braces. Instruction `printf "%s" .Body` вызывает function и выводит `.Body` как string, а не поток bytes.

Package `html/template` помогает гарантировать, что template actions создают безопасный и корректный HTML. Например, он автоматически escaping'ит `>`, чтобы user data не повредили HTML form.

Создадим `view.html`:

```html
<h1>{{.Title}}</h1>

<p>[<a href="/edit/{{.Title}}">edit</a>]</p>

<div>{{printf "%s" .Body}}</div>
```

Изменим `viewHandler`:

```go
func viewHandler(w http.ResponseWriter, r *http.Request) {
    title := r.URL.Path[len("/view/"):]
    p, _ := loadPage(title)
    t, _ := template.ParseFiles("view.html")
    t.Execute(w, p)
}
```

В обоих handlers используется почти одинаковый templating code. Уберём duplication в отдельную function:

```go
func renderTemplate(w http.ResponseWriter, tmpl string, p *Page) {
    t, _ := template.ParseFiles(tmpl + ".html")
    t.Execute(w, p)
}
```

Теперь handlers становятся:

```go
func viewHandler(w http.ResponseWriter, r *http.Request) {
    title := r.URL.Path[len("/view/"):]
    p, _ := loadPage(title)
    renderTemplate(w, "view", p)
}

func editHandler(w http.ResponseWriter, r *http.Request) {
    title := r.URL.Path[len("/edit/"):]
    p, err := loadPage(title)
    if err != nil {
        p = &Page{Title: title}
    }
    renderTemplate(w, "edit", p)
}
```

Если временно закомментировать registration ещё не реализованного save handler, программу можно снова собрать и проверить.

## Обработка несуществующих pages

Что произойдёт при открытии `/view/APageThatDoesntExist`? Текущий code игнорирует error `loadPage` и пытается заполнить template отсутствующими data.

Вместо этого при отсутствии page следует redirect'ить client на edit page:

```go
func viewHandler(w http.ResponseWriter, r *http.Request) {
    title := r.URL.Path[len("/view/"):]
    p, err := loadPage(title)
    if err != nil {
        http.Redirect(w, r, "/edit/"+title, http.StatusFound)
        return
    }
    renderTemplate(w, "view", p)
}
```

`http.Redirect` добавляет HTTP status code `http.StatusFound` (302) и header `Location` в response.

## Сохранение pages

`saveHandler` обрабатывает form submission edit page:

```go
func saveHandler(w http.ResponseWriter, r *http.Request) {
    title := r.URL.Path[len("/save/"):]
    body := r.FormValue("body")
    p := &Page{Title: title, Body: []byte(body)}
    p.save()
    http.Redirect(w, r, "/view/"+title, http.StatusFound)
}
```

Title из URL и единственное field form `body` сохраняются в новый `Page`. Затем вызывается `save()`, а client redirect'ится на `/view/`.

`FormValue` возвращает `string`. Перед сохранением в `Page.Body` value преобразуется в `[]byte` через `[]byte(body)`.

## Error handling

В программе всё ещё есть места, где errors игнорируются. Это плохая практика: при ошибке program может вести себя неожиданно.

Сначала обработаем errors в `renderTemplate`:

```go
func renderTemplate(w http.ResponseWriter, tmpl string, p *Page) {
    t, err := template.ParseFiles(tmpl + ".html")
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    err = t.Execute(w, p)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
    }
}
```

`http.Error` отправляет заданный HTTP response code — здесь `Internal Server Error` — и error message. Решение вынести templating в отдельную function уже упрощает обработку ошибок.

Исправим `saveHandler`:

```go
func saveHandler(w http.ResponseWriter, r *http.Request, title string) {
    body := r.FormValue("body")
    p := &Page{Title: title, Body: []byte(body)}
    err := p.save()
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    http.Redirect(w, r, "/view/"+title, http.StatusFound)
}
```

Теперь errors из `p.save()` сообщаются пользователю.

## Кэширование templates

В текущем code есть inefficiency: `renderTemplate` вызывает `ParseFiles` при каждом render page.

Лучше вызвать `ParseFiles` один раз при initialization program, разобрав все templates в один `*Template`, а затем использовать `ExecuteTemplate`.

Создадим global variable `templates`:

```go
var templates = template.Must(template.ParseFiles("edit.html", "view.html"))
```

`template.Must` — convenience wrapper: если ему передан non-nil `error`, он panic'ит; иначе возвращает `*Template` без изменений. Здесь panic уместен: если templates невозможно загрузить, sensible action — завершить program.

`ParseFiles` принимает любое число string arguments и парсит files в templates, имена которых соответствуют base file name.

Изменим `renderTemplate`:

```go
func renderTemplate(w http.ResponseWriter, tmpl string, p *Page) {
    err := templates.ExecuteTemplate(w, tmpl+".html", p)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
    }
}
```

Template name совпадает с file name, поэтому к argument `tmpl` добавляется `.html`.

## Validation

У program есть серьёзная security flaw: пользователь может передать произвольный path для чтения/записи на server.

Чтобы уменьшить риск, проверим title регулярным выражением.

Добавьте `regexp` в imports и global variable:

```go
var validPath = regexp.MustCompile("^/(edit|save|view)/([a-zA-Z0-9]+)$")
```

`regexp.MustCompile` парсит и компилирует regular expression, возвращая `regexp.Regexp`. В отличие от `Compile`, `MustCompile` panic'ит при ошибке compilation; `Compile` возвращает `error` вторым result.

Сначала можно написать helper, который проверяет path и извлекает title:

```go
func getTitle(w http.ResponseWriter, r *http.Request) (string, error) {
    m := validPath.FindStringSubmatch(r.URL.Path)
    if m == nil {
        http.NotFound(w, r)
        return "", errors.New("invalid Page Title")
    }
    return m[2], nil // The title is the second subexpression.
}
```

Если title valid, function возвращает его и `nil`. Если invalid, function пишет `404 Not Found` в HTTP connection и возвращает error.

На этом этапе каждый handler вызывает `getTitle` и прекращает обработку при error.

## Function literals и closures

Повторение error handling в каждом handler создаёт много duplicate code.

Можно обернуть handlers в function, выполняющую validation и error checking. Для этого подходят [function literals](https://go.dev/ref/spec#Function_literals).

Изменим signatures handlers:

```go
func viewHandler(w http.ResponseWriter, r *http.Request, title string)
func editHandler(w http.ResponseWriter, r *http.Request, title string)
func saveHandler(w http.ResponseWriter, r *http.Request, title string)
```

Теперь определим wrapper function, которая принимает function такого type и возвращает `http.HandlerFunc`:

```go
func makeHandler(fn func(http.ResponseWriter, *http.Request, string)) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        // Here we will extract the page title from the Request,
        // and call the provided handler 'fn'
    }
}
```

Возвращаемая function называется **closure**, потому что она encloses values, определённые вне неё. В этом случае closure захватывает variable `fn`, единственный argument `makeHandler`.

Перенесём validation внутрь wrapper:

```go
func makeHandler(fn func(http.ResponseWriter, *http.Request, string)) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        m := validPath.FindStringSubmatch(r.URL.Path)
        if m == nil {
            http.NotFound(w, r)
            return
        }
        fn(w, r, m[2])
    }
}
```

Closure получает `http.ResponseWriter` и `*http.Request`, извлекает `title`, проверяет его через `validPath`; при invalid title вызывает `http.NotFound`, а при valid вызывает enclosed handler `fn` с `w`, `r` и `title`.

Теперь handlers регистрируются через `makeHandler`:

```go
func main() {
    http.HandleFunc("/view/", makeHandler(viewHandler))
    http.HandleFunc("/edit/", makeHandler(editHandler))
    http.HandleFunc("/save/", makeHandler(saveHandler))

    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

После удаления calls `getTitle` handlers становятся проще:

```go
func viewHandler(w http.ResponseWriter, r *http.Request, title string) {
    p, err := loadPage(title)
    if err != nil {
        http.Redirect(w, r, "/edit/"+title, http.StatusFound)
        return
    }
    renderTemplate(w, "view", p)
}

func editHandler(w http.ResponseWriter, r *http.Request, title string) {
    p, err := loadPage(title)
    if err != nil {
        p = &Page{Title: title}
    }
    renderTemplate(w, "edit", p)
}

func saveHandler(w http.ResponseWriter, r *http.Request, title string) {
    body := r.FormValue("body")
    p := &Page{Title: title, Body: []byte(body)}
    err := p.save()
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    http.Redirect(w, r, "/view/"+title, http.StatusFound)
}
```

## Попробуйте

Полный final listing:

```go
package main

import (
    "html/template"
    "log"
    "net/http"
    "os"
    "regexp"
)

type Page struct {
    Title string
    Body  []byte
}

func (p *Page) save() error {
    filename := p.Title + ".txt"
    return os.WriteFile(filename, p.Body, 0600)
}

func loadPage(title string) (*Page, error) {
    filename := title + ".txt"
    body, err := os.ReadFile(filename)
    if err != nil {
        return nil, err
    }
    return &Page{Title: title, Body: body}, nil
}

func viewHandler(w http.ResponseWriter, r *http.Request, title string) {
    p, err := loadPage(title)
    if err != nil {
        http.Redirect(w, r, "/edit/"+title, http.StatusFound)
        return
    }
    renderTemplate(w, "view", p)
}

func editHandler(w http.ResponseWriter, r *http.Request, title string) {
    p, err := loadPage(title)
    if err != nil {
        p = &Page{Title: title}
    }
    renderTemplate(w, "edit", p)
}

func saveHandler(w http.ResponseWriter, r *http.Request, title string) {
    body := r.FormValue("body")
    p := &Page{Title: title, Body: []byte(body)}
    err := p.save()
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    http.Redirect(w, r, "/view/"+title, http.StatusFound)
}

var templates = template.Must(template.ParseFiles("edit.html", "view.html"))

func renderTemplate(w http.ResponseWriter, tmpl string, p *Page) {
    err := templates.ExecuteTemplate(w, tmpl+".html", p)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
    }
}

var validPath = regexp.MustCompile("^/(edit|save|view)/([a-zA-Z0-9]+)$")

func makeHandler(fn func(http.ResponseWriter, *http.Request, string)) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        m := validPath.FindStringSubmatch(r.URL.Path)
        if m == nil {
            http.NotFound(w, r)
            return
        }
        fn(w, r, m[2])
    }
}

func main() {
    http.HandleFunc("/view/", makeHandler(viewHandler))
    http.HandleFunc("/edit/", makeHandler(editHandler))
    http.HandleFunc("/save/", makeHandler(saveHandler))

    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

Пересоберите и запустите:

```text
$ go build wiki.go
$ ./wiki
```

Открытие `http://localhost:8080/view/ANewPage` должно показать form редактирования. Введите text, нажмите `Save` — browser будет redirected на только что созданную page.

## Другие задачи

Несколько простых задач для самостоятельной работы:

- хранить templates в `tmpl/`, а page data — в `data/`;
- добавить handler, redirect'ящий web root на `/view/FrontPage`;
- улучшить templates, сделав их valid HTML и добавив CSS;
- реализовать links между pages, преобразуя `[PageName]` в `<a href="/view/PageName">PageName</a>`; для этого можно использовать `regexp.ReplaceAllFunc`.
