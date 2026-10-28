# WEKA

WEKA-style classifier evaluation for the TI-89. Give it the true and false positives and
negatives of a two-class test, or a whole N×N confusion matrix, and it reports the statistics
[WEKA](https://ml.cms.waikato.ac.nz/weka/) prints after evaluating a classifier: accuracy,
precision, recall, specificity, F1, MCC, kappa, the error rates, and the "Weighted Avg." row.

It is not a port of WEKA. It reproduces only WEKA's evaluation statistics. It loads no ARFF
files, trains no classifiers and does no cross-validation. Everything here is written from the
standard published formulas; none of WEKA's code was translated. WEKA's own source was read only
to match how it treats a ratio whose denominator is zero.

*Not affiliated with or endorsed by the WEKA project or the University of Waikato.*

Rules for writing TI-BASIC, screen limits and packing behaviour are repository-wide and live in
`docs/TI-BASIC.md`.

## Installing

Send all six variables to a folder named exactly **`weka`**. Every call between them is written
fully qualified, `weka\stat(...)`, as `docs/TI-BASIC.md` requires. So the menu and `weka\avg`
fail if the folder has any other name. Run the menu as `weka\weka()`.

## The counts convention

A confusion matrix has one row per **actual** class and one column per **predicted** class,
the same layout WEKA prints under "Confusion Matrix". For two classes, with the positive class
first, that is

```
[[tp,fn]
 [fp,tn]]
```

Read row by row, it is the **counts list `{tp,fn,fp,tn}`**, the one input every per-class
Function takes. Note the order: it is not the order TP, TN, FP, FN. For an N×N matrix,
`weka\cnt(m,i)` produces that list for class i, counting class i as positive and every other
class as negative ("one-vs-rest").

## The Functions

`weka\weka` is a menu and contains no arithmetic. Five Functions do the work, and power users can
call each one from the Home screen. They compose the way `discrete\entropy(discrete\tally(x))`
does, and each value is returned by exactly one of them:

| Function | Takes | Returns |
|---|---|---|
| `weka\cnt(m,i)` | matrix, class index | `{tp, fn, fp, tn}` for class i |
| `weka\stat(c)` | counts | `{acc, prec, rec, spec}` |
| `weka\rate(s)` | `weka\stat`'s return | `{fpr, fnr, bal, err}` |
| `weka\scr(c)` | counts | `{f1, mcc, npv, kappa}` |
| `weka\avg(m)` | matrix | `{wprec, wrec, wfpr, wf1, wmcc}` |

`stat` and `rate` are the figures an introductory statistics course uses. `scr` is the
advanced set. They are kept apart so the basic figures do not need the advanced ones. `rate`
derives everything from `stat`'s four values. `scr` needs the counts themselves, because NPV,
MCC and kappa cannot be recovered from the four ratios.

```
weka\stat({50,3,4,43})                    {0.93 0.9259 0.9434 0.9149}
weka\rate(weka\stat({50,3,4,43}))         {0.0851 0.0566 0.9291 0.07}
weka\scr({50,3,4,43})                     {0.9346 0.8595 0.9348 0.8593}
weka\stat(weka\cnt(m,2))                  class 2 of a matrix m
weka\avg([[50,3,2][4,40,6][1,5,39]])      {0.86 0.86 0.0688 0.8598 0.7909}
```

Each Function wraps its result in `approx()`, so it returns decimals even in Exact mode, which
would otherwise leave fractions and MCC's square root. The Functions do not validate their
input: a malformed argument raises the calculator's own error. The menu checks everything it
passes to them.

`weka\cnt` is only a few lines and could be inlined. It is a Function because `weka\avg` needs
the same step for every class, and a Function cannot reach code inside a Program.

## What each value means

For class i, one-vs-rest. In the two-class case class 1 is the positive class.

- **tp**, true positives: actually class i and predicted class i.
- **fn**, false negatives: actually class i, predicted something else.
- **fp**, false positives: predicted class i, actually something else.
- **tn**, true negatives: neither actually nor predicted class i.
- **N** = tp+fn+fp+tn, every instance.

`weka\stat`:
- **acc**, accuracy: the share of all predictions that are right. (tp+tn)/N.
- **prec**, precision or positive predictive value: of everything predicted positive, the share
  that is. tp/(tp+fp).
- **rec**, recall, sensitivity or TP rate: of everything actually positive, the share found.
  tp/(tp+fn).
- **spec**, specificity or TN rate: of everything actually negative, the share correctly left
  out. tn/(tn+fp).

`weka\rate`:
- **fpr**, false positive rate: actual negatives wrongly flagged. fp/(fp+tn) = 1−spec.
- **fnr**, false negative rate or miss rate: actual positives missed. fn/(fn+tp) = 1−rec.
- **bal**, balanced accuracy: (rec+spec)/2. Unlike accuracy, it is not inflated when one class
  dominates.
- **err**, error rate: (fp+fn)/N = 1−acc. This is WEKA's "Incorrectly Classified Instances" as
  a fraction.

`weka\scr`:
- **f1**, F1 score, WEKA's "F-Measure": the harmonic mean of precision and recall,
  2·prec·rec/(prec+rec). It ignores tn.
- **mcc**, Matthews correlation coefficient: the correlation between actual and predicted, from
  −1 (always wrong) through 0 (chance) to +1 (perfect).
  (tp·tn − fp·fn) / √((tp+fp)(tp+fn)(tn+fp)(tn+fn)).
- **npv**, negative predictive value: of everything predicted negative, the share that is.
  tn/(tn+fn). It is the mirror of precision.
- **kappa**, Cohen's kappa, WEKA's "Kappa statistic": agreement beyond chance, where 1 is
  perfect and 0 is chance. (po−pe)/(1−pe), with po = acc and
  pe = ((tp+fn)(tp+fp) + (fp+tn)(fn+tn))/N².

`weka\avg` is WEKA's "Weighted Avg." row. Each figure is computed per class, one-vs-rest, then
averaged with each class weighted by its share of the actual instances, row_i/N:
- **wprec**, **wf1** and **wmcc**: weighted precision, F1 and MCC.
- **wrec**: weighted recall. This always works out to Σ m[i,i]/N, the overall accuracy of the
  whole matrix.
- **wfpr**: weighted false positive rate. For each class, the share of the *other* classes'
  instances wrongly predicted as that class.

### Two things that differ for three or more classes

- `weka\stat`'s acc for one class is that class's one-vs-rest accuracy. The overall accuracy of
  the matrix is `weka\avg`'s wrec.
- `weka\scr`'s kappa is also one-vs-rest. WEKA's single "Kappa statistic" over all classes is
  not reported for N > 2. For two classes the two are identical.

## Undefined values

These follow WEKA 3.8's `Evaluation.java`:
- A ratio whose denominator is zero, such as precision when nothing was predicted positive, is
  `undef`. That is the TI-89's equivalent of the `?` WEKA prints, and the menu shows it as
  `undef`.
- F1 is 0, not `undef`, when precision and recall are both 0. It is `undef` when either one is.
- Kappa is 1 when chance agreement is 1.
- `weka\avg` skips a class with no actual instances, as WEKA does. Any other `undef` makes the
  weighted figure `undef`.

## Running `weka\weka`

Every top-level `Title` opens an `Item` dropdown, following `discrete\entinfo`.

- **F1 Binary** › *Enter counts*: prompts for TP, TN, FP and FN, then shows three pages, one per
  Function: Stats, Rates and Scores. Press ENTER at each `Pause` to move to the next page.
- **F2 Matrix**
  - *Enter matrix*: type the matrix, for example `[[50,3][4,43]]`, then see the weighted
    averages.
  - *Per class*: choose a class, then see the same three pages for it.
  - *Weighted avg*: the `weka\avg` page again for the matrix last entered.
- **F3 About**: *About* for credits, and *Quit*.

Bad input gets a one-line error at the prompt, so it never surfaces as a failure inside one of
the Functions. The menu forces Approximate mode while it runs and restores the previous setting
on Quit.

## Not yet tested on hardware

None of this has been run on a calculator or an emulator yet. The Python check behind the worked
examples above confirms the arithmetic, not the TI-BASIC. Before relying on it, confirm:

- that the packed `.89f` Functions transfer and run. `tools/ti89-pack.py` assumes a text-stored
  Function ends like a Program, which is unverified (see `docs/TI-BASIC.md`). The fallback is to
  type each `.txt` into the Program Editor with New > Function;
- that `0/0` evaluates to `undef` inside a Function rather than raising an error;
- that a program may share its folder's name. If `weka\weka` is refused, rename it, for example
  to `weka\wekaeval`.

## Possible future improvements

Other parts of WEKA that are light enough for the calculator:
- **Numeric-prediction errors**: mean absolute error, root mean squared error and relative
  absolute error, from a list of predicted values and a list of actual values.
- **ZeroR and OneR baselines** from Data-variable columns. OneR would reuse `discrete\tally`, which
  would make this folder depend on `discrete`.

Not worth it on a TI-89: ROC and PRC area, which need a probability for every instance and a
sort; cross-validation; and any real learner such as J48 or Naive Bayes, which would be too slow
and too large.
