"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
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
  message?: string;
};

type Mode = "today" | "previous";

export default function FlashcardsPage() {
  const searchParams = useSearchParams();
  const dayFromUrl = searchParams.get("day");
  const initialMode: Mode = dayFromUrl != null && dayFromUrl !== "" ? "previous" : "today";
  const initialDay =
    dayFromUrl != null && dayFromUrl !== ""
      ? Math.max(1, Math.min(20, parseInt(dayFromUrl, 10) || 1))
      : 1;

  const [mode, setMode] = useState<Mode>(initialMode);
  const [day, setDay] = useState<number | null>(initialMode === "today" ? null : initialDay);
  const [data, setData] = useState<FlashcardsData | null>(null);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const load = useCallback((m: Mode, d: number | null) => {
    setLoading(true);
    const url = m === "today" || d == null ? "/api/flashcards/today" : `/api/flashcards/today?day=${d}`;
    api<FlashcardsData>(url)
      .then((res) => {
        setData(res);
        if (m === "previous") setDay(res.day);
        setIndex(0);
        setFlipped(false);
      })
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (mode === "today") {
      load("today", null);
    } else {
      load("previous", day ?? initialDay);
    }
  }, [mode, day, load, initialDay]);

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

  const { words, total_due, total_new, total_weak, message } = data;
  const displayDay = mode === "today" ? (data?.day ?? 1) : (day ?? data?.day ?? 1);

  if (words.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium text-slate-400">Mode:</span>
          <button
            type="button"
            onClick={() => setMode("today")}
            className={`rounded-button px-3 py-1.5 text-sm font-medium ${mode === "today" ? "bg-amber-500/90 text-slate-900" : "bg-slate-700/80 text-slate-300"}`}
          >
            Today&apos;s session
          </button>
          <button
            type="button"
            onClick={() => { setMode("previous"); if (day == null) setDay(data?.day ?? 1); }}
            className={`rounded-button px-3 py-1.5 text-sm font-medium ${mode === "previous" ? "bg-amber-500/90 text-slate-900" : "bg-slate-700/80 text-slate-300"}`}
          >
            Review previous days
          </button>
        </div>
        <h1 className="text-2xl font-bold text-slate-100">Flashcards</h1>
        <EmptyState
          title={mode === "today" ? "No flashcards for today" : `No flashcards for day ${displayDay}`}
          description={message ?? "No words due for review and no new words in this day's range."}
          icon="🃏"
        />
      </div>
    );
  }

  const safeIndex = Math.max(0, Math.min(index, words.length - 1));
  const current = words[safeIndex];

  return (
    <div className="space-y-4 sm:space-y-6 md:space-y-8 min-w-0">
      <div className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium text-slate-400">Mode:</span>
          <button
            type="button"
            onClick={() => setMode("today")}
            className={`rounded-button px-3 py-1.5 text-sm font-medium transition-colors ${
              mode === "today"
                ? "bg-amber-500/90 text-slate-900"
                : "bg-slate-700/80 text-slate-300 hover:bg-slate-600"
            }`}
          >
            Today&apos;s session
          </button>
          <button
            type="button"
            onClick={() => {
              setMode("previous");
              if (day == null) setDay(data?.day ?? 1);
            }}
            className={`rounded-button px-3 py-1.5 text-sm font-medium transition-colors ${
              mode === "previous"
                ? "bg-amber-500/90 text-slate-900"
                : "bg-slate-700/80 text-slate-300 hover:bg-slate-600"
            }`}
          >
            Review previous days
          </button>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
          <h1 className="text-xl sm:text-2xl font-bold text-slate-100">Flashcards</h1>
          <div className="flex items-center gap-3 sm:gap-4 flex-wrap">
            {mode === "previous" ? (
              <>
                <label className="text-sm text-slate-400">Day</label>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={displayDay}
                  onChange={(e) => setDay(parseInt(e.target.value, 10) || 1)}
                  className="input-field w-20"
                />
              </>
            ) : (
              <span className="text-sm text-slate-400">
                Day <strong className="text-slate-200">{displayDay}</strong> (today)
              </span>
            )}
            <p className="text-sm text-slate-500">
              Due: <strong>{total_due}</strong> · New: <strong>{total_new}</strong> · Weak: <strong>{total_weak}</strong>
            </p>
          </div>
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
