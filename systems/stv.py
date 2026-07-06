"""
Single Transferable Vote (STV) implementation.

Multi-winner proportional ranked-choice system using the Droop quota
and the Gregory method for fractional surplus transfers.
"""

from math import floor

from candidate import Candidate
from result import ElectionResult, RoundSummary
from systems.base import BallotType, ElectionSystem


class SingleTransferableVote(ElectionSystem):
    """
    Single Transferable Vote (STV) — multi-winner proportional system.

    Voters rank candidates in order of preference. A Droop quota is calculated
    and candidates who meet it are elected. Any surplus votes above the quota
    are transferred to remaining candidates using the Gregory method (fractional
    weights). If no candidate meets the quota, the lowest-scoring candidate is
    eliminated and their votes are redistributed. Continues until all seats
    are filled.
    """

    name = "Single Transferable Vote"
    description = (
        "Multi-winner STV with Droop quota and Gregory surplus transfer. "
        "Voters rank candidates; seats are filled proportionally."
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
        Run the STV election and return an ElectionResult.

        Returns an empty result (no winners) if no ballots have been cast.
        """
        if not self.ballots:
            return ElectionResult(
                system_name=self.name,
                winners=[],
                vote_counts={},
                total_ballots=0,
                seats=self.seats,
                message="No ballots cast.",
            )

        total_votes = len(self.ballots)
        quota = floor(total_votes / (self.seats + 1)) + 1

        # Each ballot carries a weight (starts at 1.0) — Gregory method
        weighted_ballots = [
            {"ranking": list(ballot), "weight": 1.0} for ballot in self.ballots
        ]

        active = set(self.candidates)
        elected = []
        rounds = []
        round_num = 1

        while len(elected) < self.seats:
            if not active:
                break

            # Count weighted first-choice votes for active candidates
            counts = {c: 0.0 for c in active}
            for wb in weighted_ballots:
                for c in wb["ranking"]:
                    if c in active:
                        counts[c] += wb["weight"]
                        break

            # Candidates at or above the quota
            above_quota = [(c, v) for c, v in counts.items() if v >= quota]

            if above_quota:
                # Elect the candidate with the highest votes (alphabetical tiebreak)
                above_quota.sort(key=lambda x: (-x[1], x[0].name))
                elect_c, elect_v = above_quota[0]
                elected.append(elect_c)
                active.remove(elect_c)

                # Transfer surplus using the Gregory method
                surplus = elect_v - quota
                if surplus > 0 and elect_v > 0:
                    transfer_ratio = surplus / elect_v
                    for wb in weighted_ballots:
                        # Does this ballot currently have the elected candidate on top?
                        top = next(
                            (c for c in wb["ranking"] if c in active or c == elect_c),
                            None,
                        )
                        if top == elect_c:
                            wb["weight"] *= transfer_ratio

                # Remove elected candidate from all rankings
                for wb in weighted_ballots:
                    wb["ranking"] = [c for c in wb["ranking"] if c != elect_c]

                round_summary = RoundSummary(
                    round_number=round_num,
                    vote_counts={c.name: round(v, 2) for c, v in counts.items()},
                    quota=quota,
                    elected=[elect_c.name],
                )

            else:
                # No one meets quota — eliminate the candidate with fewest votes
                min_v = min(counts.values())
                min_cs = sorted(
                    [c for c, v in counts.items() if v == min_v],
                    key=lambda c: c.name,
                )
                elim = min_cs[0]
                active.remove(elim)

                for wb in weighted_ballots:
                    wb["ranking"] = [c for c in wb["ranking"] if c != elim]

                round_summary = RoundSummary(
                    round_number=round_num,
                    vote_counts={c.name: round(v, 2) for c, v in counts.items()},
                    quota=quota,
                    eliminated=elim.name,
                )

            rounds.append(round_summary)
            round_num += 1

            # If remaining active candidates exactly fill remaining seats, elect them all
            remaining_seats = self.seats - len(elected)
            if 0 < len(active) <= remaining_seats:
                # Final tally for the summary
                final_counts = {c: 0.0 for c in active}
                for wb in weighted_ballots:
                    for c in wb["ranking"]:
                        if c in active:
                            final_counts[c] += wb["weight"]
                            break

                for c in sorted(active, key=lambda c: -final_counts.get(c, 0)):
                    elected.append(c)

                rounds.append(
                    RoundSummary(
                        round_number=round_num,
                        vote_counts={
                            c.name: round(v, 2) for c, v in final_counts.items()
                        },
                        quota=quota,
                        elected=[c.name for c in active],
                        note="Remaining candidates fill remaining seats.",
                    )
                )
                break

        # Final vote counts: recount from current weighted ballots over all candidates
        final_vote_counts = {}
        # Use last recorded round counts for display
        for rs in reversed(rounds):
            for name, val in rs.vote_counts.items():
                if name not in final_vote_counts:
                    final_vote_counts[name] = val
        # Fill any missing candidates with 0
        for c in self.candidates:
            if c.name not in final_vote_counts:
                final_vote_counts[c.name] = 0.0

        return ElectionResult(
            system_name=self.name,
            winners=elected,
            vote_counts=final_vote_counts,
            total_ballots=len(self.ballots),
            seats=self.seats,
            rounds=rounds,
        )
