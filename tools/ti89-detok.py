#!/usr/bin/env python3
"""Decode a tokenized TI-68k program (*.89p) into a readable token listing.

A program is stored either as source text or as byte-code, depending on whether it
was run or edited more recently: executing compiles it in place, and editing it in
the Program Editor writes the source back out. `ti89-textconv.py` can only hex-dump
the byte-code form. This tool walks it instead.

    python3 tools/ti89-detok.py CHEM/chem.radiate.89p
    python3 tools/ti89-detok.py --tags estack.h KADICH/kadich.kbdprgm1.89p

Scope: this recovers the statement structure (every instruction, label, jump,
name, string, integer and program call) but does NOT reconstruct source. Infix
expressions are postfix in the stream and are printed as their operator tokens,
not reassembled into `a+b*c`. That is enough to audit control flow, find a
formula, or see which labels exist; it is not a round-trip decompiler.

## Format

The variable data at 0x58 holds one postfix expression stack. **It reads from the
last byte backwards**: walking down from the end yields the program top to bottom.

Token forms, as read backwards:

    <tag>                     one-byte tag from `enum Tags`
    00 E4 <idx>  /  E4 <idx>  instruction, `idx` into the `_ITAG` names of
                              `enum InstructionTags`
    00 E3 <idx>  /  E3 <idx>  extended function, `idx` into `enum ExtTags`
    00 <name> 00              VAR_NAME_TAG, a user name, up to 8 chars
    00 <text> 00 2D           STR_TAG, a string literal
    <digits> <len> 1F         POSINT_TAG, little-endian integer
    00 folder\\name 00 DA      USERFUNC_TAG, a call to another program

The trap in `enum InstructionTags` is that every value carries two names, an
`_ITAG` and a `_TAG`, and they are different tables. `EXT_INSTR_TAG` indexes only
the `_ITAG` set. Read the `_TAG` half by mistake and `0x30` looks like `Trace`
when it is `Lbl`, and `0x2F` looks like `int2Hex` when it is `Goto`.

The tables come from GCC4TI's `estack.h`:
https://github.com/debrouxl/gcc4ti -> trunk/tigcc/include/C/estack.h
A trimmed copy is inlined below so this script has no dependencies. Pass
`--tags <path to estack.h>` to parse a full copy instead.
"""
import re
import sys

# Minimal tables, enough for the statement layer. Instruction names are the
# _ITAG half of enum InstructionTags.
TAGS = {
    0x00: "VAR_NAME", 0x1C: "EXT_SYSTEM", 0x1F: "POSINT", 0x20: "NEGINT",
    0x21: "POSFRAC", 0x22: "NEGFRAC", 0x23: "FLOAT", 0x24: "PI", 0x25: "EXP",
    0x2A: "UNDEF", 0x2B: "FALSE", 0x2C: "TRUE", 0x2D: "STR", 0x2E: "NOTHING",
    0x5C: "ADD", 0x5D: "SUB", 0x5E: "MUL", 0x5F: "DIV", 0x60: "POW",
    0x80: "LT", 0x81: "LE", 0x82: "GT", 0x83: "GE", 0x84: "NE", 0x87: "EQ",
    0x7F: "ISTORE", 0xD9: "LIST", 0xDA: "USERFUNC", 0xDC: "FUNC",
    0xE3: "EXT", 0xE4: "EXT_INSTR", 0xE5: "END", 0xE8: "NEWLINE",
    0xE9: "ENDSTACK", 0xF0: "LOCALVAR",
}
# 0x01..0x1B are the reserved single-letter variables, in the order q,r,s..z,a..p.
TAGS.update({0x01 + n: "var %s" % c
             for n, c in enumerate("qrstuvwxyzabcdefghijklmnop")})
ITAGS = {
    0x01: "ClrDraw", 0x02: "ClrGraph", 0x03: "ClrHome", 0x04: "ClrIO",
    0x05: "ClrTable", 0x06: "Custom", 0x07: "Cycle", 0x08: "Dialog",
    0x0B: "Else", 0x0C: "EndCustm", 0x0E: "EndFor", 0x0F: "EndFunc",
    0x10: "EndIf", 0x11: "EndLoop", 0x12: "EndPrgm", 0x13: "EndTBar",
    0x14: "EndTry", 0x15: "EndWhile", 0x16: "Exit", 0x17: "Func",
    0x18: "Loop", 0x19: "Prgm", 0x1D: "Toolbar", 0x2F: "Goto", 0x30: "Lbl",
    0x31: "Get", 0x32: "Send", 0x39: "ElseIf", 0x3B: "If...Then",
    0x43: "Request", 0x44: "PopUp", 0x4C: "DropDown", 0x51: "Pause",
    0x52: "Return", 0x53: "Input", 0x56: "Title", 0x57: "Item",
    0x58: "InputStr", 0x62: "Text", 0x74: "For", 0x7A: "Disp",
    0x7D: "Local", 0x7F: "DelVar", 0x81: "Prompt", 0x86: "Define",
    0x8A: "DispHome", 0x3D: "While", 0x5E: "RclPic",
}
ETAGS = {0x07: "expr", 0x09: "string"}


