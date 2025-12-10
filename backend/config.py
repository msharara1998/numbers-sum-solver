"""Configuration constants for the Numbers Sum Solver backend."""

from datetime import timedelta

MAX_SOLVER_ITERATIONS: int = 100
SOLVER_ITERATION_DELAY: float = 0.1
SSE_POLL_INTERVAL: float = 0.05
SESSION_TIMEOUT: timedelta = timedelta(hours=1)
SESSION_CLEANUP_INTERVAL: int = 300
