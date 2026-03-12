import { NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { supabase } from "@/lib/supabase-server";

export async function GET(request: Request) {
  let user: { id: number; username: string };
  try {
    user = await requireAuth(request);
  } catch (res) {
    if (res instanceof Response) return res;
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const [{ data: words }, { data: progressRows }, { data: weakRows }] = await Promise.all([
    supabase.from("words").select("id, character, pinyin, meaning, pos").order("id"),
    supabase.from("user_progress").select("word_id, known, mistakes, attempts, correct").eq("user_id", user.id),
    supabase.from("weak_words").select("word_id").eq("user_id", user.id),
  ]);

  const progressMap = new Map(
    (progressRows ?? []).map((r) => [
      r.word_id,
      {
        known: r.known,
        mistakes: r.mistakes,
        attempts: r.attempts,
        correct: r.correct,
      },
    ])
  );
  const weakSet = new Set((weakRows ?? []).map((r) => r.word_id));

  const result = (words ?? []).map((w) => {
    const p = progressMap.get(w.id) ?? { known: 0, mistakes: 0, attempts: 0, correct: 0 };
    return {
      id: w.id,
      character: w.character,
      pinyin: w.pinyin,
      meaning: w.meaning,
      pos: w.pos,
      learned: Number(p.known) === 1,
      weak: weakSet.has(w.id),
      mistakes: Number(p.mistakes ?? 0),
      attempts: Number(p.attempts ?? 0),
    };
  });

  return NextResponse.json({ words: result });
}
