---
title: "Краткое руководство по Go assembler"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/go"
upstream_path: "doc/asm.html"
upstream_ref: "go1.27.1"
translation_status: "translated"
---

# Краткое руководство по Go assembler

Go assembler standard toolchain основан на Plan 9 assembler style, но **не является прямой текстовой записью machine ISA**. Compiler/assembler работают с semi-abstract instruction set, а окончательная instruction selection partly выполняется позже toolchain/linker.

Поэтому `MOV` в Go assembly не обязательно буквально превращается в hardware move. Machine-specific operations ближе к ISA; общие concepts (`CALL`, memory movement, return) могут быть pseudo/abstract operations.

Документ — quick guide, не исчерпывающий architecture manual.

## Как посмотреть compiler output

```bash
GOOS=linux GOARCH=amd64 go tool compile -S x.go
```

или:

```bash
go build -gcflags -S x.go
```

После linking:

```bash
go build -o x.exe x.go
go tool objdump -s main.main x.exe
```

`FUNCDATA` и `PCDATA` в compiler listing содержат runtime/GC metadata и обычно генерируются compiler автоматически.

## Constants

Assembler constant expressions используют Go operator precedence, а не C/Plan9 precedence.

Например:

```text
3&1<<2
```

парсится как:

```text
(3&1)<<2
```

Constants вычисляются как unsigned 64-bit values. Это важно для negative literals, shifts и division edge cases.

## Registers и symbols

Architecture определяет hardware registers (`R1`, `AX`, `LR`, ...).

Общие pseudo-registers:

| Pseudo-register | Назначение |
|---|---|
| `FP` | Virtual frame pointer для function arguments/results. |
| `PC` | Program counter / branches. |
| `SB` | Static base для global text/data symbols. |
| `SP` | Virtual stack pointer local frame/call args. |

Это не обязательно real hardware registers.

### `SB`

Global symbol:

```text
foo(SB)
```

File-local symbol:

```text
foo<>(SB)
```

Offset:

```text
foo+4(SB)
```

### `FP`

Arguments/results адресуются как named offsets:

```text
first_arg+0(FP)
second_arg+8(FP)
ret+16(FP)
```

Plain `0(FP)` rejected: name обязательна и документирует semantic argument.

Для 32-bit части 64-bit value conventions могут использовать suffix `_lo` / `_hi`.

`go vet` проверяет offsets/names against Go prototype.

### `SP`

Virtual local-frame references имеют name + negative offset:

```text
x-8(SP)
y-4(SP)
```

Если architecture имеет real register `SP`, отсутствие symbol prefix означает hardware register. Поэтому `x-8(SP)` и `-8(SP)` могут быть разными forms.

### Labels и jumps

```asm
label:
    MOVW $0, R1
    JMP label
```

Labels scoped function-local. Несколько functions одного file могут повторять label names.

Direct `CALL`/jump может target text symbol `name(SB)`, но не offset `name+4(SB)`.

## Symbol spelling

Binary symbol logical name включает package path:

```text
fmt.Printf
math/rand.Int
```

Assembler source вместо punctuation использует Unicode:

```text
fmt·Printf
math∕rand·Int
```

Middle dot `·` → `.`, division slash `∕` → `/`.

Внутри package обычно используется relative form:

```text
·Int(SB)
```

Linker добавляет current package path, что делает source movable между import paths.

## Directives

### `TEXT`

Определяет function symbol/body:

```asm
TEXT runtime·profileloop(SB),NOSPLIT,$8
    MOVQ $runtime·profileloop1(SB), CX
    MOVQ CX, 0(SP)
    CALL runtime·externalthreadhandler(SB)
    RET
```

General frame annotation:

```text
$framesize-argsize
```

Например:

```text
$24-8
```

означает 24-byte local frame и 8 bytes caller arguments.

Если `NOSPLIT` отсутствует, argument size обычно обязателен. `go vet` сверяет его с Go prototype.

`TEXT` block не fall through в следующий symbol; он должен завершаться control transfer (`RET`, jump и т. п.).

### `DATA`

Инициализирует fragment global memory:

```asm
DATA symbol+offset(SB)/width, value
```

Offsets одного symbol должны идти по возрастанию.

### `GLOBL`

Объявляет global data symbol и size; unspecified bytes zero-initialized.

```asm
DATA divtab<>+0x00(SB)/4, $0xf4f8fcff
DATA divtab<>+0x04(SB)/4, $0xe6eaedf0
GLOBL divtab<>(SB), RODATA, $64

GLOBL runtime·tlsoffset(SB), NOPTR, $4
```

## Flags `textflag.h`

| Flag | Value | Meaning |
|---|---:|---|
| `NOPROF` | 1 | Deprecated: не profile function. |
| `DUPOK` | 2 | Допустимы duplicate symbols; linker выберет один. |
| `NOSPLIT` | 4 | Не добавлять stack-split preamble; frame + callees должны помещаться в spare stack space. |
| `RODATA` | 8 | Read-only data section. |
| `NOPTR` | 16 | Data не содержит pointers и не требует GC scanning. |
| `WRAPPER` | 32 | Wrapper frame не должен ломать `recover` semantics. |
| `NEEDCTXT` | 64 | Function является closure и использует incoming context register. |
| `LOCAL` | 128 | Symbol local dynamic shared object. |
| `TLSBSS` | 256 | Thread-local storage data. |
| `NOFRAME` | 512 | Не создавать frame/save-return-address; допустим только frame size 0. |
| `TOPFRAME` | 2048 | Outermost call-stack frame; traceback останавливается здесь. |

## `PCALIGN`

Pseudo-instruction выравнивает следующий instruction до boundary, вставляя NOP padding:

