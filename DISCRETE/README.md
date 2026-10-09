# DISCRETE

Notes for this folder's programs that go beyond what belongs in an in-program comment. See the
repository root `CLAUDE.md` for why: comments cost real parse time on the calculator, so they're
kept short in the `.89p` source and the detail lives here instead.

## `discrete\entinfo`, `discrete\entropy` and `discrete\sumarray`

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
- `discrete\sumarray(r)` takes one list of **raw per-sample labels** and returns a counts list:
  sorts a local copy of `r` (the caller's own list is never touched — Func parameters are
  copies) and counts each run of equal values. This is the tally step every "Automatic" mode and
  every I.G. child/parent needs before `entropy()` can run on it.

Composed together, `entropy(sumarray(rawLabels))` goes straight from raw per-sample data to H,
e.g. `discrete\entropy(discrete\sumarray({1,1,2,2,2,3,3,4}))` → 1.9056 bits. Because `sumarray`
sorts its own copy, `Lbl auto`'s parent-entropy call (`entropy(sumarray(y))`) needs no separate
copy of `y` either, unlike the hand-written tally loop it replaced, which needed an explicit
`y→yp` first precisely because `SortA` sorts in place.

**Both `discrete\entropy` and `discrete\sumarray` are `.89f` Functions (type `0x13`), not `.89p`
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

### Implementation notes

- Uses `Input`, not `Request`, for list entry: `Request`'s dialog starts in Alpha-Lock (meant for
  names), forcing Alpha off before every numeric entry on real hardware; `Input`'s entry line
  starts in normal mode, like the Home screen, so digits and `{ }` type directly. The only cost
  is typing the braces yourself.
- `Lbl quit` runs `ClrIO` then `DispHome` so quitting returns to the Home screen instead of
  leaving the calculator on the Program I/O screen.
