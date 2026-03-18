"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import StatCard from "@/components/ui/StatCard";
import EmptyState from "@/components/ui/EmptyState";
import LoadingSpinner from "@/components/ui/LoadingSpinner";

type ProgressData = {
  plan: { current_day: number; unlocked_upto_word_id: number };
  start_date: string;
  summary: { known_words: number; accuracy: number | null };
  test_results: { date: string; test_type: string; score: number; total: number }[];
  word_stats: { word_id: number; character: string; attempts: number; correct: number }[];
};

export default function ProgressPage() {
  const [data, setData] = useState<ProgressData | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api<ProgressData>("/api/progress")
      .then(setData)
      .catch((e) => setErr(e.message));
  }, []);

  if (err) {
    return (
      <div className="rounded-card bg-red-500/10 border border-red-500/30 p-4 text-red-400">
        {err}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex justify-center py-20">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const { summary, test_results, word_stats } = data;
  const progress = Math.min(1, summary.known_words / 300);
  const withAcc = word_stats
    .filter((w) => w.attempts > 0)
    .map((w) => ({ ...w, accuracy: w.correct / w.attempts }))
    .sort((a, b) => a.accuracy - b.accuracy)
    .slice(0, 40);

  return (
    <div className="space-y-8 sm:space-y-10 min-w-0">
      <h1 className="text-xl sm:text-2xl font-bold text-slate-100">Progress</h1>

      <section className="min-w-0">
        <h2 className="text-base sm:text-lg font-semibold text-slate-200 mb-4">Overall</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          <StatCard
            title="Words learned"
            value={`${summary.known_words} / 300`}
            icon="📚"
          />
          {summary.accuracy != null && (
            <StatCard
              title="Flashcard accuracy"
              value={`${(summary.accuracy * 100).toFixed(1)}%`}
              icon="🎯"
            />
          )}
        </div>
        <div className="card p-4 min-w-0">
          <p className="text-base font-medium text-slate-400 mb-2">Overall progress</p>
          <div className="h-3 rounded-full bg-slate-700 overflow-hidden min-w-0">
            <div
              className="h-full bg-amber-500 rounded-full transition-all"
              style={{ width: `${progress * 100}%` }}
            />
          </div>
        </div>
      </section>

      <section className="min-w-0">
        <h2 className="text-base sm:text-lg font-semibold text-slate-200 mb-4">Test scores</h2>
        {test_results.length === 0 ? (
          <EmptyState
            title="No test results yet"
            description="Complete daily, weekly, or final tests to see scores."
            icon="📝"
          />
        ) : (
          <>
            {/* Mobile: card list */}
            <div className="md:hidden space-y-3">
              {test_results.map((r, i) => (
                <div key={i} className="card p-4 border border-slate-700/50 rounded-button flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="font-medium text-slate-200">{r.date}</p>
                    <p className="text-sm text-slate-500">{r.test_type}</p>
                  </div>
                  <p className="text-lg font-semibold text-slate-100">{r.score} / {r.total}</p>
                </div>
              ))}
            </div>
            {/* Desktop: table */}
            <div className="hidden md:block card overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-base">
                  <thead>
                    <tr className="border-b border-slate-600 bg-slate-800/50 text-left">
                      <th className="py-4 px-4 font-semibold text-slate-300">Date</th>
                      <th className="py-4 px-4 font-semibold text-slate-300">Type</th>
                      <th className="py-4 px-4 font-semibold text-slate-300">Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {test_results.map((r, i) => (
                      <tr key={i} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                        <td className="py-4 px-4 text-slate-300">{r.date}</td>
                        <td className="py-4 px-4 text-slate-300">{r.test_type}</td>
                        <td className="py-4 px-4 text-slate-200">{r.score} / {r.total}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </section>

      <section className="min-w-0">
        <h2 className="text-base sm:text-lg font-semibold text-slate-200 mb-4">Accuracy by word (weakest)</h2>
        {withAcc.length === 0 ? (
          <EmptyState
            title="No flashcard data yet"
            description="Review flashcards to see accuracy by word."
            icon="📊"
          />
        ) : (
          <>
            {/* Mobile: card list */}
            <div className="md:hidden space-y-3">
              {withAcc.map((w) => (
                <div key={w.word_id} className="card p-4 border border-slate-700/50 rounded-button flex flex-wrap items-center justify-between gap-2">
                  <p className="text-lg font-medium text-slate-200">{w.character}</p>
                  <div className="flex items-center gap-4 text-sm text-slate-400">
                    <span>{w.attempts} attempts</span>
                    <span>{w.correct} correct</span>
                    <span className="font-medium text-slate-300">{(w.accuracy * 100).toFixed(0)}%</span>
                  </div>
                </div>
              ))}
            </div>
            {/* Desktop: table */}
            <div className="hidden md:block card overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-base">
                  <thead>
                    <tr className="border-b border-slate-600 bg-slate-800/50 text-left">
                      <th className="py-4 px-4 font-semibold text-slate-300">Word</th>
                      <th className="py-4 px-4 font-semibold text-slate-300">Attempts</th>
                      <th className="py-4 px-4 font-semibold text-slate-300">Correct</th>
                      <th className="py-4 px-4 font-semibold text-slate-300">Accuracy</th>
                    </tr>
                  </thead>
                  <tbody>
                    {withAcc.map((w) => (
                      <tr key={w.word_id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                        <td className="py-4 px-4 text-slate-200 font-medium">{w.character}</td>
                        <td className="py-4 px-4 text-slate-300">{w.attempts}</td>
                        <td className="py-4 px-4 text-slate-300">{w.correct}</td>
                        <td className="py-4 px-4 text-slate-300">{(w.accuracy * 100).toFixed(0)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
