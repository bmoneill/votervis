class Party:
    def __init__(self, name: str, abbreviation: str = "", color: str = ""):
        self.name = name
        self.abbreviation = abbreviation or name[:3].upper()
        self.color = color

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Party(name={self.name!r}, abbreviation={self.abbreviation!r})"

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Party) and self.name == other.name
