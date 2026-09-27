"""Sample-size shrinkage for small-sample aggregates.

Per the spec's rule that "small samples must be clearly identified" and
never treated as strong evidence: a batter-vs-bowler matchup built from 4
balls should not be trusted as much as one built from 400. This applies a
standard empirical-Bayes-style shrinkage — pull the observed rate toward a
population prior in proportion to how little data supports it.
"""


def shrink_rate(observed_rate: float, sample_size: int, prior_rate: float, prior_strength: float = 20.0) -> float:
    """Blend `observed_rate` toward `prior_rate`.

    `prior_strength` is the "equivalent sample size" of the prior — with
    `sample_size=0` the result is exactly `prior_rate`; as `sample_size`
    grows large relative to `prior_strength`, the result converges to
    `observed_rate`.
    """
    if sample_size < 0:
        raise ValueError("sample_size must be >= 0")
    weight = sample_size / (sample_size + prior_strength)
    return weight * observed_rate + (1 - weight) * prior_rate


def confidence_label(sample_size: int, low: int = 10, medium: int = 50) -> str:
    """Coarse, human-facing confidence label for a sample size — used
    wherever the UI needs to flag "small sample" rather than silently
    presenting a shrunken rate as if it were fully reliable.
    """
    if sample_size < low:
        return "low"
    if sample_size < medium:
        return "medium"
    return "high"
