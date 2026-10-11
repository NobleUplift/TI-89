# DISCRETE

What this folder's programs do and how to run them. Rules for writing TI-BASIC, screen limits and
packing behaviour are repository-wide and live in `docs/TI-BASIC.md`.

## `discrete\entinfo`, `discrete\entropy` and `discrete\tally`

`discrete\entinfo` is a menu-driven front end for Shannon entropy and decision-tree information
gain: `H(S) = -Σ p·log2(p)`. It contains no entropy or tallying arithmetic of its own. Two
Functions do that work, and every path through `entinfo` composes them rather than duplicating
either calculation inline:

- **`discrete\entropy(c)`** takes one list of **counts** (not raw labels) and returns `{h, n}`:
  the entropy in bits and the total count. That pair is exactly what information gain's weighting,
  `Σ (n(child)/N)·H(child)`, needs from each child without recomputing anything. It also produces
  the "Max (uniform)" figure, via `discrete\entropy(newList(dim(p))+1)` over a uniform list of
  `dim(p)` ones, since the entropy of a uniform distribution over k classes is exactly `log2(k)`.
  That also means a single-class input needs no special case: a length-1 uniform list already
  returns 0.
- **`discrete\tally(r)`** takes one list of **raw per-sample labels** and returns a counts list.
  For each element it linearly searches the distinct values seen so far, incrementing that value's
  count or appending it fresh. It never sorts, and never modifies its input. This is the step
  every Automatic mode and every information-gain subset needs before `discrete\entropy()` can run.

Composed, `discrete\entropy(discrete\tally(rawLabels))` goes straight from raw per-sample data to
entropy in bits:

```
discrete\entropy(discrete\tally({1,1,2,2,2,3,3,4}))   → 1.9056 bits
```

Both helpers are Functions (`.89f`) rather than Programs, because only a Function can be called
inside an expression and return a value.

## Running `discrete\entinfo`

Every top-level `Title` opens an `Item` dropdown; none act directly. This matches
`main\kbdprgm3`'s own "Mathematics" `Title`, which nests a single "Main Program" `Item`
specifically because a direct-jump `Title` confused users who expected F1 to open a dropdown,
a lesson recorded in that program's own Info screen.

In both the Entropy and the I.G. menus, the first item is the by-hand version of the calculation,
for working through the arithmetic yourself, and the second automates the same step.

- **F1 Entropy**
  - *Manual*: type counts or probabilities as a list in braces, for example `{16,14}` or
    `{.25,.25,.5}`. For learning the arithmetic once you have counted by hand.
  - *Automatic*: type one raw label per sample as a list, for example `{1,1,1,2,2}`, or give a
    Data variable column such as `mydata[1]` in place of a literal list, since `Input` evaluates
    whatever is typed. It tallies the distinct values itself before computing entropy.
- **F2 I.G.** (information gain), for a split into several children
  - *Manual*: asks how many children, then each child's raw labels, as a literal list or a
    `db[col]` column. You decide which rows belong to which child. The parent is never entered
    separately, because pooling every child's labels reconstructs it exactly. For learning how a
    split's gain is assembled.
  - *Automatic*: asks for a whole attribute column and a whole class-label column, for example
    `mydata[1]` and `mydata[2]`, then groups rows into children by matching attribute value
    itself, with no manual partitioning. It sorts both columns together so each row's class label
    stays attached to its attribute value. Give it two Data columns rather than a Matrix.
- **F3 About**: *About* for credits, and *Quit*.

Quitting returns to the Home screen rather than leaving the calculator on the Program I/O screen.
`entinfo` also forces Approximate mode while it runs and restores the previous setting on exit,
because accumulating logarithms in Exact mode returns a wrong answer.

Every prompt that feeds a list to `discrete\entropy` or `discrete\tally` checks the type first
and shows a one-line error with a corrected example, so typing `16` where `{16}` was wanted is
reported at the prompt instead of surfacing as a failure inside one of the Functions.

## Possible future improvements

- **Prompt for more than one attribute in Information Gain.** Automatic currently asks for one
  attribute column and reports its gain. It could ask for the class column once and then loop over
  further attribute columns, printing each one's gain, so a session can compare every candidate
  attribute without restarting. Each attribute needs a fresh copy of the class column before its
  sort, since sorting permutes that column in place to match whichever attribute it was paired
  with.
- **Let a Data variable be named once and referenced by column index**, instead of typing the full
  `db[1]` or `db[2]` expression at every prompt, which would save re-entering the variable name
  for every column of the same table.
