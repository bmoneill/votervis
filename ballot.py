"""Ballot types used across the different voting systems."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from candidate import Candidate


@dataclass
class RankedBallot:
    """An ordered list of candidate preferences (first choice first).

    Used by: RCV/IRV, STV, Borda Count, Condorcet.
    Partial rankings are allowed — unranked candidates are treated as least-preferred.
    """

    ranking: list["Candidate"] = field(default_factory=list)


@dataclass
class ApprovalBallot:
    """A set of candidates the voter approves of.

    Used by: Approval Voting.
    """

    approved: set["Candidate"] = field(default_factory=set)
