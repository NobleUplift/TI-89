# DISCRETE

Notes for this folder's programs that go beyond what belongs in an in-program comment. In-program
comments here stay short, succinct blurbs rather than full explanations, so the `.txt` source
reads easily without becoming its own essay; the detail lives here instead. (`©` comments never
reach the calculator at all — see "Indentation and comments are for `.txt` readability only"
below — but the root `CLAUDE.md` rule to keep comments short predates that fix and still shapes
how these are written.)

## `discrete\entinfo`, `discrete\entropy` and `discrete\tally`

`discrete\entinfo` is a UI harness over Shannon entropy and information-gain: `H(S) = -Σ
p·log2(p)`. It contains no entropy or tallying math itself — two Functions do that, and every
path in `entinfo` (F1 Manual, F1 Automatic, F2 Manual's per-child and parent, F2 Automatic's
per-child and parent) composes them instead of duplicating either computation inline:

- `discrete\entropy(c)` takes one list of **counts** (not raw labels) and returns `{h, n}`:
  entropy in bits and the total count, which is exactly the pair I.G.'s weighting
  (`Σ (n(child)/N)·H(child)`) needs from each child without recomputing anything. Also used to
  compute F1's "Max (uniform)" display, via `entropy(newList(dim(p))+1)` — a uniform list of
  `dim(p)` ones — since Shannon entropy of a uniform distribution over k classes is exactly
  `log2(k)`; this also means the `dim(p)=1` case needs no special-casing, since `entropy()` on a
  length-1 uniform list already returns 0 on its own.
- `discrete\tally(r)` takes one list of **raw per-sample labels** and returns a counts list: for
  each element of `r`, it linearly searches a running list of distinct values seen so far,
  bumping that value's count if found or adding it fresh otherwise. No sorting involved — see
  below for why. This is the tally step every "Automatic" mode and every I.G. child/parent needs
  before `entropy()` can run on it.

Composed together, `entropy(tally(rawLabels))` goes straight from raw per-sample data to H, e.g.
`discrete\entropy(discrete\tally({1,1,2,2,2,3,3,4}))` → 1.9056 bits. `tally` only ever reads
`r`, never mutates it, so `Lbl auto`'s parent-entropy call (`entropy(tally(y))`) needs no
separate copy of `y` either, unlike the hand-written tally loop it replaced, which needed an
explicit `y→yp` first precisely because `SortA` sorts in place.

**`SortA` cannot be used inside a Function.** `tally`'s first implementation sorted its input
(same approach as the hand-written loops it replaced) and failed on real hardware with "SortA
is invalid in a function or current expression." `SortA` is a command with an in-place side
effect, not an expression function, and a `Func` body is restricted to expression-style
operations (`Return`, assignments, `For`/`If`, and non-mutating functions like `augment()`) —
nothing that mutates a variable as a statement in its own right. The fix was the
linear-search-and-accumulate algorithm above, which never needs to sort anything. Recorded in
the repository root `README.md`'s TI-BASIC notes too, since it isn't specific to this program.

