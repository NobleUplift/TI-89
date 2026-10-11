# PC-side tools

Everything in `tools/` runs on a PC, never on the calculator. The scripts exist so that binary
calculator variables can be read, diffed and rebuilt without a device in the loop. All are
dependency-free Python 3.

| Script | Does | Format it encodes | Verified against |
|---|---|---|---|
| `ti89-textconv.py` | prints one variable as text | `.89p`/`.89f` container, text-stored body | every text-stored program |
| `ti89-detok.py` | decodes a byte-code program to a token listing | `.89p` byte-code, `estack.h` tag tables | all 47 byte-code programs decode without error |
| `ti89-pack.py` | builds a `.89p`/`.89f` from a `.txt` source | container, with the three dependent header fields | the three `DISCRETE` sources rebuild byte for byte |
| `studycards.py` | build, dump, verify StudyCards stacks | `.89y` StudyCards layout | 22 of 22 tracked stacks rebuild byte for byte |
| `notefolio.py` | build, dump, verify NoteFolio documents | `.89y` NoteFolio layout | 9 of 9 documents rebuild byte for byte |

`ti89charset.py` is the shared TI character table, not a command.

Each script's docstring is the authoritative format reference for what it parses. The one format
too large for a docstring is `.89p` byte-code, which has its own document in
`docs/TOKENIZATION.md`.

## Reading a program

```
python3 tools/ti89-textconv.py MAIN/main.kbdprgm3.89p   # text-stored: prints TI-BASIC
python3 tools/ti89-detok.py CHEM/chem.radiate.89p       # byte-code: prints a token listing
```

`ti89-textconv.py` is also wired in as a Git textconv driver, so `git diff` and `git log -p` show
programs as source once `git config include.path ../.gitconfig` has been run. It hex-dumps a
byte-code program rather than decoding it; `ti89-detok.py` is the one that reads those, and it
recovers statement structure rather than source. Each refuses the other's input with a message
pointing at the right tool.

## Rebuilding a program from text

```
python3 tools/ti89-pack.py DISCRETE/discrete.entropy.txt DISCRETE/discrete.entropy.89f
```

The packer is the only thing that recomputes all three dependent header fields (data length at
0x56, total file size at 0x4C, trailing checksum). Hand-editing a container without updating all
three produces a file the calculator rejects.

Two details of its behaviour matter when comparing a `.txt` against its `.89p`:

- It strips each line's leading whitespace and drops whole-line `©` comments, so a `.txt` source
  is a more readable rendering than what ships. `.txt` to `.89p` is exact; `.89p` back to text
  will not reproduce the indentation or the comments.
- The folder and variable name come from the **output filename**, not from the source. Writing to
  `out.89f` produces a variable called `out`.

Comments are not stripped because the calculator cannot store them. It can: the byte-code census
in `docs/TOKENIZATION.md` counts 159 `COMMENT_TAG` tokens across 8 of the 47 byte-code programs,
so `©` text survives compilation. Stripping is this packer's choice, not a platform limit.

## The `.89y` document tools

`.89y` is a Flash application document rather than a program, and the two applications in this
backup use unrelated layouts, so each has its own tool. Both follow the same three-verb shape:

```
python3 tools/notefolio.py  dump   MAIN/NoteFolio/main.manual.89y -o manual.txt
python3 tools/notefolio.py  build  manual.txt
python3 tools/notefolio.py  verify MAIN/NoteFolio/*.89y MATH/*.89y

python3 tools/studycards.py dump   MAIN/StudyCards/main.latinu01.89y
python3 tools/studycards.py build  stack.txt -o out.89y
python3 tools/studycards.py verify MAIN/StudyCards/main.latinu01.89y
```

`verify` parses and rebuilds a file and compares the bytes, which is what makes the layouts
trustworthy: neither format has a published specification, and both were reverse-engineered from
the documents here, so a byte-for-byte rebuild of every known file is the only available proof.

Two cautions:

- **`studycards.py verify MAIN/StudyCards/*.89y` aborts partway.** That glob picks up the eight
  stock TI stacks, which are gitignored but present on disk and use a different layout; the tool
  raises `AssertionError: not a StudyCards stack` and stops rather than skipping them. Pass
  `$(git ls-files 'MAIN/StudyCards/*.89y')` to verify only the 22 tracked stacks.
- A `.89y` filename is not its variable name. Both applications derive an eight-character name by
  running folder and title together and truncating, and the results collide (five Latin stacks are
  all `MAIN\mainlati`), so the filename carries the only usable identity.

## Duplicated copies

`PERIODIC/` carries its own `tools/`, because it is a submodule and has to stand alone. Of those,
`ti89-textconv.py` and `ti89charset.py` are byte-identical to the root copies, but
**`ti89-pack.py` is not**: the root copy is 106 lines, the `PERIODIC` copy 70. They have diverged
rather than being deliberately different. Before relying on packer behaviour inside `PERIODIC/`,
check which copy is on the path. `PERIODIC/tools/build-mkdata.py` has no root equivalent and is
specific to that submodule.
