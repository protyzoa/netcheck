"""Abstract base class for all network checkers."""

from abc import ABC, abstractmethod

from netcheck.core.models import CheckResult


class BaseChecker(ABC):
    """Base class that all checker modules must implement.

    Each checker is responsible for one category of network diagnostics.
    Checkers are run sequentially by the CheckerEngine, and results are
    emitted as they complete.
    """

    @abstractmethod
    def check(self) -> list[CheckResult]:
        """Run the check and return results.

        Returns:
            A list of CheckResult objects. A single checker may return
            multiple results (e.g., adapter checker returns one result
            per active adapter).
        """
        ...

    @abstractmethod
    def name(self) -> str:
        """Return the unique name identifier for this checker.

        Returns:
            A string identifier, e.g. "adapter", "dns", "gateway".
        """
        ...

    def depends_on(self) -> list[str]:
        """Return names of checkers this one depends on.

        If any dependency checker has FAIL status, this checker will
        be skipped. Override to specify dependencies.

        Returns:
            List of checker name strings.
        """
        return []

