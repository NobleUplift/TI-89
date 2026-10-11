#!/usr/bin/env python3
"""Generate, dump and check TI-89 StudyCards stacks (*.89y).

    studycards.py build  stack.txt [-o out.89y]   text source -> .89y
    studycards.py dump   file.89y                 .89y -> the same text source
    studycards.py verify file.89y ...             parse + rebuild, compare bytes

The layout below was reverse-engineered from the stacks in MAIN/StudyCards/
(no public document for the TI-89 StudyCards format could be found), so it is
verified only against those files. `verify` rebuilds each one byte for byte.

File: a standard single-variable TI-89 file (see ti89-textconv.py) holding one
AppVar (type 0x1C). The 2-byte-length-prefixed variable data is:

    0x00  4  f3 47 bf a7   (constant in every stack)
    0x04  4  01 00 00 00   (constant)
    0x08  8  u16 LE offsets of: title, author, date, version strings
    0x10  3  flags: 00 00 00, or 01 01 00 in some stacks (meaning unknown)
    0x13  1  number of cards N (the last card of a stack is usually blank)
    0x14  2N u16 LE offset of each card
          1  02, then four NUL-terminated strings: title, author, date, version
          .. the cards
          7  00 "STDY" 00 f8   trailer (f8 is the TI-OS "other" tag)
    checksum: u16 LE sum of the length prefix and the data

A card is   u16 LE offset of side A, u16 LE offset of side B (both from the
card start), NUL-terminated card title, side A, side B.

A side is   01 03 00 <n>, then n lines of `01 <y> 00 <text> 00` (y = pixel row,
8.2 px apart), then a tail (`50 00 00 00 00 01` for A, `50 00 00 00 00 00 01`
for B in the Latin stacks). A few stacks use a second, longer side format
(leading 02 05 ...); those are kept as raw bytes.

Text source:
    title: / author: / date: / version: / name:   header fields
    = Card title                                  starts a card
    ...lines of the front, verbatim...
    ---
    ...lines of the back...
"""
import argparse
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ti89charset  # noqa: E402

MAGIC = bytes.fromhex("f347bfa7" "01000000")
TRAILER = b"\0STDY\0\xf8"
TAIL_A = bytes.fromhex("500000000001")
TAIL_B = bytes.fromhex("50000000000001")
BLANK_SIDE = bytes.fromhex("0103000050")
MAX_LINES = 7
MAX_WIDTH = 28


def u16(b, i):
    return int.from_bytes(b[i:i + 2], "little")


def le16(n):
    return n.to_bytes(2, "little")


def line_y(i, count):
    """Row of line i; 5 lines start at 7 and 6 lines at 3, as in the Latin stacks."""
    return max(1, 3 + 4 * (6 - count)) + round(8.2 * i)


class Side:
    def __init__(self, lines, tail, raw=None):
        self.lines = lines          # [(y, bytes)]
        self.tail = tail
        self.raw = raw              # bytes of an unparsed (second-format) side

    @classmethod
    def parse(cls, s):
        if s[:3] == b"\x01\x03\0":
            p, lines = 4, []
            try:
                for _ in range(s[3]):
                    if s[p] != 1 or s[p + 2] != 0:
                        raise IndexError
                    end = s.index(b"\0", p + 3)
                    lines.append((s[p + 1], s[p + 3:end]))
                    p = end + 1
                return cls(lines, s[p:])
            except (IndexError, ValueError):
                pass
        return cls([], b"", raw=s)

    def build(self):
        if self.raw is not None:
            return self.raw
        out = bytearray(b"\x01\x03\0" + bytes([len(self.lines)]))
        for y, text in self.lines:
            out += b"\x01" + bytes([y]) + b"\0" + text + b"\0"
        return bytes(out) + self.tail


class Card:
    def __init__(self, title, a, b):
        self.title, self.a, self.b = title, a, b

    def build(self):
        a, b = self.a.build(), self.b.build()
        head = 4 + len(self.title) + 1
        return (le16(head) + le16(head + len(a)) + self.title + b"\0" + a + b)


