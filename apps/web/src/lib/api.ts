const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export interface TeamSummary {
  id: number;
  name: string;
  short_name: string | null;
}

export interface MatchOut {
  id: number;
  sport: "cricket" | "football";
  status: string;
  scheduled_start: string;
  home_team: TeamSummary;
  away_team: TeamSummary;
  venue_name: string | null;
  competition_name: string;
  data_quality: "high" | "medium" | "low" | "mock";
  result_summary: Record<string, unknown>;
}

export interface PredictionOut {
  id: number;
  match_id: number;
  sport: string;
  prediction_type: string;
  prediction_time: string;
  model_name: string;
  model_version: string;
  probabilities: Record<string, number>;
  model_confidence: number | null;
  data_quality: string;
  explanation: string | null;
  result_status: string;
}

export interface PredictionChange {
  outcome: string;
  previous_probability: number | null;
  new_probability: number;
  delta: number | null;
  triggering_event: string;
  reasons: string[];
  model_version_id: number;
}

export interface PlayerOut {
  id: number;
  sport: string;
  full_name: string;
  country: string | null;
  date_of_birth: string | null;
  batting_style: string | null;
  bowling_style: string | null;
  primary_position: string | null;
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail || res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listMatches: (params?: { sport?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.sport) qs.set("sport", params.sport);
    if (params?.limit) qs.set("limit", String(params.limit));
    const query = qs.toString();
    return request<MatchOut[]>(`/matches${query ? `?${query}` : ""}`);
  },
  getMatch: (id: number) => request<MatchOut>(`/matches/${id}`),
  getMatchPredictions: (id: number) => request<PredictionOut[]>(`/matches/${id}/predictions`),
  getPredictionChange: (id: number) =>
    request<PredictionChange>(`/matches/${id}/predictions/change`).catch(() => null),
  getPlayer: (id: number) => request<PlayerOut>(`/players/${id}`),
};

export { ApiError, API_BASE };
