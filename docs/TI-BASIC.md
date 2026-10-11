# Writing TI-BASIC for this calculator

Rules and hardware limits for writing 68k TI-BASIC, gathered as they were discovered so they do
not have to be rediscovered. Most were confirmed on a real TI-89 Titanium; where a claim rests on
something weaker, it says so.

These apply to **new** work. The 2009 export is an archive and is not to be corrected to match
anything here; see `CLAUDE.md`.

`docs/TOKENIZATION.md` is the companion for the other direction, reading a compiled program.

## Calls and name resolution

**Fully qualify every cross-folder call: `discrete\entropy(...)`, never bare `entropy(...)`.**
The TI-89 resolves an unqualified name against the *currently active* folder, not against the
folder the calling program lives in. So a bare call works only while its own folder happens to be
current, which is a condition no program can rely on.

It fails in two different ways, and neither is an obvious error:

- **A bare call in a plain expression stays symbolic.** The CAS does not raise on the undefined
  name; it keeps the call unevaluated and carries that expression onward, so `round()` and
  `string()` eventually display the literal expression text. You get
  `Parent H = round(entropy(...),4) bits` on screen instead of a number. Confirmed on hardware.
- **A bare call nested inside another call becomes a "Domain error".** With
  `discrete\entropy(tally(child))`, the symbolic `tally(child)` is passed straight into
  `entropy`'s own `sum(c)→n`, and `sum()` of a symbolic non-list is where the error actually
  fires. Confirmed on hardware.

