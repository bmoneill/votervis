class Candidate:
    def __init__(self, name: str, party: str):
        self.name = name
        self.party = party

    def __str__(self) -> str:
        return f"{self.name} ({self.party})"

    def __repr__(self) -> str:
        return f"Candidate(name={self.name!r}, party={self.party!r})"

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Candidate) and self.name == other.name
