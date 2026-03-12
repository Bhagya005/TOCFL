import { NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { refreshUserStats } from "@/lib/db";
import { supabase } from "@/lib/supabase-server";

export async function GET(request: Request) {
  try {
    await requireAuth(request);
  } catch (res) {
    if (res instanceof Response) return res;
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const { data: users } = await supabase.from("users").select("id");
  const userIds = (users ?? []).map((u) => u.id);
  for (const id of userIds) {
    await refreshUserStats(id);
  }

  const { data: rows } = await supabase
    .from("user_stats")
    .select("user_id, username, streak_days, words_learned, tests_taken, avg_test_score, total_points")
    .order("total_points", { ascending: false });

  const leaderboard: { rank: number; user: string; points: number; streak: number; words_learned: number; avg_test: string }[] = [];

  (rows ?? []).forEach((r, idx) => {
    const testsTaken = Number(r.tests_taken ?? 0);
    const avgDisplay =
      testsTaken > 0 ? `${Math.round(Number(r.avg_test_score ?? 0) * 100)}%` : "0%";
    leaderboard.push({
      rank: idx + 1,
      user: r.username,
      points: Math.round(Number(r.total_points ?? 0)),
      streak: Number(r.streak_days ?? 0),
      words_learned: Number(r.words_learned ?? 0),
      avg_test: avgDisplay,
    });
  });

  return NextResponse.json({ leaderboard });
}
