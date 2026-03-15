"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import FlashcardCard, { type FlashcardWord } from "@/components/ui/FlashcardCard";
import ProgressBar from "@/components/ui/ProgressBar";
import EmptyState from "@/components/ui/EmptyState";
import LoadingSpinner from "@/components/ui/LoadingSpinner";

type FlashcardsData = {
  words: FlashcardWord[];
  count: number;
  total_due: number;
  total_new: number;
  total_weak: number;
  start_id: number;
  end_id: number;
  day: number;
};

export default function FlashcardsPage() {
  const [day, setDay] = useState(1);
  const [data, setData] = useState<FlashcardsData | null>(null);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const load = useCallback((d: number) => {
    setLoading(true);
    api<FlashcardsData>(`/api/flashcards/today?day=${d}`)
      .then((res) => {
        setData(res);
        setIndex(0);
        setFlipped(false);
      })
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load(day);
  }, [day, load]);

  const submitAnswer = useCallback(async (wordId: number, knew: boolean) => {
    await api("/api/flashcards/answer", {
      method: "POST",
      body: JSON.stringify({ word_id: wordId, knew }),
    });
  }, []);

  if (err) {
    return (
      <div className="rounded-card bg-red-500/10 border border-red-500/30 p-4 text-red-400">
        {err}
      </div>
    );
  }

  if (loading && !data) {
    return (
      <div className="flex justify-center py-20">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!data) return null;

  const { words, total_due, total_new, total_weak } = data;
  if (words.length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-100">Flashcards</h1>
        <EmptyState
          title="No flashcards for this day"
          description="No words due for review and no new words in this day's range."
          icon="🃏"
        />
      </div>
    );
  }

  const safeIndex = Math.max(0, Math.min(index, words.length - 1));
  const current = words[safeIndex];

  return (
    <div className="space-y-4 sm:space-y-6 md:space-y-8 min-w-0">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
        <h1 className="text-xl sm:text-2xl font-bold text-slate-100">Flashcards</h1>
        <div className="flex items-center gap-3 sm:gap-4 flex-wrap">
          <label className="text-sm text-slate-400">Day</label>
          <input
            type="number"
            min={1}
            max={20}
            value={day}
            onChange={(e) => setDay(parseInt(e.target.value, 10) || 1)}
            className="input-field w-20"
          />
          <p className="text-sm text-slate-500">
            Due: <strong>{total_due}</strong> · New: <strong>{total_new}</strong> · Weak: <strong>{total_weak}</strong>
          </p>
        </div>
      </div>

      <ProgressBar
        current={safeIndex + 1}
        total={words.length}
        label={`Word ${safeIndex + 1} / ${words.length}`}
      />

      <FlashcardCard
        word={current}
        flipped={flipped}
        onFlip={() => setFlipped((f) => !f)}
        onKnew={async () => {
          await submitAnswer(current.id, true);
          setFlipped(false);
          setIndex((i) => Math.min(words.length - 1, i + 1));
        }}
        onDidNotKnow={async () => {
          await submitAnswer(current.id, false);
          setFlipped(false);
          setIndex((i) => Math.min(words.length - 1, i + 1));
        }}
        onReset={() => {
          setIndex(0);
          setFlipped(false);
        }}
      />
    </div>
  );
}