**The name `tally` is reused two ways in `entinfo` itself**: `Lbl tally` (F1's Automatic entry
point, jumped to by a `Toolbar` `Item`) and the `discrete\tally` Function are different things
sharing one word, including inside `Lbl tally` itself, where the line is
`tally(r)→p` — a function call, from within the identically-named label. This works correctly
(labels are only ever resolved after `Goto`/`Item`/`Title`; `tally(x)` with parentheses in an
expression always resolves to the Function; they're different namespaces), but it reads
ambiguously at a glance, so it's called out here rather than left for a future reader to puzzle
over.

**Both `discrete\entropy` and `discrete\tally` are `.89f` Functions (type `0x13`), not `.89p`
Programs**, since only a Function can be called inside an expression and hand back a value — a
Program called as `name()` is always a void statement. `discrete\entropy` was the first `.89f`
file in this repository, so `tools/ti89-pack.py` was extended to support packing one (previously
`.89p`-only, type `0x12` hard-coded). **The exact tail bytes a text-stored Function needs have
not been confirmed**: every file this format was reverse-engineered against is a Program, and
this repo had no `.89f` sample to check against before these two. `tools/ti89-textconv.py`'s own
comment says a Program and a Function's text-stored body ends in the same
`... E5 00 01 <flag> <tag>` suffix, which is some evidence the tail is shared — but the 2 bytes
before that suffix are documented elsewhere as specifically "the `Prgm` command," and whether
`Func` needs a different 2 bytes there is unconfirmed. `ti89-pack.py` currently assumes the tail
is identical for both. **If either `.89f` fails to transfer or won't run after sending it to a
calculator, this assumption is the first thing to revisit** — the fallback is typing that file's
`.txt` source into the calculator's own Program Editor (choose New > Function there) instead of
sending the packed file, since the calculator's own editor tokenizes correctly regardless of
this repo's guess.

### Toolbar (`discrete\entinfo`)

Every top-level `Title` opens an `Item` dropdown; none act directly. This matches
`main\kbdprgm3`'s own "Mathematics" `Title`, which nests a single `Item` ("Main Program")
specifically because a direct-jump `Title` once confused users who expected F1 to open a
dropdown — documented in that program's own Info screen as a lesson learned.

- **F1 Entropy**
  - *Manual*: type counts or probabilities as a list, in braces, e.g. `{16,14}` or
    `{.25,.25,.5}`. For learning the arithmetic once you've counted by hand.
  - *Automatic*: type one raw label per sample as a list, in braces, e.g. `{1,1,1,2,2}`, or a
    Data variable column (e.g. `mydata[1]`) in place of a literal list — `Input` evaluates
    whatever is typed. Tallies occurrences of each distinct value itself before computing H.
- **F2 I.G.** (information gain), for a split into several children:
  - *Manual*: asks how many children, then each child's raw labels (literal list or `db[col]`,
    same as F1's Automatic). You decide which rows belong to which child; the parent is never
    entered separately, since pooling all children's labels reconstructs it exactly. For
    learning how a split's gain is actually assembled.
  - *Automatic*: asks for a whole attribute column and a whole class-label column (e.g.
    `mydata[1]`, `mydata[2]`); groups rows into children by matching attribute value itself
    (`SortA` on both together keeps each row's class label attached to its attribute value), so
    no manual grouping at all. Works on two Data columns, not the combined Matrix built earlier
    for viewing the whole table: `db[col]` column access is a confirmed-working primitive here,
    while extracting a column back out of a genuine Matrix type is not.
- **F3 About**: *About* (credits) / *Quit*.

### Indentation and comments are for `.txt` readability only, never shipped to the calculator

The `.txt` sources in this folder indent nested blocks one space per level (`For`/`EndFor`,
`If...Then`/`EndIf`, `Toolbar`/`EndTBar`, `Dialog`/`EndDlog` at the same column, contents one
space deeper) and carry `©` comments (a one-line purpose blurb for every `Local` variable, plus
a few lines explaining non-obvious steps) purely so a human reviewing the source can follow it.
**`tools/ti89-pack.py` strips every line's leading spaces, and drops every whole-line `©`
comment, before encoding**, so the `.89p`/`.89f` files sent to a calculator are never larger for
either.

This matters because the costs are not the same size for a human reader and for the device.
Parse time is negligible — a space or a comment line is skipped once, at tokenization, not
re-paid per loop iteration — but storage is a real, measured cost, and comments are the bigger
of the two: stripping leading spaces alone saved 48 bytes on `discrete.entinfo.89p`, 3 on
`discrete.entropy.89f`, 19 on `discrete.tally.89f`; stripping the `©` comment lines on top of
that saved a further 1178, 118, and 151 bytes respectively (down to 1983, 218, and 310 bytes).
RAM/Flash on the calculator is one finite pool shared across *every* program on it — the same
reason `CLAUDE.md` says to keep in-program comments short — but stripping on pack means the
`.txt` source doesn't have to choose between that limit and being readable.

**Write one long comment line, not several short `©` lines pre-wrapped to fit.** A long line
wraps for display on its own once it passes roughly 25 characters, the same whether it's one
logical comment or several `©`-prefixed ones hand-broken to that width — so hand-wrapping buys
nothing visually and costs more lines for the same words. For example, don't write:

```
© parent entropy from the whole class column; tally(y)
© only reads y, so it stays row-aligned with r for the
© grouping pass below
```

when one line reads exactly the same once wrapped, and is one `©` and one line instead of three:

```
© parent entropy from the whole class column; tally(y) only reads y, so it stays row-aligned with r for the grouping pass below
```

### Implementation notes

- Uses `Input`, not `Request`, for list entry: `Request`'s dialog starts in Alpha-Lock (meant for
  names), forcing Alpha off before every numeric entry on real hardware; `Input`'s entry line
  starts in normal mode, like the Home screen, so digits and `{ }` type directly. The only cost
  is typing the braces yourself.
- `Lbl quit` runs `ClrIO` then `DispHome` so quitting returns to the Home screen instead of
  leaving the calculator on the Program I/O screen.
