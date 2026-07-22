"""Generate index.html — self-contained static web app for Vercel/any static host.

Inlines tables.json, the TL-Hemalatha font (base64), and a browser port of the
converter. Run after changing tables or conversion logic:  python3 build_web.py
"""
import base64
import json
from pathlib import Path

HERE = Path(__file__).parent
tables = (HERE / "tables.json").read_text(encoding="utf-8")
font_b64 = base64.b64encode((HERE / "TL-TTHemalatha-Normal.ttf").read_bytes()).decode()

CONVERTER_JS = r"""
const GLYPHS = TABLES.glyphs;
const g = (i) => GLYPHS[String(i)] ?? '';

const CONSONANTS = [...'కఖగఘఙచఛజఝఞటఠడఢణతథదధనపఫబభమయరఱలళవశషసహ'];
const RANK = new Map(CONSONANTS.map((c, i) => [c, i]));
const BASE_BLOCK = 20, HALANT_BLOCK = 524, VATTU_BASE = 700, RA_HOOK = 726, ALT_RA_VATTU = 737;
const VATTU_OVERRIDES = new Map([['ట', 727]]);
const MATRA_BLOCK = new Map([
  ['ా',56],['ి',92],['ీ',128],['ు',164],['ూ',200],['ృ',236],['ౄ',272],
  ['ె',308],['ే',344],['ై',380],['ొ',416],['ో',452],['ౌ',488],
]);
const KSHA_SERIES = new Map([
  ['',758],['ా',759],['ి',760],['ీ',761],['ు',762],['ూ',763],['ృ',764],
  ['ౄ',765],['ె',766],['ే',767],['ై',768],['ొ',769],['ో',770],['ౌ',771],['్',772],
]);
const SINGLES = new Map([...'అఆఇఈఉఊఋౠఎఏఐఒఓఔఌౡఁంః'].map((c, i) => [c, i + 1]));
const TELUGU_DIGITS = new Map([...'౦౧౨౩౪౫౬౭౮౯'].map((c, i) => [c, String(i)]));
const MISC = new Map([
  ['₹', g(777)], ['‘', g(752)], ['’', g(752)],
  ['“', g(751)], ['”', g(751)], ['…', g(776)],
  ['​', ''], ['‌', ''], ['‍', ''],
]);
const VIRAMA = '్', ZWNJ = '‌', ZWJ = '‍';
const APPROX = new Map([['ౘ', 'చ'], ['ౙ', 'జ'], ['ౚ', 'ఱ'], ['ఴ', 'ళ']]);
const DROP = new Set([...'ౕౖౢౣఀఄ఼ఽ౷']);

function vattus(subs, afterVattu = false) {
  let s = '';
  for (let k = 0; k < subs.length; k += 1) {
    const c = subs[k];
    if (c === 'ర' && (k > 0 || afterVattu)) s += g(ALT_RA_VATTU);
    else if (VATTU_OVERRIDES.has(c)) s += g(VATTU_OVERRIDES.get(c));
    else s += g(VATTU_BASE + RANK.get(c));
  }
  return s;
}

function convert(input) {
  const text = [...input.normalize('NFC')]
    .filter((c) => !DROP.has(c))
    .map((c) => APPROX.get(c) ?? c);
  let out = '';
  let i = 0;
  while (i < text.length) {
    const c = text[i];
    if (RANK.has(c)) {
      const base = c;
      const subs = [];
      let j = i + 1;
      let halantFinal = false;
      while (text[j] === VIRAMA) {
        const nxt = text[j + 1];
        if (nxt !== undefined && RANK.has(nxt)) { subs.push(nxt); j += 2; }
        else if (nxt === ZWNJ || nxt === ZWJ) { halantFinal = true; j += 2; break; }
        else { halantFinal = true; j += 1; break; }
      }
      let matra = '';
      if (!halantFinal && MATRA_BLOCK.has(text[j])) { matra = text[j]; j += 1; }
      const traPair = subs.length >= 2 && subs[subs.length - 1] === 'ర' && subs[subs.length - 2] === 'త';
      const preRa = subs.includes('ర') && !traPair;
      if (preRa) { out += g(RA_HOOK); subs.splice(subs.indexOf('ర'), 1); }
      if (base === 'క' && subs[0] === 'ష') {
        out += g(KSHA_SERIES.get(halantFinal ? '్' : matra));
        out += vattus(subs.slice(1), true);
      } else {
        const r = RANK.get(base);
        if (halantFinal) out += g(HALANT_BLOCK + r);
        else if (matra) out += g(MATRA_BLOCK.get(matra) + r);
        else out += g(BASE_BLOCK + r);
        out += vattus(subs, preRa);
      }
      i = j;
      continue;
    }
    if (SINGLES.has(c)) out += g(SINGLES.get(c));
    else if (TELUGU_DIGITS.has(c)) out += TELUGU_DIGITS.get(c);
    else if (MISC.has(c)) out += MISC.get(c);
    else if (MATRA_BLOCK.has(c) || c === VIRAMA) { /* stray matra: drop */ }
    else out += c.codePointAt(0) <= 0xff ? c : '?';
    i += 1;
  }
  return out;
}
"""

