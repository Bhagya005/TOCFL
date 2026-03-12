"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import LoadingSpinner from "@/components/ui/LoadingSpinner";

type Word = {
  id: number;
  character: string;
  pinyin: string;
  meaning: string;
  pos: string;
  learned: boolean;
  weak: boolean;
  mistakes: number;
  attempts: number;
};

export default function WordBankPage() {
  const [data, setData] = useState<{ words: Word[] } | null>(null);
  const [err, setErr] = useState("");
  const [search, setSearch] = useState("");
  const [showLearned, setShowLearned] = useState(true);
  const [showUnlearned, setShowUnlearned] = useState(true);
  const [weakOnly, setWeakOnly] = useState(false);

  useEffect(() => {
    api<{ words: Word[] }>("/api/word-bank")
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

  let words = data.words;
  if (search) {
    const s = search.toLowerCase();
    words = words.filter(
      (w) =>
        w.character.includes(search) ||
        (w.pinyin && w.pinyin.toLowerCase().includes(s)) ||
        (w.meaning && w.meaning.toLowerCase().includes(s))
    );
  }
  if (!showLearned) words = words.filter((w) => !w.learned);
  if (!showUnlearned) words = words.filter((w) => w.learned);
  if (weakOnly) words = words.filter((w) => w.weak);

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-slate-100">Word Bank</h1>
      <div className="card p-4 md:p-6">
        <input
          type="text"
          placeholder="Search (character / pinyin / meaning)"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-field mb-4"
        />
        <div className="flex flex-wrap gap-4">
          <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={showLearned}
              onChange={(e) => setShowLearned(e.target.checked)}
              className="rounded border-slate-500 text-amber-500 focus:ring-amber-500"
            />
            Learned
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={showUnlearned}
              onChange={(e) => setShowUnlearned(e.target.checked)}
              className="rounded border-slate-500 text-amber-500 focus:ring-amber-500"
            />
            Unlearned
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={weakOnly}
              onChange={(e) => setWeakOnly(e.target.checked)}
              className="rounded border-slate-500 text-amber-500 focus:ring-amber-500"
            />
            Weak only
          </label>
        </div>
      </div>
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
                <th className="py-4 px-4 font-semibold text-slate-300">Learned</th>
                <th className="py-4 px-4 font-semibold text-slate-300">Weak</th>
                <th className="py-4 px-4 font-semibold text-slate-300">Mistakes</th>
                <th className="py-4 px-4 font-semibold text-slate-300">Attempts</th>
              </tr>
            </thead>
            <tbody>
              {words.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-500">
                    No words match your filters.
                  </td>
                </tr>
              ) : (
                words.map((w) => (
                  <tr key={w.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                    <td className="py-4 px-4 text-slate-300">{w.id}</td>
                    <td className="py-4 px-4 text-slate-200 font-medium">{w.character}</td>
                    <td className="py-4 px-4 text-slate-300">{w.pinyin}</td>
                    <td className="py-4 px-4 text-slate-300">{w.meaning}</td>
                    <td className="py-4 px-4 text-slate-500">{w.pos || "—"}</td>
                    <td className="py-4 px-4 text-slate-400">{w.learned ? "Yes" : "—"}</td>
                    <td className="py-4 px-4 text-slate-400">{w.weak ? "Yes" : "—"}</td>
                    <td className="py-4 px-4 text-slate-400">{w.mistakes}</td>
                    <td className="py-4 px-4 text-slate-400">{w.attempts}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