def load_estack(path):
    """Replace the inlined tables with a parse of a real estack.h."""
    src = open(path, encoding="latin-1").read()
    out = {}
    for enum in ("Tags", "ExtTags", "InstructionTags"):
        m = re.search(r"enum %s\{(.*?)\};" % enum, src, re.S)
        body = re.sub(r"#\w+[^\n]*", "", m.group(1))
        table = {}
        for item in body.split(","):
            if "=" not in item:
                continue
            name, _, val = item.partition("=")
            name, val = name.strip(), val.strip().split()[0]
            try:
                num = int(val, 16)
            except ValueError:
                continue
            # EXT_INSTR_TAG indexes the _ITAG half; prefer it.
            prev = table.get(num)
            if prev is None or (enum == "InstructionTags"
                                and name.endswith("_ITAG")
                                and not prev.endswith("_ITAG")):
                table[num] = name
        out[enum] = table
    return out["Tags"], out["InstructionTags"], out["ExtTags"]


def read_body(path):
    d = open(path, "rb").read()
    if not d.startswith((b"**TI92P*", b"**TI89**")):
        sys.exit("%s: not a TI-89/92+ variable file" % path)
    size = int.from_bytes(d[0x56:0x58], "big")
    body = d[0x58:0x58 + size]
    if len(body) >= 2 and body[-2] == 0x08:
        sys.exit("%s: stored as text, use ti89-textconv.py instead" % path)
    return body


def walk(b):
    """Yield (addr, raw_hex, text) reading backwards, i.e. in program order."""
    i = len(b) - 1
    while i >= 0:
        t, at = b[i], i

        if t in (0xE4, 0xE3) or (t == 0x00 and i >= 2 and b[i - 1] in (0xE4, 0xE3)):
            wide = t == 0x00                      # 00 E4 <idx> vs E4 <idx>
            kind = b[i - 1] if wide else t
            idx = b[i - 2] if wide else b[i - 1]
            tbl = ITAGS if kind == 0xE4 else ETAGS
            n = 3 if wide else 2
            label = tbl.get(idx) or "%s:0x%02X" % (
                "instr" if kind == 0xE4 else "ext", idx)
            yield at, b[i - n + 1:i + 1].hex(" "), label
            i -= n
            continue

        if t == 0x2D:                             # 00 <text> 00 2D
            j = i - 2
            while j >= 0 and b[j] != 0x00:
                j -= 1
            yield at, "..2d", '"%s"' % b[j + 1:i - 1].decode("latin-1")
            i = j - 1
            continue

        if t == 0x1F and i >= 1:                  # <digits> <len> 1F
            n = b[i - 1]
            yield at, b[i - 1 - n:i + 1].hex(" "), str(
                int.from_bytes(b[i - 1 - n:i - 1], "little"))
            i -= 2 + n
            continue

        if t == 0x00:
            j = i - 1
            while j >= 0 and b[j] != 0x00 and 0x20 <= b[j] < 0x7F and i - j <= 13:
                j -= 1
            if j >= 0 and b[j] == 0x00 and i - j > 1:
                yield at, "00..00", b[j + 1:i].decode("latin-1")
                i = j - 1
            else:
                yield at, "00", "."
                i -= 1
            continue

        yield at, "%02x" % t, TAGS.get(t, "?%02X" % t)
        i -= 1


def main(argv):
    global TAGS, ITAGS, ETAGS
    if len(argv) > 2 and argv[0] == "--tags":
        TAGS, ITAGS, ETAGS = load_estack(argv[1])
        argv = argv[2:]
    if not argv:
        sys.exit(__doc__.strip().split("\n\n")[1])
    for path in argv:
        body = read_body(path)
        print("# %s, %d bytes of byte-code, read bottom-up" % (path, len(body)))
        for at, raw, text in walk(body):
            if text == ".":
                continue
            print("%04x  %-14s %s" % (at, raw, text))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:])
