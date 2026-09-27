import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import Layout from "@/components/Layout";
import { api, ApiError, type PlayerOut } from "@/lib/api";

export default function PlayerPage() {
  const router = useRouter();
  const id = typeof router.query.id === "string" ? Number(router.query.id) : undefined;

  const [player, setPlayer] = useState<PlayerOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id === undefined || Number.isNaN(id)) return;
    let cancelled = false;
    api
      .getPlayer(id)
      .then((p) => {
        if (!cancelled) setPlayer(p);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Could not load this player.");
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (error) {
    return (
      <Layout>
        <div className="rounded-lg border border-negative/30 bg-negative/5 p-4 text-sm text-negative">{error}</div>
      </Layout>
    );
  }

  if (!player) {
    return (
      <Layout>
        <div className="h-24 animate-pulse rounded-xl border border-black/10 bg-surface-raised dark:border-white/10" />
      </Layout>
    );
  }

  const facts = [
    ["Sport", player.sport],
    ["Country", player.country ?? "Unknown"],
    ["Batting style", player.batting_style],
    ["Bowling style", player.bowling_style],
    ["Position", player.primary_position],
  ].filter(([, value]) => Boolean(value)) as [string, string][];

  return (
    <Layout>
      <h1 className="text-2xl font-semibold">{player.full_name}</h1>
      <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3">
        {facts.map(([label, value]) => (
          <div key={label} className="rounded-lg border border-black/10 bg-surface-raised p-3 dark:border-white/10">
            <dt className="text-xs uppercase tracking-wide text-ink-muted">{label}</dt>
            <dd className="mt-1 font-medium">{value}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-6 text-sm text-ink-muted">
        Career/venue/opponent breakdowns and matchup history are modeled in the database
        (player_venue_stats, player_opponent_stats, player_bowler_matchups) but not yet surfaced here — see
        docs/ARCHITECTURE.md.
      </p>
    </Layout>
  );
}
