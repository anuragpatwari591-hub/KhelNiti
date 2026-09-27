class DataValidationError(Exception):
    """Base class for all data-validation failures."""


class LeakageError(DataValidationError):
    """A feature's timestamp is after the prediction timestamp it would be
    used for — using it would leak future information into a prediction."""


class DuplicateDataError(DataValidationError):
    """The same match/delivery/event is being ingested more than once."""


class InvalidDataError(DataValidationError):
    """A record fails basic domain sanity checks (score, timestamp, etc.)."""


class ProbabilityError(DataValidationError):
    """A probability value or distribution violates the 0..1 / sums-to-1 rule."""
