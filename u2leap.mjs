/**
 * Unicode Telugu -> TL-Hemalatha (iLEAP) converter.
 *
 * Replicates the logic of the legacy VB6 "UNI 2 LEAP" tool, reconstructed from
 * its data files (U2LEAP.dll = glyph table, UNI_DECIM.dll = token table).
 *
 * Glyph table layout (indices into U2LEAP):
 *   1..19    independent vowels + candrabindu/anusvara/visarga
 *   20..559  36 consonants (35 + ksha) x 15 forms, stride 36:
 *            base(20) aa(56) i(92) ii(128) u(164) uu(200) r.(236) rr.(272)
 *            e(308) ee(344) ai(380) o(416) oo(452) au(488) halant(524)
 *   700..734 vattu (subjoined consonant) glyphs, same consonant order
 *   735..777 specials: alt ra-vattu(737), digits, quotes, ksha series(758..772)
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const tables = JSON.parse(
  readFileSync(join(dirname(fileURLToPath(import.meta.url)), 'tables.json'), 'utf8'),
);
const g = (i) => tables.glyphs[String(i)] ?? '';

const CONSONANTS = [...'కఖగఘఙచఛజఝఞటఠడఢణతథదధనపఫబభమయరఱలళవశషసహ'];
const RANK = new Map(CONSONANTS.map((c, i) => [c, i]));

const BASE_BLOCK = 20;
const HALANT_BLOCK = 524;
const VATTU_BASE = 700;
const ALT_RA_VATTU = 737; // 'û' — used for ra in 3-consonant clusters (స్త్ర)

const MATRA_BLOCK = new Map([
  ['ా', 56], ['ి', 92], ['ీ', 128], ['ు', 164], ['ూ', 200],
  ['ృ', 236], ['ౄ', 272], ['ె', 308], ['ే', 344], ['ై', 380],
  ['ొ', 416], ['ో', 452], ['ౌ', 488],
]);

// క్ష ligature series (glyph indices 758..772)
const KSHA_SERIES = new Map([
  ['', 758], ['ా', 759], ['ి', 760], ['ీ', 761], ['ు', 762], ['ూ', 763],
  ['ృ', 764], ['ౄ', 765], ['ె', 766], ['ే', 767], ['ై', 768],
  ['ొ', 769], ['ో', 770], ['ౌ', 771], ['్', 772],
]);

const SINGLES = new Map(
  [...'అఆఇఈఉఊఋౠఎఏఐఒఓఔఌౡఁంః'].map((c, i) => [c, i + 1]),
);

const TELUGU_DIGITS = new Map([...'౦౧౨౩౪౫౬౭౮౯'].map((c, i) => [c, String(i)]));

// From the token table: legacy app's own substitutions for non-Telugu chars.
const MISC = new Map([
  ['₹', g(777)],          // 'Rs'
  ['‘', g(752)], ['’', g(752)],   // -> '
  ['“', g(751)], ['”', g(751)],   // -> "
  ['…', g(776)],          // '...'
  ['​', ''], ['‌', ''], ['‍', ''], // ZW chars consumed
]);

const VIRAMA = '్';
const ZWNJ = '‌';
const ZWJ = '‍';

// Rare letters approximated to their nearest classical equivalent
const APPROX = new Map([['ౘ', 'చ'], ['ౙ', 'జ'], ['ౚ', 'ఱ'], ['ఴ', 'ళ']]);
// Combining marks/signs with no Hemalatha equivalent: dropped like stray matras
const DROP = new Set([...'ౕౖౢౣఀఄ఼ఽ౷']);

const isConsonant = (c) => RANK.has(c);

/**
 * Convert Unicode Telugu text to TL-Hemalatha glyph text.
 * Output chars map 1:1 to the legacy font's byte values via latin-1.
 */
export function convert(input) {
  const text = [...input.normalize('NFC')]
    .filter((c) => !DROP.has(c))
    .map((c) => APPROX.get(c) ?? c);
  let out = '';
  let i = 0;

  while (i < text.length) {
    const c = text[i];

    if (isConsonant(c)) {
      // --- parse one cluster: C (virama C)* (matra | virama-final)? ---
      let base = c;
      const subs = [];
      let j = i + 1;
      let halantFinal = false;
      while (text[j] === VIRAMA) {
        const nxt = text[j + 1];
        if (nxt !== undefined && isConsonant(nxt)) {
          // virama + consonant = subjoined vattu
          subs.push(nxt);
          j += 2;
        } else if (nxt === ZWNJ || nxt === ZWJ) {
          halantFinal = true;
          j += 2;
          break;
        } else {
          halantFinal = true;
          j += 1;
          break;
        }
      }
      let matra = '';
      if (!halantFinal && MATRA_BLOCK.has(text[j])) {
        matra = text[j];
        j += 1;
      }

      // --- emit ---
      if (base === 'క' && subs[0] === 'ష') {
        // క్ష ligature takes the whole matra/halant slot
        out += g(KSHA_SERIES.get(halantFinal ? '్' : matra));
        out += vattus(subs.slice(1));
      } else {
        const r = RANK.get(base);
        if (halantFinal) out += g(HALANT_BLOCK + r);
        else if (matra) out += g(MATRA_BLOCK.get(matra) + r);
        else out += g(BASE_BLOCK + r);
        out += vattus(subs);
      }
      i = j;
      continue;
    }

    if (SINGLES.has(c)) { out += g(SINGLES.get(c)); i += 1; continue; }
    if (TELUGU_DIGITS.has(c)) { out += TELUGU_DIGITS.get(c); i += 1; continue; }
    if (MISC.has(c)) { out += MISC.get(c); i += 1; continue; }
    if (MATRA_BLOCK.has(c) || c === VIRAMA) { i += 1; continue; } // stray matra: drop
    // pass through, but never let a >0xFF char corrupt the byte output
    out += c.codePointAt(0) <= 0xff ? c : '?';
    i += 1;
  }
  return out;
}

function vattus(subs) {
  let s = '';
  for (let k = 0; k < subs.length; k += 1) {
    const c = subs[k];
    if (c === 'ర' && k > 0) s += g(ALT_RA_VATTU); // స్త్ర-style alt ra-vattu
    else s += g(VATTU_BASE + RANK.get(c));
  }
  return s;
}

/** Encode converted text to the raw legacy byte values. */
export function toBytes(hemalatha) {
  return Buffer.from(hemalatha, 'latin1');
}

// --- CLI: node u2leap.mjs "తెలుగు"  (or pipe stdin) ---
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const arg = process.argv[2];
  const input = arg ?? readFileSync(0, 'utf8');
  process.stdout.write(convert(input) + (arg ? '\n' : ''));
}
