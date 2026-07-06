"""Borda Count voting system implementation."""

from collections import defaultdict

from candidate import Candidate
from result import ElectionResult, RoundSummary
from systems.base import BallotType, ElectionSystem


class BordaCount(ElectionSystem):
    """Borda Count: voters rank all candidates; rank 1 earns (n-1) points,
    rank 2 earns (n-2) points, …, last place earns 0.  Unranked candidates
    receive 0 points.  The candidate(s) with the highest total win."""

    name: str = "Borda Count"
    description: str = (
        "Positional scoring rule — candidates earn points based on their "
        "position on each ranked ballot; most points wins."
    )

    @property
    def ballot_type(self) -> BallotType:
        return BallotType.RANKED

    def cast_ballot(self, ranking: list["Candidate"]) -> None:
        """Record a ranked ballot.

        Args:
            ranking: Ordered list of Candidate objects, most-preferred first.
        """
        self.ballots.append(list(ranking))

    def run_election(self) -> ElectionResult:
        """Tally Borda points and return the election result.

        Each position *i* (0-indexed) awards ``n - 1 - i`` points, where
        *n* is the total number of candidates.  Candidates omitted from a
        ballot receive 0 points for that ballot.  Ties return all tied
        candidates in the winners list.
        """
        n = len(self.candidates)
        totals: dict[str, float] = defaultdict(float)

        # Initialise every candidate at 0 so they appear in vote_counts
        for c in self.candidates:
            totals[c.name] = 0.0

        for ballot in self.ballots:
            for position, candidate in enumerate(ballot):
                points = (n - 1) - position
                if points < 0:
                    points = 0  # extra candidates beyond n get nothing
                totals[candidate.name] += points

        vote_counts = dict(totals)
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

        max_points = max(vote_counts.values())
        winner_names = {name for name, pts in vote_counts.items() if pts == max_points}
        winners = [c for c in self.candidates if c.name in winner_names]

        if len(winners) == 1:
            message = (
                f"{winners[0]} wins with {max_points:g} Borda point"
                f"{'s' if max_points != 1 else ''} "
                f"across {total_ballots} ballot"
                f"{'s' if total_ballots != 1 else ''}."
            )
        else:
            names = ", ".join(str(w) for w in winners)
            message = (
                f"Tie between {names} — each scored {max_points:g} Borda point"
                f"{'s' if max_points != 1 else ''} "
                f"across {total_ballots} ballot"
                f"{'s' if total_ballots != 1 else ''}."
            )

        rounds = [
            RoundSummary(
                round_number=1,
                vote_counts=vote_counts,
                elected=[w.name for w in winners],
                note="Borda point totals" + (" — tie" if len(winners) > 1 else ""),
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
