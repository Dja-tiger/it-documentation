---
title: "Writing Web Applications"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/articles/wiki/index.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Writing Web Applications

Классический официальный tutorial показывает базовый web application без framework: `net/http`, file persistence, `html/template`, regex route validation и closures.

Приложение — простая wiki с URL:

```text
/view/PageTitle
/edit/PageTitle
/save/PageTitle
```

## Data structure

```go
type Page struct {
    Title string
    Body  []byte
}
```

Каждая page сохраняется отдельным text file `<Title>.txt`.

## Save/load

```go
func (p *Page) save() error {
    filename := p.Title + ".txt"
    return os.WriteFile(filename, p.Body, 0o600)
}

func loadPage(title string) (*Page, error) {
    filename := title + ".txt"
    body, err := os.ReadFile(filename)
    if err != nil {
        return nil, err
    }
    return &Page{Title: title, Body: body}, nil
}
```

Проверка:

```go
func main() {
    p1 := &Page{Title: "TestPage", Body: []byte("This is a sample Page.")}
    _ = p1.save()
    p2, _ := loadPage("TestPage")
    fmt.Println(string(p2.Body))
}
```

В production errors нельзя игнорировать — tutorial упрощает intermediate steps.

## HTTP handler

```go
func handler(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintf(w, "Hi there, I love %s!", r.URL.Path[1:])
}
```

Registration/server:

```go
func main() {
    http.HandleFunc("/", handler)
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

`http.HandleFunc` регистрирует function подходящей signature как handler. Default server начинает слушать TCP address.

## View page

```go
func viewHandler(w http.ResponseWriter, r *http.Request) {
    title := r.URL.Path[len("/view/"):]
    p, err := loadPage(title)
    if err != nil {
        http.Redirect(w, r, "/edit/"+title, http.StatusFound)
        return
    }
    fmt.Fprintf(w, "<h1>%s</h1><div>%s</div>", p.Title, p.Body)
}
```

Route:

```go
http.HandleFunc("/view/", viewHandler)
```

Но direct `fmt.Fprintf` HTML unsafe: page text может содержать markup/script. Следующий шаг — templates с auto-escaping.

## Editing

```go
func editHandler(w http.ResponseWriter, r *http.Request) {
    title := r.URL.Path[len("/edit/"):]
    p, err := loadPage(title)
    if err != nil {
        p = &Page{Title: title}
    }
    fmt.Fprintf(
        w,
        "<h1>Editing %s</h1><form action=\"/save/%s\" method=\"POST\"><textarea name=\"body\">%s</textarea><br><input type=\"submit\" value=\"Save\"></form>",
        p.Title,
        p.Title,
        p.Body,
    )
}
```

Again, tutorial quickly заменяет string-built HTML на `html/template`.

## Save handler

```go
func saveHandler(w http.ResponseWriter, r *http.Request) {
    title := r.URL.Path[len("/save/"):]
    body := r.FormValue("body")
    p := &Page{Title: title, Body: []byte(body)}

    if err := p.save(); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    http.Redirect(w, r, "/view/"+title, http.StatusFound)
}
```

`FormValue` parses submitted form fields. После save client redirect'ится на view page.

## Templates

`html/template` безопаснее ручной HTML interpolation: escaping выбирается по HTML context.

`edit.html`:

```html
<h1>Editing {{.Title}}</h1>
<form action="/save/{{.Title}}" method="POST">
<div><textarea name="body" rows="20" cols="80">{{printf "%s" .Body}}</textarea></div>
<div><input type="submit" value="Save"></div>
</form>
```

Load/execute:

```go
func editHandler(w http.ResponseWriter, r *http.Request) {
    title := r.URL.Path[len("/edit/"):]
    p, err := loadPage(title)
    if err != nil {
        p = &Page{Title: title}
    }

    t, err := template.ParseFiles("edit.html")
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    if err := t.Execute(w, p); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
    }
}
```

View template:

```html
<h1>{{.Title}}</h1>
<p>[<a href="/edit/{{.Title}}">edit</a>]</p>
<div>{{printf "%s" .Body}}</div>
```

> [!important]
> Используйте `html/template`, а не `text/template`, когда output вставляется в HTML. `html/template` выполняет context-aware escaping.

## Cache templates

Parsing files на каждый request inefficient и создаёт runtime failure surface. Tutorial предлагает parse templates once:

```go
var templates = template.Must(
    template.ParseFiles("edit.html", "view.html"),
)
```

Helper:

```go
func renderTemplate(w http.ResponseWriter, tmpl string, p *Page) {
    err := templates.ExecuteTemplate(w, tmpl+".html", p)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
    }
}
```

`template.Must` уместен для invariant startup resources: при invalid template program fail fast вместо скрытого runtime error позднее.

## Path validation

Исходный code позволяет title вроде `../../etc/passwd`, что превращается в path traversal risk.

Разрешим только `[A-Za-z0-9]+`:

```go
var validPath = regexp.MustCompile("^/(edit|save|view)/([a-zA-Z0-9]+)$")
```

Wrapper:

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

Handlers теперь получают validated `title`:

```go
func viewHandler(w http.ResponseWriter, r *http.Request, title string) {
    // ...
}
```

Registration:

```go
http.HandleFunc("/view/", makeHandler(viewHandler))
http.HandleFunc("/edit/", makeHandler(editHandler))
http.HandleFunc("/save/", makeHandler(saveHandler))
```

Это показывает idiomatic closure/adaptor pattern: wrapper выполняет common validation и передаёт normalized argument business handler'у.

## Полная версия

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
    return os.WriteFile(filename, p.Body, 0o600)
}

func loadPage(title string) (*Page, error) {
    filename := title + ".txt"
    body, err := os.ReadFile(filename)
    if err != nil {
        return nil, err
    }
    return &Page{Title: title, Body: body}, nil
}

var templates = template.Must(
    template.ParseFiles("edit.html", "view.html"),
)

var validPath = regexp.MustCompile("^/(edit|save|view)/([a-zA-Z0-9]+)$")

func renderTemplate(w http.ResponseWriter, tmpl string, p *Page) {
    if err := templates.ExecuteTemplate(w, tmpl+".html", p); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
    }
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

    if err := p.save(); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    http.Redirect(w, r, "/view/"+title, http.StatusFound)
}

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

## Что tutorial учит кроме HTTP

- methods на domain type;
- error propagation;
- file I/O;
- handlers as functions;
- closures/adapters;
- regex validation;
- templates и escaping;
- initialization/cache of immutable templates;
- separation common request validation от endpoint logic.

Для production добавьте context/timeouts, structured storage, authentication/authorization, CSRF strategy, logging/metrics, graceful shutdown и explicit HTTP server timeouts.
