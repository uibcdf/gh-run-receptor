"""Defining the stable process exit-code contract."""

SUCCESS = 0
FAILURE = 1
TERMINAL_NON_SUCCESS = 2
PENDING = 3
INCOMPLETE = 4
RECEPTOR_ERROR = 5
USAGE_ERROR = 64
INTERRUPTED = 130

ALL = frozenset(
    {
        SUCCESS,
        FAILURE,
        TERMINAL_NON_SUCCESS,
        PENDING,
        INCOMPLETE,
        RECEPTOR_ERROR,
        USAGE_ERROR,
        INTERRUPTED,
    }
)