HTML = """<!DOCTYPE html>
<html lang="te">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Telugu Unicode → TL-Hemalatha (iLEAP)</title>
<style>
  @font-face {{
    font-family: 'TLHemalatha';
    src: url(data:font/ttf;base64,{font_b64}) format('truetype');
  }}
  :root {{
    --bg: #f6f7f9; --panel: #ffffff; --text: #1a1d21; --muted: #5c6570;
    --border: #d9dee4; --accent: #2563eb;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #101418; --panel: #1a2027; --text: #e8eaed; --muted: #9aa4af;
             --border: #2c343d; --accent: #60a5fa; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--text);
         font: 15px/1.5 system-ui, -apple-system, sans-serif; }}
  .wrap {{ max-width: 1100px; margin: 0 auto; padding: 24px 16px 48px; }}
  h1 {{ font-size: 1.35rem; margin: 0 0 4px; }}
  .sub {{ color: var(--muted); margin: 0 0 20px; font-size: .9rem; }}
  .cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  @media (max-width: 760px) {{ .cols {{ grid-template-columns: 1fr; }} }}
  .panel {{ background: var(--panel); border: 1px solid var(--border);
            border-radius: 10px; padding: 14px; }}
  .panel h2 {{ font-size: .95rem; margin: 0 0 10px; }}
  textarea {{ width: 100%; height: 320px; resize: vertical; border: 1px solid var(--border);
              border-radius: 8px; padding: 10px; background: var(--bg); color: var(--text);
              font-size: 1.05rem; line-height: 1.7; }}
  #out {{ font-family: 'TLHemalatha', monospace; font-size: 1.45rem; line-height: 1.6; }}
  .btns {{ margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap; }}
  button {{ border: 1px solid var(--border); background: var(--panel); color: var(--text);
            border-radius: 8px; padding: 7px 14px; cursor: pointer; font-size: .88rem; }}
  button:hover {{ border-color: var(--accent); color: var(--accent); }}
  .stats {{ color: var(--muted); font-size: .85rem; margin-top: 14px; }}
  details {{ margin-top: 10px; }}
  summary {{ cursor: pointer; color: var(--muted); font-size: .85rem; }}
  #raw {{ font-family: ui-monospace, monospace; font-size: .95rem; white-space: pre-wrap;
          word-break: break-all; background: var(--bg); border-radius: 8px; padding: 10px;
          border: 1px solid var(--border); }}
  .note {{ color: var(--muted); font-size: .82rem; margin-top: 20px; }}
  .warn {{ display: none; margin-top: 10px; padding: 10px 12px; border-radius: 8px;
           font-size: .85rem; line-height: 1.5; border: 1px solid #d97706;
           background: rgba(217, 119, 6, .08); color: inherit; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Telugu Unicode → TL-Hemalatha (iLEAP)</h1>
  <p class="sub">Portable replica of the legacy “UNI 2 LEAP” tool. Runs entirely in your browser — nothing is uploaded anywhere.</p>
  <div class="cols">
    <div class="panel">
      <h2>Unicode Telugu (Gautami)</h2>
      <textarea id="inp" placeholder="ఇక్కడ యూనికోడ్ తెలుగు టెక్స్ట్ పేస్ట్ చేయండి…" autofocus></textarea>
      <div class="btns">
        <button id="sample">Load sample</button>
        <button id="clear">Clear</button>
      </div>
    </div>
    <div class="panel">
      <h2>TL-Hemalatha (iLEAP)</h2>
      <textarea id="out" readonly></textarea>
      <div class="btns">
        <button id="copy">Copy</button>
        <button id="download">Download ANSI .txt</button>
      </div>
      <div class="warn" id="warn"></div>
      <details><summary>Raw characters (what actually gets copied)</summary><div id="raw"></div></details>
    </div>
  </div>
  <div class="stats" id="stats"></div>
  <p class="note">The output box renders with the embedded TL-Hemalatha font. The underlying characters are legacy
  font byte values. Use <b>Download ANSI .txt</b> for byte-exact files, or paste the copied text <b>directly</b>
  into the target application (iLEAP/PageMaker). Do not route it through Word or web editors — they silently
  delete the invisible byte-173 piece that వి, వీ, మి and మీ are built from (వినయ్ becomes ఇనయ్).</p>
</div>
<script>
const TABLES = {tables};
{converter_js}
const $ = (id) => document.getElementById(id);
const SAMPLE = 'నమస్కారం! తెలుగు వార్తలు ఆంధ్రప్రభ ముఖ్యమంత్రి ప్రభుత్వం స్త్రీ క్షమించండి ౧౨౩';
function run() {{
  const src = $('inp').value;
  const out = src ? convert(src) : '';
  $('out').value = out;
  $('raw').textContent = out;
  const shy = (out.match(/\\u00AD/g) || []).length;
  $('warn').style.display = shy ? 'block' : 'none';
  if (shy) $('warn').textContent = '\\u26A0 This output contains ' + shy + ' invisible glyph piece(s) '
    + '(byte 173 \\u2014 the left part of \\u0C35\\u0C3F/\\u0C35\\u0C40/\\u0C2E\\u0C3F/\\u0C2E\\u0C40). '
    + 'Word and web editors delete it on paste, so \\u0C35\\u0C3F\\u0C28\\u0C2F\\u0C4D turns into '
    + '\\u0C07\\u0C28\\u0C2F\\u0C4D. Paste directly into iLEAP/PageMaker only, or use Download ANSI .txt.';
  $('stats').textContent = src
    ? `Characters: ${{src.length}} · Words: ${{src.trim().split(/\\s+/).filter(Boolean).length}} · Output characters: ${{out.length}}`
    : '';
}}
$('inp').addEventListener('input', run);
$('sample').onclick = () => {{ $('inp').value = SAMPLE; run(); }};
$('clear').onclick = () => {{ $('inp').value = ''; run(); }};
$('copy').onclick = async () => {{
  await navigator.clipboard.writeText($('out').value);
  $('copy').textContent = 'Copied!'; setTimeout(() => $('copy').textContent = 'Copy', 1200);
}};
$('download').onclick = () => {{
  const s = $('out').value;
  const bytes = new Uint8Array([...s].map((c) => c.charCodeAt(0) & 0xff));
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([bytes], {{ type: 'text/plain' }}));
  a.download = 'converted_hemalatha.txt';
  a.click();
  URL.revokeObjectURL(a.href);
}};
</script>
</body>
</html>
"""

out = HTML.format(font_b64=font_b64, tables=tables, converter_js=CONVERTER_JS)
(HERE / "index.html").write_text(out, encoding="utf-8")
print(f"wrote index.html ({len(out)//1024} KB)")
