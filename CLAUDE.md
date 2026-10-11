# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A backup of one TI-89 Titanium, exported 2009-01-27 and merged with the earlier exports that
survived, plus a small amount of work written since. 136 calculator variables and two submodules.
Nothing is built, linted or tested here. The programs are 68k TI-BASIC and run on a calculator or
an emulator (TiEmu). The only code that runs on a PC is `tools/`.

The repository is a history-rewriting project as much as a code dump: provenance, authorship and
dates are the point. See [Commits and provenance](#commits-and-provenance).

Further reading, in the order it usually matters:

- `docs/PROGRAMS.md` is the per-program reference: what calls what, what is unreachable, which
  programs never worked, and which are byte-code only. Consult it when a task touches a named
  program; do not duplicate it here.
- `docs/TI-BASIC.md` is the rules and hardware limits for **writing** TI-BASIC: name resolution,
  Programs versus Functions, comments, screen limits, input and modes. Read it before writing or
  editing any calculator program.
- `docs/TOOLS.md` is what each script in `tools/` does and which format it encodes.
- `docs/TOKENIZATION.md` is the `.89p` byte-code format and the tag tables, with sourced
  references. Read it before writing anything that parses a tokenized program.
- `PERIODIC/CLAUDE.md` governs everything under that directory. Read it before touching any of it.
- `README.md` is the human-facing account of provenance, the renames and the file format.

## The 2009 set is an archive; new work is separate

Two kinds of thing live here and the rules differ. Establish which one a task touches before
changing anything.

**The 2009 export, and the earlier exports merged into it, are evidence.** Their state at export
time is the thing being preserved, including the parts that are broken.

- **Do not fix bugs, modernize, refactor or tidy them.** Wrong formulas, dead labels, debug output
  and calls to programs that no longer exist are all catalogued in `docs/PROGRAMS.md` and are all
  staying. If a task seems to require fixing one, say so and stop rather than changing it.
- **Do not add, remove or reorder the variables in that set** to make it more consistent.
- Byte-for-byte fidelity to the export is the standing constraint for them. Exactly one byte in
  the repository deviates from it, and the README explains which and why.
- When one of them looks wrong, the useful output is a note, not a patch.

**Programs written after the backup are ordinary code** and may be edited, fixed and extended.
`discrete\entinfo`, `discrete\entropy` and `discrete\tally` are the current examples: added in
2026, with `.txt` sources committed beside the containers and `DISCRETE/README.md` explaining
them. New work follows that pattern (a `.txt` source that `tools/ti89-pack.py` builds), and must
not alter, renumber or re-home anything from the 2009 set.

## Commands

```
git config include.path ../.gitconfig                 # once per clone, readable .89p diffs
python3 tools/ti89-textconv.py MAIN/main.kbdprgm3.89p # print one variable as text
python3 tools/ti89-detok.py CHEM/chem.radiate.89p     # decode a byte-code program
python3 tools/ti89-pack.py <source.txt> <out.89p>     # rebuild a .89p from text
python3 tools/notefolio.py  verify <file.89y> ...     # NoteFolio documents
python3 tools/studycards.py verify <file.89y> ...     # StudyCards stacks
```

`docs/TOOLS.md` covers all of them, including the traps. The two that bite most often: the packer
takes the variable name from the **output filename**, and it strips leading whitespace and
whole-line `©` comments, so a `.txt` source is a more readable rendering than what ships.

A program stored as text prints as TI-BASIC; one stored as byte-code can only be hex-dumped by
`ti89-textconv.py`, so use `ti89-detok.py` for those 47. It recovers statement structure, not
source. Which form a program is in reflects whether it was run or edited more recently, and is
not evidence either way about how much it was used.

## Directories are calculator folders

**Every directory equals the calculator folder its files record at offset 0x0A.** A path
therefore never implies a call that does not exist. The exceptions are `MAIN/NoteFolio/` and
`MAIN/StudyCards/`, which both hold `MAIN` variables and are split by document type, and `MATH/`,
which holds the NoteFolio documents left behind in the `math` folder that predates the split into
subjects.

This was not always true. Six programs were moved into the folder they belong in, committed as
renames; the README has the table and the `--follow` invocation. Do not reintroduce the old
layout, and do not assume a program is where an old call says it is.

A `.89y` filename is not its variable name: NoteFolio and StudyCards derive an eight-character
name by running folder and title together and truncating, and the results collide, so the
filename carries the only usable identity.

## How to read a dependency

Every cross-program call is fully qualified, `folder\name()`. A scan for unqualified same-folder
calls finds none, including inside `periodic`. So a qualified name is the only reliable signal,
and it survives tokenization as literal ASCII: grepping the raw container for `folder\name` finds
every call a program can make, byte-code or not.

The inverse is the trap, and it is easy to fall into. Toolbar item labels, `Lbl` names and `Local`
declarations also survive as ASCII, so an unqualified token is almost never a call.
`geometry\tetra` contains `Volume`, `Main`, `Height` and `Exit`; those are menu labels, not calls
to `geometry\volume` or `main\*`. An analysis that counts them produces a graph in which almost
everything is reachable. **Only trust qualified matches.**

In byte-code, use `tools/ti89-detok.py` rather than inferring tags from byte frequency. That
inference is what produced an earlier wrong table here; `docs/TOKENIZATION.md` records the
verified one and the `_ITAG`/`_TAG` trap that breaks naive readings.

## File format and editing rules

The byte layout is documented at the top of `tools/ti89-textconv.py` and again in the README.

- Never open a `.89p` in a text editor and never let line-ending conversion near one.
  `.gitattributes` marks `*.89[a-z]` as `-text` to prevent that.
- Changing the data means updating all three of: data length at 0x56 (big-endian), total file size
  at 0x4C (little-endian), and the trailing checksum. Miss one and the calculator rejects the
  file. `tools/ti89-pack.py` does all three.
- Programs stored as source text use CR line endings in the TI character set and end with the
  `0x08` text flag. Of the 102 tracked `.89p`/`.89f` programs, 55 are text and 47 are byte-code,
  which the diff driver shows as a hex dump. (`history\factors.89z` is assembly, and is neither.)
- A `.txt` source committed beside a container is pinned to LF by `.gitattributes`, because the
  packer rewrites line endings and a file that flips between clones diffs on every checkout.
- The comment at 0x12 is the export timestamp written by the PC link software, not part of the
  program. It changes on every backup and is noise in a diff.

## Writing a calculator program

`docs/TI-BASIC.md` is the full set. The four that come up on almost any such task:

- **Fully qualify every cross-folder call**, `folder\name()`. A bare name resolves against the
  calculator's current folder, so it fails whenever that is not the caller's own folder, and it
  fails silently: the call stays symbolic and prints as literal expression text, or raises a
  misleading "Domain error" from inside the callee.
- **Anything returning a value must be a Function (`.89f`)**, not a Program. `SortA` and `SortD`
  cannot be used inside one.
- **Keep in-program comments short**, one brief line each. Indentation and whole-line `©`
  comments cost nothing on the device when the program is built with `tools/ti89-pack.py`, which
  strips both, so a `.txt` source can be laid out for a reader. That is the packer's behaviour,
  not the calculator's: comments typed on the device itself are stored and survive compilation.
- **26.5 characters fit on a `Disp` line** (the 27th is cut off but still partly visible), and
  the Program I/O screen holds **6 lines** before it scrolls.

## Commits and provenance

Most of this code is not the repository owner's. The rules the history follows:

- Commit author is whoever the file says wrote it; files recording nothing are authored to
  "Marist High School Math Team".
- Commit date is the authorship date, not the export date. A stated copyright year supplies the
  year, and the export timestamp at 0x12 supplies month, day and time. Where the file records
  nothing, the export timestamp stands in and the commit message says so.
- Every commit body records the export timestamp regardless.
- One third-party file per commit, so any of them can be removed with a single `git revert`.
- Where a move also changed content, the move and the change are separate commits, or Git loses
  the rename.

`MESSAGES.tsv` is the working manifest driving this: one row per commit of
`seq, author_date, author_name, author_email, subject, body, files`. It and `migration/` are
listed in `.git/info/exclude`, so they stay local and leave no trace in the published history.
`migration/README.md` is the handoff note for that pipeline and names the two design documents
that take precedence over it.

## Do not commit

- `*.89k` Flash application binaries, including everything in `MAIN/Unused Applications/`. They
  are proprietary.
- The eight stock StudyCards stacks listed by name in `.gitignore`.
