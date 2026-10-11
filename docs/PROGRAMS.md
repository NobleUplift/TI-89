# Program map and program state

Per-program reference for the calculator variables in this backup: what calls what, what is
reachable, and what never worked. Derived by reading the programs, not from any contemporaneous
documentation.

`CLAUDE.md` holds the rules that matter on every task, including the method this map depends on
(only a fully qualified `folder\name` is a call) and the standing rule that nothing here is a bug
to fix. Read that first; this file is for when a task touches a specific program.

For the `periodic` submodule see `PERIODIC/CLAUDE.md`. The README covers provenance, the renames
and the file format.

## Scope

**Everything below describes the 2009 calculator set.** Three programs added in 2026 are not part
of it and are not catalogued here, because none of the findings apply to them: `discrete\entinfo`
with its two helper Functions `discrete\entropy` and `discrete\tally`. They form a closed cluster
that nothing else calls and that calls nothing else, documented in `DISCRETE/README.md`, with
`.txt` sources committed beside the containers. Unlike the archived programs they may be edited
and fixed. Treat the counts here as counts of the archive, not of the repository.

## Coverage, and what it does not cover

The 52 text-stored programs of the 2009 set were read in full, so their call graph, label
structure and block structure are exact.

The 47 tokenized programs were **not** label-audited. At the time the defect list was compiled
there was no working byte-code decoder, so they were checked only for size, for the strings they
display, and for qualified calls.

**A tokenized program's absence from the defect list below is not a clean bill of health.**

That limit is now liftable: `tools/ti89-detok.py` decodes the statement structure, so the same
label and control-flow audit can be run across all 47. Doing so is outstanding work, and it is
the most likely source of further findings.

## Tokenized programs, priority to export

47 of the 102 tracked `.89p`/`.89f` programs are stored as byte-code rather than source, 74,119
bytes in total. All 47 are from the 2009 set.
The diff driver prints them as a hex dump, which means they are invisible to review: they cannot
be label-audited, searched for a formula, or diffed meaningfully. Recovering them as text is the
single biggest gap in this repository.

Being byte-code is not evidence that a program was used, only that it was run more recently than
it was edited: `main\kbdprgm3` was run constantly and is stored as text because it was edited
even more often. See `docs/TOKENIZATION.md`.

| Folder | Count | Programs, with data size in bytes |
|---|---|---|
| `algebra` | 1 | quadform (2545) |
| `biology` | 1 | hardyw (1791) |
| `chem` | 5 | radiate (8703), ultwaves (802), temp (757), enthalpy (488), accuracy (273) |
| `coordin` | 1 | ptsolver (1532) |
| `discrete` | 2 | binomial (845), fib (232) |
| `geometry` | 8 | circthms (1996), polyarea (1945), unitcirc (1455), tetra (1149), polygon (1068), pappusv (1031), poly (785), polyform (165) |
| `kadich` | 2 | kbdprgm1 (167), cssc (22) |
| `main` | 5 | mathem2 (6284), clrvs (2534), appclr (521), custom1 (373), keycode (101) |
| `miscam` | 3 | intr (703), lstdigit (350), bernouli (183) |
| `miscnz` | 10 | vect (3547), vecg (1113), prime (1033), simuln (710), sequ (699), syn (630), stat_reg (567), simul (314), summ (235), trib (208) |
| `physics` | 1 | multivec (958) |
| `trigonom` | 8 | triangle (13055), trig (3733), stewarts (3088), trithms (1785), ptdst (1441), lawofsin (1159), tritest (656), pythagor (388) |

Where to start, in order of payoff:

1. **`main\mathem2` (6284)** is the menu that defines the whole math half of the program set. Its
   call list had to be reconstructed by string-scanning; as text it would be directly readable.
2. **`trigonom\triangle` (13055)** is the largest program in the backup by a wide margin and
   nothing is known about its internals.
3. **`chem\radiate` (8703)** is the second largest, and the one program whose tag structure is
   already partly understood (below).
4. The rest of the live menu entries, largest first: `trigonom\trig`, `miscnz\vect`,
   `trigonom\stewarts`, `algebra\quadform`, `geometry\circthms`, `geometry\polyarea`.
5. `kadich\cssc` (22 bytes) and `main\keycode` (101) are trivially small and make good test cases
   for a detokenizer before it is pointed at anything large.

Lowest priority, since nothing reaches them: `discrete\fib`, `trigonom\pythagor`,
`coordin\ptsolver` and `main\custom1`.

### How to read the byte-code

`tools/ti89-detok.py` decodes it:

```
python3 tools/ti89-detok.py CHEM/chem.radiate.89p
```

**`docs/TOKENIZATION.md` is the format reference**: the container offsets, the reverse-postfix
reading order, every token form, the complete tag tables as used by this backup, the sourced
references, and the `_ITAG`/`_TAG` trap that breaks naive readings. Read it before writing
anything that parses a tokenized program.

The short version: the body at 0x58 is one postfix expression stack that reads from its last byte
backwards, instructions are `<idx> E4` indexing the `_ITAG` half of `enum InstructionTags`, and
`0x30` is `Lbl` while `0x2F` is `Goto`.

