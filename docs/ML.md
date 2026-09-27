# Machine Learning

## Design principles

- **Leakage safety is enforced, not assumed.** Every feature is a
  `TimestampedFeature` (`data/validation/leakage.py`); `assert_no_leakage`
  rejects anything timestamped after the prediction it would feed.
- **No single model is trusted alone.** Cricket win probability blends a
  logistic regression with an independent Monte Carlo simulation and
  reports their agreement as `model_confidence`. Football uses Dixon-Coles
  (a well-established statistical technique, not a black box) rather than
  reaching for a heavier model that "sounds more advanced."
- **Splits are chronological, always.** `ml/backtesting/splits.py:temporal_split`
  sorts by date and cuts — there is no shuffle anywhere in the training or
  backtesting path. See `docs/BACKTESTING.md`.
- **Small samples are shrunk, not trusted.** `ml/feature_engineering/shrinkage.py`
  pulls low-sample-size aggregates (e.g. a batter-vs-bowler matchup from a
  handful of balls) toward a population prior.
- **Currently trained on mock data.** Every metric in this document comes
  from a real run against `MockCricketProvider`/`MockFootballProvider`
  synthetic corpora (see `docs/DATA_SOURCES.md`) — reproducible, but not
  evidence of skill on real matches. See `docs/MODEL_LIMITATIONS.md`.

## Cricket: win probability

`ml/cricket/`:

1. **Features** (`features.py`) — from deliveries bowled so far: balls
   remaining, wickets in hand, current run rate, required run rate (second
   innings), pressure index, phase indicators. All timestamped at the last
   delivery's `delivery_time`.
2. **Monte Carlo** (`monte_carlo.py`) — `estimate_phase_distributions`
   computes empirical run/wicket frequencies per phase (powerplay/middle/
   death) from historical deliveries; `simulate_match_win_probability`
   vectorized-simulates the rest of the match ball-by-ball (numpy), and for
   a first-innings state, simulates a representative sample of possible
   second-innings chases against the projected final-total distribution.
3. **Ensemble** (`win_probability.py`) — blends a logistic regression
   (fit on match-state feature vectors from historical checkpoints) with
   the Monte Carlo win fraction 50/50; `model_confidence = 1 - |gap|`
   between the two. Also exposes next-over run distribution, wicket
   probability, and boundary probability, all derived from the same
   empirical phase distributions.
4. **Explanation** — `_explain()` turns the actual feature values (not a
   template guess) into 1-3 plain-language factors, feeding the "why did
   the prediction change" audit trail.

**Verified result** (`ml/training/train_cricket_win_probability.py`, 260
matches, 70/15/15 chronological split, phase distributions estimated only
from the training split): test-set ensemble Brier score **0.176**,
accuracy **71.7%**, expected calibration error **0.035** — meaningfully
better than a no-skill 0.25 Brier / 50% accuracy baseline, and well
calibrated.

## Football: expected goals

`ml/football/expected_goals.py` implements Dixon-Coles (1997): each team
has an `attack` and `defense` parameter; goals are Poisson with
`mu_home = exp(attack_home - defense_away + home_advantage)`, plus the
paper's `tau` correction for the 0-0/1-0/0-1/1-1 scoreline correlation.
Parameters are fit by maximum likelihood (`scipy.optimize.minimize`) on
historical match goal counts — never hand-picked. `score_matrix()` builds
the full scoreline probability grid, from which
`outcome_probabilities`/`clean_sheet_probability`/
`both_teams_to_score_probability`/`top_scorelines` are all simple sums over
cells — no separate model per market.

`ml/football/monte_carlo.py` projects a live match's remaining minutes by
scaling the pre-match expected-goal rates to the time left and drawing
additional goals from a Poisson distribution — documented as a
simplification (no in-match tactical adjustment, e.g. "parking the bus").

**Verified result** (`ml/training/train_football_expected_goals.py`, 400
matches, 70/15/15 split): test-set 3-way (home/draw/away) accuracy
**61.7%**, Brier **0.54** — clearly above chance (33%) and the fitted
attack strengths recover the correct relative team ordering from the
underlying (otherwise hidden) generative parameters, which is the real
test of the estimator working correctly.

## Market data separation

`odds_snapshots` and `market_movements` (`database/models/context.py`) are
never joined into the feature vectors that `ml/cricket` or `ml/football`
consume by default. `market_movements.model_probability` is filled in
*after* the independent model runs, purely to compute a divergence metric
— the model never sees the market price as an input feature. This is
deliberate: it's the only way to later answer, with evidence, whether
market data would improve the independent model rather than just letting
it anchor on the market's own probability.

## Calibration

`ml/calibration/metrics.py`: `brier_score`, `log_loss`, `accuracy`,
`expected_calibration_error`, `reliability_bins` for binary forecasts, and
`multiclass_brier_score`/`multiclass_log_loss`/`multiclass_accuracy` for
K-outcome forecasts (football home/draw/away). These are the only source
of any accuracy/calibration figure presented anywhere in this project —
there is no hard-coded performance claim.

## Retraining

```bash
python -m ml.training.train_cricket_win_probability
python -m ml.training.train_football_expected_goals
```

Both scripts: generate/load a training corpus, split chronologically,
fit, evaluate on validation and test, save a joblib artifact to
`ml/artifacts/` (gitignored), and — if `DATABASE_URL` is set — persist a
`model_versions` row, `model_metrics` rows, and a `backtest_runs` row.
Nothing is persisted silently; if `DATABASE_URL` is unset the script
prints the metrics and exits without writing to a database.
