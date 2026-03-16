import { supabase } from "./supabase-server";

export async function getOrSetStartDate(userId: number): Promise<string> {
  const today = new Date().toISOString().slice(0, 10);
  const { data: row } = await supabase
    .from("user_settings")
    .select("start_date")
    .eq("user_id", userId)
    .single();

  if (row?.start_date) return row.start_date;

  await supabase
    .from("user_settings")
    .upsert({ user_id: userId, start_date: today }, { onConflict: "user_id" });
  return today;
}

export async function refreshUserStats(userId: number) {
  const [progressRows, testRows, userRow] = await Promise.all([
    supabase.from("user_progress").select("word_id, known").eq("user_id", userId),
    supabase.from("test_results").select("score, total").eq("user_id", userId),
    supabase.from("users").select("username").eq("id", userId).single(),
  ]);

  const wordsLearned = (progressRows.data ?? []).filter((r) => r.known === 1).length;
  const tests = testRows.data ?? [];
  const testsTaken = tests.length;
  const avgTestScore =
    tests.length > 0
      ? tests.reduce((a, t) => a + (Number(t.total) ? Number(t.score) / Number(t.total) : 0), 0) / tests.length
      : 0;

  // Streak = consecutive days (including today) with at least one test completed.
  const { data: testDateRows } = await supabase
    .from("test_results")
    .select("date")
    .eq("user_id", userId);

  const activeDates = new Set<string>();
  (testDateRows ?? []).forEach((r) => activeDates.add(r.date));

  const sorted = Array.from(activeDates).sort().reverse();
  let streak = 0;
  const today = new Date().toISOString().slice(0, 10);
  let cur = today;
  while (sorted.includes(cur)) {
    streak++;
    const d = new Date(cur);
    d.setDate(d.getDate() - 1);
    cur = d.toISOString().slice(0, 10);
  }

  const totalPoints = streak * 10 + wordsLearned * 5 + avgTestScore * testsTaken;

  await supabase.from("user_stats").upsert(
    {
      user_id: userId,
      username: userRow?.data?.username ?? "",
      streak_days: streak,
      words_learned: wordsLearned,
      tests_taken: testsTaken,
      avg_test_score: avgTestScore,
      total_points: totalPoints,
    },
    { onConflict: "user_id" }
  );
}