What the tool does not do is reassemble infix expressions. Operators appear as postfix tokens
rather than as `a+b*c`, which is enough to audit control flow or locate a formula but is not a
round-trip decompiler. Reconstructing source is the remaining work.

## Entry points

Two keyboard programs. On the TI-89, diamond plus a digit runs `kbdprgm<digit>`, so
`main\kbdprgm3` and `kadich\kbdprgm1` are reachable from the keyboard and nothing calls them
except their own children returning home.

### `main\kbdprgm3`, the science menu (21 callees, all resolving)

```
main\kbdprgm3
├── main\mathem2        (the math menu, below)
├── main\clrvs          (cleanup manifest)
├── main\appclr         (cleanup manifest)
├── periodic\periodic   (submodule)
├── biology\hardyw      ──┐ returns via main\kbdprgm3()
├── chem\radiate        ──┘
├── chem\accuracy, density, enthalpy, fracabun, halflife, precise, prog1, temp, ultwaves
└── physics\multivec, vector, vectora, vectors, veloc, velocity
```

`chem` and `physics` hang off this menu only. `main\mathem2` never reaches them.

### `main\mathem2`, the math menu (66 callees, 9 of them already broken)

Tokenized, so read it with the hex dump plus a string scan. Its credits screen names the earlier
programmers; the README reproduces what is quotable.

```
main\mathem2
├── algebra\conic, quadform
├── calculus\info
├── coordin\abls, linedst, ptdst3, ptplane, reflect, rotator, wronskia
├── discrete\baseconv, binary, binomial, hexadeci, octal, pascalst
├── geometry\circ, circent, circthms, clockdeg, degminse, frustum, geometry,
│            pappusv, poly, polyarea, polyform, polygon, sector, tetra,
│            trapzoid, unitcirc, volume
├── main\twoman, clrvs, kbdprgm3
├── miscam\av_spe, bernouli, book, intr, lstdigit
├── miscnz\path, prime, proba, sequ, simul, simuln, stat_reg, summ, syn,
│           trib, vecg, vect
├── trigonom\apothem, centroid, concur, lawofsin, ptdst, pythag, stewarts,
│             triangle, trig, tritest, trithms, ulttri
└── BROKEN: miscam\fib, miscam\inqsolve, miscnz\weekdays (moved before the 2009 export)
           math\sss, math\sas, math\simu, math\tran, math\hype, math\inter (never exported)
```

Six callees return to the menu with `main\mathem2()`: `algebra\quadform`, `discrete\binary`,
`geometry\frustum`, `geometry\geometry`, `geometry\tetra` and `trigonom\apothem`. Those are the
whole of the mutual recursion in the non-periodic set; every other callee is a leaf.

## Broken calls

Already broken when the backup was taken. The README covers the nine `main\mathem2` entries; the
rest are:

| Caller | Calls | Why it fails |
|---|---|---|
| `geometry\volume` | `math\mathem2()` | the menu lives in `main`, and `math` holds only NoteFolio documents |
| `trigonom\ulttri` | `math\ultdel()` | no such variable in the backup |
| `main\mtprogsd` | `algebra\fact()`, `algebra\factors()` | present in the backup as `history\fact` and `history\factors` |
| `main\clrvs` | `chem\periodic`, `algebra\fact` | stale names |

## Independent clusters

```
kadich\kbdprgm1 ──> kadich\cssc                     (the only other keyboard entry point)

heart\heartp    ──> heart\heart1..heart5, broken2, broken3, smiley, smiley2, smiley3
                    (RclPic; heart\maybe is never recalled)

periodic\table  <─> periodic\mkdata                 (draft replacement, see PERIODIC/CLAUDE.md)
```

None of these connects to either menu.

## `periodic` (submodule)

A dense 112-program cluster. `periodic\periodic` dispatches to `periodic\atomnum` and all 110
element programs; each element calls `periodic\periodic` to go home plus five to seven neighbours
for next/previous by atomic number, by name and by symbol. Changing one element means updating its
neighbours in three orders plus the two dispatch tables. `PERIODIC/CLAUDE.md` has the detail.

## Manifests, which look like callers but are not

Three programs name dozens of variables without calling them. Exclude them from any dependency
graph or almost everything looks reachable.

- `main\mtprogsd` is a calculator-to-calculator transfer list: 90 `Send` lines, grouped by folder
  under `©` comments. All but one are `Send <folder>\<name>()`; `Send main\default` has no parens
  because it is a graph database, not a program.
- `main\clrvs` is a `DelVar` list: every program name in the set, each followed by that program's
  local variable names. Its folder prefixes are inconsistently capitalized (`Chem\temp`,
  `Main\twoman`), so match case-insensitively.
- `main\appclr` is a `DelVar` list for Flash application variables (`finance\*`, `list1`..`list6`,
  `zzconfig`, the Table and Polynomial Root Finder variables).

Both lists still use pre-2008 names, so being named by one is not evidence a program was
reachable. They are the only inbound reference for `algebra\system`, `coordin\ptsolver`,
`main\custom1`, `main\keycode` and `main\default`.

