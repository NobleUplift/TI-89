#!/usr/bin/env python3
"""Git textconv driver for TI-89 / TI-92 Plus variable files (*.89p, *.9xp).

Prints the header fields and the program source as UTF-8 text with LF line
endings, so `git diff` / `git log -p` show readable line-by-line diffs.
The file in the repository is never modified.

Setup (once per clone), either:
    git config include.path ../.gitconfig
or:
    git config diff.ti89.textconv "python3 tools/ti89-textconv.py"

Single-variable file layout (integers little-endian unless noted), per
TiLP's libtifiles (files9x.cc) and the TI-89 Link Protocol Guide:
    0x00  8   signature: "**TI89**", "**TI92P*", "**TI92**" or "**V200**"
    0x08  2   01 00
    0x0A  8   default folder name, NUL-padded
    0x12  40  comment, NUL-padded
    0x3A  2   number of variable entries (1)
    0x3C  4   offset of this entry's data (0x52)
    0x40  8   variable name, NUL-padded
    0x48  1   type (0x12 program, 0x13 function, 0x0C string, ...)
    0x49  1   attribute (0 none, 1 locked, 2/3 archived)
    0x4A  2   00 00
    0x4C  4   total file size
    0x50  2   A5 5A
    0x52  4   00 00 00 00
    0x56  n   variable data; starts with a 2-byte BIG-endian length
    ...   2   checksum: sum of the n data bytes, mod 0x10000
"""
import sys

import ti89charset


def cstr(raw):
    return raw.split(b"\0", 1)[0].decode("latin-1")


def main(path):
    data = open(path, "rb").read()
    out = sys.stdout

    if not data.startswith((b"**TI92P*", b"**TI89**")) or len(data) < 0x5A:
        out.write(data.decode("latin-1"))
        return

    folder = cstr(data[0x0A:0x12])
    comment = cstr(data[0x12:0x3A])
    name = cstr(data[0x40:0x48])
    vtype = data[0x48]
    out.write("# folder:  %s\n# name:    %s\n# type:    0x%02X\n# comment: %s\n"
              % (folder, name, vtype, comment))

    size = int.from_bytes(data[0x56:0x58], "big")
    body = data[0x58:0x58 + size]
    checksum = data[0x58 + size:0x5A + size]
    out.write("# size:    %d bytes, checksum %s\n\n" % (size, checksum.hex()))

    # Programs (0x12) and functions (0x13) end in ... E5 00 01 <flag> <tag>.
    # Flag 0x08 means the source is stored as plain text; otherwise the
    # variable was tokenized on the calculator and holds bytecode.
    if vtype in (0x12, 0x13) and len(body) >= 2 and body[-2] == 0x08:
        text = body.split(b"\0", 1)[0]
        out.write(ti89charset.decode(text))
        out.write("\n")
    else:
        out.write("# (tokenized/binary content; hex dump follows)\n")
        for i in range(0, len(body), 16):
            out.write("%04x  %s\n" % (i, body[i:i + 16].hex(" ")))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    main(sys.argv[1])
