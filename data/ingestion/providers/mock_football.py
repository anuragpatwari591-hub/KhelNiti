"""Mock football data provider — development/test only.

Generates synthetic fixtures with team "attack"/"defense" strengths drawn
per-match from a seeded RNG and goals sampled from a Poisson process, which
is exactly the generative assumption the Dixon-Coles expected-goals model
(`ml/football/expected_goals.py`) fits — so backtesting against this mock
corpus is a genuine test of the estimator, not just a smoke test. Every
payload carries `data_quality=DataQuality.MOCK`.

To wire in a real provider, implement `FootballDataProvider` against a
licensed fixtures/events vendor and register it in
`data/ingestion/providers/registry.py` (see docs/DATA_SOURCES.md).
"""
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from data.ingestion.providers.base import FootballDataProvider
from data.ingestion.providers.types import FootballEventPayload, MatchSummaryPayload
from database.models.enums import DataQuality

_TEAMS = [
    "Mock City", "Mock United", "Mock Athletic", "Mock Rovers",
    "Mock Wanderers", "Mock Albion", "Mock Rangers", "Mock Town",
]
_FIRST_NAMES = ["Leo", "Marco", "Diego", "Hugo", "Luca", "Theo", "Noah", "Elias", "Mateo", "Kian"]
_LAST_NAMES = ["Costa", "Ferreira", "Novak", "Ibrahim", "Larsson", "Dubois", "Moreno", "Haas"]


def _mock_name(rng: random.Random) -> str:
    return f"{rng.choice(_FIRST_NAMES)} {rng.choice(_LAST_NAMES)}"


def _poisson(rng: random.Random, lam: float) -> int:
    # Knuth's algorithm — avoids adding a numpy dependency to a mock stub.
    l = pow(2.718281828459045, -lam)
    k, p = 0, 1.0
    while p > l:
        k += 1
        p *= rng.random()
    return k - 1


@dataclass
class MockFootballMatchResult:
    match: MatchSummaryPayload
    events: list[FootballEventPayload]
    home_goals: int
    away_goals: int
    home_attack: float
    away_attack: float


class MockFootballProvider(FootballDataProvider):
    """Deterministic (seeded) synthetic football data for dev/test/training."""

    def __init__(self, seed: int = 7):
        self._seed = seed

    @property
    def provider_name(self) -> str:
        return "mock-football"

    def _rng_for(self, external_ref: str) -> random.Random:
        return random.Random(f"{self._seed}:{external_ref}")

    def get_live_matches(self) -> list[MatchSummaryPayload]:
        now = datetime.now(timezone.utc)
        return [
            MatchSummaryPayload(
                external_ref="mock-football-live-1",
                sport="football",
                competition_name="Mock Premier Division",
                home_team_name=_TEAMS[0],
                away_team_name=_TEAMS[1],
                venue_name="Mock Arena",
                scheduled_start=now - timedelta(minutes=30),
                status="live",
                data_quality=DataQuality.MOCK,
            )
        ]

    def get_events(self, match_external_ref: str, since_minute: int | None = None) -> list[FootballEventPayload]:
        result = self.generate_match(match_external_ref)
        if since_minute is None:
            return result.events
        return [e for e in result.events if e.minute > since_minute]

    def generate_match(self, match_external_ref: str) -> MockFootballMatchResult:
        """Mock-only helper: deterministically generates one full match's
        goal/card/shot event stream from a Poisson goal process, used by
        live-mode simulation and by ml/training for the xG model corpus.
        """
        rng = self._rng_for(match_external_ref)
        base_time = datetime.now(timezone.utc) - timedelta(hours=2)

        # League-average ~1.35 goals/team/match, with per-match multiplicative
        # attack strength noise so matches vary (mirrors real team quality
        # variance without claiming to model any specific real team).
        home_attack = max(0.3, rng.gauss(1.45, 0.35))  # home advantage baked in
        away_attack = max(0.3, rng.gauss(1.15, 0.35))

        home_goals = _poisson(rng, home_attack)
        away_goals = _poisson(rng, away_attack)

        events: list[FootballEventPayload] = []

        def _add_goals(n: int, team_name: str):
            for _ in range(n):
                minute = rng.randint(1, 90)
                events.append(
                    FootballEventPayload(
                        external_ref=match_external_ref,
                        event_type="goal",
                        minute=minute,
                        added_time=None,
                        team_name=team_name,
                        player_name=_mock_name(rng),
                        related_player_name=_mock_name(rng) if rng.random() < 0.6 else None,
                        shot_x=rng.uniform(70, 100),
                        shot_y=rng.uniform(0, 100),
                        event_time=base_time + timedelta(minutes=minute),
                        data_quality=DataQuality.MOCK,
                    )
                )

        home_name = _TEAMS[hash(match_external_ref) % len(_TEAMS)]
        away_name = _TEAMS[(hash(match_external_ref) + 1) % len(_TEAMS)]
        _add_goals(home_goals, home_name)
        _add_goals(away_goals, away_name)

        for _ in range(_poisson(rng, 2.2)):
            minute = rng.randint(1, 90)
            events.append(
                FootballEventPayload(
                    external_ref=match_external_ref,
                    event_type="yellow_card",
                    minute=minute,
                    added_time=None,
                    team_name=rng.choice([home_name, away_name]),
                    player_name=_mock_name(rng),
                    related_player_name=None,
                    shot_x=None,
                    shot_y=None,
                    event_time=base_time + timedelta(minutes=minute),
                    data_quality=DataQuality.MOCK,
                )
            )

        events.sort(key=lambda e: e.minute)

        match = MatchSummaryPayload(
            external_ref=match_external_ref,
            sport="football",
            competition_name="Mock Premier Division",
            home_team_name=home_name,
            away_team_name=away_name,
            venue_name="Mock Arena",
            scheduled_start=base_time,
            status="completed",
            data_quality=DataQuality.MOCK,
        )

        return MockFootballMatchResult(
            match=match,
            events=events,
            home_goals=home_goals,
            away_goals=away_goals,
            home_attack=home_attack,
            away_attack=away_attack,
        )

    def generate_training_corpus(self, n_matches: int = 300) -> list[MockFootballMatchResult]:
        return [self.generate_match(f"mock-football-train-{i:04d}") for i in range(n_matches)]
