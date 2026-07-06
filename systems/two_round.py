"""Two-Round System (TRS) voting system implementation."""

from collections import Counter

from candidate import Candidate
from result import ElectionResult, RoundSummary
from systems.base import BallotType, ElectionSystem


class TwoRoundSystem(ElectionSystem):
    """Two-Round System: if no candidate wins an outright majority in round 1,
    the top two advance to a runoff.  The runoff winner takes the seat."""

    name: str = "Two-Round System"
    description: str = (
        "Majority-runoff system — a candidate wins outright with >50 % in "
        "round 1; otherwise the top two face a second decisive round."
    )

    def __init__(self, candidates, seats: int = 1):
        super().__init__(candidates, seats)
        self.round: int = 1
        self.round1_ballots: list = []
        self.round2_ballots: list = []
        self.runoff_candidates: list = []  # List[Candidate]

    @property
    def ballot_type(self) -> BallotType:
        return BallotType.SINGLE

    def cast_ballot(self, candidate: Candidate) -> None:
        """Record a vote for *candidate* in the current round.

        Round-2 ballots are validated against the declared runoff candidates;
        an attempt to vote for someone not on the runoff ballot raises
        ValueError.
        """
        if self.round == 1:
            self.round1_ballots.append(candidate)
            self.ballots.append(candidate)
        elif self.round == 2:
            runoff_names = {c.name for c in self.runoff_candidates}
            if candidate.name not in runoff_names:
                raise ValueError(
                    f"{candidate} is not a runoff candidate. "
                    f"Valid choices: {', '.join(runoff_names)}"
                )
            self.round2_ballots.append(candidate)
            self.ballots.append(candidate)
        else:
            raise RuntimeError(f"Unexpected round number: {self.round}")

    # ------------------------------------------------------------------
    # Round helpers
    # ------------------------------------------------------------------

    def finalize_round1(self) -> ElectionResult:
        """Evaluate round-1 ballots.

        Returns an ElectionResult with needs_runoff=False when a majority
        winner exists, or needs_runoff=True with the top-two runoff
        candidates identified.
        """
        counts = Counter(b.name for b in self.round1_ballots)
        total = len(self.round1_ballots)

        vote_counts = {c.name: counts.get(c.name, 0) for c in self.candidates}

        round1_summary = RoundSummary(
            round_number=1,
            vote_counts=vote_counts,
        )

        if total == 0:
            return ElectionResult(
                system_name=self.name,
                winners=[],
                vote_counts=vote_counts,
                total_ballots=0,
                seats=1,
                rounds=[round1_summary],
                message="No ballots were cast in round 1.",
            )

        # Check for an outright majority
        for candidate in self.candidates:
            v = counts.get(candidate.name, 0)
            if v > total / 2:
                round1_summary.elected = [candidate.name]
                round1_summary.note = "Outright majority — no runoff needed."
                return ElectionResult(
                    system_name=self.name,
                    winners=[candidate],
                    vote_counts=vote_counts,
                    total_ballots=total,
                    seats=1,
                    rounds=[round1_summary],
                    needs_runoff=False,
                    message=(
                        f"{candidate} wins outright with {v} vote"
                        f"{'s' if v != 1 else ''} ({v / total:.1%})."
                    ),
                )

        # No majority — identify top-2 for runoff (alphabetical name tiebreak)
        sorted_candidates = sorted(
            self.candidates,
            key=lambda c: (-counts.get(c.name, 0), c.name),
        )
        top2 = sorted_candidates[:2]
        self.runoff_candidates = top2
        self.round = 2

        round1_summary.note = (
            "No majority; runoff between " + " and ".join(c.name for c in top2) + "."
        )

        return ElectionResult(
            system_name=self.name,
            winners=[],
            vote_counts=vote_counts,
            total_ballots=total,
            seats=1,
            rounds=[round1_summary],
            needs_runoff=True,
            runoff_candidates=top2,
            message=(
                "No candidate achieved a majority. "
                "Runoff between: " + ", ".join(str(c) for c in top2) + "."
            ),
        )

    def finalize_round2(self) -> ElectionResult:
        """Evaluate round-2 ballots and declare a winner.

        In the event of a tie both candidates are returned as winners.
        """
        r2_counts = Counter(b.name for b in self.round2_ballots)
        r2_total = len(self.round2_ballots)

        # vote_counts for round 2 covers only runoff candidates
        r2_vote_counts = {
            c.name: r2_counts.get(c.name, 0) for c in self.runoff_candidates
        }

        # Reconstruct round-1 summary for the rounds list
        r1_counts = Counter(b.name for b in self.round1_ballots)
        r1_total = len(self.round1_ballots)
        r1_vote_counts = {c.name: r1_counts.get(c.name, 0) for c in self.candidates}
        round1_summary = RoundSummary(
            round_number=1,
            vote_counts=r1_vote_counts,
            note="No outright majority; advanced to runoff.",
        )

        round2_summary = RoundSummary(
            round_number=2,
            vote_counts=r2_vote_counts,
        )

        if r2_total == 0:
            return ElectionResult(
                system_name=self.name,
                winners=[],
                vote_counts=r2_vote_counts,
                total_ballots=r1_total + r2_total,
                seats=1,
                rounds=[round1_summary, round2_summary],
                message="No ballots were cast in round 2.",
            )

        max_votes = max(r2_counts.values(), default=0)
        winner_names = {name for name, v in r2_counts.items() if v == max_votes}
        winners = [c for c in self.runoff_candidates if c.name in winner_names]

        if len(winners) == 1:
            message = (
                f"{winners[0]} wins the runoff with {max_votes} vote"
                f"{'s' if max_votes != 1 else ''} "
                f"({max_votes / r2_total:.1%})."
            )
            round2_summary.elected = [winners[0].name]
            round2_summary.note = "Runoff winner."
        else:
            names = ", ".join(str(w) for w in winners)
            message = (
                f"Runoff tie between {names} — "
                f"each received {max_votes} vote"
                f"{'s' if max_votes != 1 else ''}."
            )
            round2_summary.elected = [w.name for w in winners]
            round2_summary.note = "Runoff ended in a tie."

        return ElectionResult(
            system_name=self.name,
            winners=winners,
            vote_counts=r2_vote_counts,
            total_ballots=r1_total + r2_total,
            seats=1,
            rounds=[round1_summary, round2_summary],
            message=message,
        )

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run_election(self) -> ElectionResult:
        """Run whichever round has ballots outstanding and return its result."""
        if self.round == 1:
            return self.finalize_round1()
        return self.finalize_round2()
