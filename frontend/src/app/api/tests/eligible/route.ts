import { NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { getOrSetStartDate } from "@/lib/db";
import { getCurrentStudyDay, getLastCompletedStudyDay, areFlashcardsDoneForDay, getFlashcardsCompletedCountForDay } from "@/lib/study-progress";
import { dayWordRange, weekWordUpto, WORDS_PER_DAY } from "@/lib/study";
import { supabase } from "@/lib/supabase-server";

const DAILY_TEST_LOCK_MESSAGE = "Complete today's flashcards to unlock the daily test.";

export async function GET(request: Request) {
  let user: { id: number; username: string };
  try {
    user = await requireAuth(request);
  } catch (res) {
    if (res instanceof Response) return res;
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const startDateStr = await getOrSetStartDate(user.id);
  const testType = (new URL(request.url).searchParams.get("test_type") ?? "daily").toLowerCase();

  if (testType === "daily") {
    const currentDay = await getCurrentStudyDay(user.id);
    const flashcardsDone = await areFlashcardsDoneForDay(user.id, currentDay);
    if (!flashcardsDone) {
      const completedInDay = await getFlashcardsCompletedCountForDay(user.id, currentDay);
      return NextResponse.json({
        can_start: false,
        message: DAILY_TEST_LOCK_MESSAGE,
        test_type: "daily",
        current_day: currentDay,
        flashcards_completed: completedInDay,
        words_per_day: WORDS_PER_DAY,
      });
    }
    const [startId, endId] = dayWordRange(currentDay);
    const { data: words } = await supabase
      .from("words")
      .select("id, character, pinyin, meaning, pos")
      .gte("id", startId)
      .lte("id", endId)
      .order("id");
    const { data: exRows } = await supabase
      .from("examples")
      .select("word_id, sentence, pinyin, translation")
      .in("word_id", (words ?? []).map((w) => w.id));
    const exMap = new Map((exRows ?? []).map((e) => [e.word_id, e]));
    const eligible = (words ?? []).map((w) => {
      const ex = exMap.get(w.id);
      return {
        ...w,
        example_sentence: ex?.sentence,
        example_translation: ex?.translation,
        example_pinyin: ex?.pinyin,
      };
    });
    const seed = Math.abs(
      parseInt(startDateStr.replace(/-/g, ""), 10) + user.id * 997
    );
    return NextResponse.json({
      can_start: true,
      eligible,
      seed,
      test_type: "daily",
      current_day: currentDay,
    });
  }

  if (testType === "weekly") {
    const lastCompleted = await getLastCompletedStudyDay(user.id);
    if (lastCompleted < 7) {
      return NextResponse.json({
        can_start: false,
        message:
          "Weekly tests unlock after completing Day 7, Day 14, and Day 20.",
        eligible: [],
      });
    }
    const currentDay = await getCurrentStudyDay(user.id);
    const upto = weekWordUpto(currentDay);
    const { data: words } = await supabase
      .from("words")
      .select("id, character, pinyin, meaning, pos")
      .lte("id", upto)
      .order("id");
    const { data: exRows } = await supabase
      .from("examples")
      .select("word_id, sentence, pinyin, translation")
      .in("word_id", (words ?? []).map((w) => w.id));
    const exMap = new Map((exRows ?? []).map((e) => [e.word_id, e]));
    const eligible = (words ?? []).map((w) => {
      const ex = exMap.get(w.id);
      return {
        ...w,
        example_sentence: ex?.sentence,
        example_translation: ex?.translation,
        example_pinyin: ex?.pinyin,
      };
    });
    const seed =
      parseInt(startDateStr.replace(/-/g, ""), 10) + user.id * 997 + 7;
    return NextResponse.json({
      can_start: true,
      eligible,
      seed,
      test_type: "weekly",
    });
  }

  if (testType === "final") {
    const lastCompleted = await getLastCompletedStudyDay(user.id);
    if (lastCompleted < 20) {
      return NextResponse.json({
        can_start: false,
        message: "Final test unlocks after completing Day 20.",
        eligible: [],
      });
    }
    const { data: words } = await supabase
      .from("words")
      .select("id, character, pinyin, meaning, pos")
      .lte("id", 300)
      .order("id");
    const { data: exRows } = await supabase
      .from("examples")
      .select("word_id, sentence, pinyin, translation")
      .in("word_id", (words ?? []).map((w) => w.id));
    const exMap = new Map((exRows ?? []).map((e) => [e.word_id, e]));
    const eligible = (words ?? []).map((w) => {
      const ex = exMap.get(w.id);
      return {
        ...w,
        example_sentence: ex?.sentence,
        example_translation: ex?.translation,
        example_pinyin: ex?.pinyin,
      };
    });
    const seed =
      parseInt(startDateStr.replace(/-/g, ""), 10) + user.id * 997 + 20;
    return NextResponse.json({
      can_start: true,
      eligible,
      seed,
      test_type: "final",
    });
  }

  return NextResponse.json({
    can_start: false,
    message: "Unknown test type",
    eligible: [],
  });
}
