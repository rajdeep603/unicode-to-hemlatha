"""Unicode Telugu -> TL-Hemalatha (iLEAP) converter.

Python port of u2leap.mjs — same tables.json, same algorithm.
See README.md for the table layout and algorithm details.
"""
import json
import unicodedata
from pathlib import Path

_tables = json.loads((Path(__file__).parent / "tables.json").read_text(encoding="utf-8"))
_GLYPHS = _tables["glyphs"]


def _g(i: int) -> str:
    return _GLYPHS.get(str(i), "")


CONSONANTS = list("కఖగఘఙచఛజఝఞటఠడఢణతథదధనపఫబభమయరఱలళవశషసహ")
RANK = {c: i for i, c in enumerate(CONSONANTS)}

BASE_BLOCK = 20
HALANT_BLOCK = 524
VATTU_BASE = 700
RA_HOOK = 726       # 'ú' — pre-positioned ్ర hook, emitted BEFORE the base glyph
ALT_RA_VATTU = 737  # 'û' — ్ర after another vattu (స్త్ర pattern), appended after
# Glyphs whose vattu is not at VATTU_BASE + rank (confirmed against known-good
# output): ్ట is the plain-cup glyph at 727, not the loop+cup at 710.
VATTU_OVERRIDES = {"ట": 727}

MATRA_BLOCK = {
    "ా": 56, "ి": 92, "ీ": 128, "ు": 164, "ూ": 200,
    "ృ": 236, "ౄ": 272, "ె": 308, "ే": 344, "ై": 380,
    "ొ": 416, "ో": 452, "ౌ": 488,
}

KSHA_SERIES = {
    "": 758, "ా": 759, "ి": 760, "ీ": 761, "ు": 762, "ూ": 763,
    "ృ": 764, "ౄ": 765, "ె": 766, "ే": 767, "ై": 768,
    "ొ": 769, "ో": 770, "ౌ": 771, "్": 772,
}

SINGLES = {c: i + 1 for i, c in enumerate("అఆఇఈఉఊఋౠఎఏఐఒఓఔఌౡఁంః")}
TELUGU_DIGITS = {c: str(i) for i, c in enumerate("౦౧౨౩౪౫౬౭౮౯")}

MISC = {
    "₹": _g(777),                       # 'Rs'
    "‘": _g(752), "’": _g(752),  # ‘ ’ -> '
    "“": _g(751), "”": _g(751),  # “ ” -> "
    "…": _g(776),                  # … -> '...'
    "​": "", "‌": "", "‍": "",
}

VIRAMA = "్"
ZWNJ = "‌"
ZWJ = "‍"

# Rare letters approximated to their nearest classical equivalent
APPROX = {"ౘ": "చ", "ౙ": "జ", "ౚ": "ఱ", "ఴ": "ళ"}
# Combining marks/signs with no Hemalatha equivalent: dropped like stray matras
DROP = set("ౕౖౢౣఀఄ఼ఽ౷")


def _vattus(subs: list, after_vattu: bool = False) -> str:
    out = ""
    for k, c in enumerate(subs):
        if c == "ర" and (k > 0 or after_vattu):
            out += _g(ALT_RA_VATTU)
        elif c in VATTU_OVERRIDES:
            out += _g(VATTU_OVERRIDES[c])
        else:
            out += _g(VATTU_BASE + RANK[c])
    return out


def convert(text: str) -> str:
    """Convert Unicode Telugu to TL-Hemalatha glyph text.

    Output chars map 1:1 to the legacy font's byte values via latin-1.
    """
    chars = [
        APPROX.get(c, c)
        for c in unicodedata.normalize("NFC", text)
        if c not in DROP
    ]
    out = []
    i, n = 0, len(chars)

    while i < n:
        c = chars[i]

        if c in RANK:
            base = c
            subs = []
            j = i + 1
            halant_final = False
            while j < n and chars[j] == VIRAMA:
                nxt = chars[j + 1] if j + 1 < n else None
                if nxt is not None and nxt in RANK:
                    subs.append(nxt)
                    j += 2
                elif nxt in (ZWNJ, ZWJ):
                    halant_final = True
                    j += 2
                    break
                else:
                    halant_final = True
                    j += 1
                    break
            matra = ""
            if not halant_final and j < n and chars[j] in MATRA_BLOCK:
                matra = chars[j]
                j += 1

            # ్ర in a cluster: pre-positioned hook ú before the whole cluster
            # glyph (ప్రై = ú\|ms, స్ట్రీ = ú{qsí). Exception: the ్త్ర family
            # (స్త్ర/స్త్రీ) keeps the legacy post-form ò+û per tokens 133/193.
            tra_pair = len(subs) >= 2 and subs[-1] == "ర" and subs[-2] == "త"
            pre_ra = "ర" in subs and not tra_pair
            if pre_ra:
                out.append(_g(RA_HOOK))
                subs = list(subs)
                subs.remove("ర")
            if base == "క" and subs and subs[0] == "ష":
                out.append(_g(KSHA_SERIES["్" if halant_final else matra]))
                out.append(_vattus(subs[1:], after_vattu=True))
            else:
                r = RANK[base]
                if halant_final:
                    out.append(_g(HALANT_BLOCK + r))
                elif matra:
                    out.append(_g(MATRA_BLOCK[matra] + r))
                else:
                    out.append(_g(BASE_BLOCK + r))
                out.append(_vattus(subs, after_vattu=pre_ra))
            i = j
            continue

        if c in SINGLES:
            out.append(_g(SINGLES[c]))
        elif c in TELUGU_DIGITS:
            out.append(TELUGU_DIGITS[c])
        elif c in MISC:
            out.append(MISC[c])
        elif c in MATRA_BLOCK or c == VIRAMA:
            pass  # stray matra: drop
        else:
            # pass through, but never let a >0xFF char corrupt the byte output
            out.append(c if ord(c) <= 0xFF else "?")
        i += 1

    return "".join(out)


def to_bytes(hemalatha: str) -> bytes:
    """Raw legacy byte values (latin-1)."""
    return hemalatha.encode("latin-1")
