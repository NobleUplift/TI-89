# TI-89 Titanium

A backup of a TI-89 Titanium graphing calculator, taken on 27 January 2009, merged with the
earlier exports that survived. It holds the Marist High School math team's accumulated
program set: 133 calculator variables in this repository, plus three submodules, written
between 1998 and 2008 by eleven students and eight outside authors whose programs were
downloaded from the public TI-89 archives.

The 2009 session accounts for 101 of them. The rest come from earlier exports, chiefly one
dated 16 April 2007, and six of those are the earlier home of a program the 2009 backup holds
under a different folder. Those six are committed as renames, so the history tracks a program
across the reorganisation rather than listing it twice. See [Moves](#moves).

**Most of this code is not mine.** I joined the math team in 2006 and inherited the program
set from the programmers before me. Where a file records who wrote it, that person is the
commit author; where it records nothing, the commit is authored to the team collectively.
See [Contributors](#contributors).

```
git clone --recurse-submodules https://github.com/NobleUplift/TI-89.git
```

The submodules matter: `main\kbdprgm3` calls `periodic\periodic()`, so the program set is
incomplete without them.

## Layout

| Path | Contents |
|---|---|
| `ALGEBRA/` … `TRIGONOM/` | calculator programs, grouped by subject |
| `MAIN/` | the keyboard programs, menus and maintenance tools |
| `MAIN/NoteFolio/` | NoteFolio documents, including the programmer's manual; `tools/notefolio.py` reads and builds them |
| `MAIN/StudyCards/` | StudyCards stacks for Latin and Western Civilization |
| `MATH/` | NoteFolio documents left in the `math` folder, which predates the split into subjects |
| `PERIODIC/` | submodule: periodic table browser |
| `HEART/` | submodule |
| `RANDOM/` | submodule |
| `tools/` | `.89p` diff driver, so programs show as source |

**Every directory is the calculator folder its files record at offset `0x0A`**, so a path
never implies a call that does not exist. `MAIN/NoteFolio/` and `MAIN/StudyCards/` are the
exception: both hold `MAIN` variables and are split by document type instead.

Filenames are as the PC link software wrote them. For a program that means
`<calculator folder>.<variable name>.<extension>`: `chem.density.89p` is the variable
`density` in the calculator folder `chem`, called as `chem\density()`.

A `.89y` works differently. NoteFolio and StudyCards derive an eight-character variable name
by running the folder and the title together and truncating, so `MAIN/NoteFolio/math.sine.89y`
holds `MAIN\mathsine` and `MAIN/StudyCards/main.westcivm.89y` holds `MAIN\mainwest`. Those
names are not unique, five Latin stacks all being `MAIN\mainlati`, so the filename carries the
only usable identity and is left alone.

| Extension | Type |
|---|---|
| `.89p` | program |
| `.89f` | function |
| `.89y` | Flash app document (NoteFolio, StudyCards) |
| `.89i` | picture |
| `.89d` | graph database |
| `.89z` | assembly program |

## Readable diffs

`.89p` files wrap the program text in a binary header and footer, so Git shows them as binary
by default. Run this once per clone:

```
git config include.path ../.gitconfig
```

After that `git diff`, `git log -p` and `git show` print the program source as text. To view
one file directly:

```
python3 tools/ti89-textconv.py MAIN/main.kbdprgm3.89p
```

Text-stored programs print as TI-BASIC. Programs that were run on the calculator before the
backup were tokenized into byte-code and print as a hex dump. GitHub's web interface ignores
textconv and still shows these files as binary.

NoteFolio documents are plain text in an app-variable wrapper. `tools/notefolio.py` prints one
as UTF-8 text, with a form-feed line between notes, and builds a `.89y` from text in the same
form, and `verify` checks that a document rebuilds byte for byte. Its docstring records the file
layout.

```
python3 tools/notefolio.py dump MAIN/NoteFolio/main.manual.89y -o manual.txt
python3 tools/notefolio.py build manual.txt          # writes main.manual.89y
python3 tools/notefolio.py verify MAIN/NoteFolio/*.89y MATH/*.89y
```

## Moves

Programs were reorganised twice. The `.tig` dumps that preceded this backup show everything in
one `math` folder, then split into `miscam` and `miscnz` during 2007, then landing in
`discrete` and `history` by 2009. Six programs are in the repository under both their old and
their new folder, and the 2009 session exported other variables from `miscam` and `miscnz`
without these, so the originals were gone from the calculator by then. They are committed as
renames:

| From | To | What changed with the move |
|---|---|---|
| `miscnz\weekdays` | `history\weekdays` | rewritten: a retry loop, input validation and the week of the year |
| `miscam\baseconv` | `discrete\baseconv` | one space, in a `Local` declaration |
| `miscam\binomial` | `discrete\binomial` | blank lines, and a trailing space on a `Dialog` title |
| `miscam\fib` | `discrete\fib` | nothing, byte for byte |
| `miscnz\pasc` | `discrete\pascalst` | nothing but the variable name |
| `miscam\inqsolve` | `miscam\inqslve2` | one line: `part(equ,1)` becomes `part(u[1,1])` |

Where the content changed, the move and the change are separate commits. Git decides a rename
by hashing chunks of a file, and shifting a single byte re-chunks everything after it: folded
together, `miscam\baseconv` to `discrete\baseconv` scores 0 and the rename is lost. Moved on
its own it scores 97. So the move commit carries the old body under the new folder, and the
edit follows as an ordinary diff:

```
git log --follow -p HISTORY/history.weekdays.89p
```

`discrete\binary` went the other way. It survives in four versions, all archived and all
exported in the same second, so only the code orders them: features accumulate, commented-out
`Disp` and `Pause` lines peak at 60 in the third while the octal and hexadecimal paths were
being made to work, and the fourth finally clears in `DelVar` the labels its own `Toolbar`
declares. They are committed onto one path as four successive revisions. The three earlier
versions have the variable name at `0x40` rewritten from `binary0N` to `binary` so that the
path and the container agree and every commit holds a file the calculator would accept. That
field is fixed width and sits below `0x56`, so no length or checksum changes, and it is the
only place in the repository where a byte differs from the export. `HEAD` is the export
untouched throughout.

### Calls that were already broken

`main\mathem2` was only partly updated when the folders changed. It calls `discrete\baseconv`,
`discrete\binomial` and `discrete\pascalst`, but still calls `miscam\fib`, `miscnz\weekdays`
and `miscam\inqsolve`, none of which the 2009 calculator still had. Those three menu entries
failed at export time, alongside `math\sss`, `math\sas`, `math\simu`, `math\tran`, `math\hype`
and `math\inter`, which are in no dump here at all. They are left as they are: they are
evidence about programs that no longer exist.

`main\mtprogsd` and `main\clrvs` list almost every program in the set but call none of them,
one being a transfer list and the other a `DelVar` list. Both still use pre-2008 names, so
being named by them is not evidence that a program was reachable.

## The `.89p` file format

Each file holds one calculator variable. Numbers are little-endian unless noted.

| Offset | Size | Field |
|---|---|---|
| 0x00 | 8 | Signature: `**TI92P*` (the TI-89 and TI-92 Plus run the same OS) |
| 0x0A | 8 | Calculator folder name |
| 0x12 | 40 | Comment, `Program file MM/DD/YY, HH:MM`, written by the PC link software at export time |
| 0x40 | 8 | Variable name |
| 0x48 | 1 | Type: 0x12 program, 0x13 function, 0x10 picture, 0x1C Flash app document |
| 0x49 | 1 | Attribute: 0 none, 1 locked, 2 or 3 archived |
| 0x4C | 4 | Total file size |
| 0x56 | 2 | Data length, **big-endian** |
| end | 2 | Checksum: sum of the length and data bytes, mod 65536 |

Editing one by hand means updating the data length, the total file size and the checksum, or
the calculator rejects it. `.gitattributes` marks every `.89*` file `-text` so no line-ending
conversion can corrupt them.

## Dates

Commit dates are authorship dates, not export dates. Where a file states a copyright year,
that year dates the commit, with the month, day and time taken from the file's own export
timestamp at offset 0x12. Where a file records nothing, the export timestamp stands in and
the commit message says so explicitly. Every commit body records the export timestamp
regardless.

This means a program Randall Lewis wrote in 1998 is dated 1998, even though it did not leave
the calculator until 2007.

A move is a repository event rather than an authorship one, so it is dated to the
reorganisation and not to the program. `miscam\baseconv` is Jesse Lai's, 1999; the commit that
moves it to `discrete\baseconv` is dated 2008 and authored to Patrick Seiter, whom
`main\mathem2`'s credits screen and the programmer's manual credit with reorganising the set.
No file records who moved what, so every move commit says which evidence dates it.

## Contributors

### Marist High School Math Team

Coaches, per the team's page as archived on 10 February 2005:

- **Head Coach: Mr. Jeffrey Nicholson**
- **Assistant Coach: Mr. Owen Glennon**

Programmers, from the roster in `MAIN/NoteFolio/main.manual.89y`, in the order it lists them.
Years and credits are the manual's own.

| Name | Years | Credited with |
|---|---|---|
| Brian Cis | not recorded | helped write `kbdprgm7` (not in this backup) |
| Dave Krydynski | not recorded | not recorded |
| Mike Januszyk | not recorded | not recorded |
| Evan Lunt | not recorded | `coordin\ptplane` and `coordin\ptsolver`; the latter inlined into `geometry\geometry` |
| Christopher Chinske | not recorded | `geometry\clockdeg` |
| Sean Pedota | not recorded | `geometry\geometry` |
| Adam Golz | 2003-2007 | `geometry\frustum` (2005, later revised), `geometry\volume` (2005), `geometry\polyarea` |
| Daniel Soso | 2003-2007 | `chem\density`, `chem\enthalpy`, `chem\fracabun`, `chem\temp`, `chem\ultwaves`, `chem\period1c`, `discrete\binomial`, `main\twoman`, `miscnz\weekdays`, `history\weekdays`, `physics\multivec`, `physics\vectors`, `physics\veloc`, `physics\velocity`, `trigonom\concur`, `trigonom\pythag`, `trigonom\tritest`, and one label in `geometry\geometry` |
| Kyle McQuaid | 2003-2007 | the roster credits him with the single word "trigonom". Too vague to attribute individual commits, so the undated `trigonom` programs are authored to the team |
| Timothy Kadich | 2004-2008 | `kadich\cssc`, `kadich\kbdprgm1`, `kadich\kbdprgm6` |
| Patrick Seiter | joined 2006 | 2006: `chem\accuracy`, `chem\precise`, `biology\hardyw`, `main\kbdprgm3`, the manual and the geometry theorems. 2007: `periodic\periodic`, `chem\radiate`, `chem\metpre`, `algebra\quadform`, `algebra\system`, `geometry\degminse`, `trigonom\apothem`. 2008: the seven `discrete` programs, all incomplete. Plus the Latin and Western Civilization StudyCards, and revisions to `geometry\geometry`, `geometry\frustum`, `history\weekdays`, `kadich\kbdprgm6` and `chem\period1c` |

`main\mathem2`, the menu that reaches 66 of these programs, is authored to the team. Its own
credits screen names the earlier programmers:

> Programs organized and written in the prototype policy by Brian Cis (Yahweh), Dave
> Krydynski, Mike Januszyk, Dan Soso, Adam Golz, Kyle McQuaid, Chris Chinske & Sean Pedota

and records that Patrick Seiter reorganized and fixed many of them and added his own.

### Outside authors, from the public TI-89 archives

| Name | Contribution | Published |
|---|---|---|
| Randall Lewis | `trigonom\pythagor` | [pythagor.zip](https://www.ticalc.org/archives/files/fileinfo/65/6557.html), 1998-09-09 |
| Evan Lunt | `coordin\ptsolver` (also on the roster above) | [ptsolver.zip](https://www.ticalc.org/archives/files/fileinfo/80/8008.html), 1999-02-28 |
| Kevin Chern | `calculus\info` | [info89.zip](https://www.ticalc.org/archives/files/fileinfo/80/8004.html), 1999-02-28 |
| Jonathan Lin | the TI-89 port of `calculus\info` | credited inside the program |
| Jesse Lai, publishing as ChaoticSoft | `discrete\baseconv`, `miscam\baseconv`, `physics\vector` | [baseconv.zip](https://www.ticalc.org/archives/files/fileinfo/83/8301.html) and [vector.zip](https://www.ticalc.org/archives/files/fileinfo/83/8307.html), both 1999-03-29 |
| Eric P. Esterle | `coordin\wronskia` | [wron2.zip](https://www.ticalc.org/pub/89/basic/math/linearalgebra/wron2.zip), 1999-04-11 |
| Nicholas Young-Soares | `trigonom\trig` | [trig.zip](https://www.ticalc.org/archives/files/fileinfo/67/6761.html), 2000-01-02 |
| Mike Grass | `history\factors` (assembly), probable | [factors2.zip](https://www.ticalc.org/pub/89/asm/math/factors2.zip), 2000-06-15 |
| Richard Smith | `binomial` and `centroid`, downloaded by the team; `discrete\binomial` may be derived from his | ticalc.org, 1999-02-28 |

### Content sources, not code authors

| Source | Where it appears |
|---|---|
| Richard Rhoad, *Geometry for Enjoyment and Challenge* | `math\circles` transcribes chapter 10 |
| SparkNotes (Barnes & Noble) | `snlatin1` vocabulary, typed in by Patrick Seiter |

If your work is here and you would rather it were not, open an issue. Every third-party file
is in its own commit precisely so it can be removed with a single `git revert`.

## Not included

**Flash applications.** 36 `.89k` application binaries were on the calculator and are
excluded: they are proprietary and not mine to redistribute. The manual lists what was
installed, including Cabri Geometry, CellSheet, Finance, NoteFolio, Organizer, Polynomial
Root Finder, Simultaneous Equation Solver, Statistics with List Editor, StudyCards, Symbolic
Math Guide, The Geometer's Sketchpad, TI-Reader, EE*Pro and US Presidents. Download them from
Texas Instruments.

**Eight StudyCards stacks** that shipped with the calculator: `calculus`, `math1`, `math2`,
`math3`, `science1`, `science2`, `science3` and `tiinfo`. Seven name Texas Instruments as
their author and are stamped "SAMPLE ONLY"; `calculus` carries "Copyright (C) 2003 by the
College Board. All rights reserved."
