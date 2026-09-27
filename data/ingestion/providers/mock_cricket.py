"""Mock cricket data provider — development/test only.

Generates synthetic T20 matches ball-by-ball using a phase-aware random
model (powerplay / middle / death overs have different run and wicket
distributions, matching real T20 scoring patterns qualitatively). This is
NOT real match data: every payload carries `data_quality=DataQuality.MOCK`
so it can never be confused with production data downstream. It exists so
the platform is runnable and testable — including training a genuinely
functioning model end-to-end — without any provider credentials.

To wire in a real provider, implement `CricketDataProvider` against a
licensed ball-by-ball data vendor and register it in
`data/ingestion/providers/registry.py` (see docs/DATA_SOURCES.md).
"""
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from data.ingestion.providers.base import CricketDataProvider
from data.ingestion.providers.types import DeliveryPayload, MatchSummaryPayload
from database.models.enums import DataQuality

_TEAMS = [
    "Mock Strikers", "Mock Titans", "Mock Warriors", "Mock Riders",
    "Mock Kings", "Mock Super Giants", "Mock Capitals", "Mock Royals",
]

_FIRST_NAMES = [
    "Arjun", "Rohan", "Vikram", "Karan", "Aditya", "Sanjay", "Rahul", "Dev",
    "Ishaan", "Neel", "Varun", "Aryan", "Kabir", "Shaurya", "Yuvan", "Reyansh",
]
_LAST_NAMES = [
    "Sharma", "Verma", "Iyer", "Nair", "Rathore", "Chauhan", "Malhotra",
    "Bhatt", "Reddy", "Menon", "Kapoor", "Joshi", "Singh", "Pillai",
]


def _mock_name(rng: random.Random) -> str:
    return f"{rng.choice(_FIRST_NAMES)} {rng.choice(_LAST_NAMES)}"


def _phase(over_number: int) -> str:
    if over_number < 6:
        return "powerplay"
    if over_number < 16:
        return "middle"
    return "death"


# (runs distribution weights for 0,1,2,3,4,6, wicket_probability) per phase
_PHASE_PROFILE = {
    "powerplay": {"weights": [0.34, 0.30, 0.08, 0.02, 0.18, 0.08], "wicket_p": 0.035},
    "middle": {"weights": [0.38, 0.34, 0.10, 0.02, 0.11, 0.05], "wicket_p": 0.028},
    "death": {"weights": [0.28, 0.24, 0.06, 0.01, 0.20, 0.21], "wicket_p": 0.055},
}
_RUN_VALUES = [0, 1, 2, 3, 4, 6]


@dataclass
class _InningsResult:
    deliveries: list[DeliveryPayload]
    total_runs: int
    total_wickets: int


def _simulate_innings(
    rng: random.Random,
    match_external_ref: str,
    innings_number: int,
    batting_players: list[str],
    bowling_players: list[str],
    base_time: datetime,
    target: int | None,
    max_overs: int = 20,
) -> _InningsResult:
    deliveries: list[DeliveryPayload] = []
    runs = 0
    wickets = 0
    sequence = 0
    batter_idx = 0
    non_striker_idx = 1
    ball_time = base_time

    for over_number in range(max_overs):
        if wickets >= 10 or (target is not None and runs >= target):
            break
        phase = _phase(over_number)
        profile = _PHASE_PROFILE[phase]

        for ball_number in range(1, 7):
            if wickets >= 10 or (target is not None and runs >= target):
                break
            sequence += 1
            ball_time = ball_time + timedelta(seconds=90)
            score_before = runs
            wickets_before = wickets

            is_wicket = rng.random() < profile["wicket_p"] and wickets < 9
            runs_batter = 0
            extras = 0
            extras_type = None
            dismissal_type = None
            dismissed_name = None

            if rng.random() < 0.06:
                extras = 1
                extras_type = rng.choice(["wide", "no_ball", "bye", "leg_bye"])
                runs += extras
            elif is_wicket:
                wickets += 1
                dismissal_type = rng.choice(["bowled", "caught", "lbw", "run_out", "stumped"])
                dismissed_name = batting_players[batter_idx % len(batting_players)]
            else:
                runs_batter = rng.choices(_RUN_VALUES, weights=profile["weights"], k=1)[0]
                runs += runs_batter

            deliveries.append(
                DeliveryPayload(
                    external_ref=match_external_ref,
                    innings_number=innings_number,
                    sequence=sequence,
                    over_number=over_number,
                    ball_number=ball_number,
                    batter_name=batting_players[batter_idx % len(batting_players)],
                    bowler_name=bowling_players[over_number % len(bowling_players)],
                    non_striker_name=batting_players[non_striker_idx % len(batting_players)],
                    runs_batter=runs_batter,
                    runs_extras=extras,
                    extras_type=extras_type,
                    is_wicket=is_wicket,
                    dismissal_type=dismissal_type,
                    dismissed_player_name=dismissed_name,
                    score_before_ball=score_before,
                    wickets_before_ball=wickets_before,
                    delivery_time=ball_time,
                    data_quality=DataQuality.MOCK,
                )
            )

            if is_wicket:
                batter_idx = max(batter_idx, non_striker_idx) + 1
            elif runs_batter % 2 == 1:
                batter_idx, non_striker_idx = non_striker_idx, batter_idx

    return _InningsResult(deliveries=deliveries, total_runs=runs, total_wickets=wickets)


