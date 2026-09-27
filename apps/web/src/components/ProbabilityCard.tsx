import type { PredictionOut } from "@/lib/api";

const DATA_QUALITY_LABEL: Record<string, string> = {
  high: "High",
  medium: "Medium",
  low: "Low",
  mock: "Mock (development data)",
};

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, { hour12: false });
}

function formatOutcomeLabel(key: string, homeLabel: string, awayLabel: string): string {
  if (key === "home" || key === "batting_team") return homeLabel;
  if (key === "away" || key === "bowling_team") return awayLabel;
  if (key === "draw") return "Draw";
  return key;
}

/**
 * Renders exactly what docs/README's "probability display" rule requires:
 * a probability is never shown without its timestamp, model version, and
 * data-quality label alongside it.
 */
export default function ProbabilityCard({
  prediction,
  homeLabel,
  awayLabel,
}: {
  prediction: PredictionOut;
  homeLabel: string;
  awayLabel: string;
}) {
  const entries = Object.entries(prediction.probabilities).sort(([, a], [, b]) => b - a);
  const isMock = prediction.data_quality === "mock";

  return (
    <div className="rounded-xl border border-black/10 bg-surface-raised p-5 dark:border-white/10">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {entries.map(([outcome, probability]) => (
          <div key={outcome} className="text-center sm:text-left">
            <div className="text-xs uppercase tracking-wide text-ink-muted">
              {formatOutcomeLabel(outcome, homeLabel, awayLabel)}
            </div>
            <div className="text-3xl font-bold tabular-nums">{(probability * 100).toFixed(1)}%</div>
          </div>
        ))}
      </div>
      <div className="mt-1 text-xs text-ink-muted">Estimated {prediction.prediction_type.replace("_", " ")}</div>

      <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-1 border-t border-black/10 pt-3 text-xs text-ink-muted dark:border-white/10 sm:grid-cols-4">
        <div>
          <dt className="uppercase tracking-wide">Updated</dt>
          <dd className="text-ink">{formatTime(prediction.prediction_time)}</dd>
        </div>
        <div>
          <dt className="uppercase tracking-wide">Model</dt>
          <dd className="text-ink">
            {prediction.model_name} v{prediction.model_version}
          </dd>
        </div>
        <div>
          <dt className="uppercase tracking-wide">Data quality</dt>
          <dd className={isMock ? "font-medium text-negative" : "text-ink"}>
            {DATA_QUALITY_LABEL[prediction.data_quality] ?? prediction.data_quality}
          </dd>
        </div>
        {prediction.model_confidence !== null && (
          <div>
            <dt className="uppercase tracking-wide">Confidence</dt>
            <dd className="text-ink">{(prediction.model_confidence * 100).toFixed(0)}%</dd>
          </div>
        )}
      </dl>

      {prediction.explanation && (
        <p className="mt-3 text-sm text-ink-muted">
          <span className="font-medium text-ink">Why: </span>
          {prediction.explanation}
        </p>
      )}

      {isMock && (
        <p className="mt-3 rounded-md bg-negative/10 px-3 py-2 text-xs text-negative">
          This prediction was computed from mock development data, not a real match. See docs/DATA_SOURCES.md.
        </p>
      )}
    </div>
  );
}
