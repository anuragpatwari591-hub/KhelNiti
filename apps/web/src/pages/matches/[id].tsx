import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import Layout from "@/components/Layout";
import ProbabilityCard from "@/components/ProbabilityCard";
import PredictionHistoryChart from "@/components/PredictionHistoryChart";
import { api, ApiError, type MatchOut, type PredictionOut } from "@/lib/api";

export default function MatchCentre() {
  const router = useRouter();
  const id = typeof router.query.id === "string" ? Number(router.query.id) : undefined;

  const [match, setMatch] = useState<MatchOut | null>(null);
  const [predictions, setPredictions] = useState<PredictionOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id === undefined || Number.isNaN(id)) return;
    let cancelled = false;
    Promise.all([api.getMatch(id), api.getMatchPredictions(id)])
      .then(([m, p]) => {
        if (!cancelled) {
          setMatch(m);
          setPredictions(p);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Could not load this match.");
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

  if (!match) {
    return (
      <Layout>
        <div className="h-40 animate-pulse rounded-xl border border-black/10 bg-surface-raised dark:border-white/10" />
      </Layout>
    );
  }

  const latestPrediction = predictions?.[0] ?? null;
  const primaryOutcomeKey = latestPrediction ? Object.keys(latestPrediction.probabilities)[0] : null;

  return (
    <Layout>
      <div className="text-xs uppercase tracking-wide text-ink-muted">{match.competition_name}</div>
      <h1 className="mt-1 text-2xl font-semibold">
        {match.home_team.name} <span className="text-ink-muted">vs</span> {match.away_team.name}
      </h1>
      <div className="mt-1 text-sm text-ink-muted">
        {match.venue_name ?? "Venue TBC"} · {new Date(match.scheduled_start).toLocaleString()} · {match.status}
      </div>

      <section className="mt-6">
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-ink-muted">Win probability</h2>
        {latestPrediction ? (
          <ProbabilityCard prediction={latestPrediction} homeLabel={match.home_team.name} awayLabel={match.away_team.name} />
        ) : (
          <div className="rounded-lg border border-black/10 p-6 text-center text-sm text-ink-muted dark:border-white/10">
            No prediction has been computed for this match yet.
          </div>
        )}
      </section>

      {predictions && predictions.length > 1 && primaryOutcomeKey && (
        <section className="mt-6">
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-ink-muted">Prediction history</h2>
          <div className="rounded-xl border border-black/10 bg-surface-raised p-4 dark:border-white/10">
            <PredictionHistoryChart
              predictions={predictions}
              outcomeKey={primaryOutcomeKey}
              outcomeLabel={primaryOutcomeKey === "home" || primaryOutcomeKey === "batting_team" ? match.home_team.name : match.away_team.name}
            />
          </div>
        </section>
      )}
    </Layout>
  );
}
