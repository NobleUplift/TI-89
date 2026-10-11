# `.89p` tokenization and tag tables

How a TI-68k TI-BASIC program is encoded as byte-code, and the tag tables needed to read it.

A program in a `.89p` container is stored one of two ways: as plain source text, or as byte-code.
47 of the 102 `.89p`/`.89f` programs in this repository are byte-code, which is why
`tools/ti89-textconv.py` can only hex-dump them and `tools/ti89-detok.py` exists.

Which form a program is in records **what happened to it last**, not whether it was ever run.
Executing a program compiles it in place; opening it in the Program Editor and leaving writes the
source back out as text. So byte-code means "run more recently than edited" and text means
"edited more recently than run". The evidence is in this backup: `main\kbdprgm3` is the keyboard
program that was run constantly and is stored as text, because it was also the one most often
edited. A naive reading of the split as "the programs that got used" is wrong.

Nothing here is specific to this backup. It applies to any `*.89p`, `*.9xp`, `*.92p` or `*.v2p`
program from a TI-89, TI-89 Titanium, TI-92 Plus or Voyage 200.

## References

| Source | What it establishes |
|---|---|
| [TI-BASIC Developer, 68k tokenization](https://tibasicdev.wikidot.com/68k:tokenization) | That commands are replaced by a one- or two-byte token, and that a program is converted to **postfix** notation. It gives no byte values, but it names the reference that does. |
| [GCC4TI](https://github.com/debrouxl/gcc4ti) (`debrouxl/gcc4ti`) | The maintained successor to TIGCC. Holds the real tables. |
| [`trunk/tigcc/include/C/estack.h`](https://github.com/debrouxl/gcc4ti/blob/next/trunk/tigcc/include/C/estack.h) ([raw](https://raw.githubusercontent.com/debrouxl/gcc4ti/next/trunk/tigcc/include/C/estack.h)) | The four enumerations below. This is the authoritative table; everything in this document was derived from it and then checked against the programs. |
| [GCC4TI `estack.h` documentation](https://debrouxl.github.io/gcc4ti/estack.html) | Prose description of the expression stack. Describes the `Tags` enum but does **not** list its values, so the header itself is required. |
| [TIGCC `estack.h` documentation](http://tigcc.ticalc.org/doc/estack.html) | The original of the above. Served over HTTP; its HTTPS certificate does not cover the `tigcc` subdomain, so an HTTPS-upgrading fetcher will fail on it. |

The four enumerations in `estack.h`, with **unique values** and **declared names** counted
separately. The gap between those two columns is not noise: it is the dual naming described under
"The `_ITAG` / `_TAG` trap" below, and it is the one thing most likely to make a decoder wrong in
a way that still looks plausible.

| Enum | Unique values | Names | Purpose |
|---|---|---|---|
| `Tags` | 322 | 379 | primary one-byte tags: literals, operators, functions, structure |
| `InstructionTags` | 216 | 314 | statements, indexed by `EXT_INSTR_TAG` |
| `ExtTags` | 91 | 112 | extended functions, indexed by `EXT_TAG` |
| `SysvarTags` | 113 | 113 | system variable names |

## Where the byte-code is

Inside the container, the variable data begins at `0x56` with a two-byte **big-endian** length,
so the body is `data[0x58 : 0x58 + length]`. The full container layout is at the top of
`tools/ti89-textconv.py` and in the README.

To tell the two storage forms apart, look at the second-to-last byte of the body: `0x08` means
the program is stored as source text, anything else means byte-code.

## The stream reads backwards

The body is a single postfix expression stack, and **it reads from its last byte toward its
first**. Walking down from the end yields the program from its first line to its last. A decoder
that starts at offset 0 and reads forward will produce nonsense.

The outermost frame of a program is therefore, reading backwards from the final byte:

```
DC            FUNC_TAG            the variable is a program or function
...           argument list        e.g. 00 01 00 for ()
E5            END_TAG
19 E4         Prgm                 or 17 E4 for Func
...           the program body, one statement at a time, E8 between lines
12 E4         EndPrgm              or 0F E4 for EndFunc
E9            ENDSTACK_TAG         first byte of the body
```

## Token forms

Each form below is written in the order the bytes appear **in the file**. The decoder meets them
right to left.

| Form | Meaning |
|---|---|
| `<tag>` | one-byte primary tag from `Tags` |
| `<idx> E4` or `<idx> E4 00` | statement; `idx` indexes `InstructionTags` |
| `<idx> E3` or `<idx> E3 00` | extended function; `idx` indexes `ExtTags` |
| `00 <name> 00` | `VAR_NAME_TAG`: a user name, at most 8 characters |
| `00 <text> 00 2D` | `STR_TAG`: a string literal |
| `<digits> <len> 1F` | `POSINT_TAG`: integer, `len` bytes, little-endian |
| `00 folder\name 00 DA` | `USERFUNC_TAG`: a call to another program or function |
| `0x01`..`0x1B` | the reserved single-letter variables, in the order q, r, s…z, a…p |
| `E8` | line break |
| `E6` | comment, so `©` text survives compilation |
| `E9` | end of stack, the first byte of the body |

Two consequences matter in practice. First, string literals and qualified program names survive
compilation as literal ASCII, so a call graph can be recovered from a tokenized program without
decoding anything. Second, `0x00` is `VAR_NAME_TAG`, so a name followed by `0x00` is simply
another name: `DelVar a,b,c` and a `Toolbar` operand list look identical at the byte level.

## The `_ITAG` / `_TAG` trap

Every value in `InstructionTags` carries **two names**, an `_ITAG` and a `_TAG`, and they are two
different numbering spaces for the same statements:

| Statement | `_ITAG` | `_TAG` |
|---|---|---|
| `Prgm` | `0x19` | `0x25` |
| `EndPrgm` | `0x12` | `0x18` |
| `Lbl` | `0x30` | `0x48` |
| `Goto` | `0x2F` | `0x47` |
| `Toolbar` | `0x1D` | `0x29` |
| `EndTBar` | `0x13` | `0x19` |
| `Disp` | `0x7A` | `0x122` |
| `Local` | `0x7D` | `0x125` |

**`EXT_INSTR_TAG` indexes the `_ITAG` half only.** Two independent facts establish this: the
`_TAG` values run past one byte (`DISP_TAG` is `0x122`, `LOCAL_PRGM_TAG` is `0x249`), so they
cannot be a single-byte stream index; and decoding with the `_ITAG` half produces block
constructs that balance exactly, which the `_TAG` half does not.

Reading the wrong half is silently plausible rather than obviously broken, which is what makes it
a trap. `0x30` becomes `Trace` instead of `Lbl`, and `0x2F` becomes `int2Hex` instead of `Goto`.
Note also that distinct statements collide across the halves: `PRGM_ITAG` and `ENDTBAR_TAG` are
both `0x19`, and `ENDPRGM_TAG` and `LOOP_ITAG` are both `0x18`. `Prgm` and `EndPrgm` themselves
never share a value.

## How the decoding was verified

Every paired block construct in the 47 tokenized programs balances, which a wrong table would not
produce:

| Opening | Count | Closing | Count |
|---|---|---|---|
| `Prgm` | 46 | `EndPrgm` | 46 |
| `Func` | 1 | `EndFunc` | 1 |
| `If...Then` | 332 | `EndIf` | 332 |
| `Toolbar` | 12 | `EndTBar` | 12 |
| `Dialog` | 23 | `EndDlog` | 23 |
| `For` | 18 | `EndFor` | 18 |
| `While` | 5 | `EndWhile` | 5 |
| `Loop` | 5 | `EndLoop` | 5 |
| `Custom` | 1 | `EndCustm` | 1 |

46 programs plus 1 function is exactly the 47 files scanned, and `FUNC_TAG`, `ENDSTACK_TAG` and
`Local` each occur 47 times, once per file. Separately, `kadich\kbdprgm1` decodes to a coherent
program end to end: `Prgm / ClrIO / Local y / PopUp {"Csc","End"},pu / If pu=1 Then / InputStr
"Number..." / expr(string(…)) / kadich\cssc / DispHome / EndIf / If pu=2 Then / Goto end / EndIf
/ Lbl end / DelVar pu / EndPrgm`.

## Statement tags observed

65 of the 216 `InstructionTags` values occur in this repository. Names are verbatim from
`estack.h`; the index is the byte that precedes `E4`.

| Index | Enum name | Uses |
|---|---|---|
| `0x01` | `CLRDRAW_ITAG` | 16 |
| `0x02` | `CLRGRAPH_ITAG` | 5 |
| `0x03` | `CLRHOME_ITAG` | 5 |
| `0x04` | `CLRIO_ITAG` | 336 |
| `0x05` | `CLRTABLE_ITAG` | 1 |
| `0x06` | `CUSTOM_ITAG` | 1 |
| `0x08` | `DIALOG_ITAG` | 23 |
| `0x0B` | `ELSE_ITAG` | 30 |
| `0x0C` | `ENDCUSTM_ITAG` | 1 |
| `0x0D` | `ENDDLOG_ITAG` | 23 |
| `0x0E` | `ENDFOR_ITAG` | 18 |
| `0x0F` | `ENDFUNC_ITAG` | 1 |
| `0x10` | `ENDIF_ITAG` | 332 |
| `0x11` | `ENDLOOP_ITAG` | 5 |
| `0x12` | `ENDPRGM_ITAG` | 46 |
| `0x13` | `ENDTBAR_ITAG` | 12 |
| `0x15` | `ENDWHILE_ITAG` | 5 |
| `0x17` | `FUNC_ITAG` | 1 |
| `0x18` | `LOOP_ITAG` | 5 |
| `0x19` | `PRGM_ITAG` | 46 |
| `0x1A` | `SHOWSTAT_ITAG` | 1 |
| `0x1B` | `STOP_ITAG` | 11 |
| `0x1D` | `TOOLBAR_ITAG` | 12 |
| `0x2F` | `GOTO_ITAG` | 461 |
| `0x30` | `LBL_ITAG` | 229 |
| `0x39` | `ELSEIF_ITAG` | 45 |
| `0x3A` | `IF_ITAG` | 53 |
| `0x3B` | `IFTHEN_ITAG` | 332 |
| `0x3D` | `WHILE_ITAG` | 5 |
| `0x43` | `REQUEST_ITAG` | 44 |
| `0x44` | `POPUP_ITAG` | 30 |
| `0x4C` | `DROPDOWN_ITAG` | 9 |
| `0x4D` | `OUTPUT_ITAG` | 18 |
| `0x4F` | `PXLTEXT_ITAG` | 102 |
| `0x51` | `PAUSE_ITAG` | 283 |
| `0x52` | `RETURN_ITAG` | 4 |
| `0x53` | `INPUT_ITAG` | 126 |
| `0x56` | `TITLE_ITAG` | 101 |
| `0x57` | `ITEM_ITAG` | 161 |
| `0x58` | `INPUTSTR_ITAG` | 2 |
| `0x62` | `TEXT_ITAG` | 49 |
| `0x6A` | `CUBICREG_ITAG` | 1 |
| `0x6B` | `EXPREG_ITAG` | 1 |
| `0x6C` | `LINREG_ITAG` | 1 |
| `0x6D` | `LNREG_ITAG` | 1 |
| `0x6E` | `MEDMED_ITAG` | 1 |
| `0x6F` | `POWERREG_ITAG` | 1 |
| `0x70` | `QUADREG_ITAG` | 1 |
| `0x71` | `QUARTREG_ITAG` | 1 |
| `0x74` | `FOR_ITAG` | 18 |
| `0x76` | `PXLCRCL_ITAG` | 10 |
| `0x79` | `PXLLINE_ITAG` | 64 |
| `0x7A` | `DISP_ITAG` | 516 |
| `0x7B` | `FNOFF_ITAG` | 2 |
| `0x7C` | `FNON_ITAG` | 2 |
| `0x7D` | `LOCAL_ITAG` | 47 |
| `0x7E` | `DELFOLD_ITAG` | 3 |
| `0x7F` | `DELVAR_ITAG` | 81 |
| `0x81` | `PROMPT_ITAG` | 28 |
| `0x82` | `SORTA_ITAG` | 1 |
| `0x86` | `DEFINE_ITAG` | 10 |
| `0x88` | `CLRERR_ITAG` | 1 |
| `0x8A` | `DISPHOME_ITAG` | 25 |
| `0x93` | `SINREG_ITAG` | 1 |
| `0x94` | `LOGISTIC_ITAG` | 1 |

## Primary tags observed

143 of the 322 `Tags` values occur. Grouped by role.

### Structure

| Tag | Enum name | Uses |
|---|---|---|
| `0x00` | `VAR_NAME_TAG` | 1,875 |
| `0x1C` | `EXT_SYSTEM_TAG` | 3 |
| `0xD9` | `LIST_TAG` | 54 |
| `0xDA` | `USERFUNC_TAG` | 80 |
| `0xDC` | `FUNC_TAG` | 47 |
| `0xE5` | `END_TAG` | 1,887 |
| `0xE6` | `COMMENT_TAG` | 159 |
| `0xE7` | `NEXTEXPR_TAG` | 96 |
| `0xE8` | `NEWLINE_TAG` | 5,328 |
| `0xE9` | `ENDSTACK_TAG` | 47 |
| `0xF0` | `LOCALVAR_TAG` | 2,987 |

### Literals

| Tag | Enum name | Uses |
|---|---|---|
| `0x1F` | `POSINT_TAG` | 1,604 |
| `0x20` | `NEGINT_TAG` | 59 |
| `0x22` | `NEGFRAC_TAG` | 9 |
| `0x23` | `FLOAT_TAG` | 18 |
| `0x24` | `PI_TAG` | 1 |
| `0x25` | `EXP_TAG` | 5 |
| `0x27` | `NEGINFINITY_TAG` | 3 |
| `0x28` | `INFINITY_TAG` | 5 |
| `0x29` | `PN_INFINITY_TAG` | 5 |
| `0x2B` | `FALSE_TAG` | 1 |
| `0x2C` | `TRUE_TAG` | 14 |
| `0x2D` | `STR_TAG` | 1,828 |
| `0x2E` | `NOTHING_TAG` | 3 |

### Operators

| Tag | Enum name | Uses |
|---|---|---|
| `0x79` | `NOT_TAG` | 59 |
| `0x7A` | `MINUS_TAG` | 45 |
| `0x80` | `STORE_TAG` | 712 |
| `0x81` | `WITH_TAG` | 113 |
| `0x83` | `OR_TAG` | 115 |
| `0x84` | `AND_TAG` | 35 |
| `0x85` | `LT_TAG` | 23 |
| `0x86` | `LE_TAG` | 27 |
| `0x87` | `EQ_TAG` | 382 |
| `0x88` | `GE_TAG` | 44 |
| `0x89` | `GT_TAG` | 17 |
| `0x8A` | `NE_TAG` | 49 |
| `0x8B` | `ADD_TAG` | 217 |
| `0x8D` | `SUB_TAG` | 227 |
| `0x8F` | `MUL_TAG` | 346 |
| `0x91` | `DIV_TAG` | 178 |
| `0x93` | `POW_TAG` | 327 |
| `0xD5` | `SUBSCRIPT_TAG` | 69 |

### Single-letter variables

Values `0x01`..`0x1B` are the reserved one-letter variables, with use counts in parentheses.
The order is q, r, s…z, then a…p. There are two `q` slots: `0x01` is `_VAR_Q_TAG`, the reserved
`q` that AMS uses internally, and `0x1B` is the ordinary user `q`.

`0x01` q (reserved) (65) · `0x02` r (145) · `0x03` s (107) · `0x04` t (73) · `0x05` u (19) · `0x06` v (27) · `0x07` w (3) · `0x08` x (221) · `0x09` y (162) · `0x0A` z (44) · `0x0B` a (350) · `0x0C` b (247) · `0x0D` c (268) · `0x0E` d (141) · `0x0F` e (87) · `0x10` f (65) · `0x11` g (30) · `0x12` h (27) · `0x13` i (40) · `0x14` j (55) · `0x15` k (57) · `0x16` l (59) · `0x17` m (93) · `0x18` n (274) · `0x19` o (3) · `0x1A` p (352) · `0x1B` q (68)

### Functions

74 function tags occur:

`0x2F` acosh · `0x31` atanh · `0x32` asech · `0x33` acsch · `0x36` sinh · `0x38` sech · `0x3A` coth · `0x3B` acos · `0x3C` asin · `0x3D` atan · `0x40` acot · `0x41` racos · `0x42` rasin · `0x43` ratan · `0x44` cos · `0x45` sin · `0x46` tan · `0x47` sec · `0x48` csc · `0x49` cot · `0x4A` itan · `0x4B` abs · `0x4C` angle · `0x4D` ceiling · `0x50` sign · `0x51` sqrt · `0x52` expf · `0x53` ln · `0x54` log · `0x55` fpart · `0x56` ipart · `0x5A` approx · `0x5C` tcollect · `0x5E` getnum · `0x5F` error · `0x61` det · `0x62` colnorm · `0x63` rownorm · `0x64` norm · `0x65` mean · `0x66` median · `0x67` product · `0x68` stddev · `0x69` sum · `0x6B` unitv · `0x6C` dim · `0x6D` mat2list · `0x6E` newlist · `0x6F` rref · `0x70` ref · `0x71` identity · `0x72` diag · `0x73` coldim · `0x74` rowdim · `0x75` transpose · `0x76` factorial · `0x77` percent · `0x78` radians · `0x96` solve · `0x97` csolve · `0xA2` gcd · `0xA7` ncr · `0xA8` npr · `0xAD` augment · `0xAE` newmat · `0xB0` simult · `0xB2` exp2list · `0xBA` sigma_sum · `0xBE` exact · `0xC4` integrate · `0xCF` right · `0xD2` seq · `0xD3` list2mat · `0xF4` isprime

## Extended function tags observed

11 of the 91 `ExtTags` values occur. The index is the byte that precedes `E3`.

| Index | Enum name | Uses |
|---|---|---|
| `0x02` | `GETKEY_TAG` | 6 |
| `0x06` | `ORD_TAG` | 1 |
| `0x07` | `EXPR_TAG` | 52 |
| `0x09` | `STRING_TAG` | 397 |
| `0x0A` | `GETTYPE_TAG` | 1 |
| `0x0B` | `GETMODE_TAG` | 2 |
| `0x0F` | `SETGRAPH_TAG` | 4 |
| `0x11` | `SETMODE_TAG` | 71 |
| `0x12` | `FORMAT_TAG` | 3 |
| `0x14` | `APPEND_TAG` | 510 |
| `0x16` | `EXPR2DMS_TAG` | 12 |

## What is still unsolved

`tools/ti89-detok.py` recovers the statement layer completely: every instruction, label, jump,
name, string, integer and program call. It does **not** reassemble infix expressions. Operators
appear as the postfix tokens they are, so `a+b*c` comes out as its operand and operator tokens in
stack order rather than as source.

Closing that gap means walking the postfix stream with an operand stack, applying each operator
tag at its documented arity, and re-parenthesising by precedence. The arity is the missing data:
`estack.h` gives the tag values but not how many operands each consumes, and several tags are
variadic (`MEAN_TAG` and `STDDEV_TAG` have two-argument forms, `PRODLIST` and `SUMLIST` three).
Until that is done the 47 programs are auditable but not readable as source, which is the task
recorded in `docs/PROGRAMS.md`.
