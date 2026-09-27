from datetime import datetime, timezone

import pytest

from data.ingestion.providers.types import DeliveryPayload, FootballEventPayload
from data.validation.exceptions import InvalidDataError
from data.validation.schema_checks import (
    validate_delivery,
    validate_delivery_sequence_monotonic,
    validate_football_event,
)
from database.models.enums import DataQuality

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _delivery(**overrides) -> DeliveryPayload:
    defaults = dict(
        external_ref="match-1",
        innings_number=1,
        sequence=1,
        over_number=0,
        ball_number=1,
        batter_name="Batter A",
        bowler_name="Bowler A",
        non_striker_name="Batter B",
        runs_batter=1,
        runs_extras=0,
        extras_type=None,
        is_wicket=False,
        dismissal_type=None,
        dismissed_player_name=None,
        score_before_ball=0,
        wickets_before_ball=0,
        delivery_time=NOW,
        data_quality=DataQuality.MOCK,
    )
    defaults.update(overrides)
    return DeliveryPayload(**defaults)


def test_validate_delivery_accepts_normal_ball():
    assert validate_delivery(_delivery()) == []


def test_validate_delivery_rejects_impossible_runs():
    with pytest.raises(InvalidDataError):
        validate_delivery(_delivery(runs_batter=7))


def test_validate_delivery_rejects_negative_extras():
    with pytest.raises(InvalidDataError):
        validate_delivery(_delivery(runs_extras=-1))


def test_validate_delivery_rejects_too_many_wickets():
    with pytest.raises(InvalidDataError):
        validate_delivery(_delivery(wickets_before_ball=11))


def test_validate_delivery_rejects_delivery_before_match_start():
    from datetime import timedelta

    with pytest.raises(InvalidDataError):
        validate_delivery(_delivery(delivery_time=NOW - timedelta(hours=1)), match_scheduled_start=NOW)


def test_validate_delivery_warns_on_wicket_without_dismissal_type():
    warnings = validate_delivery(_delivery(is_wicket=True, dismissal_type=None))
    assert any("dismissal_type" in w for w in warnings)


def test_validate_delivery_sequence_monotonic_accepts_increasing():
    validate_delivery_sequence_monotonic([_delivery(sequence=1), _delivery(sequence=2)])  # must not raise


def test_validate_delivery_sequence_monotonic_rejects_repeat():
    with pytest.raises(InvalidDataError):
        validate_delivery_sequence_monotonic([_delivery(sequence=1), _delivery(sequence=1)])


def _football_event(**overrides) -> FootballEventPayload:
    defaults = dict(
        external_ref="match-1",
        event_type="goal",
        minute=45,
        added_time=None,
        team_name="Team A",
        player_name="Player A",
        related_player_name=None,
        shot_x=80.0,
        shot_y=50.0,
        event_time=NOW,
        data_quality=DataQuality.MOCK,
    )
    defaults.update(overrides)
    return FootballEventPayload(**defaults)


def test_validate_football_event_accepts_normal_goal():
    assert validate_football_event(_football_event()) == []


def test_validate_football_event_rejects_impossible_minute():
    with pytest.raises(InvalidDataError):
        validate_football_event(_football_event(minute=200))


def test_validate_football_event_rejects_out_of_range_shot_coordinates():
    with pytest.raises(InvalidDataError):
        validate_football_event(_football_event(shot_x=150.0))


def test_validate_football_event_warns_on_goal_without_player():
    warnings = validate_football_event(_football_event(player_name=None))
    assert any("player_name" in w for w in warnings)
