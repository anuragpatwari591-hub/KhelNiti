import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import Layout from "@/components/Layout";
import MatchCard from "@/components/MatchCard";
import { api, ApiError, type MatchOut } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const sport = typeof router.query.sport === "string" ? router.query.sport : undefined;

  const [matches, setMatches] = useState<MatchOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setMatches(null);
    setError(null);
    api
      .listMatches({ sport, limit: 20 })
      .then((data) => {
        if (!cancelled) setMatches(data);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Could not reach the KhelNiti API.");
      });
    return () => {
      cancelled = true;
    };
  }, [sport]);

  return (
    <Layout>
      <h1 className="text-xl font-semibold">{sport ? `${sport[0].toUpperCase()}${sport.slice(1)} matches` : "Matches"}</h1>
      <p className="mt-1 text-sm text-ink-muted">
        Live and recent matches with probability estimates — never a guarantee, always timestamped and versioned.
      </p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {error && (
          <div className="col-span-full rounded-lg border border-negative/30 bg-negative/5 p-4 text-sm text-negative">
            {error} Is the backend running at {process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}?
          </div>
        )}
        {!error && matches === null &&
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-28 animate-pulse rounded-xl border border-black/10 bg-surface-raised dark:border-white/10" />
          ))}
        {matches !== null && matches.length === 0 && !error && (
          <div className="col-span-full rounded-lg border border-black/10 p-6 text-center text-sm text-ink-muted dark:border-white/10">
            No matches yet. Run the mock data ingestion (see README) to populate some.
          </div>
        )}
        {matches?.map((m) => <MatchCard key={m.id} match={m} />)}
      </div>
    </Layout>
  );
}
