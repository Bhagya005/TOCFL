/**
 * Pinyin normalization for writing test validation.
 * Converts tone numbers (lao3shi1) to tone marks (lǎoshī) so we can compare
 * user input (either format) with the correct answer (stored as numbers).
 */

const TONE_MARKS: Record<string, string[]> = {
  a: ["a", "ā", "á", "ǎ", "à"],
  e: ["e", "ē", "é", "ě", "è"],
  i: ["i", "ī", "í", "ǐ", "ì"],
  o: ["o", "ō", "ó", "ǒ", "ò"],
  u: ["u", "ū", "ú", "ǔ", "ù"],
  ü: ["ü", "ǖ", "ǘ", "ǚ", "ǜ"],
};

const VOWELS = new Set("aeiouü");

/** Map tone-mark vowels to base vowels for comparison (strip tones). */
const TONE_MARK_TO_BASE: Record<string, string> = {
  ā: "a", á: "a", ǎ: "a", à: "a",
  ē: "e", é: "e", ě: "e", è: "e",
  ī: "i", í: "i", ǐ: "i", ì: "i",
  ō: "o", ó: "o", ǒ: "o", ò: "o",
  ū: "u", ú: "u", ǔ: "u", ù: "u",
  ǖ: "ü", ǘ: "ü", ǚ: "ü", ǜ: "ü",
};

/**
 * Find which vowel index in the syllable gets the tone mark (pinyin rules).
 * - If 'a' or 'e' exists, mark the first of those.
 * - Else if "ou" exists, mark 'o'.
 * - Else mark the last vowel.
 */
function vowelIndexToMark(s: string): number | null {
  const lower = s.toLowerCase();
  for (const v of ["a", "e"]) {
    const i = lower.indexOf(v);
    if (i !== -1) return i;
  }
  const ou = lower.indexOf("ou");
  if (ou !== -1) return ou;
  let last = -1;
  for (let i = 0; i < lower.length; i++) {
    if (VOWELS.has(lower[i])) last = i;
  }
  return last >= 0 ? last : null;
}

function applyTone(s: string, idx: number, tone: number): string {
  const ch = s[idx].toLowerCase();
  const replacement = TONE_MARKS[ch]?.[tone];
  if (!replacement) return s;
  return s.slice(0, idx) + replacement + s.slice(idx + 1);
}

/**
 * Convert one syllable token (e.g. "lao3", "shi1") to tone marks.
 * Token = letters + optional tone digit 0-5.
 */
function convertSyllableToken(token: string): string {
  const trimmed = token.trim();
  const match = trimmed.match(/^([a-zA-ZüÜ]*)([0-5])?$/);
  if (!match) return trimmed;
  const [, core, toneStr] = match;
  if (!core || !toneStr) return trimmed;
  const tone = parseInt(toneStr, 10);
  if (tone === 0 || tone === 5) return core; // neutral

  let coreNorm = core.toLowerCase().replace(/v/g, "ü");
  const idx = vowelIndexToMark(coreNorm);
  if (idx === null) return core;
  return applyTone(coreNorm, idx, tone);
}

/**
 * Convert numbered pinyin to tone marks (e.g. lao3shi1 → lǎoshī).
 * Splits by syllable boundaries: letter run + digit 1-4 (or 0/5 for neutral).
 * If the string contains "(", only the part before "(" is converted; the rest is reattached as-is (e.g. wa2(wa) → wá(wa)).
 */
function numbersToToneMarksCore(s: string): string {
  if (!s) return "";
  const syllableRegex = /[a-zü]+[1-4]|[a-zü]+[05]?/gi;
  const tokens = s.match(syllableRegex) || [];
  return tokens.map(convertSyllableToken).join("");
}

export function numbersToToneMarks(pinyin: string): string {
  if (!pinyin || typeof pinyin !== "string") return "";
  const s = pinyin.trim().replace(/u:/gi, "ü").replace(/v/gi, "ü");
  const parenIdx = s.indexOf("(");
  if (parenIdx !== -1) {
    const pinyinPart = s.slice(0, parenIdx);
    const parenPart = s.slice(parenIdx);
    return numbersToToneMarksCore(pinyinPart) + parenPart;
  }
  return numbersToToneMarksCore(s);
}

/**
 * Convert tone-mark vowels to base vowels (ā→a, ē→e, etc.) so comparison is tone-agnostic.
 */
export function stripToneMarks(pinyin: string): string {
  if (!pinyin || typeof pinyin !== "string") return "";
  let s = pinyin;
  for (const [accented, base] of Object.entries(TONE_MARK_TO_BASE)) {
    s = s.split(accented).join(base);
  }
  return s;
}

/**
 * Normalize pinyin for comparison:
 * 1. Convert tone numbers in input to tone marks.
 * 2. Strip tone marks (convert to base vowels) on both user and dataset side.
 * 3. Lower case, no spaces, NFC.
 * Correct answer in the report is shown as original dataset pinyin (with tone marks), not this normalized form.
 */
export function normalizePinyinForComparison(input: string): string {
  if (!input || typeof input !== "string") return "";
  const trimmed = input.trim().toLowerCase().replace(/\s/g, "");
  if (!trimmed) return "";
  const withToneMarks = /[1-4]/.test(trimmed)
    ? numbersToToneMarks(trimmed).toLowerCase()
    : trimmed;
  return stripToneMarks(withToneMarks).normalize("NFC");
}
