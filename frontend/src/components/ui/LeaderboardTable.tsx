export type LeaderboardRow = {
  rank: number;
  user: string;
  points: number;
  streak: number;
  words_learned: number;
  avg_test: string;
};

type LeaderboardTableProps = {
  rows: LeaderboardRow[];
  currentUsername: string | null;
};

export default function LeaderboardTable({ rows, currentUsername }: LeaderboardTableProps) {
  return (
    <div className="min-w-0">
      {/* Mobile: card list */}
      <div className="md:hidden space-y-3">
        {rows.map((r) => {
          const isCurrentUser = currentUsername != null && r.user === currentUsername;
          return (
            <div
              key={r.rank}
              className={`
                card p-4 border rounded-button space-y-2
                ${isCurrentUser ? "border-amber-500/50 bg-amber-500/10" : "border-slate-700/50"}
              `}
            >
              <div className="flex items-center justify-between gap-2 flex-wrap">
                <span className="text-lg font-bold text-slate-300">#{r.rank}</span>
                <span className={isCurrentUser ? "font-semibold text-amber-400" : "font-medium text-slate-200"}>
                  {r.user}
                  {isCurrentUser && " (you)"}
                </span>
              </div>
              <div className="text-xl font-semibold text-slate-100">{r.points} pts</div>
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-500">
                <span>Streak: {r.streak}</span>
                <span>Words: {r.words_learned}</span>
                <span>Avg: {r.avg_test}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Desktop: table */}
      <div className="hidden md:block card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-base">
            <thead>
              <tr className="border-b border-slate-600 bg-slate-800/50">
                <th className="py-4 px-4 text-left font-semibold text-slate-300 text-base">Rank</th>
                <th className="py-4 px-4 text-left font-semibold text-slate-300 text-base">User</th>
                <th className="py-4 px-4 text-left font-semibold text-slate-300 text-base">Points</th>
                <th className="py-4 px-4 text-left font-semibold text-slate-300 text-base">Streak</th>
                <th className="py-4 px-4 text-left font-semibold text-slate-300 text-base">Words Learned</th>
                <th className="py-4 px-4 text-left font-semibold text-slate-300 text-base">Avg Test Score</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const isCurrentUser = currentUsername != null && r.user === currentUsername;
                return (
                  <tr
                    key={r.rank}
                    className={`
                      border-b border-slate-700/50 transition-colors
                      ${isCurrentUser ? "bg-amber-500/10 border-l-4 border-l-amber-500" : "hover:bg-slate-700/30"}
                    `}
                  >
                    <td className="py-4 px-4 font-medium text-slate-200 text-base">{r.rank}</td>
                    <td className="py-4 px-4">
                      <span className={isCurrentUser ? "font-semibold text-amber-400" : "text-slate-200"}>
                        {r.user}
                        {isCurrentUser && " (you)"}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-slate-300 font-medium">{r.points}</td>
                    <td className="py-4 px-4 text-slate-300 font-medium">{r.streak}</td>
                    <td className="py-4 px-4 text-slate-300 font-medium">{r.words_learned}</td>
                    <td className="py-4 px-4 text-slate-300 font-medium">{r.avg_test}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