```asm
PCALIGN $32
MOVD $2, R0
```

Документированная поддержка: arm64, amd64, ppc64, loong64, riscv64.

## Взаимодействие с Go types: `go_asm.h`

Если package содержит `.s`, `go build` генерирует `go_asm.h`, который assembly может include.

Он содержит constants для:

- Go `const` values;
- field offsets;
- struct sizes.

Используйте их вместо hard-coded layout assumptions.

Go:

```go
const bufSize = 1024

type reader struct {
    buf [bufSize]byte
    r   int
}
```

Assembly names:

```text
const_bufSize
reader__size
reader_buf
reader_r
```

При pointer на `reader` в `R1`:

```asm
MOVQ reader_r(R1), R2
```

Если generated macro names конфликтуют, `#include "go_asm.h"` выдаст macro redefinition error.

## Runtime coordination и GC

Hand-written assembly обязана учитывать GC pointer maps.

### Global data

- `NOPTR` → symbol не содержит Go heap pointers;
- `RODATA` implicitly считается `NOPTR`;
- symbol меньше pointer size также implicitly `NOPTR`;
- symbol, реально содержащий Go pointers, следует определять в Go source, а assembly только reference'ить.

Practical rule: non-RODATA data по возможности объявляйте в Go.

### Stack frames

Runtime должен знать live pointers arguments/results/locals.

Для assembly function обязательно иметь Go prototype в том же package, особенно если есть args/results/calls. Это также позволяет `go vet` проверять offsets.

Если args/results отсутствуют:

```text
$framesize-0
```

может позволить omission pointer metadata.

Если result pointers могут быть live через `CALL`, их сначала нужно zero-initialize и использовать pseudo-instruction `GO_RESULTS_INITIALIZED`. В standard library стараются проектировать assembly functions так, чтобы этого не требовалось.

Если local frame size 0:

```text
$0-argsize
```

pointer map locals может быть не нужна. Function без calls также проще. Иначе local stack frame не должен хранить Go pointers без соответствующей metadata; `NO_LOCAL_POINTERS` подтверждает отсутствие pointers.

Поскольку goroutine stack может перемещаться при calls, pointer на stack data нельзя безопасно хранить как opaque local integer/pointer без правильной runtime awareness.

## Instruction direction

Go assembler convention: data обычно flows **left → right**.

```asm
MOVQ $0, CX
```

очищает `CX`, даже если native assembler конкретной architecture convention opposite.

## Architecture-specific notes

Полный ISA следует смотреть в `src/cmd/internal/obj/<arch>`; constants `A...` в `a.out.go` задают spellings, известные Go assembler/linker.

### 386

Runtime `g` доступается через TLS macro `get_tls` (`go_tls.h`).

```asm
get_tls(CX)
MOVL g(CX), AX
MOVL g_m(AX), BX
```

Indexed addressing:

```text
(DI)(BX*2)
64(DI)(BX*2)
```

Scale factors: 1, 2, 4, 8.

В `-dynlink`/`-shared` mode fixed global memory accesses могут clobber `CX`, поэтому hand-written code должен учитывать это.

### amd64

Многие conventions аналогичны 386, но используются 64-bit instructions:

```asm
get_tls(CX)
MOVQ g(CX), AX
MOVQ g_m(AX), BX
```

`BP` callee-save. Toolchain автоматически save/restore `BP` для non-zero frame. Использование `BP` как general register возможно, но может ухудшать sampling-profiler stack behavior.

### ARM

- `R10`/`R11` reserved compiler/linker;
- goroutine pointer logical name — `g`;
- real hardware `SP` — `R13`, `PC` — `R15`;
- frame size `$-4` может обозначать leaf function без LR save;
- linker расширяет pseudo addressing/instructions и может использовать `R11` temporary;
- condition suffixes: `MOVW.EQ`, `MOVM.IA.W`.

Shift forms:

```text
R0<<16
R0>>16
R0->16
R0@>16
```

и variants с shift count register.

### ARM64

- `R18_PLATFORM` reserved platform register на Apple platforms;
- `R27`, `R28` reserved;
- `R29` frame pointer;
- `R30` link register;
- modifiers `.P` (postincrement) и `.W` (preincrement).

Supports register-offset, shifted/extended-register addressing, pre/post-indexed forms и architecture-specific SIMD/system instructions.

### PPC64 / PPC64LE

Go assembler follows POWER-family Plan 9 style. Architecture has rich register pairs, condition registers и branch conventions; используйте source `cmd/internal/obj/ppc64` как authoritative instruction list.

### MIPS / MIPS64

Plan 9-style register and branch syntax применяется с architecture-specific constraints. `g` register и linker conventions зависят от port.

### RISC-V 64

Go assembler предоставляет RISC-V instructions в Go/Plan9 operand order, pseudo operations и standard Go runtime stack/GC integration. Authoritative opcode set — `cmd/internal/obj/riscv`.

### S390X, Loong64 и другие supported ports

Instruction list и addressing modes определяются соответствующим `cmd/internal/obj/<arch>`. Общие rules этого guide — pseudo-registers, symbols, `TEXT/DATA/GLOBL`, GC metadata, Go prototype, left-to-right operands — сохраняются.

## Практический вывод

Hand-written Go assembly — часть Go toolchain ABI/runtime, а не portable standalone assembler language. Для безопасного кода необходимо одновременно учитывать:

- конкретную architecture;
- Go assembler syntax;
- Go ABI/prototypes;
- stack growth;
- GC pointer maps;
- linker transformations;
- `go vet` checks.

Если производительность не требует assembly, Go source + compiler intrinsics/optimizations обычно безопаснее и проще сопровождать.
