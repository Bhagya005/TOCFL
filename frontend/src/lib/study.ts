const WORDS_PER_DAY = 15;
const TOTAL_DAYS = 20;
const TOTAL_WORDS = 300;

export function computeStudyPlan(
  startDate: Date,
  today: Date = new Date()
): { currentDay: number; unlockedUptoWordId: number } {
  const start = new Date(startDate);
  start.setHours(0, 0, 0, 0);
  const t = new Date(today);
  t.setHours(0, 0, 0, 0);
  const deltaDays = Math.floor((t.getTime() - start.getTime()) / (24 * 60 * 60 * 1000));
  const currentDay = Math.max(1, Math.min(TOTAL_DAYS, deltaDays + 1));
  const unlockedUptoWordId = Math.min(TOTAL_WORDS, currentDay * WORDS_PER_DAY);
  return { currentDay, unlockedUptoWordId };
}

export function dayWordRange(day: number): [number, number] {
  const d = Math.max(1, Math.min(TOTAL_DAYS, day));
  const startId = (d - 1) * WORDS_PER_DAY + 1;
  const endId = Math.min(TOTAL_WORDS, d * WORDS_PER_DAY);
  return [startId, endId];
}

export function weekWordUpto(day: number): number {
  if (day >= 20) return 300;
  if (day >= 14) return 210;
  if (day >= 7) return 105;
  return Math.min(300, day * WORDS_PER_DAY);
}

export { TOTAL_WORDS, WORDS_PER_DAY, TOTAL_DAYS };