So **a "Domain error" from inside a Function does not only mean a malformed or empty list reached
it.** It can equally mean a name in the expression that produced its argument was not qualified.
Check every `folder\` prefix in the call before anything else.

**Labels and functions are separate namespaces**, so one word can be both. A `Lbl tally` and a
`discrete\tally` Function coexist, including a `tally(r)→p` call inside `Lbl tally` itself: a
label is only ever resolved by `Goto`, `Item` or `Title`, while a name followed by parentheses in
an expression always resolves to the function. It works, but it reads ambiguously, so prefer not
to introduce the collision in new code.

## Programs and Functions

**Anything that returns a value must be a Function (`.89f`, type `0x13`), not a Program
(`.89p`, type `0x12`).** A Program invoked as `name()` is always a void statement; only a Function
can be called inside an expression and hand back a value.

A `Func` body is restricted to expression-style operations: `Return`, assignments, `For`, `If`,
`While`, and non-mutating functions such as `augment()`. Nothing that mutates a variable as a
statement in its own right is allowed. In particular:

**`SortA` and `SortD` cannot be used inside a Function, or in any expression.** On hardware this
fails with `"SortA is invalid in a function or current expression"`. They are commands with an
in-place side effect, not expression functions. To tally or order values inside a Function, use
linear search and accumulate instead (`DISCRETE/discrete.tally.txt` is a worked example), or move
the sort into a calling Program.

Sorting in place has a second consequence even where it is legal: `SortA` permutes its operands,
so anything that must stay usable afterwards needs copying first. `SortA attr,class` keeps two
lists row-aligned with each other, which is the point of the two-argument form, but it destroys
the original order of both.

**Caveat on packing a Function.** `tools/ti89-pack.py` assumes a text-stored Function ends in the
same tail bytes as a Program. That is unverified: every file the container format was
reverse-engineered against is a Program, and the two bytes before the shared
`... E5 00 01 <flag> <tag>` suffix are documented elsewhere as specifically the `Prgm` command.
If a packed `.89f` fails to transfer or will not run, this assumption is the first thing to
revisit; the fallback is typing the `.txt` into the calculator's own Program Editor with
New > Function, which tokenizes correctly regardless.

## Comments and layout in `.txt` sources

**Keep in-program comments short.** One brief line per `Local` variable, and a line for a step
whose purpose is not obvious. Anything longer than that belongs in the folder's `README.md`, not
in the program.

**Indentation and whole-line `©` comments never reach the calculator when a program is built with
`tools/ti89-pack.py`.** The packer strips every line's leading whitespace and drops every
whole-line comment before encoding. So a `.txt` source can be indented one space per nesting level
and commented for a human reader without costing anything on the device.

This is a property of the packer, not of the calculator. A comment typed into the calculator's own
Program Editor is stored and survives compilation: the byte-code census in `docs/TOKENIZATION.md`
counts 159 `COMMENT_TAG` tokens across 8 of the 47 compiled programs in this repository. The rule
above is "comments are free *if packed*", not "the device cannot hold them".

What makes the stripping worth having is that storage, not parse time, is the real cost. A space
or a comment line is skipped once at tokenization, never re-paid per loop iteration. But RAM and
Flash are a single finite pool shared across every program on the calculator, and comments
dominate: on the `discrete` sources, dropping `©` lines saved an order of magnitude more than
dropping indentation did. Exact figures are deliberately not recorded here, because they change
with every edit to the programs.

**Write one long comment line rather than several short `©` lines hand-wrapped to fit.** A long
line wraps on its own for display, so pre-breaking it buys nothing visually and costs extra lines
for the same words. Prefer:

```
© parent entropy from the whole class column; tally(y) only reads y, so it stays row-aligned with r for the grouping pass below
```

over the same text split across three `©` lines. This does not apply to the one-line blurbs above
`Local`, which are already independent short items, one per variable. Keep those on separate
lines; only consolidate a single thought that was broken across lines it did not need.

## Screen limits

- **26.5 characters fit on a `Disp` line.** The 27th character is cut off at the end of the line
  but still partly visible, so 26 is the last fully readable column on the 160-pixel screen.
- **The Program I/O screen holds 6 lines before it scrolls**, confirmed on hardware. Any group of
  `Disp` calls meant to be read together must total 6 lines or fewer between one `ClrIO` and the
  next, or the top scrolls away before the user can read it.

Related screen-management habits that follow from that limit:

- `ClrIO` immediately before printing a screen that replaces a previous one of possibly different
  length. That is a functional clear.
- Do not `ClrIO` at the top of a menu loop; it just reprints the same static header every time a
  command returns.
- Print an error in place, without clearing, directly below the prompt that produced it, so the
  context of what was being entered stays visible. Let the next successful result clear it.

## Input and modes

**Use `Input`, not `Request`, for anything numeric.** `Request`'s dialog opens in Alpha-Lock,
which is meant for names, so every numeric entry needs Alpha switched off first on real hardware.
`Input`'s entry line starts in normal mode like the Home screen, so digits and braces type
directly. The cost is typing the braces yourself.

**Validate before handing a value to a Function.** Check `getType(...)≠"LIST"` and print a short
one-line error with a corrected example, rather than letting the failure surface from inside the
Function on an unrelated line number. A bare `16` typed where `{16}` was wanted otherwise appears
as a "Data type" error attributed to the callee. Keep such messages to a single `Disp`: unlike
comments, error strings are shipped to the device and are a real storage cost.

**Force Approximate mode for any run that accumulates logarithms, and restore it on exit.** Save
`getMode("Exact/Approx")`, call `setMode("Exact/Approx","Approximate")`, and restore the saved
value when quitting. In Exact mode, `ln()` of a rational can stay symbolic rather than becoming a
decimal, and a loop that accumulates several `ln()` calls before anything forces evaluation will
carry a mis-simplified symbolic expression through: on hardware this produced the same wrong
value, `log2(3)`, regardless of input.

**The mode string is case-sensitive on this AMS build.** `"Approximate"`, capitalised exactly like
that, works. `"APPROXIMATE"` and `"APPROX"` both failed with a Domain error on the same device,
despite case-insensitivity being documented elsewhere for `setMode`.

## Data variables and matrices

- **Every column of a Data variable into one Matrix:** `{d[1],d[2],d[3],d[4]}`, indexing the Data
  variable per column inside braces, evaluates directly to a Matrix with one row per column.
  Confirmed on hardware. `list→mat(list,matrix)` takes only one list at a time, so the brace form
  is the one-shot way to get every column at once.
- **`db[col]` column access on a Data variable is a working primitive; extracting a column back
  out of a genuine Matrix is not.** Code that wants a column should read it from the Data variable
  rather than from a Matrix assembled for display.
