"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import EmptyState from "@/components/ui/EmptyState";

type Eligible = { can_start: boolean; message?: string; test_type?: string; seed?: number };

const TESTS = [
  {
    type: "daily",
    href: "/tests/daily",
    title: "Daily Test",
    questions: 35,
    description: "Words learned today.",
    icon: "📅",
  },
  {
    type: "weekly",
    href: "/tests/weekly",
    title: "Weekly Test",
    questions: 120,
    description: "Words learned this week.",
    icon: "📆",
  },
  {
    type: "final",
    href: "/tests/final",
    title: "Final Test",
    questions: 200,
    description: "All 300 words.",
    icon: "🏁",
  },
] as const;

export default function TestsPage() {
  const [eligibility, setEligibility] = useState<Record<string, Eligible>>({});
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([
      api<Eligible>("/api/tests/eligible?test_type=daily").then((r) => ({ daily: r })),
      api<Eligible>("/api/tests/eligible?test_type=weekly").then((r) => ({ weekly: r })),
      api<Eligible>("/api/tests/eligible?test_type=final").then((r) => ({ final: r })),
    ])
      .then((arr) => {
        const next: Record<string, Eligible> = {};
        arr.forEach((o) => Object.assign(next, o));
        setEligibility(next);
      })
      .catch(() => setEligibility({}))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-slate-100">Tests</h1>
      <div className="grid grid-cols-1 gap-4 md:gap-6 md:grid-cols-3">
        {TESTS.map(({ type, href, title, questions, description, icon }) => {
          const e = eligibility[type] ?? { can_start: false, message: "Loading..." };
          return (
            <div key={type} className="card p-4 md:p-6 flex flex-col min-w-0">
              <span className="text-3xl mb-3" aria-hidden>{icon}</span>
              <h2 className="text-lg font-semibold text-slate-100 mb-2">{title}</h2>
              <p className="text-base font-medium text-slate-400 mb-4 flex-1">{description}</p>
              <p className="text-sm font-medium text-slate-500 mb-4">{questions} questions</p>
              {e.can_start ? (
                <Link href={href} className="btn-primary text-center">
                  Start
                </Link>
              ) : (
                <p className="text-sm text-slate-500">{e.message || "Not available"}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
