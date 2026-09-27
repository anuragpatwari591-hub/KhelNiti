"""Train the cricket win-probability ensemble on the mock training corpus.

Run: python -m ml.training.train_cricket_win_probability

This is a genuine, working training pipeline — chronological split, real
logistic regression fit, real calibration metrics computed on held-out
data — but it currently trains on `MockCricketProvider` synthetic matches
because no real ball-by-ball provider is configured (see
docs/DATA_SOURCES.md). Swap `get_cricket_provider()` for a real provider
and this script does not need to change.
"""
import os
from datetime import date, timedelta

from sklearn.linear_model import LogisticRegression

from data.ingestion.providers.mock_cricket import MockCricketProvider, MockMatchResult
from ml.backtesting.splits import temporal_split
from ml.calibration.metrics import accuracy, brier_score, expected_calibration_error, log_loss
from ml.cricket.features import build_match_state, extract_features, feature_vector
from ml.cricket.monte_carlo import estimate_phase_distributions, simulate_match_win_probability
from ml.cricket.win_probability import CricketWinProbabilityEnsemble

MODEL_NAME = "cricket_win_probability"
CHECKPOINT_STRIDE = 12  # sample a state roughly every two overs


def _dated(matches: list[MockMatchResult], base: date) -> list[tuple[date, MockMatchResult]]:
    return [(base - timedelta(days=len(matches) - i), m) for i, m in enumerate(matches)]


def _label_and_state(result: MockMatchResult, innings_number: int, idx: int):
    innings_deliveries = [d for d in result.deliveries if d.innings_number == innings_number]
    if idx >= len(innings_deliveries):
        return None
    target = result.first_innings_runs + 1 if innings_number == 2 else None
    state = build_match_state(innings_deliveries[: idx + 1], innings_number, target)
    batting_team_wins = (innings_number == 1 and result.winner == "home") or (
        innings_number == 2 and result.winner == "away"
    )
    return state, int(batting_team_wins)


def build_examples(dated_matches: list[tuple[date, MockMatchResult]]):
    examples = []
    for match_date, result in dated_matches:
        for innings_number in (1, 2):
            innings_deliveries = [d for d in result.deliveries if d.innings_number == innings_number]
            for idx in range(CHECKPOINT_STRIDE, len(innings_deliveries), CHECKPOINT_STRIDE):
                labeled = _label_and_state(result, innings_number, idx)
                if labeled is None:
                    continue
                state, label = labeled
                examples.append((match_date, state, label))
    return examples


def _evaluate(model, distributions, examples, n_simulations=300):
    logistic_probs, mc_probs, blended_probs, labels = [], [], [], []
    for _, state, label in examples:
        features = extract_features(state)
        vector = [feature_vector(features)]
        logistic_p = float(model.predict_proba(vector)[0, 1])
        mc = simulate_match_win_probability(
            distributions, state.innings_number, state.current_score, state.wickets_lost,
            state.balls_bowled, state.total_balls, state.target, n_simulations=n_simulations,
        )
        mc_p = mc["batting_team_win_probability"]
        logistic_probs.append(logistic_p)
        mc_probs.append(mc_p)
        blended_probs.append(0.5 * logistic_p + 0.5 * mc_p)
        labels.append(label)

    def _metrics(probs):
        return {
            "brier_score": brier_score(probs, labels),
            "log_loss": log_loss(probs, labels),
            "accuracy": accuracy(probs, labels),
            "expected_calibration_error": expected_calibration_error(probs, labels),
        }

    return {"logistic": _metrics(logistic_probs), "monte_carlo": _metrics(mc_probs), "ensemble": _metrics(blended_probs)}


def main():
    provider = MockCricketProvider(seed=42)
    n_matches = 260
    matches = provider.generate_training_corpus(n_matches=n_matches)
    dated_matches = _dated(matches, base=date.today())

    split = temporal_split(dated_matches, date_key=lambda dm: dm[0], train_frac=0.70, validation_frac=0.15)
    print(f"train: {len(split.train)} matches {split.train_range}")
    print(f"validation: {len(split.validation)} matches {split.validation_range}")
    print(f"test: {len(split.test)} matches {split.test_range}")

    train_examples = build_examples(split.train)
    validation_examples = build_examples(split.validation)
    test_examples = build_examples(split.test)
    print(f"examples -> train={len(train_examples)} validation={len(validation_examples)} test={len(test_examples)}")

    # Phase distributions are estimated ONLY from training-split deliveries,
    # so validation/test evaluation never leaks future-match statistics into
    # the simulator's priors.
    train_deliveries = [d for _, m in split.train for d in m.deliveries]
    distributions = estimate_phase_distributions(train_deliveries)

    X_train = [feature_vector(extract_features(state)) for _, state, _ in train_examples]
    y_train = [label for _, _, label in train_examples]
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    validation_metrics = _evaluate(model, distributions, validation_examples)
    test_metrics = _evaluate(model, distributions, test_examples)

    print("\nvalidation metrics:")
    for component, m in validation_metrics.items():
        print(f"  {component}: {m}")
    print("\ntest metrics:")
    for component, m in test_metrics.items():
        print(f"  {component}: {m}")

    version = "1.0.0-mock"
    os.makedirs("ml/artifacts", exist_ok=True)
    ensemble = CricketWinProbabilityEnsemble(model, distributions, version)
    artifact_path = f"ml/artifacts/{MODEL_NAME}_{version}.joblib"
    ensemble.save(artifact_path)
    print(f"\nsaved artifact to {artifact_path}")

    _persist_to_db(version, split, validation_metrics, test_metrics, artifact_path)


def _persist_to_db(version, split, validation_metrics, test_metrics, artifact_path):
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not set — skipping model_versions/model_metrics persistence")
        return

    from datetime import datetime, timezone

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from database.models.enums import Sport
    from database.models.predictions import ModelMetric, ModelVersion
    from ml.backtesting.runner import persist_backtest_run

    engine = create_engine(database_url)
    with Session(engine) as session:
        model_version = ModelVersion(
            sport=Sport.CRICKET,
            model_name=MODEL_NAME,
            version=version,
            trained_at=datetime.now(timezone.utc),
            training_data_start=split.train_range[0],
            training_data_end=split.train_range[1],
            hyperparameters={"model": "logistic_regression", "monte_carlo_blend_weight": 0.5},
            artifact_path=artifact_path,
            is_active=True,
            notes="Trained on MockCricketProvider synthetic data — see docs/DATA_SOURCES.md.",
        )
        session.add(model_version)
        session.flush()

        for metric_name, value in test_metrics["ensemble"].items():
            session.add(
                ModelMetric(
                    model_version_id=model_version.id,
                    metric_name=metric_name,
                    metric_value=value,
                    sample_size=len(split.test),
                    evaluated_at=datetime.now(timezone.utc),
                )
            )

        backtest_run = persist_backtest_run(
            session,
            sport=Sport.CRICKET,
            model_name=MODEL_NAME,
            model_version=version,
            train_range=split.train_range,
            validation_range=split.validation_range,
            test_range=split.test_range,
            metrics={"validation": validation_metrics, "test": test_metrics},
            notes="Trained on MockCricketProvider synthetic data — see docs/DATA_SOURCES.md.",
        )
        session.commit()
        print(
            f"persisted model_versions.id={model_version.id}, "
            f"backtest_runs.id={backtest_run.id} with {len(test_metrics['ensemble'])} ensemble metrics"
        )


if __name__ == "__main__":
    main()
