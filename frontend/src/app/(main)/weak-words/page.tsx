"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import EmptyState from "@/components/ui/EmptyState";
import LoadingSpinner from "@/components/ui/LoadingSpinner";

type Word = { id: number; character: string; pinyin: string; meaning: string; pos?: string };

export default function WeakWordsPage() {
  const [data, setData] = useState<{ words: Word[] } | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api<{ words: Word[] }>("/api/weak-words")
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

  if (data.words.length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-100">Weak Words</h1>
        <EmptyState
          title="No weak words yet"
          description="A word becomes weak after 3 mistakes. Keep practicing!"
          icon="⚠️"
        />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-slate-100">Weak Words</h1>
      <p className="text-slate-400">Words you&apos;ve missed 3+ times. Review them in flashcards.</p>
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-600 bg-slate-800/50 text-left">
                <th className="py-4 px-4 font-semibold text-slate-300">ID</th>
                <th className="py-4 px-4 font-semibold text-slate-300">Character</th>
                <th className="py-4 px-4 font-semibold text-slate-300">Pinyin</th>
                <th className="py-4 px-4 font-semibold text-slate-300">Meaning</th>
                <th className="py-4 px-4 font-semibold text-slate-300">POS</th>
              </tr>
            </thead>
            <tbody>
              {data.words.map((w) => (
                <tr key={w.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                  <td className="py-4 px-4 text-slate-300">{w.id}</td>
                  <td className="py-4 px-4 text-slate-200 font-medium">{w.character}</td>
                  <td className="py-4 px-4 text-slate-300">{w.pinyin}</td>
                  <td className="py-4 px-4 text-slate-300">{w.meaning}</td>
                  <td className="py-4 px-4 text-slate-500">{w.pos || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