@dataclass
class MockMatchResult:
    match: MatchSummaryPayload
    deliveries: list[DeliveryPayload]
    first_innings_runs: int
    second_innings_runs: int
    winner: str  # "home" | "away"


class MockCricketProvider(CricketDataProvider):
    """Deterministic (seeded) synthetic cricket data for dev/test/training."""

    def __init__(self, seed: int = 42):
        self._seed = seed

    @property
    def provider_name(self) -> str:
        return "mock-cricket"

    def _rng_for(self, external_ref: str) -> random.Random:
        return random.Random(f"{self._seed}:{external_ref}")

    def get_live_matches(self) -> list[MatchSummaryPayload]:
        now = datetime.now(timezone.utc)
        return [
            MatchSummaryPayload(
                external_ref="mock-cricket-live-1",
                sport="cricket",
                competition_name="Mock T20 Premier League",
                home_team_name=_TEAMS[0],
                away_team_name=_TEAMS[1],
                venue_name="Mock Central Stadium",
                scheduled_start=now - timedelta(minutes=45),
                status="live",
                data_quality=DataQuality.MOCK,
            )
        ]

    def get_deliveries(self, match_external_ref: str, since_sequence: int | None = None) -> list[DeliveryPayload]:
        result = self.generate_match(match_external_ref)
        if since_sequence is None:
            return result.deliveries
        return [d for d in result.deliveries if d.sequence > since_sequence]

    def generate_match(self, match_external_ref: str) -> MockMatchResult:
        """Mock-only helper (not part of the CricketDataProvider interface):
        deterministically generates one full two-innings T20 match, used by
        both live-mode simulation and by ml/training to build a synthetic
        but schema-correct training corpus.
        """
        rng = self._rng_for(match_external_ref)
        home_players = [_mock_name(rng) for _ in range(11)]
        away_players = [_mock_name(rng) for _ in range(11)]
        base_time = datetime.now(timezone.utc) - timedelta(hours=3)

        first = _simulate_innings(
            rng, match_external_ref, 1, home_players, away_players, base_time, target=None
        )
        second_start = base_time + timedelta(minutes=100)
        second = _simulate_innings(
            rng, match_external_ref, 2, away_players, home_players, second_start,
            target=first.total_runs + 1,
        )

        winner = "away" if second.total_runs >= first.total_runs + 1 else "home"

        match = MatchSummaryPayload(
            external_ref=match_external_ref,
            sport="cricket",
            competition_name="Mock T20 Premier League",
            home_team_name=_TEAMS[hash(match_external_ref) % len(_TEAMS)],
            away_team_name=_TEAMS[(hash(match_external_ref) + 1) % len(_TEAMS)],
            venue_name="Mock Central Stadium",
            scheduled_start=base_time,
            status="completed",
            data_quality=DataQuality.MOCK,
        )

        return MockMatchResult(
            match=match,
            deliveries=first.deliveries + second.deliveries,
            first_innings_runs=first.total_runs,
            second_innings_runs=second.total_runs,
            winner=winner,
        )

    def generate_training_corpus(self, n_matches: int = 300) -> list[MockMatchResult]:
        """Mock-only helper: a batch of deterministic synthetic matches for
        model training/backtesting. Always labeled `data_quality=mock`.
        """
        return [self.generate_match(f"mock-cricket-train-{i:04d}") for i in range(n_matches)]
