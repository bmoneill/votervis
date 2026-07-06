"""Result objects returned by election systems."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from candidate import Candidate


@dataclass
class RoundSummary:
    """A snapshot of vote counts at the end of one counting round."""

    round_number: int
    vote_counts: dict[str, Any]  # candidate name → weighted votes
    quota: float | None = None  # Droop quota (for STV/RCV)
    elected: list[str] = field(
        default_factory=list
    )  # candidate names elected this round
    eliminated: str | None = None  # candidate name eliminated this round
    note: str = ""


@dataclass
class ElectionResult:
    """Final result returned by every election system."""

    system_name: str
    winners: list["Candidate"]
    vote_counts: dict[str, Any]  # final tally: candidate name → votes/points
    total_ballots: int
    seats: int = 1
    rounds: list[RoundSummary] = field(default_factory=list)
    message: str = ""

    # Two-Round System: round-1 may signal that a runoff is required
    needs_runoff: bool = False
    runoff_candidates: list["Candidate"] = field(default_factory=list)

    # AMS: track how each winner got their seat
    seat_types: dict[str, str] = field(
        default_factory=dict
    )  # name → "constituency"|"list"

    # AMS: extra details attached by AMSElection.run_election()
    party_votes: dict[str, Any] | None = None  # party name → vote count
    dhondt_allocation: dict[str, Any] | None = None  # party name → total seats

    # Condorcet: pairwise comparison matrix attached by CondorcetElection.run_election()
    pairwise: dict[str, Any] | None = None  # {name_a: {name_b: count}}
