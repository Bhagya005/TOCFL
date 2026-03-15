import { NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { getOrSetStartDate } from "@/lib/db";
import { getCurrentStudyDay, getLastCompletedStudyDay } from "@/lib/study-progress";
import { dayWordRange, weekWordUpto } from "@/lib/study";
import { buildDailyTest, buildWeeklyTest, buildFinalTest } from "@/lib/test-builder";
import { supabase } from "@/lib/supabase-server";

export async function POST(request: Request) {
  let user: { id: number; username: string };
  try {
    user = await requireAuth(request);
  } catch (res) {
    if (res instanceof Response) return res;
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const body = await request.json().catch(() => ({}));
  const testType = (body?.test_type ?? "daily").toLowerCase();

  const startDateStr = await getOrSetStartDate(user.id);
  const today = new Date().toISOString().slice(0, 10);

  let words: { id: number; character?: string; pinyin?: string; meaning?: string; example_sentence?: string; example_translation?: string; example_pinyin?: string }[];
  let seed: number;
  let dailyStudyDay: number | null = null;

  if (testType === "daily") {
    const currentDay = await getCurrentStudyDay(user.id);
    dailyStudyDay = currentDay;
    const [startId, endId] = dayWordRange(currentDay);
    const { data } = await supabase
      .from("words")
      .select("id, character, pinyin, meaning, pos")
      .gte("id", startId)
      .lte("id", endId)
      .order("id");
    words = data ?? [];
    const { data: exRows } = await supabase
      .from("examples")
      .select("word_id, sentence, pinyin, translation")
      .in("word_id", words.map((w) => w.id));
    const exMap = new Map((exRows ?? []).map((e) => [e.word_id, e]));
    words = words.map((w) => {
      const ex = exMap.get(w.id);
      return { ...w, example_sentence: ex?.sentence, example_translation: ex?.translation, example_pinyin: ex?.pinyin };
    });
    seed = parseInt(startDateStr.replace(/-/g, ""), 10) + user.id * 997;
  } else if (testType === "weekly") {
    const lastCompleted = await getLastCompletedStudyDay(user.id);
    if (lastCompleted < 7) {
      return NextResponse.json(
        { detail: "Weekly tests unlock after completing Day 7." },
        { status: 400 }
      );
    }
    const currentDay = await getCurrentStudyDay(user.id);
    const upto = weekWordUpto(currentDay);
    const { data } = await supabase
      .from("words")
      .select("id, character, pinyin, meaning, pos")
      .lte("id", upto)
      .order("id");
    words = data ?? [];
    const { data: exRows } = await supabase
      .from("examples")
      .select("word_id, sentence, pinyin, translation")
      .in("word_id", words.map((w) => w.id));
    const exMap = new Map((exRows ?? []).map((e) => [e.word_id, e]));
    words = words.map((w) => {
      const ex = exMap.get(w.id);
      return { ...w, example_sentence: ex?.sentence, example_translation: ex?.translation, example_pinyin: ex?.pinyin };
    });
    seed = parseInt(startDateStr.replace(/-/g, ""), 10) + user.id * 997 + 7;
  } else if (testType === "final") {
    const lastCompleted = await getLastCompletedStudyDay(user.id);
    if (lastCompleted < 20) {
      return NextResponse.json(
        { detail: "Final test unlocks after completing Day 20." },
        { status: 400 }
      );
    }
    const { data } = await supabase
      .from("words")
      .select("id, character, pinyin, meaning, pos")
      .lte("id", 300)
      .order("id");
    words = data ?? [];
    const { data: exRows } = await supabase
      .from("examples")
      .select("word_id, sentence, pinyin, translation")
      .in("word_id", words.map((w) => w.id));
    const exMap = new Map((exRows ?? []).map((e) => [e.word_id, e]));
    words = words.map((w) => {
      const ex = exMap.get(w.id);
      return { ...w, example_sentence: ex?.sentence, example_translation: ex?.translation, example_pinyin: ex?.pinyin };
    });
    seed = parseInt(startDateStr.replace(/-/g, ""), 10) + user.id * 997 + 20;
  } else {
    return NextResponse.json(
      { detail: "Unknown test type" },
      { status: 400 }
    );
  }

  const { data: cached } = await supabase
    .from("generated_tests")
    .select("payload_json")
    .eq("user_id", user.id)
    .eq("date", today)
    .eq("test_type", testType)
    .single();

  let questions: Record<string, unknown>[];
  if (cached?.payload_json && Array.isArray((cached.payload_json as { questions?: unknown[] }).questions)) {
    questions = (cached.payload_json as { questions: Record<string, unknown>[] }).questions;
  } else {
    if (testType === "daily") questions = buildDailyTest(words, seed);
    else if (testType === "weekly") questions = buildWeeklyTest(words, seed);
    else questions = buildFinalTest(words, seed);
    const payload: Record<string, unknown> = { questions };
    if (dailyStudyDay != null) payload.study_day = dailyStudyDay;
    await supabase.from("generated_tests").upsert(
      {
        user_id: user.id,
        date: today,
        test_type: testType,
        payload_json: payload,
      },
      { onConflict: "user_id,date,test_type" }
    );
  }

  return NextResponse.json({ questions });
}
