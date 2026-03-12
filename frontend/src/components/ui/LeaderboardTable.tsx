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
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-600 bg-slate-800/50">
              <th className="py-4 px-4 text-left font-semibold text-slate-300">Rank</th>
              <th className="py-4 px-4 text-left font-semibold text-slate-300">User</th>
              <th className="py-4 px-4 text-left font-semibold text-slate-300">Points</th>
              <th className="py-4 px-4 text-left font-semibold text-slate-300">Streak</th>
              <th className="py-4 px-4 text-left font-semibold text-slate-300">Words Learned</th>
              <th className="py-4 px-4 text-left font-semibold text-slate-300">Avg Test Score</th>
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
                  <td className="py-4 px-4 font-medium text-slate-200">{r.rank}</td>
                  <td className="py-4 px-4">
                    <span className={isCurrentUser ? "font-semibold text-amber-400" : "text-slate-200"}>
                      {r.user}
                      {isCurrentUser && " (you)"}
                    </span>
                  </td>
                  <td className="py-4 px-4 text-slate-300">{r.points}</td>
                  <td className="py-4 px-4 text-slate-300">{r.streak}</td>
                  <td className="py-4 px-4 text-slate-300">{r.words_learned}</td>
                  <td className="py-4 px-4 text-slate-300">{r.avg_test}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
