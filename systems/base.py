"""Abstract base class shared by all election systems."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from candidate import Candidate
    from result import ElectionResult


class BallotType(str, Enum):
    SINGLE = "single"  # one candidate per ballot (FPTP, Two-Round)
    RANKED = "ranked"  # ordered preference list (RCV, STV, Borda, Condorcet)
    APPROVAL = "approval"  # a set of approved candidates (Approval Voting)
    AMS = "ams"  # constituency vote + party vote (AMS)


class ElectionSystem(ABC):
    """Base class for all voting systems.

    Subclasses must set class attributes `name` and `description`, and
    implement `ballot_type`, `cast_ballot`, and `run_election`.
    """

    name: str = "Unknown System"
    description: str = ""

    def __init__(self, candidates: list["Candidate"], seats: int = 1) -> None:
        self.candidates: list["Candidate"] = list(candidates)
        self.seats: int = seats
        self.ballots: list = []

    @property
    @abstractmethod
    def ballot_type(self) -> BallotType:
        """The kind of ballot this system accepts."""

    def cast_ballot(self, *args, **kwargs) -> None:
        """Record a ballot. Argument signature varies per subclass by BallotType.

        Subclasses must override this method with their specific ballot parameter(s).
        """
        raise NotImplementedError(f"{type(self).__name__} must implement cast_ballot")

    @abstractmethod
    def run_election(self) -> "ElectionResult":
        """Tally all ballots and return the election result."""

    @property
    def ballot_count(self) -> int:
        return len(self.ballots)
