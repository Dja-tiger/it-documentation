---
title: "Краткое руководство по Go assembler"
technology: "Go"
version: "1.27.1"
upstream_repository: "golang/go"
upstream_path: "doc/asm.html"
upstream_ref: "go1.27.1"
translation_status: "reviewed"
---

# Краткое руководство по Go assembler

Этот документ — краткий обзор необычной формы assembly language, используемой Go compiler `gc`. Документ не является исчерпывающим.

Assembler основан на input style Plan 9 assemblers, подробно описанном в [Plan 9 assembler manual](https://9p.io/sys/doc/asm.html). Если вы собираетесь писать assembly, этот документ стоит прочитать, хотя большая его часть специфична для Plan 9.

Здесь приведены summary syntax, отличия от Plan 9 assembler и особенности написания assembly code, взаимодействующего с Go.

Самое важное: **Go assembler не является прямым представлением underlying machine**.

Некоторые details точно соответствуют machine, некоторые — нет. Compiler suite работает с semi-abstract instruction set, а instruction selection частично происходит уже после code generation.

Assembler принимает эту semi-abstract form. Поэтому instruction вроде `MOV` может в итоге стать не machine move instruction, а, например, clear или load. В других случаях она может точно соответствовать hardware instruction с таким name.

В общем случае machine-specific operations чаще отображаются напрямую, а более общие concepts — memory move, subroutine call, return — представлены более abstract. Details различаются по architectures.

Assembler program разбирает описание semi-abstract instruction set и превращает его в instructions для linker.

Чтобы посмотреть examples для конкретной architecture, например amd64, изучите assembly sources standard library, особенно packages [`runtime`](https://pkg.go.dev/runtime) и [`math/big`](https://pkg.go.dev/math/big).

Также можно посмотреть assembly, генерируемый compiler:

```text
$ cat x.go
package main

func main() {
	println(3)
}
$ GOOS=linux GOARCH=amd64 go tool compile -S x.go        # or: go build -gcflags -S x.go
"".main STEXT size=74 args=0x0 locals=0x10
	0x0000 00000 (x.go:3)	TEXT	"".main(SB), $16-0
	0x0000 00000 (x.go:3)	MOVQ	(TLS), CX
	0x0009 00009 (x.go:3)	CMPQ	SP, 16(CX)
	0x000d 00013 (x.go:3)	JLS	67
	0x000f 00015 (x.go:3)	SUBQ	$16, SP
	0x0013 00019 (x.go:3)	MOVQ	BP, 8(SP)
	0x0018 00024 (x.go:3)	LEAQ	8(SP), BP
	0x001d 00029 (x.go:3)	FUNCDATA	$0, gclocals·33cdeccccebe80329f1fdbee7f5874cb(SB)
	0x001d 00029 (x.go:3)	FUNCDATA	$1, gclocals·33cdeccccebe80329f1fdbee7f5874cb(SB)
	0x001d 00029 (x.go:3)	FUNCDATA	$2, gclocals·33cdeccccebe80329f1fdbee7f5874cb(SB)
	0x001d 00029 (x.go:4)	PCDATA	$0, $0
	0x001d 00029 (x.go:4)	PCDATA	$1, $0
	0x001d 00029 (x.go:4)	CALL	runtime.printlock(SB)
	0x0022 00034 (x.go:4)	MOVQ	$3, (SP)
	0x002a 00042 (x.go:4)	CALL	runtime.printint(SB)
	0x002f 00047 (x.go:4)	CALL	runtime.printnl(SB)
	0x0034 00052 (x.go:4)	CALL	runtime.printunlock(SB)
	0x0039 00057 (x.go:5)	MOVQ	8(SP), BP
	0x003e 00062 (x.go:5)	ADDQ	$16, SP
	0x0042 00066 (x.go:5)	RET
	0x0043 00067 (x.go:5)	NOP
	0x0043 00067 (x.go:3)	PCDATA	$1, $-1
	0x0043 00067 (x.go:3)	PCDATA	$0, $-1
	0x0043 00067 (x.go:3)	CALL	runtime.morestack_noctxt(SB)
	0x0048 00072 (x.go:3)	JMP	0
...
```

Directives `FUNCDATA` и `PCDATA` содержат information для garbage collector; compiler добавляет их автоматически.

После linking binary можно исследовать через `go tool objdump`:

```text
$ go build -o x.exe x.go
$ go tool objdump -s main.main x.exe
TEXT main.main(SB) /tmp/x.go
  x.go:3		0x10501c0		65488b0c2530000000	MOVQ GS:0x30, CX
  x.go:3		0x10501c9		483b6110		CMPQ 0x10(CX), SP
  x.go:3		0x10501cd		7634			JBE 0x1050203
  x.go:3		0x10501cf		4883ec10		SUBQ $0x10, SP
  x.go:3		0x10501d3		48896c2408		MOVQ BP, 0x8(SP)
  x.go:3		0x10501d8		488d6c2408		LEAQ 0x8(SP), BP
  x.go:4		0x10501dd		e86e45fdff		CALL runtime.printlock(SB)
  x.go:4		0x10501e2		48c7042403000000	MOVQ $0x3, 0(SP)
  x.go:4		0x10501ea		e8e14cfdff		CALL runtime.printint(SB)
  x.go:4		0x10501ef		e8ec47fdff		CALL runtime.printnl(SB)
  x.go:4		0x10501f4		e8d745fdff		CALL runtime.printunlock(SB)
  x.go:5		0x10501f9		488b6c2408		MOVQ 0x8(SP), BP
  x.go:5		0x10501fe		4883c410		ADDQ $0x10, SP
  x.go:5		0x1050202		c3			RET
  x.go:3		0x1050203		e83882ffff		CALL runtime.morestack_noctxt(SB)
  x.go:3		0x1050208		ebb6			JMP main.main(SB)
```

## Constants

Хотя assembler ориентируется на Plan 9 assemblers, это отдельная program, поэтому существуют отличия.

Одно из них — вычисление constants.

Constant expressions assembler разбираются с Go operator precedence, а не C-like precedence оригинального assembler.

Поэтому:

```text
3&1<<2
```

равно `4`, а не `0`, поскольку expression разбирается как:

```text
(3&1)<<2
```

а не:

```text
3&(1<<2)
```

Constants всегда вычисляются как unsigned 64-bit integers.

Следовательно, `-2` — не signed integer minus two, а unsigned 64-bit integer с тем же bit pattern.

Разница редко важна, но для устранения ambiguity assembler отвергает division или right shift, если high bit right operand установлен.

## Symbols

Некоторые symbols, например `R1` или `LR`, predefined и обозначают registers. Exact set зависит от architecture.

Существуют четыре predeclared pseudo-registers. Это не реальные hardware registers, а virtual registers, поддерживаемые toolchain.

Они одинаковы для всех architectures:

- `FP` — frame pointer: arguments и locals;
- `PC` — program counter: jumps и branches;
- `SB` — static base pointer: global symbols;
- `SP` — stack pointer: highest address внутри local stack frame.

Все user-defined symbols записываются как offsets от `FP` для arguments/locals или `SB` для globals.

### `SB`

Pseudo-register `SB` можно считать origin memory.

```text
foo(SB)
```

означает global symbol `foo` как memory address.

Добавление `<>`:

```text
foo<>(SB)
```

делает symbol visible только в текущем source file, аналогично top-level `static` declaration в C.

Offset:

```text
foo+4(SB)
```

означает address на 4 bytes после начала `foo`.

### `FP`

`FP` — virtual frame pointer для function arguments.

Compiler обращается к stack arguments как offsets от этого pseudo-register:

```text
0(FP)
8(FP)
```

Однако при обращении к argument необходимо добавить name:

```text
first_arg+0(FP)
second_arg+8(FP)
```

Assembler отвергает plain forms `0(FP)` и `8(FP)`.

Сам name semantically irrelevant, но должен документировать argument name.

`FP` **всегда** является pseudo-register, даже на architecture с hardware frame pointer.

Для assembly functions с Go prototypes `go vet` проверяет names и offsets arguments.

На 32-bit systems low/high 32 bits 64-bit value различаются suffixes `_lo` и `_hi`:

```text
arg_lo+0(FP)
arg_hi+4(FP)
```

Если Go prototype не называет result, ожидаемое assembly name — `ret`.

### `SP`

`SP` pseudo-register — virtual stack pointer для frame-local variables и arguments, подготавливаемых для function calls.

Он указывает на highest address local stack frame, поэтому references используют negative offsets в range `[−framesize, 0)`:

```text
x-8(SP)
y-4(SP)
```

На architectures с hardware register `SP` наличие symbol prefix отличает virtual stack pointer от architectural register.

Поэтому:

```text
x-8(SP)
-8(SP)
```

обозначают разные memory locations.

На machines, где `SP` и `PC` традиционно aliases physical numbered registers, Go assembler всё равно обрабатывает names `SP` и `PC` specially. Для actual hardware register используйте real `R` name.

Например, на ARM hardware `SP` и `PC` доступны как `R13` и `R15`.

### Labels и jumps

Branches и direct jumps записываются как offsets от `PC` либо как jumps к labels:

```asm
label:
	MOVW $0, R1
	JMP label
```

Каждый label visible только внутри function, в которой определён. Поэтому несколько functions одного file могут использовать одинаковые label names.

Direct jumps и call instructions могут target'ить text symbols вроде:

```text
name(SB)
```

но не offsets:

```text
name+4(SB)
```

Instructions, registers и assembler directives всегда пишутся UPPER CASE, чтобы напоминать, что assembly programming — опасная работа. Исключение — rename register `g` на ARM.

### Полные symbol names

В Go object files и binaries полный name symbol состоит из package path, точки и symbol name:

```text
fmt.Printf
math/rand.Int
```

Assembler parser воспринимает `.` и `/` как punctuation, поэтому в source используется:

- middle dot U+00B7 `·` вместо `.`;
- division slash U+2215 `∕` вместо `/`.

То есть:

```text
fmt·Printf
math∕rand·Int
```

Compiler listings с flag `-S` показывают обычные `.` и `/`, а не Unicode replacements.

Большинство handwritten assembly files не указывают полный package path. Linker добавляет current package path к любому name, начинающемуся с dot.

Например, внутри package `math/rand` function `Int` можно reference'ить как:

```text
·Int
```

Это позволяет перемещать package между import paths без hard-coded path в assembly source.

## Directives

Assembler использует directives для привязки text/data к symbol names.

### `TEXT`

Пример complete function definition:

```asm
TEXT runtime·profileloop(SB),NOSPLIT,$8
	MOVQ	$runtime·profileloop1(SB), CX
	MOVQ	CX, 0(SP)
	CALL	runtime·externalthreadhandler(SB)
	RET
```

`TEXT` объявляет symbol `runtime·profileloop`; последующие instructions образуют body function.

Последняя instruction в `TEXT` block должна быть jump, обычно pseudo-instruction `RET`. Если её нет, linker добавит jump-to-itself. Fallthrough между `TEXT` blocks отсутствует.

После symbol идут optional flags и frame size.

В общем случае после frame size указывается argument size через minus sign:

```text
$24-8
```

Это не subtraction: syntax означает frame 24 bytes и 8 bytes arguments в caller frame.

Если `NOSPLIT` не указан, argument size обязателен.

Для assembly functions с Go prototypes `go vet` проверяет корректность argument size.

Symbol name использует middle dot и задаётся как offset от `SB`.

Function выше из Go code package `runtime` вызывается как `profileloop`.

### `DATA` и `GLOBL`

Global data symbols определяются sequence initializing `DATA` directives, после которых идёт `GLOBL`.

Каждый `DATA` инициализирует section corresponding memory. Неинициализированная memory zeroed.

General form:

```text
DATA	symbol+offset(SB)/width, value
```

`DATA` directives одного symbol должны идти с increasing offsets.

`GLOBL` объявляет symbol global. Arguments — optional flags и data size. Initial value по default all zeros, кроме bytes, заданных `DATA`.

`GLOBL` должен идти после соответствующих `DATA` directives.

Пример:

```asm
DATA divtab<>+0x00(SB)/4, $0xf4f8fcff
DATA divtab<>+0x04(SB)/4, $0xe6eaedf0
...
DATA divtab<>+0x3c(SB)/4, $0x81828384
GLOBL divtab<>(SB), RODATA, $64

GLOBL runtime·tlsoffset(SB), NOPTR, $4
```

Здесь `divtab<>` — read-only 64-byte table 4-byte integer values, а `runtime·tlsoffset` — 4-byte implicitly zeroed variable без pointers.

### Flags из `textflag.h`

Если directive имеет два arguments, первый — bit mask flags. Его можно записывать numeric expressions либо symbolic names.

Значения из `textflag.h`:

- `NOPROF = 1` — для `TEXT`; не profile function. Deprecated.
- `DUPOK = 2` — допускается несколько экземпляров symbol в одном binary; linker выберет один.
- `NOSPLIT = 4` — для `TEXT`; не вставлять preamble stack-split check. Frame routine и всё, что она вызывает, должны помещаться в spare space current stack segment. Используется, например, самим stack splitting code.
- `RODATA = 8` — для `DATA`/`GLOBL`; поместить data в read-only section.
- `NOPTR = 16` — для `DATA`/`GLOBL`; data не содержит pointers и не требует GC scan.
- `WRAPPER = 32` — для `TEXT`; function является wrapper и не должна считаться disabling `recover`.
- `NEEDCTXT = 64` — для `TEXT`; function является closure и использует incoming context register.
- `LOCAL = 128` — symbol local dynamic shared object.
- `TLSBSS = 256` — для `DATA`/`GLOBL`; поместить data в thread local storage.
- `NOFRAME = 512` — для `TEXT`; не вставлять instructions для allocation stack frame и save/restore return address, даже если function не leaf. Valid только при frame size 0.
- `TOPFRAME = 2048` — для `TEXT`; function — outermost call-stack frame, traceback должен останавливаться здесь.

## Special instructions

### `PCALIGN`

Pseudo-instruction `PCALIGN` указывает выровнять следующую instruction до заданной boundary с помощью no-op padding.

Сейчас поддерживается на:

- arm64;
- amd64;
- ppc64;
- loong64;
- riscv64.

Пример: начало `MOVD` выровнено по 32 bytes:

```asm
PCALIGN $32
MOVD $2, R0
```

## Взаимодействие с Go types и constants

Если package содержит `.s` files, `go build` просит compiler сгенерировать special header `go_asm.h`, который `.s` files могут `#include`.

Он содержит symbolic `#define` constants для:

- offsets Go struct fields;
- sizes Go struct types;
- большинства Go `const` declarations current package.

Go assembly должен избегать assumptions о layout Go types и использовать эти constants. Это повышает readability и делает assembly устойчивым к changes data layout и compiler layout rules.

Constants имеют форму:

```text
const_name
```

Например:

```go
const bufSize = 1024
```

становится:

```text
const_bufSize
```

Field offsets имеют form:

```text
type_field
```

Struct sizes:

```text
type__size
```

Например:

```go
type reader struct {
	buf [bufSize]byte
	r   int
}
```

Assembly может использовать:

```text
reader__size
reader_buf
reader_r
```

Если `R1` содержит pointer на `reader`:

```asm
MOVQ reader_r(R1), R2
```

Если generated `#define` names ambiguous, например struct имеет field `_size`, `#include "go_asm.h"` завершится error `redefinition of macro`.

## Runtime coordination

Для корректной garbage collection runtime должен знать location pointers во всех global data и большинстве stack frames.

Go compiler генерирует эту information для Go source, но assembly programs обязаны определить её явно.

### Global data

Data symbol с flag `NOPTR` считается не содержащим pointers на runtime-allocated data.

`RODATA` symbol находится в read-only memory и поэтому implicitly считается `NOPTR`.

Data symbol total size меньше pointer size также implicitly считается `NOPTR`.

Нельзя определить symbol, содержащий pointers, в assembly source file. Такой symbol должен быть объявлен в Go source file. Assembly всё равно может reference'ить его по name без `DATA` и `GLOBL` directives.

Хорошее правило: все non-`RODATA` symbols определяйте в Go, а не в assembly.

### Stack frames и pointer maps

Каждой function нужны annotations, указывающие live pointers в arguments, results и local stack frame.

Для assembly function без pointer results и либо без local stack frame, либо без function calls достаточно определить Go prototype в Go source file того же package.

Assembly function name в `TEXT` не должен включать package component. Например, function `Syscall` в package `syscall` должна называться:

```text
·Syscall
```

а не:

```text
syscall·Syscall
```

Для сложных случаев нужны explicit annotations через pseudo-instructions из `funcdata.h`.

Если function не имеет arguments и results, pointer information можно опустить. Это обозначается argument-size annotation:

```text
$n-0
```

на `TEXT` instruction.

Иначе pointer information должен предоставлять Go prototype, даже если assembly function не вызывается напрямую из Go. Prototype также позволяет `go vet` проверять argument references.

В начале function arguments считаются initialized, results — uninitialized.

Если results будут содержать live pointers во время `CALL`, function должна сначала zero-initialize results, а затем выполнить:

```text
GO_RESULTS_INITIALIZED
```

Instruction сообщает runtime, что results теперь initialized и должны scan'иться во время stack movement и GC.

Обычно проще спроектировать assembly functions так, чтобы они либо не возвращали pointers, либо не содержали calls. В standard library ни одна assembly function не использует `GO_RESULTS_INITIALIZED`.

Если function не имеет local stack frame, local pointer information можно опустить. Это обозначается frame-size annotation:

```text
$0-n
```

Pointer information также можно опустить, если function не содержит call instructions.

В остальных случаях local stack frame не должен содержать pointers, а assembly должна подтвердить это pseudo-instruction:

```text
NO_LOCAL_POINTERS
```

Stack resizing реализован перемещением stack, поэтому stack pointer может измениться во время любого function call. Даже pointers на stack data нельзя хранить в local variables.

Assembly functions следует **всегда** снабжать Go prototypes — и ради pointer information, и чтобы `go vet` проверял offsets argument accesses.

# Architecture-specific details

Перечислить все instructions и details каждой machine непрактично.

Чтобы узнать instructions конкретной architecture, например ARM, смотрите implementation `obj` support library:

```text
src/cmd/internal/obj/arm
```

File `a.out.go` содержит constants, начинающиеся с `A`:

```go
const (
	AAND = obj.ABaseARM + obj.A_ARCHSPECIFIC + iota
	AEOR
	ASUB
	ARSB
	AADD
	...
)
```

Это список instructions и их spellings, известных assembler/linker.

Leading `A` служит частью Go constant name: `AAND` соответствует assembly instruction `AND`.

Enumeration в основном alphabetical. Architecture-independent `AXXX` из `cmd/internal/obj` обозначает invalid instruction.

Order constants не связан с actual machine encoding; этим занимается `cmd/internal/obj`.

Instructions 386 и AMD64 перечислены вместе в:

```text
cmd/internal/obj/x86/a.out.go
```

Architectures используют common syntax addressing modes:

```text
(R1)
4(R1)
$foo(SB)
```

Assembler также поддерживает architecture-specific addressing modes, описанные ниже.

Во всех examples data flows **left to right**:

```asm
MOVQ $0, CX
```

очищает `CX`, даже если conventional notation architecture использует opposite direction.

## 32-bit Intel 386

Runtime pointer на structure `g` хранится через otherwise unused register в MMU.

В package `runtime` assembly может include `go_tls.h`, который определяет OS/architecture-dependent macro `get_tls` для доступа к этому register.

`get_tls` принимает register, куда загрузить pointer `g`.

Пример загрузки `g` и `m` через `CX`:

```asm
#include "go_tls.h"
#include "go_asm.h"
...
get_tls(CX)
MOVL	g(CX), AX     // Move g into AX.
MOVL	g_m(AX), BX   // Move g.m into BX.
```

`get_tls` также defined на amd64.

Addressing modes:

- `(DI)(BX*2)` — location at `DI + BX*2`;
- `64(DI)(BX*2)` — location at `DI + BX*2 + 64`.

Scale factors: `1`, `2`, `4`, `8`.

При `-dynlink` или `-shared` любой load/store fixed memory location, например global variable, может overwrite `CX`.

Поэтому assembly, которая должна работать в этих modes, обычно не должна использовать `CX` между memory references.

## 64-bit Intel 386 (amd64)

На assembler level amd64 и 386 в основном ведут себя одинаково.

Доступ к `m` и `g`:

```asm
get_tls(CX)
MOVQ	g(CX), AX     // Move g into AX.
MOVQ	g_m(AX), BX   // Move g.m into BX.
```

`BP` — callee-save register.

Assembler автоматически вставляет save/restore `BP`, если frame size больше zero.

Использовать `BP` как general-purpose register разрешено, но это может мешать sampling-based profiling.

## ARM

Registers `R10` и `R11` зарезервированы compiler/linker.

`R10` указывает на `g` structure. В assembly source этот pointer должен называться `g`; name `R10` не распознаётся.

ARM linker позволяет general addressing forms и pseudo-operations вроде `DIV`/`MOD`, которые могут не выражаться одной hardware instruction.

Он реализует их несколькими instructions и часто использует `R11` как temporary. Handwritten assembly может использовать `R11`, но тогда необходимо убедиться, что linker не использует его для expansion других instructions той же function.

Frame size:

```text
$-4
```

в `TEXT` сообщает linker, что это leaf function и `LR` сохранять не нужно.

Name `SP` всегда означает virtual stack pointer. Hardware register доступен как `R13`.

Condition code syntax: period + one/two-letter code:

```text
MOVW.EQ
MOVM.IA.W
```

Order modifiers не важен.

Addressing modes:

```text
R0->16
R0>>16
R0<<16
R0@>16
```

- `<<` — left shift;
- `->` — arithmetic right shift;
- `>>` — logical right shift;
- `@>` — rotate right.

Register-count variants:

```text
R0->R1
R0>>R1
R0<<R1
R0@>R1
```

Здесь shift count берётся из `R1`.

Multi-register set:

```text
[R0,g,R12-R15]
```

означает `R0`, `g` и inclusive range `R12`–`R15`.

Destination register pair:

```text
(R5, R6)
```

## ARM64

`R18` — platform register, reserved на Apple platform. Чтобы предотвратить accidental use, он называется:

```text
R18_PLATFORM
```

Также:

- `R27`, `R28` reserved compiler/linker;
- `R29` — frame pointer;
- `R30` — link register.

Instruction modifiers после period:

- `P` — postincrement;
- `W` — preincrement.

Examples:

```text
MOVW.P
MOVW.W
```

Addressing modes:

```text
R0->16
R0>>16
R0<<16
R0@>16
```

такие же, как ARM32.

Immediate shift:

```text
$(8<<12)
```

сдвигает immediate `8` влево на 12 bits.

Offset:

```text
8(R0)
```

означает `R0 + 8`.

Register offset:

```text
(R2)(R0)
```

location at `R0 + R2`.

Zero-extension:

```text
R0.UXTB
R0.UXTB<<imm
```

`UXTB` извлекает low 8 bits `R0` и zero-extends до size `R0`. Variant с `<<imm` дополнительно shifts result на `imm`, где `imm` ∈ `{0,1,2,3,4}`.

Другие extensions:

- `UXTH` — 16-bit;
- `UXTW` — 32-bit;
- `UXTX` — 64-bit.

Sign-extension:

```text
R0.SXTB
R0.SXTB<<imm
```

`SXTB` извлекает low 8 bits и sign-extends. Также существуют `SXTH`, `SXTW`, `SXTX`.

Register pair для `LDAXP`/`LDP`/`LDXP`/`STLXP`/`STP`:

```text
(R5, R6)
```

Reference: [Go ARM64 Assembly Instructions Reference Manual](https://pkg.go.dev/cmd/internal/obj/arm64).

## PPC64

Этот assembler используется для `GOARCH=ppc64` и `GOARCH=ppc64le`.

Reference: [Go PPC64 Assembly Instructions Reference Manual](https://pkg.go.dev/cmd/internal/obj/ppc64).

## IBM z/Architecture (s390x)

Registers `R10` и `R11` reserved. Assembler использует их как temporary при assembling некоторых instructions.

`R13` указывает на `g` structure и должен называться `g`; name `R13` не распознаётся.

`R15` указывает на stack frame и обычно должен использоваться через virtual registers `SP` и `FP`.

Load/store-multiple instructions работают с register range, заданным start/end register.

Например:

```text
LMG (R9), R5, R7
```

загружает:

- `R5` из `0(R9)`;
- `R6` из `8(R9)`;
- `R7` из `16(R9)`.

Storage-and-storage instructions вроде `MVC` и `XC` записываются с length первым argument.

Например:

```text
XC $8, (R9), (R9)
```

очищает 8 bytes по address в `R9`.

Если vector instruction принимает length или index, он идёт первым argument.

Например:

```text
VLEIF $1, $16, V2
```

загружает value `16` в index `1` vector `V2`.

Перед использованием vector instructions убедитесь, что они доступны runtime. Machine должна иметь:

- vector facility — bit 129 facility list;
- kernel support.

Без kernel support vector instruction не имеет effect и эквивалентна `NOP`.

Addressing mode:

```text
(R5)(R6*1)
```

означает `R5 + R6`. Это scaled mode как x86, но разрешён только scale `1`.

## MIPS / MIPS64

General-purpose registers: `R0`–`R31`.

Floating-point registers: `F0`–`F31`.

`R30` reserved для pointer `g`.

`R23` используется как temporary register.

В `TEXT` frame size:

- `$-4` для MIPS;
- `$-8` для MIPS64

указывает linker не сохранять `LR`.

`SP` означает virtual stack pointer. Hardware register — `R29`.

Addressing modes:

```text
16(R1)
```

location at `R1 + 16`.

```text
(R1)
```

alias `0(R1)`.

Environment `GOMIPS` (`hardfloat`/`softfloat`) доступен assembly через predefined:

```text
GOMIPS_hardfloat
GOMIPS_softfloat
```

А `GOMIPS64` через:

```text
GOMIPS64_hardfloat
GOMIPS64_softfloat
```

## RISCV64

Reference: [Go RISCV64 Assembly Instructions Reference Manual](https://pkg.go.dev/cmd/internal/obj/riscv).

## Unsupported opcodes

Assemblers созданы прежде всего для compiler, поэтому не все hardware instructions определены для всех architectures. Если compiler не генерирует instruction, её может не быть в assembler.

Если нужна отсутствующая instruction, возможны два пути:

1. добавить support в assembler — straightforward и имеет смысл, если instruction будет использоваться снова;
2. для one-off case использовать directives `BYTE` и `WORD`, чтобы явно записать machine data в instruction stream внутри `TEXT`.

Так 386 runtime определяет 64-bit atomic load function:

```asm
// uint64 atomicload64(uint64 volatile* addr);
// so actually
// void atomicload64(uint64 *res, uint64 volatile *addr);
TEXT runtime·atomicload64(SB), NOSPLIT, $0-12
	MOVL	ptr+0(FP), AX
	TESTL	$7, AX
	JZ	2(PC)
	MOVL	0, AX // crash with nil ptr deref
	LEAL	ret_lo+4(FP), BX
	// MOVQ (%EAX), %MM0
	BYTE $0x0f; BYTE $0x6f; BYTE $0x00
	// MOVQ %MM0, 0(%EBX)
	BYTE $0x0f; BYTE $0x7f; BYTE $0x03
	// EMMS
	BYTE $0x0F; BYTE $0x77
	RET
```
