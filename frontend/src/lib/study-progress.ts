/**
 * Completion-based study progression: next session = last_completed_study_day + 1.
 * A study day is marked complete only after both flashcards and daily test are done.
 */

import { supabase } from "./supabase-server";
import { dayWordRange, TOTAL_DAYS, WORDS_PER_DAY } from "./study";

export async function getLastCompletedStudyDay(userId: number): Promise<number> {
  const { data } = await supabase
    .from("user_settings")
    .select("last_completed_study_day")
    .eq("user_id", userId)
    .single();
  const n = data?.last_completed_study_day;
  if (n == null || typeof n !== "number") return 0;
  return Math.max(0, Math.min(TOTAL_DAYS, n));
}

/**
 * Advance last_completed for any day that was fully completed (flashcards + test) on a previous calendar day.
 * Called so we advance "tomorrow" not on submit, allowing retakes the same day.
 */
export async function syncLastCompletedFromPastDays(userId: number): Promise<void> {
  const today = new Date().toISOString().slice(0, 10);
  let last = await getLastCompletedStudyDay(userId);
  let advanced: boolean;
  do {
    advanced = false;
    const day = last + 1;
    if (day > TOTAL_DAYS) break;
    const [flashcardsDone, testDone] = await Promise.all([
      areFlashcardsDoneForDay(userId, day),
      isDailyTestDoneForDay(userId, day),
    ]);
    if (!flashcardsDone || !testDone) break;
    const { data: testRow } = await supabase
      .from("test_results")
      .select("date")
      .eq("user_id", userId)
      .eq("test_type", "daily")
      .eq("study_day", day)
      .order("date", { ascending: false })
      .limit(1)
      .single();
    if (testRow?.date && testRow.date < today) {
      await setLastCompletedStudyDay(userId, day);
      last = day;
      advanced = true;
    }
  } while (advanced);
}

/** Next study day to work on (1–20). Vocabulary for this day is loaded for flashcards and daily test. */
export async function getCurrentStudyDay(userId: number): Promise<number> {
  await syncLastCompletedFromPastDays(userId);
  const last = await getLastCompletedStudyDay(userId);
  return Math.min(TOTAL_DAYS, last + 1);
}

export async function setLastCompletedStudyDay(userId: number, day: number): Promise<void> {
  const value = Math.max(0, Math.min(TOTAL_DAYS, day));
  await supabase
    .from("user_settings")
    .update({ last_completed_study_day: value })
    .eq("user_id", userId);
}

/** Number of words in this day's range that the user has studied (have user_progress). */
export async function getFlashcardsCompletedCountForDay(userId: number, day: number): Promise<number> {
  const [startId, endId] = dayWordRange(day);
  const { data: wordsInRange } = await supabase
    .from("words")
    .select("id")
    .gte("id", startId)
    .lte("id", endId);
  const wordIds = (wordsInRange ?? []).map((r) => r.id);
  if (wordIds.length === 0) return 0;
  const { data: progress } = await supabase
    .from("user_progress")
    .select("word_id")
    .eq("user_id", userId)
    .in("word_id", wordIds);
  return (progress ?? []).length;
}

/** True if user has at least one user_progress row for every word in this day's range. */
export async function areFlashcardsDoneForDay(userId: number, day: number): Promise<boolean> {
  const [startId, endId] = dayWordRange(day);
  const expected = endId - startId + 1;
  const count = await getFlashcardsCompletedCountForDay(userId, day);
  return count >= expected;
}

/** True if user has a daily test result with this study_day. */
export async function isDailyTestDoneForDay(userId: number, day: number): Promise<boolean> {
  const { data, count } = await supabase
    .from("test_results")
    .select("id", { count: "exact", head: true })
    .eq("user_id", userId)
    .eq("test_type", "daily")
    .eq("study_day", day)
    .limit(1);
  return (count ?? 0) > 0;
}

/** If both flashcards and daily test are done for this day, advance last_completed_study_day. */
export async function tryAdvanceStudyDay(userId: number, day: number): Promise<boolean> {
  const [flashcardsDone, testDone] = await Promise.all([
    areFlashcardsDoneForDay(userId, day),
    isDailyTestDoneForDay(userId, day),
  ]);
  if (!flashcardsDone || !testDone) return false;
  const last = await getLastCompletedStudyDay(userId);
  if (day <= last) return false;
  await setLastCompletedStudyDay(userId, day);
  return true;
}

/** Unlocked word ID for display (current study day * 15). */
export function unlockedUptoWordIdForDay(day: number): number {
  return Math.min(300, day * WORDS_PER_DAY);
}
