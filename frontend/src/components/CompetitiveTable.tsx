import { Trophy, Star, MessageSquare } from "lucide-react";

export default function CompetitiveTable({ rankings }) {
  if (!rankings || rankings.length === 0) return null;

  return (
    <div className="flex flex-col h-full bg-[var(--surface-alt)]">
      <div className="p-5 border-b border-[var(--border-subtle)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Trophy size={18} className="text-[var(--chai)]" />
          <h2 className="text-lg">Competitive Rankings</h2>
        </div>
        <span className="text-xs font-mono text-[var(--text-secondary)]">
          Score = Rating + Vol + Sentiment
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-[var(--border-subtle)] bg-[var(--surface)] text-[var(--text-secondary)] text-xs font-mono uppercase tracking-wider">
              <th className="px-5 py-4 font-normal">Rank</th>
              <th className="px-5 py-4 font-normal">Café</th>
              <th className="px-5 py-4 font-normal hidden md:table-cell">Neighborhood</th>
              <th className="px-5 py-4 font-normal hidden sm:table-cell">Format</th>
              <th className="px-5 py-4 font-normal text-right">Rating</th>
              <th className="px-5 py-4 font-normal text-right hidden lg:table-cell">Sentiment</th>
              <th className="px-5 py-4 font-normal text-right text-[var(--chai)]">Score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-subtle)] text-sm">
            {rankings.map((cafe) => (
              <tr 
                key={cafe.place_id} 
                className="hover:bg-[var(--surface-hover)] transition-colors group"
              >
                <td className="px-5 py-4 font-mono text-[var(--text-secondary)]">
                  #{cafe.rank}
                </td>
                <td className="px-5 py-4">
                  <div className="font-medium text-[var(--text-primary)] group-hover:text-[var(--chai)] transition-colors">
                    {cafe.name}
                  </div>
                  <div className="text-xs text-[var(--text-tertiary)] flex items-center gap-1 sm:hidden mt-1">
                    {cafe.neighborhood} • {cafe.cafe_type ? cafe.cafe_type.replace(/_/g, " ") : "Unknown"}
                  </div>
                </td>
                <td className="px-5 py-4 text-[var(--text-secondary)] hidden md:table-cell">
                  {cafe.neighborhood || "-"}
                </td>
                <td className="px-5 py-4 hidden sm:table-cell">
                  {cafe.cafe_type ? (
                    <span className="px-2 py-1 bg-[var(--surface)] border border-[var(--border-subtle)] rounded text-xs capitalize text-[var(--text-secondary)]">
                      {cafe.cafe_type.replace(/_/g, " ")}
                    </span>
                  ) : "-"}
                </td>
                <td className="px-5 py-4 text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    <span className="font-mono">{cafe.rating ? cafe.rating.toFixed(1) : "-"}</span>
                    <Star className={`w-3.5 h-3.5 ${cafe.rating ? "text-[var(--chai)] fill-current" : "text-[var(--border-strong)]"}`} />
                  </div>
                  <div className="text-xs text-[var(--text-tertiary)] mt-1 flex items-center justify-end gap-1">
                    <MessageSquare className="w-3 h-3" /> {cafe.review_count}
                  </div>
                </td>
                <td className="px-5 py-4 text-right font-mono hidden lg:table-cell">
                  {cafe.sentiment_score !== null ? (
                    <span className={
                      cafe.sentiment_score > 0.3 ? "text-[var(--cardamom)]" :
                      cafe.sentiment_score < -0.1 ? "text-[var(--chili)]" :
                      "text-[var(--text-secondary)]"
                    }>
                      {cafe.sentiment_score.toFixed(2)}
                    </span>
                  ) : "-"}
                </td>
                <td className="px-5 py-4 text-right font-mono font-medium text-[var(--text-primary)]">
                  {cafe.competitive_score ? cafe.competitive_score.toFixed(1) : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
