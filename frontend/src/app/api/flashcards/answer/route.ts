import { NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { supabase } from "@/lib/supabase-server";

function nextReview(score: number): string {
  const now = new Date();
  let days = 1;
  if (score <= 0) days = 1;
  else if (score === 1) days = 3;
  else if (score === 2) days = 7;
  else days = 14;
  const next = new Date(now);
  next.setDate(next.getDate() + days);
  return next.toISOString().slice(0, 19).replace("T", " ");
}

export async function POST(request: Request) {
  let user: { id: number; username: string };
  try {
    user = await requireAuth(request);
  } catch (res) {
    if (res instanceof Response) return res;
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const body = await request.json();
  const wordId = Number(body?.word_id);
  const knew = Boolean(body?.knew);
  if (!wordId) {
    return NextResponse.json({ detail: "word_id required" }, { status: 400 });
  }

  const now = new Date().toISOString().slice(0, 19).replace("T", " ");

  const { data: wp } = await supabase
    .from("word_progress")
    .select("difficulty_score, review_count")
    .eq("word_id", wordId)
    .single();

  const currentScore = wp ? Number(wp.difficulty_score) : 0;
  const currentCount = wp ? Number(wp.review_count) : 0;
  const newScore = knew ? currentScore + 1 : 0;
  const nextRev = nextReview(newScore);
  const newCount = currentCount + 1;

  await supabase.from("word_progress").upsert(
    {
      word_id: wordId,
      last_reviewed: now,
      next_review: nextRev,
      difficulty_score: newScore,
      review_count: newCount,
    },
    { onConflict: "word_id" }
  );

  const { data: existing } = await supabase
    .from("user_progress")
    .select("attempts, correct, mistakes, known")
    .eq("user_id", user.id)
    .eq("word_id", wordId)
    .single();

  if (existing) {
    await supabase
      .from("user_progress")
      .update({
        attempts: Number(existing.attempts) + 1,
        correct: Number(existing.correct) + (knew ? 1 : 0),
        mistakes: Number(existing.mistakes) + (knew ? 0 : 1),
        known: knew ? 1 : existing.known,
        last_seen: now,
      })
      .eq("user_id", user.id)
      .eq("word_id", wordId);
  } else {
    await supabase.from("user_progress").insert({
      user_id: user.id,
      word_id: wordId,
      known: knew ? 1 : 0,
      mistakes: knew ? 0 : 1,
      attempts: 1,
      correct: knew ? 1 : 0,
      last_seen: now,
    });
  }

  return NextResponse.json({ ok: true });
}
