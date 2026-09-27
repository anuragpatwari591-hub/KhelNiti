"""Train the football Dixon-Coles expected-goals model on the mock corpus.

Run: python -m ml.training.train_football_expected_goals
"""
import os
from datetime import date, timedelta

from data.ingestion.providers.mock_football import MockFootballProvider
from ml.backtesting.splits import temporal_split
from ml.calibration.metrics import multiclass_accuracy, multiclass_brier_score, multiclass_log_loss
from ml.football.expected_goals import MatchResult, fit_dixon_coles, outcome_probabilities

MODEL_NAME = "football_match_outcome"


def _label(home_goals: int, away_goals: int) -> str:
    if home_goals > away_goals:
        return "home"
    if home_goals < away_goals:
        return "away"
    return "draw"


def main():
    provider = MockFootballProvider(seed=7)
    n_matches = 400
    matches = provider.generate_training_corpus(n_matches=n_matches)
    base = date.today()
    dated = [(base - timedelta(days=n_matches - i), m) for i, m in enumerate(matches)]

    split = temporal_split(dated, date_key=lambda dm: dm[0], train_frac=0.70, validation_frac=0.15)
    print(f"train: {len(split.train)} matches {split.train_range}")
    print(f"validation: {len(split.validation)} matches {split.validation_range}")
    print(f"test: {len(split.test)} matches {split.test_range}")

    train_results = [
        MatchResult(m.match.home_team_name, m.match.away_team_name, m.home_goals, m.away_goals, d)
        for d, m in split.train
    ]
    model = fit_dixon_coles(train_results, xi=0.0)
    model.version = "1.0.0-mock"

    def _evaluate(dated_matches):
        distributions, labels = [], []
        for _, m in dated_matches:
            matrix = model.score_matrix(m.match.home_team_name, m.match.away_team_name)
            distributions.append(outcome_probabilities(matrix))
            labels.append(_label(m.home_goals, m.away_goals))
        return {
            "brier_score": multiclass_brier_score(distributions, labels),
            "log_loss": multiclass_log_loss(distributions, labels),
            "accuracy": multiclass_accuracy(distributions, labels),
        }

    validation_metrics = _evaluate(split.validation)
    test_metrics = _evaluate(split.test)
    print(f"\nfitted: home_advantage={model.home_advantage:.3f} rho={model.rho:.3f}")
    print(f"attack strengths: { {k: round(v, 3) for k, v in model.attack.items()} }")
    print(f"\nvalidation metrics: {validation_metrics}")
    print(f"test metrics: {test_metrics}")

    os.makedirs("ml/artifacts", exist_ok=True)
    artifact_path = f"ml/artifacts/{MODEL_NAME}_{model.version}.joblib"
    model.save(artifact_path)
    print(f"\nsaved artifact to {artifact_path}")

    _persist_to_db(model.version, split, validation_metrics, test_metrics, artifact_path)


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
            sport=Sport.FOOTBALL,
            model_name=MODEL_NAME,
            version=version,
            trained_at=datetime.now(timezone.utc),
            training_data_start=split.train_range[0],
            training_data_end=split.train_range[1],
            hyperparameters={"model": "dixon_coles_poisson"},
            artifact_path=artifact_path,
            is_active=True,
            notes="Trained on MockFootballProvider synthetic data — see docs/DATA_SOURCES.md.",
        )
        session.add(model_version)
        session.flush()

        for metric_name, value in test_metrics.items():
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
            sport=Sport.FOOTBALL,
            model_name=MODEL_NAME,
            model_version=version,
            train_range=split.train_range,
            validation_range=split.validation_range,
            test_range=split.test_range,
            metrics={"validation": validation_metrics, "test": test_metrics},
            notes="Trained on MockFootballProvider synthetic data — see docs/DATA_SOURCES.md.",
        )
        session.commit()
        print(
            f"persisted model_versions.id={model_version.id}, "
            f"backtest_runs.id={backtest_run.id} with {len(test_metrics)} metrics"
        )


if __name__ == "__main__":
    main()
