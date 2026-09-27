import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { PredictionOut } from "@/lib/api";

export default function PredictionHistoryChart({
  predictions,
  outcomeKey,
  outcomeLabel,
}: {
  predictions: PredictionOut[];
  outcomeKey: string;
  outcomeLabel: string;
}) {
  const data = [...predictions]
    .sort((a, b) => new Date(a.prediction_time).getTime() - new Date(b.prediction_time).getTime())
    .map((p) => ({
      time: new Date(p.prediction_time).toLocaleTimeString(undefined, { hour12: false }),
      probability: Math.round((p.probabilities[outcomeKey] ?? 0) * 1000) / 10,
    }));

  if (data.length < 2) {
    return (
      <p className="text-sm text-ink-muted">
        Not enough prediction history yet to chart — check back after more live events.
      </p>
    );
  }

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
          <XAxis dataKey="time" stroke="var(--ink-muted)" fontSize={11} tickLine={false} />
          <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} stroke="var(--ink-muted)" fontSize={11} tickLine={false} />
          <Tooltip
            formatter={(value: number) => [`${value}%`, outcomeLabel]}
            contentStyle={{ background: "var(--surface-raised)", border: "1px solid rgba(128,128,128,0.2)" }}
          />
          <Line type="monotone" dataKey="probability" stroke="#2563eb" strokeWidth={2} dot={{ r: 3 }} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
