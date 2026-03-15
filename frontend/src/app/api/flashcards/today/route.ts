import { NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { getOrSetStartDate } from "@/lib/db";
import { getCurrentStudyDay } from "@/lib/study-progress";
import { dayWordRange, WORDS_PER_DAY } from "@/lib/study";
import { supabase } from "@/lib/supabase-server";

function toWordId(v: unknown): number {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
}

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
  let day: number;
  if (dayParam == null || dayParam === "") {
    await getOrSetStartDate(user.id);
    day = await getCurrentStudyDay(user.id);
  } else {
    day = Math.max(1, Math.min(20, parseInt(dayParam, 10) || 1));
  }
  const [startId, endId] = dayWordRange(day);

  const now = new Date().toISOString().slice(0, 19).replace("T", " ");

  const { data: wordsData, error: wordsError } = await supabase
    .from("words")
    .select("id, character, pinyin, meaning, pos")
    .gte("id", startId)
    .lte("id", endId)
    .order("id");

  if (wordsError) {
    return NextResponse.json(
      { detail: "Failed to load words", error: wordsError.message },
      { status: 500 }
    );
  }

  const wpRows = await supabase
    .from("word_progress")
    .select("word_id, next_review, difficulty_score");
  const wpMap = new Map(
    (wpRows.data ?? []).map((r) => [toWordId(r.word_id), r])
  );

  const upRows = await supabase
    .from("user_progress")
    .select("word_id, mistakes, correct")
    .eq("user_id", user.id);
  const upMap = new Map(
    (upRows.data ?? []).map((r) => [toWordId(r.word_id), r])
  );

  const weakWordIds = new Set<number>();
  const dueWordIds = new Set<number>();
  const newWordIds = new Set<number>();

  (wordsData ?? []).forEach((w) => {
    const wid = toWordId(w.id);
    const wp = wpMap.get(wid);
    const up = upMap.get(wid);
    const isWeak =
      !wp ||
      (wp.difficulty_score === 0) ||
      (Number(up?.mistakes ?? 0) > Number(up?.correct ?? 0));
    if (isWeak) weakWordIds.add(wid);
    if (wp?.next_review && wp.next_review <= now) dueWordIds.add(wid);
    if (!up) newWordIds.add(wid);
  });

  const due = (wordsData ?? []).filter((w) => dueWordIds.has(toWordId(w.id))).sort((a, b) => toWordId(a.id) - toWordId(b.id));
  const newW = (wordsData ?? []).filter((w) => newWordIds.has(toWordId(w.id))).sort((a, b) => toWordId(a.id) - toWordId(b.id));

  // Single source of truth: 1) due for review first, 2) fill remaining slots with new words (cap at WORDS_PER_DAY)
  type WordRow = { id: number; character: string | null; pinyin: string | null; meaning: string | null; pos: string | null };
  const sessionRows: WordRow[] = [...due, ...newW].slice(0, WORDS_PER_DAY);

  const wordDicts = sessionRows.map((r) => ({
    id: toWordId(r.id),
    character: r.character,
    pinyin: r.pinyin ?? "",
    meaning: r.meaning ?? "",
  }));

  const ids = wordDicts.map((w) => w.id);
  const { data: exRows } = await supabase
    .from("examples")
    .select("word_id, sentence, pinyin, translation")
    .in("word_id", ids);

  const exMap = new Map((exRows ?? []).map((e) => [toWordId(e.word_id), e]));
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
  const count = wordDicts.length;
  const wordsInRange = wordsData?.length ?? 0;

  return NextResponse.json({
    words: wordDicts,
    count,
    total_due: totalDue,
    total_new: totalNew,
    total_weak: totalWeak,
    start_id: startId,
    end_id: endId,
    day,
    ...(count === 0 && wordsInRange === 0
      ? { message: "No words in database for this range. Seed the words table with vocabulary (ids 1–300) in Supabase." }
      : {}),
  });
}
