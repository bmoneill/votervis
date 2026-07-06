"""
Additional Member System (AMS) implementation.

A mixed electoral system combining First-Past-The-Post constituency seats
with proportional D'Hondt list seats to produce an overall result that
approximates proportionality while retaining local representation.
"""

from collections import Counter

from candidate import Candidate
from result import ElectionResult
from systems.base import BallotType, ElectionSystem


class AdditionalMemberSystem(ElectionSystem):
    """
    Additional Member System (AMS) — mixed-member proportional system.

    Each voter casts two ballots:
      1. A *constituency ballot* for an individual candidate (FPTP).
      2. A *party ballot* for a party list (used for proportional top-up).

    Constituency seats are awarded by FPTP (highest vote-getters win).
    Party list seats are allocated using D'Hondt to compensate parties
    under-represented after the constituency round. Candidates are drawn
    from party lists in ranked order, skipping anyone already elected
    via a constituency seat.
    """

    name = "Additional Member System"
    description = (
        "Mixed-member proportional system: constituency seats by FPTP, "
        "list seats by D'Hondt to top up proportionality."
    )

    def __init__(
        self,
        candidates,
        seats=6,
        constituency_seats=None,
        party_lists=None,
    ):
        """
        Parameters
        ----------
        candidates : list[Candidate]
            All candidates standing in the election.
        seats : int
            Total seats to fill (constituency + list).
        constituency_seats : int | None
            Number of FPTP constituency seats. Defaults to seats // 2.
        party_lists : dict[str, list[Candidate]] | None
            Mapping of party name → ordered list of candidates (most
            preferred first) used for top-up list allocation.
        """
        super().__init__(candidates, seats=seats)
        self.constituency_seats = (
            constituency_seats if constituency_seats is not None else seats // 2
        )
        self.list_seats = self.seats - self.constituency_seats
        self.party_lists = party_lists or {}

        self.constituency_ballots: list = []  # list[Candidate]
        self.party_ballots: list = []  # list[str]
        # self.ballots stores (Candidate, str) tuples for ballot_count

    @property
    def ballot_type(self):
        return BallotType.AMS

    def cast_ballot(self, constituency_candidate: Candidate, party_name: str):
        """
        Record an AMS ballot (one constituency vote + one party vote).

        Parameters
        ----------
        constituency_candidate : Candidate
            The individual candidate chosen for the constituency seat.
        party_name : str
            The party chosen for the proportional list vote.

        Raises
        ------
        ValueError
            If constituency_candidate is not in self.candidates.
        """
        if constituency_candidate not in self.candidates:
            raise ValueError(f"{constituency_candidate} is not a registered candidate.")
        self.constituency_ballots.append(constituency_candidate)
        self.party_ballots.append(party_name)
        self.ballots.append((constituency_candidate, party_name))

    def run_election(self) -> ElectionResult:
        """
        Run the AMS election and return an ElectionResult.

        The returned result object has two dynamic attributes added:
            result.party_votes        — dict[party_name → vote_count]
            result.dhondt_allocation  — dict[party_name → total_seats_allocated]
        """
        if not self.ballots:
            return ElectionResult(
                system_name=self.name,
                winners=[],
                vote_counts={c.name: 0 for c in self.candidates},
                total_ballots=0,
                seats=self.seats,
                message="No ballots cast.",
            )

        total_ballots = len(self.ballots)

        # ------------------------------------------------------------------ #
        # Step 1: Constituency seats — FPTP top-N
        # ------------------------------------------------------------------ #
        cand_counts = Counter(self.constituency_ballots)
        sorted_cands = sorted(
            self.candidates, key=lambda c: (-cand_counts.get(c, 0), c.name)
        )
        constituency_winners = sorted_cands[: self.constituency_seats]

        # ------------------------------------------------------------------ #
        # Step 2: Party vote counts
        # ------------------------------------------------------------------ #
        party_counts = Counter(self.party_ballots)
        all_parties = sorted(party_counts.keys())

        # ------------------------------------------------------------------ #
        # Step 3: D'Hondt allocation for *total* seats
        # Each round awards one seat to the party with the highest quotient
        # votes / (seats_so_far + 1).
        # ------------------------------------------------------------------ #
        allocation = {p: 0 for p in all_parties}
        for _ in range(self.seats):
            if not all_parties:
                break
            quotients = {p: party_counts[p] / (allocation[p] + 1) for p in all_parties}
            winner_party = max(quotients, key=lambda p: (quotients[p], p))
            allocation[winner_party] += 1

        # ------------------------------------------------------------------ #
        # Step 4: Assign list seats
        # Each party gets (D'Hondt allocation − constituency seats already won).
        # Candidates are drawn from the party list, skipping any already elected.
        # ------------------------------------------------------------------ #
        constituency_won_by_party = Counter(c.party for c in constituency_winners)
        list_winners = []
        seat_types = {c.name: "constituency" for c in constituency_winners}
        elected_names = {c.name for c in constituency_winners}

        for party in all_parties:
            deserved = allocation[party]
            already_won = constituency_won_by_party.get(party, 0)
            list_seats_for_party = max(0, deserved - already_won)

            party_list = self.party_lists.get(party, [])
            eligible = [c for c in party_list if c.name not in elected_names]

            for c in eligible[:list_seats_for_party]:
                list_winners.append(c)
                seat_types[c.name] = "list"
                elected_names.add(c.name)

        # ------------------------------------------------------------------ #
        # Build summary message
        # ------------------------------------------------------------------ #
        total_party_votes = sum(party_counts.values())
        party_pct = (
            {
                p: round(100 * party_counts[p] / total_party_votes, 1)
                for p in all_parties
            }
            if total_party_votes > 0
            else {p: 0.0 for p in all_parties}
        )

        alloc_summary = ", ".join(
            f"{p}: {allocation[p]} seats ({party_pct.get(p, 0)}% of party vote)"
            for p in all_parties
        )
        message = (
            f"{len(constituency_winners)} constituency seat(s) filled by FPTP; "
            f"{len(list_winners)} list seat(s) allocated by D'Hondt. "
            f"Party allocation — {alloc_summary}."
        )

        result = ElectionResult(
            system_name=self.name,
            winners=constituency_winners + list_winners,
            vote_counts={c.name: cand_counts.get(c, 0) for c in self.candidates},
            total_ballots=total_ballots,
            seats=self.seats,
            seat_types=seat_types,
            message=message,
        )

        # Attach party-level data as dynamic attributes for CLI display
        result.party_votes = dict(party_counts)
        result.dhondt_allocation = dict(allocation)

        return result
