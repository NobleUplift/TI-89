#!/usr/bin/env python3
"""Pack a TI-BASIC source file into a text-stored .89p program or .89f
function variable.

    python3 tools/ti89-pack.py src/table.txt periodic.table.89p
    python3 tools/ti89-pack.py src/shannonh.txt discrete.shannonh.89f

The source is UTF-8 with LF line endings, written in the TI character set
(→ for store, ≠ ≤ ≥, − for negation, © for comments); see ti89charset.py.
The first line is the parameter list, e.g. "()", followed by Prgm...EndPrgm
(.89p) or Func...EndFunc (.89f). The folder and variable name come from the
output file name (<folder>.<name>.89p or .89f). The calculator tokenizes
the variable on first run.

UNVERIFIED for .89f: every file this was reverse-engineered against is a
Prgm (type 0x12). tools/ti89-textconv.py's own comment says "Programs
(0x12) and functions (0x13) end in ... E5 00 01 <flag> <tag>", i.e. that
suffix is shared -- but whether the two bytes before it (documented
elsewhere as "the Prgm command", 19 E4) are Prgm-specific or are a generic
marker that also covers Func has not been confirmed against a real Func
file, and no .89f file exists anywhere in this repo to check against. This
script assumes the tail is identical for both types. If a packed .89f
fails to transfer or run, that assumption is the first thing to revisit;
the fallback is typing the source into the calculator's own Program
Editor (New > Function) instead of sending this file.

Leading spaces on each line are stripped before encoding: indentation in
the .txt source is for human readability only and is never shipped to the
calculator -- every space costs a byte in a shared, finite storage pool
across every variable on the device, so it isn't free the way parse time
is. Only *leading* whitespace is touched; a space inside a quoted string
starts after other characters on its line, so centered Text/Disp strings
(e.g. discrete\\baseconv's About screen) are untouched.

Whole-line comments (a line starting with © once leading spaces are
stripped) are dropped entirely, for the same reason: they document the
.txt source for human readers and cost real bytes on the calculator for
no runtime benefit. Only a line whose first non-space character is ©
qualifies -- every comment in this repo is written that way (its own
line, never trailing after a command), so this never touches a © that
might appear inside a quoted string.
"""
import sys

import ti89charset

# Bytes after the source text: NUL, a 2-byte big-endian editor cursor offset
# (0x0001 in most files here), Prgm command (19 E4), END_TAG (E5), 00 01,
# flag 08 (stored as text), USER_DEF_TAG (DC). Repacking the repo's
# text-stored programs with this tail reproduces them byte for byte, apart
# from the cursor offset. See the module docstring for why this is used
# unchanged for .89f functions too, and why that part is unverified.
TEXT_PRGM_TAIL = bytes.fromhex("00 00 01 19 e4 e5 00 01 08 dc")

TYPE_BY_EXT = {"89p": 0x12, "89f": 0x13}


def pad(s, n):
    raw = s.encode("latin-1")
    if len(raw) > n:
        raise ValueError("%r is longer than %d bytes" % (s, n))
    return raw + b"\0" * (n - len(raw))


def pack(source, folder, name, vtype, comment="Program file"):
    text = source.replace("\r\n", "\n").rstrip("\n")
    lines = (line.lstrip(" ") for line in text.split("\n"))
    text = "\n".join(line for line in lines if not line.startswith("©"))
    body = ti89charset.encode(text) + TEXT_PRGM_TAIL
    data = len(body).to_bytes(2, "big") + body
    checksum = (sum(data) & 0xFFFF).to_bytes(2, "little")
    total = 0x56 + len(data) + 2

    out = bytearray()
    out += b"**TI92P*"
    out += b"\x01\x00"
    out += pad(folder, 8)
    out += pad(comment, 40)
    out += (1).to_bytes(2, "little")      # one variable
    out += (0x52).to_bytes(4, "little")   # its data offset
    out += pad(name, 8)
    out += bytes([vtype, 0x00])           # type: program or function; attribute: none
    out += b"\x00\x00"
    out += total.to_bytes(4, "little")
    out += b"\xa5\x5a"
    out += b"\x00\x00\x00\x00"
    out += data
    out += checksum
    assert len(out) == total
    return bytes(out)


def main(src, dst):
    base = dst.rsplit("/", 1)[-1]
    folder, name, ext = base.split(".")
    if ext not in TYPE_BY_EXT or len(name) > 8 or len(folder) > 8:
        sys.exit("output must be named <folder>.<name>.89p or .89f, names up to 8 chars")
    source = open(src, encoding="utf-8").read()
    with open(dst, "wb") as f:
        f.write(pack(source, folder, name, TYPE_BY_EXT[ext]))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
