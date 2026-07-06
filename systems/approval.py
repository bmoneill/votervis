"""Approval Voting system implementation."""

from collections import defaultdict

from candidate import Candidate
from result import ElectionResult, RoundSummary
from systems.base import BallotType, ElectionSystem


class ApprovalVoting(ElectionSystem):
    """Approval Voting: each voter may approve any number of candidates;
    every approved candidate receives one approval.  The candidate(s) with
    the most approvals win."""

    name: str = "Approval Voting"
    description: str = (
        "Voters approve as many candidates as they wish; "
        "the candidate with the most approvals wins."
    )

    @property
    def ballot_type(self) -> BallotType:
        return BallotType.APPROVAL

    def cast_ballot(self, approved: set["Candidate"]) -> None:
        """Record an approval ballot.

        Args:
            approved: Set of Candidate objects the voter approves of.
        """
        self.ballots.append(set(approved))

    def run_election(self) -> ElectionResult:
        """Tally approvals and return the election result.

        Each ballot contributes 1 approval to every candidate it contains.
        Ties return all tied candidates in the winners list.
        """
        approvals: dict[str, int] = defaultdict(int)

        # Initialise every candidate at 0
        for c in self.candidates:
            approvals[c.name] = 0

        for ballot in self.ballots:
            for candidate in ballot:
                approvals[candidate.name] += 1

        vote_counts = dict(approvals)
        total_ballots = len(self.ballots)

        if not self.ballots:
            return ElectionResult(
                system_name=self.name,
                winners=[],
                vote_counts=vote_counts,
                total_ballots=0,
                seats=1,
                rounds=[],
                message="No ballots were cast.",
            )

        max_approvals = max(vote_counts.values())
        winner_names = {name for name, v in vote_counts.items() if v == max_approvals}
        winners = [c for c in self.candidates if c.name in winner_names]

        if len(winners) == 1:
            message = (
                f"{winners[0]} wins with {max_approvals} approval"
                f"{'s' if max_approvals != 1 else ''} "
                f"from {total_ballots} ballot"
                f"{'s' if total_ballots != 1 else ''}."
            )
        else:
            names = ", ".join(str(w) for w in winners)
            message = (
                f"Tie between {names} — each received {max_approvals} approval"
                f"{'s' if max_approvals != 1 else ''} "
                f"from {total_ballots} ballot"
                f"{'s' if total_ballots != 1 else ''}."
            )

        rounds = [
            RoundSummary(
                round_number=1,
                vote_counts=vote_counts,
                elected=[w.name for w in winners],
                note="Approval totals" + (" — tie" if len(winners) > 1 else ""),
            )
        ]

        return ElectionResult(
            system_name=self.name,
            winners=winners,
            vote_counts=vote_counts,
            total_ballots=total_ballots,
            seats=1,
            rounds=rounds,
            message=message,
        )
