import Link from "next/link";
import type { MatchOut } from "@/lib/api";

export default function MatchCard({ match }: { match: MatchOut }) {
  return (
    <Link
      href={`/matches/${match.id}`}
      className="block rounded-xl border border-black/10 bg-surface-raised p-4 transition hover:border-accent dark:border-white/10"
    >
      <div className="flex items-center justify-between text-xs uppercase tracking-wide text-ink-muted">
        <span>{match.competition_name}</span>
        <span
          className={
            match.status === "live"
              ? "rounded-full bg-negative/10 px-2 py-0.5 font-semibold text-negative"
              : "rounded-full bg-black/5 px-2 py-0.5 dark:bg-white/10"
          }
        >
          {match.status}
        </span>
      </div>
      <div className="mt-2 flex items-center justify-between">
        <span className="font-medium">{match.home_team.name}</span>
        <span className="text-ink-muted">vs</span>
        <span className="font-medium">{match.away_team.name}</span>
      </div>
      <div className="mt-2 text-xs text-ink-muted">
        {match.venue_name ?? "Venue TBC"} · {new Date(match.scheduled_start).toLocaleString()}
      </div>
    </Link>
  );
}
