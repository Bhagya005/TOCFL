"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import QuizCard from "@/components/ui/QuizCard";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import ToneKeyboard from "@/components/ToneKeyboard";
import { TEST_LIMITS, getSectionCounts, type TestType } from "@/lib/test-builder";

type Question = {
  section: string;
  prompt?: string;
  options?: string[];
  answer_index?: number;
  text_to_play?: string;
  correct_pinyin?: string;
  display_cn?: string;
  display_py?: string;
};

function getOrigin(): string {
  if (typeof window !== "undefined") return window.location.origin;
  return "";
}

function AudioPlayer({ text }: { text: string }) {
  const [src, setSrc] = useState<string | null>(null);
  const [useFallback, setUseFallback] = useState(false);
  const [playing, setPlaying] = useState(false);
  const ref = useRef<string | null>(null);

  useEffect(() => {
    if (!text) return;
    setSrc(null);
    setUseFallback(false);
    const origin = getOrigin();
    const token = typeof window !== "undefined" ? localStorage.getItem("tocfl_token") : null;
    const url = origin ? `${origin}/api/audio?text=${encodeURIComponent(text)}` : `/api/audio?text=${encodeURIComponent(text)}`;
    fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((r) => (r.ok ? r.blob() : Promise.reject(new Error("Audio not available"))))
      .then((blob) => {
        const u = URL.createObjectURL(blob);
        ref.current = u;
        setSrc(u);
      })
      .catch(() => setUseFallback(true));
    return () => {
      if (ref.current) {
        URL.revokeObjectURL(ref.current);
        ref.current = null;
      }
    };
  }, [text]);

  const playFallback = useCallback(() => {
    if (!text || playing) return;
    setPlaying(true);
    import("@/lib/speech").then(({ playWithSpeechSynthesis }) =>
      playWithSpeechSynthesis(text).finally(() => setPlaying(false))
    ).catch(() => setPlaying(false));
  }, [text, playing]);

  if (src) return <audio src={src} controls className="w-full max-w-md rounded-button" />;
  if (useFallback) {
    return (
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={playFallback}
          disabled={playing}
          className="inline-flex h-10 items-center justify-center rounded-button border border-slate-600 bg-slate-700/50 px-4 text-slate-200 hover:bg-slate-600 disabled:opacity-50"
        >
          {playing ? "Playing…" : "Play (browser)"}
        </button>
        <span className="text-slate-500 text-sm">Server audio unavailable; using browser speech.</span>
      </div>
    );
  }
  return <span className="text-slate-500 text-sm">(Loading audio…)</span>;
}

const TITLES: Record<string, string> = {
  daily: "Daily Test",
  weekly: "Weekly Test",
  final: "Final Test",
};

