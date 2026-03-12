type Word = {
  id: number;
  character?: string;
  pinyin?: string;
  meaning?: string;
  example_sentence?: string;
  example_translation?: string;
  example_pinyin?: string;
};

function seededRandom(seed: number) {
  return () => {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
}

function shuffle<T>(arr: T[], rng: () => number): T[] {
  const out = [...arr];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

function sample<T>(arr: T[], k: number, rng: () => number): T[] {
  const shuffled = shuffle(arr, rng);
  return shuffled.slice(0, Math.min(k, arr.length));
}

function sampleUnique<T>(
  arr: T[],
  exclude: Set<string>,
  k: number,
  rng: () => number,
  fallback: string
): string[] {
  const allowed = arr
    .map((x) => String(x).trim())
    .filter((s) => s && !exclude.has(s));
  const uniq = [...new Set(allowed)];
  const picked = sample(uniq, k, rng);
  while (picked.length < k) {
    picked.push(`${fallback}${picked.length + 1}`);
  }
  return picked;
}

function numbersToToneMarks(pinyin: string): string {
  const toneMap: Record<string, string> = {
    a: "āáǎàa",
    e: "ēéěèe",
    i: "īíǐìi",
    o: "ōóǒòo",
    u: "ūúǔùu",
    v: "ǖǘǚǜü",
  };
  let out = pinyin;
  for (const [vowel, tones] of Object.entries(toneMap)) {
    for (let t = 1; t <= 5; t++) {
      const idx = t === 5 ? 5 : t - 1;
      const marked = tones[idx];
      const re = new RegExp(`${vowel}${t}`, "gi");
      out = out.replace(re, marked);
    }
  }
  return out.replace(/[1-5]/g, "");
}

export function buildThreeSectionTest(
  words: Word[],
  nMeaning: number,
  nListening: number,
  nWriting: number,
  seed: number
): Record<string, unknown>[] {
  const rng = seededRandom(seed);
  const pool = words.filter((w) => w.character);
  if (pool.length < 4) return [];

  const questions: Record<string, unknown>[] = [];

  const meaningPool = sample(pool, nMeaning * 2, rng);
  meaningPool.slice(0, nMeaning).forEach((w) => {
    const meaning = (w.meaning ?? "").trim() || "(meaning missing)";
    const prompt = `${(w.character ?? "").trim()} means?`;
    const exclude = new Set([meaning, ""]);
    const distractors = sampleUnique(
      pool.map((x) => (x.meaning ?? "").trim()),
      exclude,
      3,
      rng,
      "Meaning"
    );
    const options = shuffle([...distractors, meaning], rng);
    const answerIndex = options.indexOf(meaning);
    questions.push({
      section: "meaning",
      prompt,
      options,
      answer_index: answerIndex,
      word_id: w.id,
    });
  });

  const listeningPool = sample(pool, nListening * 2, rng);
  listeningPool.slice(0, nListening).forEach((w) => {
    const char = (w.character ?? "").trim();
    const textToPlay = (w.example_sentence ?? char).trim() || char;
    const displayCn = (w.example_sentence ?? char).trim() || char;
    const displayPy = (w.example_pinyin ?? w.pinyin ?? "").trim();
    const correct = char;
    const distractors = sampleUnique(
      pool.map((x) => (x.character ?? "").trim()),
      new Set([correct, ""]),
      3,
      rng,
      "字"
    );
    const options = shuffle([...distractors, correct], rng);
    const answerIndex = options.indexOf(correct);
    questions.push({
      section: "listening",
      text_to_play: textToPlay,
      display_cn: displayCn,
      display_py: displayPy ? numbersToToneMarks(displayPy) : "",
      options,
      answer_index: answerIndex,
      word_id: w.id,
    });
  });

  const writingPool = sample(pool, nWriting * 2, rng);
  writingPool.slice(0, nWriting).forEach((w) => {
    const meaning = (w.meaning ?? "").trim();
    const char = (w.character ?? "").trim();
    const pinyinRaw = (w.pinyin ?? "").trim();
    if (!meaning || !char) return;
    questions.push({
      section: "writing",
      prompt: meaning,
      correct_pinyin_numbers: pinyinRaw,
      correct_pinyin_display: pinyinRaw ? numbersToToneMarks(pinyinRaw) : "",
      correct_character: char,
      word_id: w.id,
    });
  });

  return shuffle(questions, rng);
}

const DAILY = { meaning: 15, listening: 10, writing: 10 };
const WEEKLY = { meaning: 60, listening: 30, writing: 30 };
const FINAL = { meaning: 100, listening: 50, writing: 50 };

export function buildDailyTest(words: Word[], seed: number): Record<string, unknown>[] {
  return buildThreeSectionTest(
    words,
    DAILY.meaning,
    DAILY.listening,
    DAILY.writing,
    seed
  );
}

export function buildWeeklyTest(words: Word[], seed: number): Record<string, unknown>[] {
  return buildThreeSectionTest(
    words,
    WEEKLY.meaning,
    WEEKLY.listening,
    WEEKLY.writing,
    seed
  );
}

export function buildFinalTest(words: Word[], seed: number): Record<string, unknown>[] {
  return buildThreeSectionTest(
    words,
    FINAL.meaning,
    FINAL.listening,
    FINAL.writing,
    seed
  );
}
