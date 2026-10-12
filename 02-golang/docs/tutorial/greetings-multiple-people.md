---
title: "Приветствия для нескольких людей"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/website"
upstream_path: "_content/doc/tutorial/greetings-multiple-people.html"
upstream_ref: "575a6925e2d55ad160ed77f402bfaa4ec7458749"
translation_status: "translated"
---

# Приветствия для нескольких людей

Нужно добавить API, принимающий несколько names. Менять signature существующего `Hello` после публикации было бы breaking change. Вместо этого добавим новую function `Hellos` и сохраним старую API для backward compatibility.

```go
func Hellos(names []string) (map[string]string, error) {
    messages := make(map[string]string)

    for _, name := range names {
        message, err := Hello(name)
        if err != nil {
            return nil, err
        }
        messages[name] = message
    }

    return messages, nil
}
```

Здесь:

- input — `[]string`;
- output — `map[string]string`;
- `make(map[K]V)` создаёт writable map;
- `range` возвращает index и value;
- blank identifier `_` игнорирует ненужный index;
- existing `Hello` переиспользуется вместо дублирования validation/formatting logic.

Caller:

```go
names := []string{"Gladys", "Samantha", "Darrin"}

messages, err := greetings.Hellos(names)
if err != nil {
    log.Fatal(err)
}

fmt.Println(messages)
```

Пример результата:

```text
map[Darrin:Hail, Darrin! Well met! Gladys:Hi, Gladys. Welcome! Samantha:Hail, Samantha! Well met!]
```

Главный design lesson этой части tutorial: новая backward-compatible functionality часто лучше добавляется новым exported API, чем изменением existing signature.

Следующий шаг — [[add-a-test|unit tests]].
