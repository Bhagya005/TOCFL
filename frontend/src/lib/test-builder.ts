
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
      display_py: displayPy,
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
      correct_pinyin: pinyinRaw,
      correct_character: char,
      word_id: w.id,
    });
  });

  return shuffle(questions, rng);
}

/** Ratio Meaning : Listening : Writing. Daily = 3:2:2, Weekly/Final = 2:1:1 */
const RATIOS = {
  daily: [3, 2, 2] as const,
  weekly: [2, 1, 1] as const,
  final: [2, 1, 1] as const,
} as const;

export const TEST_LIMITS = {
  daily: { max: 35, default: 35 },
  weekly: { max: 150, default: 120 },
  final: { max: 300, default: 200 },
} as const;

export type TestType = keyof typeof RATIOS;

/**
 * Split total question count by section ratio. Distributes remainder in order: Meaning → Listening → Writing.
 */
export function getSectionCounts(
  total: number,
  testType: TestType
): { nMeaning: number; nListening: number; nWriting: number } {
  const [a, b, c] = RATIOS[testType];
  const parts = a + b + c;
  let nMeaning = Math.floor((total * a) / parts);
  let nListening = Math.floor((total * b) / parts);
  let nWriting = Math.floor((total * c) / parts);
  let remainder = total - (nMeaning + nListening + nWriting);
  if (remainder > 0) {
    nMeaning += 1;
    remainder -= 1;
  }
  if (remainder > 0) {
    nListening += 1;
    remainder -= 1;
  }
  if (remainder > 0) {
    nWriting += 1;
  }
  return { nMeaning, nListening, nWriting };
}

export function buildTestWithCount(
  words: Word[],
  seed: number,
  total: number,
  testType: TestType
): Record<string, unknown>[] {
  const { nMeaning, nListening, nWriting } = getSectionCounts(total, testType);
  return buildThreeSectionTest(words, nMeaning, nListening, nWriting, seed);
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