export default function TestRunPage() {
  const params = useParams();
  const testType = (params?.testType as string) || "daily";
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<number, number | string>>({});
  const [index, setIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState<{
    total_correct: number;
    total: number;
    accuracy_percent: number;
    meaning_score: number;
    meaning_total: number;
    listening_score: number;
    listening_total: number;
    writing_score: number;
    writing_total: number;
    review_rows: { "Q#": number; Section: string; Question: string; "Your answer": string; "Correct answer": string; Result: string }[];
    already_completed: boolean;
  } | null>(null);
  const [err, setErr] = useState("");

  const limits = TEST_LIMITS[testType as TestType] ?? TEST_LIMITS.daily;
  const [questionCount, setQuestionCount] = useState(limits.default);
  const [testStarted, setTestStarted] = useState(false);

  const loadTest = useCallback((count: number) => {
    setLoading(true);
    setErr("");
    setResult(null);
    api<{ questions: Question[] }>("/api/tests/start", {
      method: "POST",
      body: JSON.stringify({ test_type: testType, question_count: count }),
    })
      .then((res) => {
        setQuestions(res.questions);
        setAnswers({});
        setIndex(0);
        setTestStarted(true);
      })
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, [testType]);

  useEffect(() => {
    setQuestionCount(limits.default);
    setTestStarted(false);
  }, [testType, limits.default]);

  const submitTest = useCallback(async () => {
    const ans: Record<string, number | string> = {};
    Object.entries(answers).forEach(([k, v]) => {
      ans[k] = v;
    });
    const res = await api<typeof result>("/api/tests/submit", {
      method: "POST",
      body: JSON.stringify({ test_type: testType, answers: ans }),
    });
    setResult(res);
  }, [testType, answers]);

  if (err) {
    const isDailyLocked =
      testType === "daily" &&
      (err.includes("flashcards") || err.includes("unlock"));
    return (
      <div className="space-y-4">
        <Link href="/tests" className="text-amber-400 hover:underline">← Back to Tests</Link>
        <div
          className={`rounded-card p-4 ${isDailyLocked ? "bg-slate-700/50 border border-slate-600" : "bg-red-500/10 border border-red-500/30"}`}
        >
          <p className={isDailyLocked ? "text-slate-200" : "text-red-400"}>{err}</p>
          {isDailyLocked && (
            <Link href="/flashcards" className="mt-3 inline-block text-amber-400 hover:underline">
              Go to Flashcards →
            </Link>
          )}
        </div>
      </div>
    );
  }

  if (loading && questions.length === 0) {
    return (
      <div className="flex justify-center py-20">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!["daily", "weekly", "final"].includes(testType)) {
    return (
      <div className="space-y-4">
        <Link href="/tests" className="text-amber-400 hover:underline">← Back to Tests</Link>
        <p className="text-slate-400">Invalid test type.</p>
      </div>
    );
  }

  if (result) {
    return (
      <div className="space-y-6 sm:space-y-8 min-w-0">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <h1 className="text-xl sm:text-2xl font-bold text-slate-100">{TITLES[testType]} – Result</h1>
          <Link href="/tests" className="btn-primary">Back to Tests</Link>
        </div>
        <div className="card p-6 space-y-4">
          <p className="text-xl text-slate-200">
            Total: <strong>{result.total_correct}</strong> / {result.total} ({result.accuracy_percent.toFixed(0)}%)
          </p>
          <p className="text-slate-400 text-base font-medium">
            Meaning: {result.meaning_score}/{result.meaning_total} · Listening: {result.listening_score}/{result.listening_total} · Writing: {result.writing_score}/{result.writing_total}
          </p>
          {result.already_completed && (
            <p className="text-amber-500 text-base font-medium">A result for today was already saved. This attempt was not stored again.</p>
          )}
        </div>
        <section className="min-w-0">
          <h2 className="text-base sm:text-lg font-semibold text-slate-200 mb-4">Test Review</h2>
          {/* Mobile: card list */}
          <div className="md:hidden space-y-3">
            {result.review_rows.map((r, i) => (
              <div
                key={i}
                className="card p-4 border border-slate-700/50 rounded-button space-y-2"
              >
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <span className="text-slate-500 text-sm">Q{r["Q#"]}</span>
                  <span className="text-slate-400 text-sm">{r.Section}</span>
                  <span className={r.Result === "Correct" ? "text-green-400" : "text-red-400"}>
                    {r.Result === "Correct" ? "✓" : "✗"}
                  </span>
                </div>
                <p className="text-slate-300 text-sm break-words">{r.Question}</p>
                <div className="text-sm space-y-0.5">
                  <p className="text-slate-400">Your answer: <span className="text-slate-200">{r["Your answer"]}</span></p>
                  <p className="text-slate-400">Correct: <span className="text-slate-200">{r["Correct answer"]}</span></p>
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
                    <th className="py-3 px-4 font-semibold text-slate-300">Q#</th>
                    <th className="py-3 px-4 font-semibold text-slate-300">Section</th>
                    <th className="py-3 px-4 font-semibold text-slate-300">Question</th>
                    <th className="py-3 px-4 font-semibold text-slate-300">Your answer</th>
                    <th className="py-3 px-4 font-semibold text-slate-300">Correct answer</th>
                    <th className="py-3 px-4 font-semibold text-slate-300">Result</th>
                  </tr>
                </thead>
                <tbody>
                  {result.review_rows.map((r, i) => (
                    <tr key={i} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                      <td className="py-3 px-4 text-slate-300">{r["Q#"]}</td>
                      <td className="py-3 px-4 text-slate-300">{r.Section}</td>
                      <td className="py-3 px-4 text-slate-300 max-w-xs truncate">{r.Question}</td>
                      <td className="py-3 px-4 text-slate-300">{r["Your answer"]}</td>
                      <td className="py-3 px-4 text-slate-300">{r["Correct answer"]}</td>
                      <td className="py-3 px-4">{r.Result === "Correct" ? "✓" : "✗"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>
    );
  }

  if (questions.length === 0) {
    const { nMeaning, nListening, nWriting } = getSectionCounts(questionCount, testType as TestType);
    return (
      <div className="space-y-6 min-w-0">
        <div className="flex items-center justify-end">
          <Link href="/tests" className="text-amber-400 hover:underline text-base font-medium">← Back to Tests</Link>
        </div>
        <div className="card p-6 space-y-6">
          <h1 className="text-xl sm:text-2xl font-bold text-slate-100">{TITLES[testType]}</h1>
          <div className="space-y-4">
            <label className="block">
              <span className="text-base font-medium text-slate-300 block mb-2">Number of questions</span>
              <div className="flex flex-wrap items-center gap-4">
                <input
                  type="range"
                  min={1}
                  max={limits.max}
                  value={questionCount}
                  onChange={(e) => setQuestionCount(Number(e.target.value))}
                  className="flex-1 min-w-[120px] h-3 rounded-full accent-amber-500 bg-slate-700"
                  aria-label="Question count"
                />
                <input
                  type="number"
                  min={1}
                  max={limits.max}
                  value={questionCount}
                  onChange={(e) => {
                    const v = Number(e.target.value);
                    if (!Number.isNaN(v)) setQuestionCount(Math.min(limits.max, Math.max(1, Math.floor(v))));
                  }}
                  className="input-field w-20 text-center"
                  aria-label="Question count (number)"
                />
              </div>
            </label>
            <p className="text-sm text-slate-500">
              Selected: <strong className="text-slate-300">{questionCount}</strong> questions
              (Meaning: {nMeaning}, Listening: {nListening}, Writing: {nWriting})
            </p>
          </div>
          <button
            type="button"
            onClick={() => loadTest(questionCount)}
            className="btn-primary w-full sm:w-auto"
          >
            Start Test
          </button>
        </div>
      </div>
    );
  }

  const q = questions[index];
  const isLast = index >= questions.length - 1;
  const progressPercent = questions.length > 0 ? ((index + 1) / questions.length) * 100 : 0;

  const questionContent = (
    <>
      {q.section === "meaning" && (
        <>
          <p className="text-lg text-slate-200 mb-4">{q.prompt}</p>
          <div className="space-y-3">
            {(q.options || []).map((opt, i) => (
              <label
                key={i}
                className="flex items-center gap-3 p-3 min-h-[48px] rounded-button border border-slate-600 bg-slate-700/30 cursor-pointer hover:bg-slate-700/50 has-[:checked]:border-amber-500 has-[:checked]:bg-amber-500/10"
              >
                <input
                  type="radio"
                  name="mcq"
                  checked={answers[index] === i}
                  onChange={() => setAnswers((a) => ({ ...a, [index]: i }))}
                  className="rounded-full border-slate-500 text-amber-500 focus:ring-amber-500"
                />
                <span className="text-slate-200">{opt}</span>
              </label>
            ))}
          </div>
        </>
      )}
      {q.section === "listening" && (
        <>
          {q.text_to_play && <AudioPlayer text={q.text_to_play} />}
          <p className="text-base font-medium text-slate-500 mt-2 mb-4">Choose the word you heard:</p>
          <div className="space-y-3">
            {(q.options || []).map((opt, i) => (
              <label
                key={i}
                className="flex items-center gap-3 p-3 min-h-[48px] rounded-button border border-slate-600 bg-slate-700/30 cursor-pointer hover:bg-slate-700/50 has-[:checked]:border-amber-500 has-[:checked]:bg-amber-500/10"
              >
                <input
                  type="radio"
                  name="listen"
                  checked={answers[index] === i}
                  onChange={() => setAnswers((a) => ({ ...a, [index]: i }))}
                  className="rounded-full border-slate-500 text-amber-500 focus:ring-amber-500"
                />
                <span className="text-slate-200">{opt}</span>
              </label>
            ))}
          </div>
        </>
      )}
      {q.section === "writing" && (
        <>
          <p className="text-lg text-slate-200 mb-2">English: {q.prompt}</p>
          <p className="text-base font-medium text-slate-500 mb-3">Type the pinyin; use the tone buttons to add tone marks to the last vowel.</p>
          <input
            type="text"
            value={(answers[index] as string) || ""}
            onChange={(e) => setAnswers((a) => ({ ...a, [index]: e.target.value }))}
            className="input-field max-w-md"
            placeholder="pinyin (e.g. péngyou)"
          />
          <ToneKeyboard
            value={(answers[index] as string) || ""}
            onChange={(value) => setAnswers((a) => ({ ...a, [index]: value }))}
          />
        </>
      )}
    </>
  );

  return (
    <>
      <div className="flex items-center justify-end mb-4">
        <Link href="/tests" className="text-amber-400 hover:underline text-base font-medium">← Back to Tests</Link>
      </div>
      <QuizCard
        title={`${TITLES[testType]} (${questions.length} questions)`}
        questionProgress={`Question ${index + 1} / ${questions.length}`}
        progressPercent={progressPercent}
        footer={
          <>
            <button
              type="button"
              onClick={() => setIndex((i) => Math.max(0, i - 1))}
              disabled={index === 0}
              className="btn-secondary w-full sm:w-auto"
            >
              Previous
            </button>
            {isLast ? (
              <button type="button" onClick={submitTest} className="btn-primary w-full sm:w-auto">
                Submit test
              </button>
            ) : (
              <button type="button" onClick={() => setIndex((i) => i + 1)} className="btn-primary w-full sm:w-auto">
                Next
              </button>
            )}
          </>
        }
      >
        {questionContent}
      </QuizCard>
    </>
  );
}
