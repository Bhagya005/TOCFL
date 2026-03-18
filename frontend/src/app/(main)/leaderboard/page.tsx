"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useUser } from "@/context/UserContext";
import LeaderboardTable, { type LeaderboardRow } from "@/components/ui/LeaderboardTable";
import EmptyState from "@/components/ui/EmptyState";
import LoadingSpinner from "@/components/ui/LoadingSpinner";

export default function LeaderboardPage() {
  const user = useUser();
  const [data, setData] = useState<{ leaderboard: LeaderboardRow[] } | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api<{ leaderboard: LeaderboardRow[] }>("/api/leaderboard")
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

  const rows = data.leaderboard || [];

  return (
    <div className="space-y-6 sm:space-y-8 min-w-0">
      <h1 className="text-xl sm:text-2xl font-bold text-slate-100">Leaderboard</h1>
      {rows.length === 0 ? (
        <EmptyState
          title="No stats yet"
          description="Start studying to appear on the leaderboard."
          icon="🏆"
        />
      ) : (
        <LeaderboardTable rows={rows} currentUsername={user?.username ?? null} />
      )}
    </div>
  );
}
