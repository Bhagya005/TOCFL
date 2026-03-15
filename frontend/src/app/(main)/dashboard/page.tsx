"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useUser } from "@/context/UserContext";
import StatCard from "@/components/ui/StatCard";
import EmptyState from "@/components/ui/EmptyState";
import LoadingSpinner from "@/components/ui/LoadingSpinner";

type DashboardData = {
  plan: { current_day: number; unlocked_upto_word_id: number };
  start_date: string;
  summary: { known_words: number; attempts: number; correct: number; accuracy: number | null };
  test_results: { date: string; test_type: string; score: number; total: number }[];
};

type LeaderboardRow = { rank: number; user: string; points: number; streak: number; words_learned: number; avg_test: string };

type FlashcardsMeta = { count: number; total_due: number; total_new: number; total_weak: number };

export default function DashboardPage() {
  const user = useUser();
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardRow[]>([]);
  const [flashcardsMeta, setFlashcardsMeta] = useState<FlashcardsMeta | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    let cancelled = false;

    // Use same endpoint as "Today's session" on flashcards (no day param) so count always matches
    Promise.allSettled([
      api<DashboardData>("/api/dashboard"),
      api<FlashcardsMeta>("/api/flashcards/today"),
    ]).then(([dashboardResult, metaResult]) => {
      if (cancelled) return;
      if (dashboardResult.status === "fulfilled") setDashboard(dashboardResult.value);
      else setErr(dashboardResult.reason?.message ?? "Failed to load dashboard");
      if (metaResult.status === "fulfilled") setFlashcardsMeta(metaResult.value);
    }).finally(() => !cancelled && setLoading(false));

    api<{ leaderboard: LeaderboardRow[] }>("/api/leaderboard")
      .then((res) => !cancelled && setLeaderboard(res.leaderboard || []))
      .catch(() => {});

    return () => {
      cancelled = true;
    };
  }, []);

  if (err) {
    return (
      <div className="rounded-card bg-red-500/10 border border-red-500/30 p-4 text-red-400">
        {err}
      </div>
    );
  }

  if (loading && !dashboard) {
    return (
      <div className="flex justify-center py-20">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!dashboard) return null;

  const { plan, summary, test_results } = dashboard;
  const currentUserRow = user ? leaderboard.find((r) => r.user === user.username) : null;
  const streak = currentUserRow?.streak ?? 0;
  const flashcardsToday = flashcardsMeta?.count ?? 0;
  const totalPoints = currentUserRow?.points ?? 0;

  const accuracyPercent = summary.accuracy != null ? summary.accuracy * 100 : null;
  const last14 = test_results.slice(-14).reverse();
  const byDate = test_results.reduce<Record<string, { score: number; total: number }>>((acc, r) => {
    if (!acc[r.date]) acc[r.date] = { score: 0, total: 0 };
    acc[r.date].score += r.score;
    acc[r.date].total += r.total;
    return acc;
  }, {});
  const dates = Object.keys(byDate).sort();
  const maxScore = Math.max(...dates.map((d) => byDate[d].total), 1);

  const heatmapDates = new Set(test_results.map((r) => r.date));

  return (
    <div className="space-y-8 md:space-y-10 min-w-0">
      <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-slate-100">Dashboard</h1>

      <section>
        <h2 className="text-base md:text-lg font-semibold text-slate-200 mb-4">Study statistics</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 md:gap-6">
          <StatCard
            title="Words learned"
            value={summary.known_words}
            icon="📚"
            subtitle="of 300 total"
          />
          <StatCard title="Current streak" value={streak} icon="📅" subtitle="days" />
          <StatCard title="Flashcards today" value={flashcardsToday} icon="🧠" subtitle="available to study" />
          <StatCard title="Total points" value={totalPoints} icon="🏆" subtitle="leaderboard" />
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6 lg:gap-8">
        <div className="card p-4 md:p-6 min-w-0">
          <h3 className="text-base font-semibold text-slate-200 mb-4">Words learned per day (tests)</h3>
          {dates.length === 0 ? (
            <EmptyState
              title="No test data yet"
              description="Complete daily tests to see activity."
              icon="📊"
            />
          ) : (
            <div className="space-y-2">
              {dates.slice(-7).map((d) => {
                const { score, total } = byDate[d];
                const pct = total > 0 ? (total / maxScore) * 100 : 0;
                return (
                  <div key={d} className="flex items-center gap-3">
                    <span className="text-xs text-slate-500 w-20 shrink-0">{d}</span>
                    <div className="flex-1 h-6 rounded bg-slate-700 overflow-hidden">
                      <div
                        className="h-full bg-amber-500/80 rounded transition-all"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="text-xs text-slate-400 w-16 text-right">{total} q</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="card p-4 md:p-6 min-w-0">
          <h3 className="text-base font-semibold text-slate-200 mb-4">Accuracy trend</h3>
          {accuracyPercent != null ? (
            <div className="flex items-end gap-1 h-32">
              {last14.map((r, i) => {
                const pct = r.total > 0 ? (r.score / r.total) * 100 : 0;
                return (
                  <div
                    key={`${r.date}-${i}`}
                    className="flex-1 min-w-0 rounded-t bg-amber-500/70 transition-all hover:bg-amber-500"
                    style={{ height: `${pct}%`, minHeight: "4px" }}
                    title={`${r.date}: ${pct.toFixed(0)}%`}
                  />
                );
              })}
            </div>
          ) : (
            <EmptyState
              title="No accuracy data yet"
              description="Do flashcards and tests to see your trend."
              icon="📈"
            />
          )}
        </div>
      </section>

      <section className="min-w-0">
        <h3 className="text-base font-semibold text-slate-200 mb-4">Study heatmap (last 12 weeks)</h3>
        <div className="card p-4 md:p-6 overflow-hidden">
          {heatmapDates.size === 0 ? (
            <EmptyState
              title="No activity yet"
              description="Tests and reviews will show up here."
              icon="🔥"
            />
          ) : (
            <div className="grid grid-cols-12 gap-1">
              {Array.from({ length: 84 }, (_, i) => {
                const d = new Date();
                d.setDate(d.getDate() - (83 - i));
                const key = d.toISOString().slice(0, 10);
                const active = heatmapDates.has(key);
                return (
                  <div
                    key={key}
                    className={`aspect-square rounded-sm ${active ? "bg-amber-500/80" : "bg-slate-700/50"}`}
                    title={key}
                  />
                );
              })}
            </div>
          )}
        </div>
      </section>

      <section>
        <h2 className="text-base md:text-lg font-semibold text-slate-200 mb-4">Today&apos;s tasks</h2>
        <ul className="card p-4 md:p-6 list-disc list-inside text-slate-300 space-y-2">
          <li>
            <Link href="/flashcards" className="text-amber-400 hover:text-amber-300 underline">
              Flashcards today: {flashcardsToday}
            </Link>
          </li>
          <li>Daily test: 35 questions</li>
        </ul>
      </section>

      <section className="min-w-0 overflow-hidden">
        <h2 className="text-base md:text-lg font-semibold text-slate-200 mb-4">Recent test scores</h2>
        {test_results.length === 0 ? (
          <EmptyState
            title="No tests taken yet"
            description="Start a daily, weekly, or final test from the sidebar."
            icon="📝"
          />
        ) : (
          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-600 bg-slate-800/50">
                    <th className="py-3 px-4 text-left font-semibold text-slate-300">Date</th>
                    <th className="py-3 px-4 text-left font-semibold text-slate-300">Type</th>
                    <th className="py-3 px-4 text-left font-semibold text-slate-300">Score</th>
                  </tr>
                </thead>
                <tbody>
                  {test_results.slice(-10).reverse().map((r, i) => (
                    <tr key={`${r.date}-${r.test_type}-${i}`} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                      <td className="py-3 px-4 text-slate-300">{r.date}</td>
                      <td className="py-3 px-4 text-slate-300">{r.test_type}</td>
                      <td className="py-3 px-4 text-slate-200">{r.score} / {r.total}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