## Completely isolated

No inbound reference anywhere, no outbound call. Nine programs:

| Variable | Note |
|---|---|
| `chem\period1c` | the periodic table before `periodic\periodic` replaced it |
| `discrete\fib` | the menu still calls the pre-move name `miscam\fib` |
| `discrete\finidiff` | unfinished, see [Empty](#empty) |
| `history\fact` | `main\mtprogsd` calls it `algebra\fact` |
| `history\factors` | `.89z` assembly, the only one in the backup |
| `history\weekdays` | the menu still calls the pre-move name `miscnz\weekdays` |
| `kadich\kbdprgm6` | mostly unimplemented, see [Advertised but unreachable](#advertised-but-unreachable-or-unimplemented) |
| `miscam\inqslve2` | the menu still calls its predecessor `miscam\inqsolve` |
| `trigonom\pythagor` | the 1998 ticalc.org download; `trigonom\pythag` is the team's own |

Also isolated, non-program: `heart\maybe` (picture), `main\zero` (graph database), and every
`.89y` Flash application document (NoteFolio, StudyCards).

## Incomplete or non-functional programs

None of this is a defect list to work through. It exists so that time is not wasted debugging a
program that never worked, and so a broken program is not cited as a working example.

### Empty

| Program | State |
|---|---|
| `discrete\hexadeci` | `Prgm` and `EndPrgm` with nothing in between. On the `main\mathem2` menu as "Hexadecimal" |
| `discrete\octal` | identical: empty body, live menu entry |
| `discrete\finidiff` | one `DelVar`, one `Input "Highest power on RHS..."`, then exits without computing anything |

### Produces a wrong answer

| Program | Defect |
|---|---|
| `miscam\av_spe` | computes `x*y/(2*x+2*y)`. Average speed over equal distances is `2xy/(x+y)`, so every result is a quarter of the right one |
| `trigonom\concur` | solves `(x1+x2+x3)/2=x` for the centroid, dividing by 2 where it must divide by 3 |
| `kadich\kbdprgm6` | the SSS branch computes `cos´(c^2-a^2-b^2)/(−2*a*b)`, taking the arc cosine before the division instead of after. The argument is a squared length, so it is outside the domain for essentially every triangle. The law-of-sines steps that follow divide by the angle rather than by a side |

### Calls a helper that does not exist

| Program | Missing |
|---|---|
| `trigonom\concur` | `slo()` and `ptline()`. Neither is an AMS built-in and neither appears anywhere in the backup, so the program dies at the orthocenter step, after printing the circumcenter |
| `main\custom1` | its custom menu pastes `ptleg(`, `pthyp(`, `slope(`, `logsolve(`, `logbase(`, `logarg(`, `arithseq(`, `geoseq(`, `deg2rad(` and `rad2deg(`, none of which exist here or in AMS. Only the `csc`/`sec`/`cot` entries and their inverses resolve to real functions |

### Advertised but unreachable or unimplemented

| Program | Detail |
|---|---|
| `kadich\kbdprgm6` | the menu offers SSS, SAS, ASA, AAS and ASS. `Lbl sas`, `Lbl asa`, `Lbl aas` and `Lbl ass` are each nothing but `Goto start`, so four of the five do nothing. It also declares `Local` inside a `For` loop and again inside a label block |
| `discrete\binary` | the Toolbar offers six conversions. `Lbl otb` and `Lbl htb` (Octal-Binary, Hexa.-Binary) are bare `Goto start`. `Lbl bto` ("Binary-Octal") is a copy of the binary-to-decimal path and still prints its `u=`, `v=`, `s=` and `t=` debug values through `Disp` and `Pause` |
| `trigonom\apothem` | `Lbl poly`, a complete regular-polygon section of about forty lines, has nothing jumping to it. The Toolbar only reaches the equilateral-triangle branch |

### Errors at runtime

| Program | Detail |
|---|---|
| `miscnz\path` | `DelVar k,l,m` is immediately followed by `2→l[1]`, storing into an index of the list it just deleted. `l` and the loop counter `b` are also missing from `Local`, so they leak into the global namespace. Both input prompts read "Dim 1" |
| `coordin\reflect` | divides by the slope `m` with no guard, so a horizontal line raises a division error. It also does not reflect anything: it returns `m*x1+b` and `(y1-b)/m`, which is a point on the line, not the mirror of the input point |

### Dead labels, harmless

A `Lbl` that nothing jumps to. In every case below the program simply runs once and exits where
the author seems to have meant it to loop, so the effect is a missing "do another" rather than a
failure: `coordin\reflect`, `geometry\circent`, `trigonom\centroid`, `miscnz\path` and
`trigonom\concur` all open with `Lbl a`; `algebra\system` has `info`, `physics\vector` has `esub`,
`physics\veloc` has `end`, `miscam\inqslve2` has `aineq` and `main`, and `main\kbdprgm3` has
`outsalt`.

`chem\halflife`'s `Lbl da` looks like one of these and is not. Nothing jumps to it, but execution
falls into it from the branch above, so its `Pause xv` is what displays the result.
