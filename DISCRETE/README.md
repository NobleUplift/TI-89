# DISCRETE

Notes for this folder's programs that go beyond what belongs in an in-program comment. See the
repository root `CLAUDE.md` for why: comments cost real parse time on the calculator, so they're
kept short in the `.89p` source and the detail lives here instead.

## `discrete\entropy`

Shannon entropy and information-gain calculator: `H(S) = -Σ p·log2(p)`.

### Toolbar

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
