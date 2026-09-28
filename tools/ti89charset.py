"""TI-89 / TI-92 Plus character set <-> Unicode.

Taken from TiLP's libticonv (charset.cc, ti9x_charset). 0x0D (carriage
return) is the line separator in program text and maps to "\\n".
"""

_CONTROL = {
    0x0B: "⤴", 0x0E: "⚓", 0x0F: "✓", 0x10: "◾",
    0x11: "◂", 0x12: "▸", 0x13: "▴", 0x14: "▾",
    0x15: "←", 0x16: "→",  # 0x16 is the store arrow
    0x17: "↑", 0x18: "↓", 0x19: "◀", 0x1A: "▶",
    0x1B: "⬆", 0x1C: "∪", 0x1D: "∩", 0x1E: "⊂",
    0x1F: "∈",
}

_HIGH = [
    # 0x80-0x94: Greek
    "α", "β", "Γ", "γ", "Δ", "δ", "ε", "ζ", "θ", "λ", "ξ", "Π", "π", "ρ",
    "Σ", "σ", "τ", "φ", "ψ", "Ω", "ω",
    # 0x95-0x9F: math symbols
    "\U0001d5a4", "ℯ", "\U0001d48a", "ʳ", "⊺", "x̅",
    "y̅", "≤", "≠", "≥", "∠",
]

_LATIN1_OVERRIDES = {
    0xA0: "…", 0xA8: "√", 0xAD: "−",  # 0xAD: negative sign
    0xB8: "⁺", 0xBC: "∂", 0xBD: "∫", 0xBE: "∞",
}

TO_UNICODE = []
for _b in range(256):
    if _b == 0x0D:
        TO_UNICODE.append("\n")
    elif _b in _CONTROL:
        TO_UNICODE.append(_CONTROL[_b])
    elif _b < 0x20:
        TO_UNICODE.append("\\x%02x" % _b)
    elif _b == 0x7F:
        TO_UNICODE.append("◆")
    elif 0x80 <= _b <= 0x9F:
        TO_UNICODE.append(_HIGH[_b - 0x80])
    elif _b in _LATIN1_OVERRIDES:
        TO_UNICODE.append(_LATIN1_OVERRIDES[_b])
    else:
        TO_UNICODE.append(chr(_b))

_FROM_UNICODE = {s: b for b, s in enumerate(TO_UNICODE) if not s.startswith("\\x")}


def decode(raw):
    return "".join(TO_UNICODE[b] for b in raw)


def encode(text):
    """Unicode text (LF line endings) -> TI bytes (CR line endings)."""
    out = bytearray()
    i = 0
    while i < len(text):
        two = text[i:i + 2]
        if len(two) == 2 and two in _FROM_UNICODE:  # x̄, ȳ
            out.append(_FROM_UNICODE[two])
            i += 2
            continue
        ch = text[i]
        if ch not in _FROM_UNICODE:
            raise ValueError("no TI-89 character for %r at offset %d" % (ch, i))
        out.append(_FROM_UNICODE[ch])
        i += 1
    return bytes(out)
