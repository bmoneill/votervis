"""First Past the Post (FPTP) voting system implementation."""

from collections import Counter

from candidate import Candidate
from result import ElectionResult, RoundSummary
from systems.base import BallotType, ElectionSystem


class FirstPastThePost(ElectionSystem):
    """First Past the Post: each voter casts a single vote; the candidate
    with the most votes wins outright. Ties return all tied candidates."""

    name: str = "First Past the Post"
    description: str = (
        "Plurality voting — the candidate with the most votes wins, "
        "regardless of whether they hold an absolute majority."
    )

    @property
    def ballot_type(self) -> BallotType:
        return BallotType.SINGLE

    def cast_ballot(self, candidate: Candidate) -> None:
        """Record a single vote for *candidate*."""
        self.ballots.append(candidate)

    def run_election(self) -> ElectionResult:
        """Tally votes and return the election result.

        In the event of a tie the winners list contains every candidate
        that shares the highest vote count.
        """
        counts = Counter(ballot.name for ballot in self.ballots)
        total = len(self.ballots)

        # Build a vote_counts dict for every candidate (including zero-vote ones)
        vote_counts = {c.name: counts.get(c.name, 0) for c in self.candidates}

        if not counts:
            return ElectionResult(
                system_name=self.name,
                winners=[],
                vote_counts=vote_counts,
                total_ballots=total,
                seats=1,
                rounds=[],
                message="No ballots were cast.",
            )

        max_votes = max(counts.values())
        winner_names = {name for name, v in counts.items() if v == max_votes}
        winners = [c for c in self.candidates if c.name in winner_names]

        if len(winners) == 1:
            message = (
                f"{winners[0]} wins with {max_votes} vote"
                f"{'s' if max_votes != 1 else ''} "
                f"({max_votes / total:.1%} of {total} ballots)."
            )
        else:
            names = ", ".join(str(w) for w in winners)
            message = (
                f"Tie between {names} — each received {max_votes} vote"
                f"{'s' if max_votes != 1 else ''} "
                f"({max_votes / total:.1%} of {total} ballots)."
            )

        rounds = [
            RoundSummary(
                round_number=1,
                vote_counts=vote_counts,
                elected=[w.name for w in winners],
                note="Final tally" + (" — tie" if len(winners) > 1 else ""),
            )
        ]

        return ElectionResult(
            system_name=self.name,
            winners=winners,
            vote_counts=vote_counts,
            total_ballots=total,
            seats=1,
            rounds=rounds,
            message=message,
        )
