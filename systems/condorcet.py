"""
Condorcet voting with the Schulze method for winner determination.

The Schulze method finds the winner(s) of a ranked-choice election by computing
the strongest pairwise paths between all candidates (Floyd-Warshall) and
selecting the candidate(s) who are not beaten on the strongest path.
"""

from result import ElectionResult
from systems.base import BallotType, ElectionSystem


class CondorcetSchulze(ElectionSystem):
    """
    Condorcet election using the Schulze (beatpath) method.

    Voters rank candidates in any order; unranked candidates are treated as
    tied last. A pairwise preference matrix is built from all ballots, then
    the Schulze strongest-path algorithm determines the social ordering.
    The winner is the candidate(s) with the strongest path to every other
    candidate.
    """

    name = "Condorcet (Schulze Method)"
    description = (
        "Ranked-ballot Condorcet election resolved via the Schulze beatpath "
        "method. Finds the candidate who wins the most pairwise contests "
        "through the strongest indirect paths."
    )

    @property
    def ballot_type(self):
        return BallotType.RANKED

    def cast_ballot(self, ranking: list):
        """
        Record a ranked ballot.

        Parameters
        ----------
        ranking : list[Candidate]
            Candidates in order of preference, most preferred first.
            Partial rankings are allowed; unranked candidates are
            treated as ranked last.
        """
        self.ballots.append(list(ranking))

    def run_election(self) -> ElectionResult:
        """
        Run the Schulze Condorcet election and return an ElectionResult.

        The returned result object has two dynamic attributes added:
            result.pairwise          — dict[name → dict[name → int]]
                                       raw pairwise preference counts
        """
        n = len(self.candidates)

        if not self.ballots or n == 0:
            return ElectionResult(
                system_name=self.name,
                winners=[],
                vote_counts={},
                total_ballots=0,
                seats=1,
                message="No ballots cast.",
            )

        # Use enumerate directly below; no need for a pre-built index dict

        # ------------------------------------------------------------------ #
        # Build pairwise preference matrix
        # pref[i][j] = number of ballots ranking candidate i above candidate j
        # ------------------------------------------------------------------ #
        pref = [[0] * n for _ in range(n)]

        for ballot in self.ballots:
            ranked_set = set(ballot)
            pos = {c: idx for idx, c in enumerate(ballot)}

            for i, a in enumerate(self.candidates):
                for j, b in enumerate(self.candidates):
                    if i == j:
                        continue
                    a_ranked = a in ranked_set
                    b_ranked = b in ranked_set
                    if a_ranked and b_ranked:
                        if pos[a] < pos[b]:
                            pref[i][j] += 1
                    elif a_ranked and not b_ranked:
                        # a is ranked; b is not → a is preferred over b
                        pref[i][j] += 1
                    # If neither ranked, or only b ranked: no preference for a

        # ------------------------------------------------------------------ #
        # Schulze strongest-path (Floyd-Warshall variant)
        # strength[i][j] = strength of the strongest path from i to j
        # ------------------------------------------------------------------ #
        strength = [[0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i != j:
                    strength[i][j] = pref[i][j] if pref[i][j] > pref[j][i] else 0

        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if i != j and i != k and j != k:
                        strength[i][j] = max(
                            strength[i][j],
                            min(strength[i][k], strength[k][j]),
                        )

        # ------------------------------------------------------------------ #
        # Find Schulze winner(s):
        # candidate w wins if strength[w][j] >= strength[j][w] for all j ≠ w
        # ------------------------------------------------------------------ #
        winners = []
        for i in range(n):
            if all(strength[i][j] >= strength[j][i] for j in range(n) if j != i):
                winners.append(self.candidates[i])

        # ------------------------------------------------------------------ #
        # Check for a "pure" Condorcet winner (beats every other candidate
        # directly in pairwise comparisons, not just via paths)
        # ------------------------------------------------------------------ #
        pure_condorcet_winner = None
        for i in range(n):
            if all(pref[i][j] > pref[j][i] for j in range(n) if j != i):
                pure_condorcet_winner = self.candidates[i]
                break

        # ------------------------------------------------------------------ #
        # vote_counts: number of pairwise wins for each candidate
        # ------------------------------------------------------------------ #
        vote_counts = {}
        for i, c in enumerate(self.candidates):
            wins = sum(1 for j in range(n) if j != i and pref[i][j] > pref[j][i])
            vote_counts[c.name] = wins

        # ------------------------------------------------------------------ #
        # Build message
        # ------------------------------------------------------------------ #
        if not winners:
            message = "No Condorcet winner found (cycle among all candidates)."
        elif len(winners) == 1:
            w = winners[0]
            if pure_condorcet_winner and pure_condorcet_winner == w:
                message = (
                    f"{w.name} is the Condorcet winner, beating every other "
                    "candidate in direct pairwise comparisons."
                )
            else:
                message = (
                    f"{w.name} wins via the Schulze beatpath method. "
                    "No pure Condorcet winner exists (there is a cycle), "
                    "but the Schulze path resolves it."
                )
        else:
            names = ", ".join(w.name for w in winners)
            message = (
                f"Tie between: {names}. "
                "Multiple candidates share the strongest beatpath."
            )

        result = ElectionResult(
            system_name=self.name,
            winners=winners,
            vote_counts=vote_counts,
            total_ballots=len(self.ballots),
            seats=1,
            message=message,
        )

        # Attach pairwise matrix as a dynamic attribute for CLI display
        result.pairwise = {
            self.candidates[i].name: {
                self.candidates[j].name: pref[i][j] for j in range(n)
            }
            for i in range(n)
        }

        return result
