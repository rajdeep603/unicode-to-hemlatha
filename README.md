# Unicode Telugu → TL-Hemalatha (iLEAP) Converter

Portable replica of the legacy VB6 **"UNI 2 LEAP"** tool. No Windows, VB6, or
legacy-machine dependency. The engine exists twice with byte-identical output:
Python (`u2leap.py`, used by the web UI) and Node.js (`u2leap.mjs`).

## Quick start — Streamlit web UI

```bash
git clone git@github.com:rajdeep603/unicode-to-hemlatha.git
cd unicode-to-hemlatha

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

streamlit run app.py
```

Then open http://localhost:8501 — paste Unicode Telugu (Gautami) on the left,
TL-Hemalatha appears on the right, rendered with the embedded Hemalatha font.
Use **Download as ANSI .txt** for byte-exact files for legacy iLEAP/PageMaker
workflows.

To run on a different port: `streamlit run app.py --server.port 8080`.
To serve on your LAN: add `--server.address 0.0.0.0`.

## Key discovery: no decompiling was needed

The legacy app's "DLLs" in `Uni_to Leap_13/tel converT/` are **plain text data
files** with fake `.dll` extensions:

| File | Actually is |
|---|---|
| `U2LEAP.dll` | CSV: glyph index → Hemalatha output byte string (637 entries) |
| `UNI_DECIM.dll` | CSV: token index → Unicode decimal codepoint sequence (222 entries) |
| `UNI2LPD.dll`, `rev*.dll` | Copy-protection / USB-dongle serial data (`USB_SNO.exe`) — irrelevant to conversion |

The EXE (VB6 **p-code**, project `U2L.vbp`) reads `C:\TEL CONVERT\UNI_DECIM.dll`
and `C:\TEL CONVERT\U2LEAP.dll` at runtime. The installer CAB contains only
standard VB6 runtime DLLs — no other data anywhere.

## Glyph table layout (U2LEAP indices)

- **1–19** — independent vowels అ…ౡ, then ఁ ం ః
- **20–559** — 36 consonants (35 + క్ష) × 15 forms, stride 36:
  base 20, ా 56, ి 92, ీ 128, ు 164, ూ 200, ృ 236, ౄ 272,
  ె 308, ే 344, ై 380, ొ 416, ో 452, ౌ 488, halant (pollu) 524.
  Glyph for consonant rank *r* with form *F* = `blockStart(F) + r`.
- **700–734** — vattu (subjoined consonant) glyphs, same consonant order
- **735–777** — specials: alt ra-vattu `û` (737), ASCII digits (739–748),
  quotes, క్ష ligature series (758–772), ₹→`Rs` (777), ellipsis (776)

## Conversion algorithm

1. NFC-normalize input; walk codepoints.
2. Parse consonant clusters: `C (్ C)* (matra | ్-final)?` (ZWNJ/ZWJ after ్
   forces the halant form and breaks the cluster).
3. Emit the **base consonant combined with the matra** (block arithmetic
   above), then append one **vattu glyph per subjoined consonant** — this is
   the "reordering": in Unicode the matra follows the last consonant, in
   Hemalatha it fuses with the first.
4. Specials: క+్+ష uses the 758–772 ligature series for base+matra;
   ర as the 2nd+ subjoined consonant uses alt ra-vattu `û` (737) instead of
   the regular `ú` (726) — inferred from the precomposed స్త్ర entry.
5. Independent vowels/signs, Telugu digits (→ ASCII), punctuation and smart
   quotes map per the token table; other characters pass through.

**Self-validation:** the algorithm's output for స్త్ర, క్ష, క్షా, క్షి, క్షో, క్ష్
is byte-identical to the table's own precomposed entries (6/6).

## Usage

```bash
node u2leap.mjs "తెలుగు వార్తలు"     # → ¾»½ÌÁVgRiV ªyLRiòÌÁV
echo "నమస్కారం" | node u2leap.mjs    # stdin works too
```

```js
import { convert, toBytes } from './u2leap.mjs';
convert('నమస్కారం');       // string, chars = font byte values via latin-1
toBytes(convert('...'));    // raw legacy bytes (for files/clipboard interop)
```

## Verification against the legacy app (TODO — needs the Win7 box or a VM)

Run each line of `verify_corpus.txt` through the real UNI 2 LEAP app and diff
byte-for-byte against `verify_expected.txt` (latin-1/ANSI encoded). Points of
uncertainty to confirm:

1. ~~ra-vattu choice~~ **RESOLVED** against known-good legacy output: ్ర as the
   first subjoined consonant emits the pre-positioned hook `ú` (726) BEFORE
   the whole base glyph (ప్రై = `ú\|ms`); ్ర after another vattu appends `û`
   (737) after (స్త్ర = `xqsòû`).
2. **Matra placement** with vattu + matra (మార్కు → `ª«sWLRiVä`, i.e. base
   takes the matra) — standard split-font convention, confirm visually.
3. Smart quotes “ ” ‘ ’, en-dash, ellipsis — token table maps exist but the
   exact glyph choices (751/752 vs 756/757) are inferred.
4. Stray/lone matras (malformed input) are dropped; legacy behavior unknown.

The legacy EXE remains useful **only** as this regression oracle.
