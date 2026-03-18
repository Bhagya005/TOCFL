"use client";

/**
 * Applies a tone (1–4) or ü to the last vowel in the given text.
 * Only modifies: a, e, i, o, u, ü (and their accented forms).
 * If the last character is not a vowel, searches backwards for the nearest vowel.
 */

const TONE_MARKS: Record<string, string[]> = {
  a: ["a", "ā", "á", "ǎ", "à"],
  e: ["e", "ē", "é", "ě", "è"],
  i: ["i", "ī", "í", "ǐ", "ì"],
  o: ["o", "ō", "ó", "ǒ", "ò"],
  u: ["u", "ū", "ú", "ǔ", "ù"],
  ü: ["ü", "ǖ", "ǘ", "ǚ", "ǜ"],
};

const VOWEL_CHARS = new Set([
  "a", "e", "i", "o", "u", "ü",
  "ā", "á", "ǎ", "à", "ē", "é", "ě", "è",
  "ī", "í", "ǐ", "ì", "ō", "ó", "ǒ", "ò",
  "ū", "ú", "ǔ", "ù", "ǖ", "ǘ", "ǚ", "ǜ",
]);

const ACCENTED_TO_BASE: Record<string, string> = {
  ā: "a", á: "a", ǎ: "a", à: "a",
  ē: "e", é: "e", ě: "e", è: "e",
  ī: "i", í: "i", ǐ: "i", ì: "i",
  ō: "o", ó: "o", ǒ: "o", ò: "o",
  ū: "u", ú: "u", ǔ: "u", ù: "u",
  ǖ: "ü", ǘ: "ü", ǚ: "ü", ǜ: "ü",
};

function getBaseVowel(ch: string): string | null {
  const lower = ch.toLowerCase();
  if (TONE_MARKS[lower]) return lower;
  return ACCENTED_TO_BASE[lower] ?? null;
}

function getToneIndex(ch: string): number {
  const lower = ch.toLowerCase();
  for (const [base, variants] of Object.entries(TONE_MARKS)) {
    const idx = variants.indexOf(lower);
    if (idx >= 0) return idx;
  }
  return 0;
}

/** Find the index of the last vowel in text (search backwards). */
function lastVowelIndex(text: string): number {
  for (let i = text.length - 1; i >= 0; i--) {
    if (VOWEL_CHARS.has(text[i])) return i;
  }
  return -1;
}

export type ToneButton = 1 | 2 | 3 | 4 | "ü";

export function applyToneToLastVowel(text: string, tone: ToneButton): string {
  if (!text) return text;
  const idx = lastVowelIndex(text);
  if (idx === -1) return text;

  const ch = text[idx];
  const base = getBaseVowel(ch);
  if (!base) return text;

  let replacement: string;
  if (tone === "ü") {
    if (base !== "u") return text;
    const toneIdx = getToneIndex(ch);
    replacement = TONE_MARKS["ü"][toneIdx];
  } else {
    replacement = TONE_MARKS[base]?.[tone as number] ?? ch;
  }

  return text.slice(0, idx) + replacement + text.slice(idx + 1);
}

type ToneKeyboardProps = {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
};

const TONE_BUTTONS: { label: string; tone: ToneButton }[] = [
  { label: "ā", tone: 1 },
  { label: "á", tone: 2 },
  { label: "ǎ", tone: 3 },
  { label: "à", tone: 4 },
  { label: "ü", tone: "ü" },
];

export default function ToneKeyboard({ value, onChange, disabled }: ToneKeyboardProps) {
  const handleTone = (tone: ToneButton) => {
    onChange(applyToneToLastVowel(value, tone));
  };

  return (
    <div className="flex flex-wrap items-center gap-2 mt-2">
      <span className="text-sm text-slate-500 mr-1">Tones:</span>
      {TONE_BUTTONS.map(({ label, tone }) => (
        <button
          key={label}
          type="button"
          disabled={disabled}
          onClick={() => handleTone(tone)}
          className="min-w-[2.25rem] h-9 px-2 rounded-button border border-slate-600 bg-slate-700/50 text-slate-200 font-medium text-lg hover:bg-slate-600 hover:border-slate-500 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-amber-500/50"
          aria-label={`Tone ${tone === "ü" ? "ü" : tone}`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
