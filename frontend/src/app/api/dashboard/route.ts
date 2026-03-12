import { NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { getOrSetStartDate } from "@/lib/db";
import { computeStudyPlan } from "@/lib/study";
import { supabase } from "@/lib/supabase-server";

export async function GET(request: Request) {
  let user: { id: number; username: string };
  try {
    user = await requireAuth(request);
  } catch (res) {
    if (res instanceof Response) return res;
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }
  const startDateStr = await getOrSetStartDate(user.id);
  const startDate = new Date(startDateStr);
  const plan = computeStudyPlan(startDate);

  const { data: progressRows } = await supabase
    .from("user_progress")
    .select("word_id, known, mistakes, attempts, correct")
    .eq("user_id", user.id);

  const knownWords = (progressRows ?? []).filter((r) => r.known === 1).length;
  const attempts = (progressRows ?? []).reduce((s, r) => s + Number(r.attempts ?? 0), 0);
  const correct = (progressRows ?? []).reduce((s, r) => s + Number(r.correct ?? 0), 0);
  const accuracy = attempts > 0 ? correct / attempts : null;

  const { data: testRows } = await supabase
    .from("test_results")
    .select("date, test_type, score, total")
    .eq("user_id", user.id)
    .order("date", { ascending: true });

  const testList = (testRows ?? []).map((r) => {
    const d = new Date(startDate);
    const t = new Date(r.date);
    const dayIndex = Math.floor((t.getTime() - d.getTime()) / (24 * 60 * 60 * 1000)) + 1;
    return {
      date: r.date,
      test_type: r.test_type,
      score: r.score,
      total: r.total,
      day_index: dayIndex,
    };
  });

  return NextResponse.json({
    plan: {
      current_day: plan.currentDay,
      unlocked_upto_word_id: plan.unlockedUptoWordId,
    },
    start_date: startDateStr,
    summary: {
      known_words: knownWords,
      attempts,
      correct,
      accuracy,
    },
    test_results: testList,
  });
}
