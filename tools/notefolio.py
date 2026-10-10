#!/usr/bin/env python3
"""Build and extract TI NoteFolio documents (*.89y, *.9xy, *.v2y).

    python3 tools/notefolio.py extract FILE.89y [-o OUT.txt] [--info]
    python3 tools/notefolio.py build IN.txt -o FILE.89y [--name VAR] [--folder main]
                                     [--calc ti89|ti92p|v200] [--comment TEXT]
                                     [--archived]

In the text form, notes are separated by a line holding only a form feed
(U+000C), and lines end in LF. Text is converted with ti89charset, so the
calculator's Greek letters, arrows and math symbols round-trip as Unicode.

NoteFolio format, reverse engineered from the documents in this repository.
A NoteFolio document is an ordinary single-variable TI-89 file (see the
header layout in ti89-textconv.py) holding one variable of type 0x1C, the
"other" type that Flash apps use for their documents. Offsets below are into
the variable data, which starts at file offset 0x56:

    +0    2   n, BIG-endian: number of bytes that follow, up to the checksum
    +2    4   note count, BIG-endian
    +6    ..  notes, each NUL-terminated; text in the TI-89 character set,
              0x0D ends a line, no other markup
    ...   1   00               \\
    ...   4   "FLIO"           |  standard 0x1C trailer: NUL, the app's type
    ...   1   00               |  string, NUL, then tag 0xF8
    ...   1   F8               /
    ...   2   checksum, LITTLE-endian: sum of every byte from +0 (the length
              included) through the F8 tag, mod 0x10000

So the smallest document, one empty note, is the data 00 0A 00 00 00 01 00
00 46 4C 49 4F 00 F8. TI calls a folio "a database of notes"; a note usually
begins with its heading line, and the documents here refer to them by number
("Note 7:Listing of All Programs"). The variable name at header offset 0x40
is whatever NoteFolio picked, up to 8 characters. StudyCards stacks use the
same 0x1C container with the type string "STDY".
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ti89charset  # noqa: E402

TYPE_STRING = b"FLIO"
TRAILER = b"\0" + TYPE_STRING + b"\0\xF8"
NOTE_BREAK = "\f"

SIGNATURES = {
    "ti89": b"**TI89**",
    "ti92p": b"**TI92P*",
    "v200": b"**V200**",
}


def cstr(raw):
    return raw.split(b"\0", 1)[0].decode("latin-1")


def parse(data):
    """Return (header fields, list of raw note bytes) for a NoteFolio file."""
    if data[:8] not in SIGNATURES.values() or len(data) < 0x5A:
        raise ValueError("not a single-variable TI-89/92+/V200 file")
    if data[0x48] != 0x1C:
        raise ValueError("variable type 0x%02X, expected 0x1C" % data[0x48])

    size = int.from_bytes(data[0x56:0x58], "big")
    end = 0x58 + size
    body = data[0x58:end]
    if len(body) != size or len(data) < end + 2:
        raise ValueError("file truncated")
    if not body.endswith(TRAILER):
        tag = body[body.rfind(b"\0", 0, len(body) - 2) + 1:-2]
        raise ValueError("app type %r, not a NoteFolio document" % tag)

    stored = int.from_bytes(data[end:end + 2], "little")
    actual = sum(data[0x56:end]) & 0xFFFF

    count = int.from_bytes(body[0:4], "big")
    notes = []
    pos = 4
    limit = len(body) - len(TRAILER)
    for _ in range(count):
        nul = body.find(b"\0", pos, limit)
        if nul < 0:
            raise ValueError("note %d is not NUL-terminated" % (len(notes) + 1))
        notes.append(body[pos:nul])
        pos = nul + 1
    if pos != limit:
        raise ValueError("%d unexpected bytes after the last note" % (limit - pos))

    header = {
        "signature": cstr(data[0:8]),
        "folder": cstr(data[0x0A:0x12]),
        "comment": cstr(data[0x12:0x3A]),
        "name": cstr(data[0x40:0x48]),
        "attribute": data[0x49],
        "notes": count,
        "checksum": "%04x (%s)" % (stored, "ok" if stored == actual else
                                   "BAD, computed %04x" % actual),
    }
    return header, notes


def build(notes, name, folder="main", calc="ti89", comment="", archived=False):
    """Return the bytes of a NoteFolio file holding the given raw notes."""
    for i, note in enumerate(notes):
        if b"\0" in note:
            raise ValueError("note %d contains a NUL byte" % (i + 1))

    body = len(notes).to_bytes(4, "big")
    body += b"".join(note + b"\0" for note in notes) + TRAILER
    if len(body) > 0xFFFF:
        raise ValueError("document is %d bytes; a variable holds at most 65535"
                         % len(body))
    var = len(body).to_bytes(2, "big") + body
    var += (sum(var) & 0xFFFF).to_bytes(2, "little")

    def field(text, width):
        raw = text.encode("latin-1")
        if len(raw) > width:
            raise ValueError("%r is longer than %d characters" % (text, width))
        return raw.ljust(width, b"\0")

    attr = 0x03 if archived else 0x00
    header = (SIGNATURES[calc] + b"\x01\x00" + field(folder, 8)
              + field(comment, 40) + b"\x01\x00" + (0x52).to_bytes(4, "little")
              + field(name, 8) + bytes([0x1C, attr, attr, 0x00])
              + (0x56 + len(var)).to_bytes(4, "little") + b"\xA5\x5A"
              + b"\0\0\0\0")
    return header + var


def text_to_notes(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if text.endswith("\n"):
        text = text[:-1]
    chunks = text.split("\n" + NOTE_BREAK + "\n")
    return [ti89charset.encode(chunk) for chunk in chunks]


def notes_to_text(notes):
    sep = "\n" + NOTE_BREAK + "\n"
    return sep.join(ti89charset.decode(note) for note in notes) + "\n"


def cmd_extract(args):
    header, notes = parse(open(args.file, "rb").read())
    out = open(args.output, "w", encoding="utf-8", newline="\n") \
        if args.output else sys.stdout
    if args.info:
        for key, value in header.items():
            sys.stderr.write("# %-10s %s\n" % (key + ":", value))
    out.write(notes_to_text(notes))


def cmd_build(args):
    text = open(args.file, encoding="utf-8").read()
    name = args.name
    if name is None:
        stem = os.path.basename(args.output).split(".")[-2]
        name = stem.lower()[:8]
    if not name or len(name) > 8:
        raise SystemExit("variable name must be 1 to 8 characters: %r" % name)
    data = build(text_to_notes(text), name, args.folder, args.calc,
                 args.comment, args.archived)
    open(args.output, "wb").write(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("extract", help="print a NoteFolio document as text")
    p.add_argument("file")
    p.add_argument("-o", "--output", help="write to this file, not stdout")
    p.add_argument("--info", action="store_true",
                   help="print the header fields to stderr")
    p.set_defaults(func=cmd_extract)

    p = sub.add_parser("build", help="make a NoteFolio document from text")
    p.add_argument("file", help="UTF-8 text; a form-feed line breaks notes")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--name", help="variable name (default: from OUTPUT)")
    p.add_argument("--folder", default="main")
    p.add_argument("--calc", choices=sorted(SIGNATURES), default="ti89")
    p.add_argument("--comment", default="")
    p.add_argument("--archived", action="store_true")
    p.set_defaults(func=cmd_build)

    args = parser.parse_args()
    try:
        args.func(args)
    except ValueError as e:
        raise SystemExit("%s: %s" % (args.file, e))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    main()