class Stack:
    def __init__(self, title, author, date, version, cards, flags=b"\0\0\0"):
        self.title, self.author, self.date, self.version = title, author, date, version
        self.cards, self.flags = cards, flags

    @classmethod
    def parse_data(cls, b):
        assert b[:8] == MAGIC and b.endswith(TRAILER), "not a StudyCards stack"
        n = b[0x13]
        offs = [u16(b, 0x14 + 2 * i) for i in range(n)] + [len(b) - len(TRAILER)]
        strs = [b[u16(b, 8 + 2 * i):b.index(b"\0", u16(b, 8 + 2 * i))] for i in range(4)]
        cards = []
        for i in range(n):
            c = b[offs[i]:offs[i + 1]]
            a_off, b_off = u16(c, 0), u16(c, 2)
            cards.append(Card(c[4:a_off - 1], Side.parse(c[a_off:b_off]), Side.parse(c[b_off:])))
        return cls(*[s.decode("latin-1") for s in strs], cards, flags=b[0x10:0x13])

    def build_data(self):
        n = len(self.cards)
        base = 0x14 + 2 * n + 1
        strs = [s.encode("latin-1") + b"\0" for s in (self.title, self.author, self.date, self.version)]
        str_offs, p = [], base
        for s in strs:
            str_offs.append(p)
            p += len(s)
        card_offs, bodies = [], []
        for c in self.cards:
            card_offs.append(p)
            bodies.append(c.build())
            p += len(bodies[-1])
        return (MAGIC + b"".join(le16(o) for o in str_offs) + self.flags + bytes([n])
                + b"".join(le16(o) for o in card_offs) + b"\x02" + b"".join(strs)
                + b"".join(bodies) + TRAILER)

    def to_text(self):
        out = ["title: " + self.title, "author: " + self.author,
               "date: " + self.date, "version: " + self.version, ""]
        cards = self.cards[:-1] if not self.cards[-1].title else self.cards
        for c in cards:
            out.append("= " + ti89charset.decode(c.title))
            for side in (c.a, c.b):
                if side.raw is not None:
                    out.append("# (unparsed second-format side, %d bytes)" % len(side.raw))
                for _, t in side.lines:
                    out.append(ti89charset.decode(t))
                if side is c.a:
                    out.append("---")
            out.append("")
        return "\n".join(out)

    @classmethod
    def from_text(cls, text):
        hdr = {"title": "Untitled", "author": "", "version": "1.0", "name": None,
               "date": datetime.date.today().strftime("%m/%d/%Y")}
        cards, cur = [], None
        for ln, raw in enumerate(text.splitlines(), 1):
            line = raw.rstrip()
            m = re.match(r"(title|author|date|version|name):\s*(.*)$", line)
            if cur is None and m:
                hdr[m.group(1)] = m.group(2)
            elif line.startswith("= "):
                cur = [ti89charset.encode(line[2:]), [], None]
                cards.append(cur)
            elif cur is None:
                if line and not line.startswith("#"):
                    raise ValueError("line %d: text before the first '= card'" % ln)
            elif line.startswith("#"):
                continue
            elif line == "---":
                if cur[2] is not None:
                    raise ValueError("line %d: second '---' in one card" % ln)
                cur[2] = []
            else:
                if len(line) > MAX_WIDTH:
                    sys.stderr.write("warning: line %d is %d chars; the screen fits ~%d\n"
                                     % (ln, len(line), MAX_WIDTH))
                (cur[1] if cur[2] is None else cur[2]).append(ti89charset.encode(line))
        out = []
        for title, front, back in cards:
            if back is None:
                raise ValueError("card %r has no '---' back side" % title)
            sides = []
            for lines, tail in ((front, TAIL_A), (back, TAIL_B)):
                while lines and not lines[-1]:
                    lines.pop()
                if not lines or len(lines) > MAX_LINES:
                    raise ValueError("card %r: a side needs 1-%d lines" % (title, MAX_LINES))
                sides.append(Side([(line_y(i, len(lines)), t) for i, t in enumerate(lines)], tail))
            out.append(Card(title, *sides))
        if not out:
            raise ValueError("no cards")
        # the TI app always ends a stack with an empty card
        out.append(Card(b"", Side([], b"P"), Side([], b"P")))
        s = cls(hdr["title"], hdr["author"], hdr["date"], hdr["version"], out)
        s.name = hdr["name"]
        return s


def wrap_file(data, name, folder="MAIN", when=None, sig=b"**TI89**"):
    when = when or datetime.datetime.now()
    comment = when.strftime("AppVariable file %m/%d/%y, %H:%M").encode()
    hdr = (sig + b"\x01\0" + folder.upper().encode().ljust(8, b"\0")
           + comment.ljust(40, b"\0") + le16(1) + (0x52).to_bytes(4, "little")
           + name.encode().ljust(8, b"\0") + b"\x1c\0\0\0")
    total = 0x58 + len(data) + 2
    hdr += total.to_bytes(4, "little") + b"\xa5\x5a" + b"\0\0\0\0"
    body = len(data).to_bytes(2, "big") + data
    return hdr + body + le16(sum(body) & 0xFFFF)


def unwrap_file(raw):
    n = int.from_bytes(raw[0x56:0x58], "big")
    return raw[0x58:0x58 + n]


def cmd_build(a):
    s = Stack.from_text(open(a.source, encoding="utf-8").read())
    name = (a.name or s.name or re.sub(r"\W", "", os.path.splitext(os.path.basename(a.source))[0]))[:8].lower()
    out = a.output or "main.%s.89y" % name
    open(out, "wb").write(wrap_file(s.build_data(), name))
    print("wrote %s: %d cards (+1 blank), variable MAIN\\%s" % (out, len(s.cards) - 1, name))


def cmd_dump(a):
    sys.stdout.write(Stack.parse_data(unwrap_file(open(a.file, "rb").read())).to_text())


def cmd_verify(a):
    bad = 0
    for f in a.files:
        raw = open(f, "rb").read()
        data = unwrap_file(raw)
        ok = Stack.parse_data(data).build_data() == data
        ok = ok and wrap_file(data, raw[0x40:0x48].rstrip(b"\0").decode(),
                              when=datetime.datetime.strptime(raw[0x23:0x3A].split(b"\0")[0].decode(), "%m/%d/%y, %H:%M")
                              , sig=raw[:8]) == raw
        print("%-6s %s" % ("ok" if ok else "DIFF", f))
        bad += not ok
    return 1 if bad else 0


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("source")
    b.add_argument("-o", "--output")
    b.add_argument("-n", "--name", help="variable name, max 8 chars (default: source file name)")
    b.set_defaults(fn=cmd_build)
    d = sub.add_parser("dump")
    d.add_argument("file")
    d.set_defaults(fn=cmd_dump)
    v = sub.add_parser("verify")
    v.add_argument("files", nargs="+")
    v.set_defaults(fn=cmd_verify)
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(a.fn(a) or 0)


if __name__ == "__main__":
    main()
