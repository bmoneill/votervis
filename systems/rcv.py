"""
Ranked-Choice Voting (Instant Runoff Voting) implementation.

Single-winner election using iterative elimination of the last-place candidate
until one candidate holds a majority of active votes.
"""

from candidate import Candidate
from result import ElectionResult, RoundSummary
from systems.base import BallotType, ElectionSystem


class RankedChoiceVoting(ElectionSystem):
    """
    Instant Runoff Voting (IRV) — single-winner ranked-choice system.

    Voters rank candidates in order of preference. If no candidate achieves
    a majority (>50%) of first-choice votes, the candidate with the fewest
    votes is eliminated and their votes are redistributed to the next
    active preference on each ballot. Repeats until a winner emerges.
    """

    name = "Ranked-Choice Voting (IRV)"
    description = (
        "Single-winner IRV: voters rank candidates; the last-place candidate "
        "is eliminated each round until one candidate holds a majority."
    )

    @property
    def ballot_type(self):
        return BallotType.RANKED

    def cast_ballot(self, ranking: list["Candidate"]):
        """
        Record a ranked ballot.

        Parameters
        ----------
        ranking : list[Candidate]
            Candidates in order of preference, most preferred first.
            Partial rankings are allowed.
        """
        self.ballots.append(list(ranking))

    def run_election(self) -> ElectionResult:
        """
        Run the IRV election and return an ElectionResult.

        Returns an empty result (no winners) if no ballots have been cast.
        """
        if not self.ballots:
            return ElectionResult(
                system_name=self.name,
                winners=[],
                vote_counts={},
                total_ballots=0,
                seats=1,
                message="No ballots cast.",
            )

        active_candidates = set(self.candidates)
        rounds = []
        round_num = 1

        while True:
            # Count first-choice votes among still-active candidates
            counts = {c: 0 for c in active_candidates}
            for ballot in self.ballots:
                for candidate in ballot:
                    if candidate in active_candidates:
                        counts[candidate] += 1
                        break
                # Exhausted ballots contribute nothing

            total_active_votes = sum(counts.values())

            if total_active_votes == 0:
                # All ballots are exhausted — no majority possible
                winner = (
                    max(counts, key=lambda c: (counts[c], -ord(c.name[0])))
                    if counts
                    else None
                )
                round_summary = RoundSummary(
                    round_number=round_num,
                    vote_counts={c.name: counts[c] for c in active_candidates},
                    elected=[winner.name] if winner else [],
                    note="All ballots exhausted; candidate with most votes wins.",
                )
                rounds.append(round_summary)
                final_counts = {c.name: counts[c] for c in active_candidates}
                return ElectionResult(
                    system_name=self.name,
                    winners=[winner] if winner else [],
                    vote_counts=final_counts,
                    total_ballots=len(self.ballots),
                    seats=1,
                    rounds=rounds,
                    message="All ballots exhausted before majority reached.",
                )

            # Check for majority winner
            for candidate, votes in counts.items():
                if votes > total_active_votes / 2:
                    final_counts = {c.name: counts[c] for c in active_candidates}
                    round_summary = RoundSummary(
                        round_number=round_num,
                        vote_counts=final_counts,
                        elected=[candidate.name],
                    )
                    rounds.append(round_summary)
                    return ElectionResult(
                        system_name=self.name,
                        winners=[candidate],
                        vote_counts=final_counts,
                        total_ballots=len(self.ballots),
                        seats=1,
                        rounds=rounds,
                    )

            # With 1 or 2 candidates and no majority, highest vote-getter wins
            if len(active_candidates) <= 2:
                winner = max(
                    counts, key=lambda c: (counts[c], [-ord(ch) for ch in c.name])
                )
                # Stable alphabetical tiebreak: higher votes wins; ties broken by name
                winner = max(
                    counts,
                    key=lambda c: (counts[c], tuple(-ord(ch) for ch in c.name)),
                )
                # Simpler: sort descending by votes, then ascending by name
                ranked = sorted(counts.keys(), key=lambda c: (-counts[c], c.name))
                winner = ranked[0]
                final_counts = {c.name: counts[c] for c in active_candidates}
                round_summary = RoundSummary(
                    round_number=round_num,
                    vote_counts=final_counts,
                    elected=[winner.name],
                    note="No majority; candidate with most votes wins.",
                )
                rounds.append(round_summary)
                return ElectionResult(
                    system_name=self.name,
                    winners=[winner],
                    vote_counts=final_counts,
                    total_ballots=len(self.ballots),
                    seats=1,
                    rounds=rounds,
                )

            # Eliminate the candidate with the fewest votes (alphabetical tiebreak)
            min_votes = min(counts.values())
            min_candidates = sorted(
                [c for c, v in counts.items() if v == min_votes],
                key=lambda c: c.name,
            )
            eliminated = min_candidates[0]
            active_candidates.remove(eliminated)

            round_summary = RoundSummary(
                round_number=round_num,
                vote_counts={c.name: counts[c] for c in counts},
                eliminated=eliminated.name,
            )
            rounds.append(round_summary)
            round_num += 1
