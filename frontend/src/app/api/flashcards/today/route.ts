import { NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { getCurrentStudyDay } from "@/lib/study-progress";
import { dayWordRange, WORDS_PER_DAY } from "@/lib/study";
import { supabase } from "@/lib/supabase-server";

export async function GET(request: Request) {
  let user: { id: number; username: string };
  try {
    user = await requireAuth(request);
  } catch (res) {
    if (res instanceof Response) return res;
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const dayParam = searchParams.get("day");
  // Use next study day when day is omitted (same as dashboard)
  let day: number;
  if (dayParam == null || dayParam === "") {
    day = await getCurrentStudyDay(user.id);
  } else {
    day = Math.max(1, Math.min(20, parseInt(dayParam, 10) || 1));
  }
  const [startId, endId] = dayWordRange(day);

  const now = new Date().toISOString().slice(0, 19).replace("T", " ");

  const { data: wordsData } = await supabase
    .from("words")
    .select("id, character, pinyin, meaning, pos")
    .gte("id", startId)
    .lte("id", endId)
    .order("id");

  const { data: wpData } = await supabase
    .from("word_progress")
    .select("word_id, next_review, difficulty_score");
  const wpMap = new Map((wpData ?? []).map((r) => [r.word_id, r]));

  const { data: upData } = await supabase
    .from("user_progress")
    .select("word_id, mistakes, correct")
    .eq("user_id", user.id);
  const upMap = new Map((upData ?? []).map((r) => [r.word_id, r]));

  const weakWordIds = new Set<number>();
  const dueWordIds = new Set<number>();
  const newWordIds = new Set<number>();

  (wordsData ?? []).forEach((w) => {
    const wid = w.id;
    const wp = wpMap.get(wid);
    const up = upMap.get(wid);
    const isWeak =
      !wp ||
      (wp.difficulty_score === 0) ||
      (Number(up?.mistakes ?? 0) > Number(up?.correct ?? 0));
    if (isWeak) weakWordIds.add(wid);
    if (wp?.next_review && wp.next_review <= now) dueWordIds.add(wid);
    // New = this user hasn't studied this word yet (no user_progress), so they always have something to learn
    if (!up) newWordIds.add(wid);
  });

  const due = (wordsData ?? []).filter((w) => dueWordIds.has(w.id)).sort((a, b) => a.id - b.id);
  const newW = (wordsData ?? []).filter((w) => newWordIds.has(w.id)).sort((a, b) => a.id - b.id);

  // Single source of truth: 1) due for review first, 2) fill remaining slots with new words (cap at WORDS_PER_DAY)
  type WordRow = { id: number; character: string | null; pinyin: string | null; meaning: string | null; pos: string | null };
  const sessionRows: WordRow[] = [...due, ...newW].slice(0, WORDS_PER_DAY);

  const wordDicts = sessionRows.map((r) => ({
    id: r.id,
    character: r.character,
    pinyin: r.pinyin ?? "",
    meaning: r.meaning ?? "",
  }));

  const ids = wordDicts.map((w) => w.id);
  const { data: exRows } = await supabase
    .from("examples")
    .select("word_id, sentence, pinyin, translation")
    .in("word_id", ids);

  const exMap = new Map((exRows ?? []).map((e) => [e.word_id, e]));
  wordDicts.forEach((w) => {
    const ex = exMap.get(w.id);
    if (ex) {
      (w as Record<string, unknown>).example_sentence = ex.sentence;
      (w as Record<string, unknown>).example_translation = ex.translation;
      (w as Record<string, unknown>).example_pinyin = ex.pinyin;
    }
  });

  const totalWeak = weakWordIds.size;
  const totalDue = dueWordIds.size;
  const totalNew = newWordIds.size;

  return NextResponse.json({
    words: wordDicts,
    count: wordDicts.length,
    total_due: totalDue,
    total_new: totalNew,
    total_weak: totalWeak,
    start_id: startId,
    end_id: endId,
    day,
  });
}
