"""
VOTERVIS — Interactive CLI for the election simulator.

Entry point: run_cli()
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import random
from collections import Counter

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.rule import Rule
from rich.table import Table

from candidate import Candidate
from result import ElectionResult
from systems import (
    AMSElection,
    ApprovalElection,
    BordaElection,
    CondorcetElection,
    FPTPElection,
    RCVElection,
    STVElection,
    TwoRoundElection,
)
from systems.base import BallotType

# ─────────────────────────────────────────────────────────────────────────────
# Module-level console (shared by all helpers)
# ─────────────────────────────────────────────────────────────────────────────
console = Console()

# ─────────────────────────────────────────────────────────────────────────────
# Random candidate generation pools
# ─────────────────────────────────────────────────────────────────────────────
_FIRST_NAMES = [
    "Alice",
    "Bob",
    "Carol",
    "David",
    "Emma",
    "Frank",
    "Grace",
    "Henry",
    "Isla",
    "James",
    "Karen",
    "Liam",
    "Maya",
    "Noah",
    "Olivia",
    "Peter",
    "Quinn",
    "Rachel",
    "Samuel",
    "Tara",
    "Uma",
    "Victor",
    "Wendy",
    "Yasmine",
    "Ahmed",
    "Beatrice",
    "Carlos",
    "Diana",
    "Elena",
    "Felix",
    "Gabriella",
    "Hassan",
    "Ingrid",
    "Julian",
    "Katrina",
    "Lorenzo",
    "Miriam",
    "Nathan",
    "Priya",
    "Rosa",
    "Santiago",
    "Theresa",
    "Vladimir",
    "Willow",
    "Yusuf",
    "Zoe",
]
_LAST_NAMES = [
    "Smith",
    "Jones",
    "Williams",
    "Taylor",
    "Brown",
    "Davies",
    "Evans",
    "Wilson",
    "Thomas",
    "Roberts",
    "Johnson",
    "Walker",
    "Wright",
    "Robinson",
    "Harris",
    "Martin",
    "Jackson",
    "Lee",
    "Garcia",
    "Martinez",
    "Anderson",
    "Chen",
    "Patel",
    "Khan",
    "Ali",
    "Singh",
    "Nakamura",
    "Santos",
    "Oliveira",
    "Mueller",
    "Rossi",
    "Dubois",
    "Johansson",
    "Kowalski",
    "Novak",
    "Costa",
]
_PARTIES = [
    "Labour",
    "Conservative",
    "Liberal Democrat",
    "Green",
    "Reform",
    "Progressive",
    "Alliance",
    "National",
    "Social Democrat",
    "Libertarian",
    "Workers' Party",
    "Civic Alliance",
    "People's Party",
    "Future Party",
    "United Front",
    "Freedom Party",
    "New Democracy",
    "Independent",
]

# (class, menu label, one-line description)
_SYSTEMS: list[tuple] = [
    (
        FPTPElection,
        "First Past the Post (FPTP)",
        "Plurality — most votes wins, no majority required.",
    ),
    (
        TwoRoundElection,
        "Two-Round System",
        "Majority runoff — top two advance if no one clears 50 %.",
    ),
    (
        RCVElection,
        "Ranked-Choice Voting (IRV)",
        "Instant runoff — weakest candidates eliminated until majority.",
    ),
    (
        STVElection,
        "Single Transferable Vote (STV)",
        "Multi-seat proportional — votes transfer to fill all seats.",
    ),
    (
        BordaElection,
        "Borda Count",
        "Positional scoring — rank 1 earns n−1 pts, rank 2 earns n−2, etc.",
    ),
    (
        ApprovalElection,
        "Approval Voting",
        "Vote for as many candidates as you approve; most approvals wins.",
    ),
    (
        CondorcetElection,
        "Condorcet (Schulze Method)",
        "Finds the candidate who wins every head-to-head matchup via beatpaths.",
    ),
    (
        AMSElection,
        "Additional Member System (AMS)",
        "Mixed: constituency seats by FPTP + proportional party list seats.",
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────


def run_cli() -> None:
    """Main entry point for the VOTERVIS interactive CLI."""
    console.print(
        Panel.fit(
            "[bold cyan]VOTERVIS[/bold cyan]\n"
            "[dim]Election Simulation Tool[/dim]\n\n"
            "Simulate and compare [bold]8 electoral systems[/bold] interactively.\n"
            "Cast ballots by hand, generate random votes, or mix both.\n"
            "Full round-by-round breakdowns are displayed after each election.",
            title="[bold white on blue] VOTERVIS [/bold white on blue]",
            border_style="blue",
            padding=(1, 4),
        )
    )

    while True:
        system_class = select_system()
        if system_class is None:
            console.print(
                "\n[bold cyan]Thanks for using VOTERVIS. Goodbye![/bold cyan]\n"
            )
            break

        candidates = setup_candidates()

        # ── System-specific initialisation ──────────────────────────────────
        if system_class is STVElection:
            default_seats = max(1, len(candidates) // 3)
            console.print("\n[dim]STV is a multi-seat system.[/dim]")
            seats = IntPrompt.ask("  Number of seats to fill", default=default_seats)
            seats = max(1, min(seats, len(candidates) - 1))
            system = system_class(candidates, seats=seats)

        elif system_class is AMSElection:
            system = _setup_ams(candidates)

        else:
            system = system_class(candidates)

        # ── Voting and results ──────────────────────────────────────────────
        if system_class is TwoRoundElection:
            _two_round_flow(system, candidates)
        else:
            voting_loop(system, candidates)
            result = system.run_election()
            display_results(result, system)

        console.print()
        if not Confirm.ask("[bold]Run another election?[/bold]", default=True):
            console.print(
                "\n[bold cyan]Thanks for using VOTERVIS. Goodbye![/bold cyan]\n"
            )
            break


# ─────────────────────────────────────────────────────────────────────────────
# System selection
# ─────────────────────────────────────────────────────────────────────────────


def select_system():
    """Show a numbered menu and return the chosen system class (or None to quit)."""
    console.print()
    console.print(Rule("[bold]Select Electoral System[/bold]", style="blue"))

    table = Table(
        box=box.SIMPLE_HEAD,
        show_header=True,
        header_style="bold magenta",
        padding=(0, 1),
    )
    table.add_column("#", style="bold", width=4, justify="right")
    table.add_column("System", style="bold cyan", min_width=36)
    table.add_column("Description", style="dim")

    for idx, (_, label, desc) in enumerate(_SYSTEMS, 1):
        table.add_row(str(idx), label, desc)
    table.add_row("[bold red]0[/bold red]", "[bold red]Quit[/bold red]", "")

    console.print(table)

    while True:
        try:
            choice = IntPrompt.ask("  Choose a system", default=1)
        except (EOFError, KeyboardInterrupt):
            return None

        if choice == 0:
            return None
        if 1 <= choice <= len(_SYSTEMS):
            cls, label, _ = _SYSTEMS[choice - 1]
            console.print(
                f"\n  [bold green]✓[/bold green] Selected: [bold cyan]{label}[/bold cyan]"
            )
            return cls
        console.print(
            f"  [yellow]⚠[/yellow]  Enter a number between 0 and {len(_SYSTEMS)}."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Candidate setup
# ─────────────────────────────────────────────────────────────────────────────


def _generate_candidates(n: int, existing: list[Candidate]) -> list[Candidate]:
    """Return *n* randomly generated Candidate objects that don't clash with *existing*."""
    existing_names = {c.name for c in existing}
    # Assign parties first so each candidate within a batch gets a party drawn
    # from a small, consistent set — this makes elections more interesting.
    num_parties = max(2, min(len(_PARTIES), round(n**0.6)))
    parties = random.sample(_PARTIES, num_parties)

    # Build a large pool of unique full names then sample from it.
    all_names = [
        f"{first} {last}"
        for first in _FIRST_NAMES
        for last in _LAST_NAMES
        if f"{first} {last}" not in existing_names
    ]
    random.shuffle(all_names)
    chosen_names = all_names[:n]

    return [Candidate(name, random.choice(parties)) for name in chosen_names]


def setup_candidates() -> list:
    """Interactively collect candidates; returns list[Candidate]."""
    console.print()
    console.print(Rule("[bold]Candidate Setup[/bold]", style="blue"))
    console.print(
        "  [dim]Format: [bold]Name, Party[/bold]  — type [bold]done[/bold] when finished.[/dim]"
    )
    console.print(
        "  [dim]Or type [bold]generate N[/bold] to add N random candidates instantly.[/dim]"
    )
    console.print("  [dim]At least 2 candidates are required.[/dim]\n")

    candidates: list[Candidate] = []
    while True:
        try:
            entry = Prompt.ask(
                f"  Candidate {len(candidates) + 1}  [dim](or done)[/dim]"
            ).strip()
        except (EOFError, KeyboardInterrupt):
            if len(candidates) >= 2:
                break
            console.print("  [yellow]⚠[/yellow]  Need at least 2 candidates.")
            continue

        if entry.lower() == "done":
            if len(candidates) < 2:
                console.print("  [yellow]⚠[/yellow]  Need at least 2 candidates.")
                continue
            break

        # ── generate N ───────────────────────────────────────────────────────
        parts_gen = entry.lower().split()
        if (
            len(parts_gen) == 2
            and parts_gen[0] == "generate"
            and parts_gen[1].isdigit()
        ):
            n = int(parts_gen[1])
            if n < 1:
                console.print("  [yellow]⚠[/yellow]  Enter a positive number.")
                continue
            generated = _generate_candidates(n, candidates)
            for c in generated:
                candidates.append(c)
                console.print(f"  [green]✓[/green] Generated: [cyan]{c}[/cyan]")
            console.print(
                f"  [bold green]{len(generated)} candidate(s) added.[/bold green]"
            )
            continue

        parts = [p.strip() for p in entry.split(",", 1)]
        if len(parts) != 2 or not parts[0] or not parts[1]:
            console.print(
                "  [yellow]⚠[/yellow]  Use format: [bold]Alice Smith, Labour[/bold]"
            )
            continue

        c = Candidate(parts[0], parts[1])
        if any(x.name == c.name for x in candidates):
            console.print(f"  [yellow]⚠[/yellow]  '{c.name}' is already in the list.")
            continue

        candidates.append(c)
        console.print(f"  [green]✓[/green] Added: [cyan]{c}[/cyan]")

    console.print(
        f"\n  [bold green]{len(candidates)} candidates registered.[/bold green]"
    )
    return candidates


def _setup_ams(candidates: list) -> AMSElection:
    """Collect AMS-specific configuration and return a configured AMSElection."""
    n = len(candidates)
    console.print(
        "\n[dim]AMS splits seats between constituency FPTP winners and proportional party lists.[/dim]"
    )
    con_seats = IntPrompt.ask("  Constituency seats", default=max(1, n // 2))
    list_seats = IntPrompt.ask("  List (top-up) seats", default=max(1, n // 2))

    parties = sorted({c.party for c in candidates})
    party_lists: dict[str, list] = {}

    console.print("\n[bold]Party List Setup[/bold]")
    console.print(
        "  [dim]Add list-only candidates for each party (additional to constituency candidates).[/dim]\n"
        "  [dim]Format: [bold]Name, Party[/bold] — type [bold]done[/bold] to move on.[/dim]\n"
    )

    for party in parties:
        console.print(f"  [cyan]{party}[/cyan] list:")
        plist: list[Candidate] = []
        while True:
            try:
                entry = Prompt.ask(
                    f"    List candidate {len(plist) + 1}  [dim](or done)[/dim]"
                ).strip()
            except (EOFError, KeyboardInterrupt):
                break

            if entry.lower() == "done":
                break
            parts = [p.strip() for p in entry.split(",", 1)]
            if len(parts) != 2 or not parts[0] or not parts[1]:
                console.print(
                    "    [yellow]⚠[/yellow]  Use format: [bold]Name, Party[/bold]"
                )
                continue
            lc = Candidate(parts[0], parts[1])
            plist.append(lc)
            console.print(
                f"    [green]✓[/green] Added list candidate: [cyan]{lc}[/cyan]"
            )
        party_lists[party] = plist

    total_seats = con_seats + list_seats
    return AMSElection(
        candidates,
        seats=total_seats,
        constituency_seats=con_seats,
        party_lists=party_lists,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Voting loop
# ─────────────────────────────────────────────────────────────────────────────


def voting_loop(system, candidates: list, label: str = "VOTING") -> None:
    """
    Interactive voting loop.  Returns when the user selects 'd' (done).

    Parameters
    ----------
    system    : any ElectionSystem subclass
    candidates: list of Candidate objects visible in this round's ballot UI
    label     : header text for the Rule divider
    """
    console.print()
    console.print(Rule(f"[bold]{label}[/bold]", style="blue"))
    console.print(
        f"  System: [cyan]{system.name}[/cyan]  │  "
        f"Ballot type: [dim]{system.ballot_type.value}[/dim]  │  "
        f"Candidates: {len(candidates)}"
    )
    console.print()

    while True:
        console.print(
            f"  [dim]Ballots cast:[/dim] [bold]{system.ballot_count}[/bold]"
            "    [[bold cyan]v[/bold cyan]] Cast vote"
            "    [[bold cyan]s[/bold cyan]] Simulate N votes"
            "    [[bold cyan]r[/bold cyan]] Running tally"
            "    [[bold cyan]d[/bold cyan]] Done"
        )
        try:
            action = (
                Prompt.ask("  Action", choices=["v", "s", "r", "d"], default="v")
                .strip()
                .lower()
            )
        except (EOFError, KeyboardInterrupt):
            break

        if action == "v":
            try:
                count = IntPrompt.ask("  How many ballots to cast", default=1)
                if count < 1:
                    console.print("  [yellow]⚠[/yellow]  Enter a positive number.")
                    continue
            except (ValueError, EOFError):
                console.print("  [yellow]⚠[/yellow]  Invalid number.")
                continue

            _cast_manual_ballot(system, candidates, count)

        elif action == "s":
            try:
                n = IntPrompt.ask("  Votes to simulate", default=10)
                if n > 0:
                    _simulate_votes(system, candidates, n)
                    console.print(
                        f"  [green]✓[/green] Simulated [bold]{n}[/bold] votes. "
                        f"Total: [bold]{system.ballot_count}[/bold]"
                    )
                else:
                    console.print("  [yellow]⚠[/yellow]  Enter a positive number.")
            except (ValueError, EOFError):
                console.print("  [yellow]⚠[/yellow]  Invalid number.")

        elif action == "r":
            _running_tally(system, candidates)

        elif action == "d":
            if system.ballot_count == 0:
                console.print(
                    "  [yellow]⚠[/yellow]  No ballots cast yet — please cast at least one."
                )
                continue
            break

        console.print()


def _cast_manual_ballot(system, candidates: list, count: int = 1) -> None:
    """Prompt the user to fill in one ballot, then submit it *count* times."""
    bt = system.ballot_type
    times = f" [dim]×{count}[/dim]" if count > 1 else ""

    # ── SINGLE ──────────────────────────────────────────────────────────────
    if bt == BallotType.SINGLE:
        console.print("\n  [bold]Candidates:[/bold]")
        for i, c in enumerate(candidates, 1):
            console.print(f"    [bold]{i}.[/bold] [cyan]{c}[/cyan]")
        while True:
            try:
                choice = IntPrompt.ask("  Enter candidate number")
                if 1 <= choice <= len(candidates):
                    for _ in range(count):
                        system.cast_ballot(candidates[choice - 1])
                    console.print(
                        f"  [green]✓[/green] Voted for [cyan]{candidates[choice - 1]}[/cyan]{times}"
                    )
                    return
                console.print(
                    f"  [yellow]⚠[/yellow]  Enter a number between 1 and {len(candidates)}."
                )
            except (ValueError, EOFError, KeyboardInterrupt):
                console.print("  [yellow]⚠[/yellow]  Invalid input.")
                return

    # ── RANKED ───────────────────────────────────────────────────────────────
    elif bt == BallotType.RANKED:
        console.print(
            "\n  [bold]Rank the candidates[/bold] (comma-separated numbers, most preferred first)."
        )
        console.print("  [dim]You may rank all or just some. E.g., '2,1,3'[/dim]")
        for i, c in enumerate(candidates, 1):
            console.print(f"    [bold]{i}.[/bold] [cyan]{c}[/cyan]")
        while True:
            try:
                raw = Prompt.ask("  Your ranking").strip()
                indices = [int(p.strip()) for p in raw.split(",") if p.strip()]
                if not indices:
                    raise ValueError("Empty ranking")
                if any(i < 1 or i > len(candidates) for i in indices):
                    raise ValueError("Index out of range")
                if len(indices) != len(set(indices)):
                    raise ValueError("Duplicate entries")
                ranking = [candidates[i - 1] for i in indices]
                for _ in range(count):
                    system.cast_ballot(ranking)
                arrow = " → ".join(f"[cyan]{c.name}[/cyan]" for c in ranking)
                console.print(f"  [green]✓[/green] Recorded: {arrow}{times}")
                return
            except (ValueError, EOFError, KeyboardInterrupt) as exc:
                console.print(
                    f"  [yellow]⚠[/yellow]  Invalid ranking ({exc}). Try again."
                )
                return

    # ── APPROVAL ─────────────────────────────────────────────────────────────
    elif bt == BallotType.APPROVAL:
        console.print(
            "\n  [bold]Enter numbers of candidates you approve[/bold] (comma-separated)."
        )
        console.print("  [dim]E.g., '1,3'[/dim]")
        for i, c in enumerate(candidates, 1):
            console.print(f"    [bold]{i}.[/bold] [cyan]{c}[/cyan]")
        while True:
            try:
                raw = Prompt.ask("  Your approvals").strip()
                indices = list({int(p.strip()) for p in raw.split(",") if p.strip()})
                if not indices:
                    raise ValueError("No approvals entered")
                if any(i < 1 or i > len(candidates) for i in indices):
                    raise ValueError("Index out of range")
                approved = {candidates[i - 1] for i in indices}
                for _ in range(count):
                    system.cast_ballot(approved)
                labels = ", ".join(
                    f"[cyan]{c.name}[/cyan]"
                    for c in sorted(approved, key=lambda x: x.name)
                )
                console.print(f"  [green]✓[/green] Approved: {labels}{times}")
                return
            except (ValueError, EOFError, KeyboardInterrupt) as exc:
                console.print(
                    f"  [yellow]⚠[/yellow]  Invalid input ({exc}). Use comma-separated numbers."
                )
                return

    # ── AMS ──────────────────────────────────────────────────────────────────
    elif bt == BallotType.AMS:
        # Constituency vote
        console.print(
            "\n  [bold]Constituency vote[/bold] — choose your local candidate:"
        )
        for i, c in enumerate(candidates, 1):
            console.print(f"    [bold]{i}.[/bold] [cyan]{c}[/cyan]")
        con_cand = None
        while con_cand is None:
            try:
                choice = IntPrompt.ask("  Candidate number")
                if 1 <= choice <= len(candidates):
                    con_cand = candidates[choice - 1]
                else:
                    console.print(f"  [yellow]⚠[/yellow]  Enter 1–{len(candidates)}.")
            except (ValueError, EOFError, KeyboardInterrupt):
                console.print("  [yellow]⚠[/yellow]  Invalid input.")
                return

        # Party vote
        parties = sorted({c.party for c in candidates})
        console.print("\n  [bold]Party vote[/bold] — choose a party:")
        for i, party in enumerate(parties, 1):
            console.print(f"    [bold]{i}.[/bold] {party}")
        party_name = None
        while party_name is None:
            try:
                pchoice = IntPrompt.ask("  Party number")
                if 1 <= pchoice <= len(parties):
                    party_name = parties[pchoice - 1]
                else:
                    console.print(f"  [yellow]⚠[/yellow]  Enter 1–{len(parties)}.")
            except (ValueError, EOFError, KeyboardInterrupt):
                console.print("  [yellow]⚠[/yellow]  Invalid input.")
                return

        for _ in range(count):
            system.cast_ballot(con_cand, party_name)
        console.print(
            f"  [green]✓[/green] Constituency: [cyan]{con_cand.name}[/cyan]  │  "
            f"Party: [cyan]{party_name}[/cyan]{times}"
        )


def _simulate_votes(system, candidates: list, n: int) -> None:
    """Generate *n* random ballots appropriate to *system*'s ballot type."""
    bt = system.ballot_type
    parties = sorted({c.party for c in candidates})

    for _ in range(n):
        if bt == BallotType.SINGLE:
            system.cast_ballot(random.choice(candidates))

        elif bt == BallotType.RANKED:
            k = random.randint(1, len(candidates))
            system.cast_ballot(random.sample(candidates, k))

        elif bt == BallotType.APPROVAL:
            k = random.randint(1, len(candidates))
            system.cast_ballot(set(random.sample(candidates, k)))

        elif bt == BallotType.AMS:
            system.cast_ballot(
                random.choice(candidates),
                random.choice(parties),
            )


def _running_tally(system, candidates: list) -> None:
    """Print a live tally of ballots cast so far."""
    bt = system.ballot_type
    total = system.ballot_count

    if bt == BallotType.SINGLE:
        counts = Counter(b.name for b in system.ballots)
        tbl = Table(
            title=f"Running Tally  ({total} ballots)",
            box=box.ROUNDED,
            header_style="bold",
        )
        tbl.add_column("Candidate", style="cyan")
        tbl.add_column("Party", style="dim")
        tbl.add_column("Votes", justify="right")
        tbl.add_column("%", justify="right")
        for c in candidates:
            v = counts.get(c.name, 0)
            pct = f"{v / total:.1%}" if total else "—"
            tbl.add_row(c.name, c.party, str(v), pct)
        console.print(tbl)

    elif bt == BallotType.RANKED:
        first: Counter = Counter()
        for ballot in system.ballots:
            if ballot:
                first[ballot[0].name] += 1
        tbl = Table(
            title=f"Running Tally — First Choices  ({total} ballots)",
            box=box.ROUNDED,
            header_style="bold",
        )
        tbl.add_column("Candidate", style="cyan")
        tbl.add_column("Party", style="dim")
        tbl.add_column("1st-Choice Votes", justify="right")
        tbl.add_column("%", justify="right")
        for c in candidates:
            v = first.get(c.name, 0)
            pct = f"{v / total:.1%}" if total else "—"
            tbl.add_row(c.name, c.party, str(v), pct)
        console.print(tbl)

    elif bt == BallotType.APPROVAL:
        counts: Counter = Counter()
        for approved in system.ballots:
            for c in approved:
                counts[c.name] += 1
        tbl = Table(
            title=f"Running Tally — Approvals  ({total} ballots)",
            box=box.ROUNDED,
            header_style="bold",
        )
        tbl.add_column("Candidate", style="cyan")
        tbl.add_column("Party", style="dim")
        tbl.add_column("Approvals", justify="right")
        tbl.add_column("%", justify="right")
        for c in candidates:
            v = counts.get(c.name, 0)
            pct = f"{v / total:.1%}" if total else "—"
            tbl.add_row(c.name, c.party, str(v), pct)
        console.print(tbl)

    elif bt == BallotType.AMS:
        con_counts: Counter = Counter()
        party_counts: Counter = Counter()
        for ballot in system.ballots:
            con_cand, party = ballot[0], ballot[1]
            if con_cand:
                con_counts[con_cand.name] += 1
            party_counts[party] += 1

        con_tbl = Table(
            title=f"Constituency Votes  ({total} ballots)",
            box=box.ROUNDED,
            header_style="bold",
        )
        con_tbl.add_column("Candidate", style="cyan")
        con_tbl.add_column("Votes", justify="right")
        con_tbl.add_column("%", justify="right")
        for c in candidates:
            v = con_counts.get(c.name, 0)
            pct = f"{v / total:.1%}" if total else "—"
            con_tbl.add_row(c.name, str(v), pct)
        console.print(con_tbl)

        party_tbl = Table(title="Party Votes", box=box.ROUNDED, header_style="bold")
        party_tbl.add_column("Party", style="cyan")
        party_tbl.add_column("Votes", justify="right")
        party_tbl.add_column("%", justify="right")
        for party in sorted({c.party for c in candidates}):
            v = party_counts.get(party, 0)
            pct = f"{v / total:.1%}" if total else "—"
            party_tbl.add_row(party, str(v), pct)
        console.print(party_tbl)


# ─────────────────────────────────────────────────────────────────────────────
# Two-Round special flow
# ─────────────────────────────────────────────────────────────────────────────


def _two_round_flow(system, candidates: list) -> None:
    """Handle the complete Two-Round election, including optional runoff."""
    # ── Round 1 ─────────────────────────────────────────────────────────────
    voting_loop(system, candidates, label="ROUND 1 — VOTING")
    r1 = system.finalize_round1()

    console.print()
    console.print(Rule("[bold]Round 1 Results[/bold]", style="yellow"))
    _vote_table(
        r1.vote_counts,
        candidates,
        r1.winners,
        r1.total_ballots,
        title="Round 1",
    )
    console.print(f"\n  [dim]{r1.message}[/dim]")

    if not r1.needs_runoff:
        # Direct majority — show full result panel and return
        display_results(r1, system)
        return

    # ── Announce runoff ──────────────────────────────────────────────────────
    names_str = "  vs.  ".join(
        f"[bold cyan]{c}[/bold cyan]" for c in r1.runoff_candidates
    )
    console.print()
    console.print(
        Panel(
            names_str,
            title="[bold yellow]→ Runoff Required[/bold yellow]",
            border_style="yellow",
            padding=(0, 2),
        )
    )

    # ── Round 2 ─────────────────────────────────────────────────────────────
    voting_loop(system, r1.runoff_candidates, label="ROUND 2 — RUNOFF")
    r2 = system.finalize_round2()
    display_results(r2, system)


# ─────────────────────────────────────────────────────────────────────────────
# Results display helpers
# ─────────────────────────────────────────────────────────────────────────────


def _vote_table(
    vote_counts: dict,
    candidates: list,
    winners: list,
    total: int,
    title: str = "Results",
) -> None:
    """Render a Candidate / Party / Votes / % / ★ table."""
    winner_names = {w.name for w in winners}
    tbl = Table(title=title, box=box.ROUNDED, header_style="bold", show_footer=False)
    tbl.add_column("Candidate", style="cyan", min_width=18)
    tbl.add_column("Party", style="dim", min_width=12)
    tbl.add_column("Votes", justify="right")
    tbl.add_column("%", justify="right")
    tbl.add_column("", justify="center", width=3)

    for c in candidates:
        votes = vote_counts.get(c.name, 0)
        pct = f"{votes / total:.1%}" if total else "—"
        star = "[bold green]★[/bold green]" if c.name in winner_names else ""
        style = "bold green" if c.name in winner_names else ""
        tbl.add_row(
            f"[{style}]{c.name}[/{style}]" if style else c.name,
            c.party,
            f"{votes:g}",
            pct,
            star,
        )
    console.print(tbl)


def display_results(result: ElectionResult, system) -> None:
    """Render a full, system-specific results panel using rich formatting."""
    console.print()
    console.print(Rule("[bold green]ELECTION RESULTS[/bold green]", style="green"))

    winner_str = (
        "  ".join(f"[bold green]{w}[/bold green]" for w in result.winners)
        or "[dim]No winner declared[/dim]"
    )
    console.print(
        Panel(
            f"[bold]System:[/bold]        {result.system_name}\n"
            f"[bold]Total ballots:[/bold] {result.total_ballots}\n"
            f"[bold]Seats:[/bold]         {result.seats}\n"
            f"[bold]Winner(s):[/bold]     {winner_str}\n\n"
            f"[dim]{result.message}[/dim]",
            title="[bold green]RESULT[/bold green]",
            border_style="green",
        )
    )

    sn = result.system_name.lower()

    # ── First Past the Post ───────────────────────────────────────────────────
    if "first past" in sn:
        _vote_table(
            result.vote_counts,
            system.candidates,
            result.winners,
            result.total_ballots,
        )

    # ── Two-Round System ──────────────────────────────────────────────────────
    elif "two-round" in sn or "two round" in sn:
        for rnd in result.rounds:
            rnd_cands = [c for c in system.candidates if c.name in rnd.vote_counts]
            rnd_winners = [
                c for c in system.candidates if c.name in (rnd.elected or [])
            ]
            rnd_total = int(sum(rnd.vote_counts.values()))
            _vote_table(
                rnd.vote_counts,
                rnd_cands,
                rnd_winners,
                rnd_total,
                title=f"Round {rnd.round_number}",
            )
            if rnd.note:
                console.print(f"  [dim]{rnd.note}[/dim]\n")

    # ── Ranked-Choice Voting (IRV) ────────────────────────────────────────────
    elif "ranked" in sn or "rcv" in sn or "instant" in sn or "choice" in sn:
        for rnd in result.rounds:
            rnd_cands = [c for c in system.candidates if c.name in rnd.vote_counts]
            rnd_total = sum(rnd.vote_counts.values())

            tbl = Table(
                title=f"Round {rnd.round_number}",
                box=box.SIMPLE_HEAD,
                header_style="bold",
            )
            tbl.add_column("Candidate", style="cyan", min_width=18)
            tbl.add_column("Votes", justify="right")
            tbl.add_column("%", justify="right")
            tbl.add_column("Status", justify="center")

            for c in rnd_cands:
                v = rnd.vote_counts.get(c.name, 0)
                pct = f"{v / rnd_total:.1%}" if rnd_total else "—"
                if c.name in (rnd.elected or []):
                    status, style = "[bold green]★ ELECTED[/bold green]", "bold green"
                elif c.name == rnd.eliminated:
                    status, style = "[bold red]✗ ELIMINATED[/bold red]", "dim red"
                else:
                    status, style = "", ""
                tbl.add_row(
                    f"[{style}]{c.name}[/{style}]" if style else c.name,
                    f"{v:g}",
                    pct,
                    status,
                )
            console.print(tbl)
            if rnd.note:
                console.print(f"  [dim]{rnd.note}[/dim]\n")

    # ── Single Transferable Vote (STV) ────────────────────────────────────────
    elif "transferable" in sn or "stv" in sn:
        if result.rounds and result.rounds[0].quota is not None:
            console.print(f"  [bold]Droop Quota:[/bold] {result.rounds[0].quota:g}\n")

        for rnd in result.rounds:
            rnd_cands = [c for c in system.candidates if c.name in rnd.vote_counts]
            quota = rnd.quota

            tbl = Table(
                title=f"Round {rnd.round_number}",
                box=box.SIMPLE_HEAD,
                header_style="bold",
            )
            tbl.add_column("Candidate", style="cyan", min_width=18)
            tbl.add_column("Votes", justify="right")
            if quota:
                tbl.add_column("vs Quota", justify="right")
            tbl.add_column("Status", justify="center")

            for c in rnd_cands:
                v = rnd.vote_counts.get(c.name, 0)
                if c.name in (rnd.elected or []):
                    status, style = "[bold green]★ ELECTED[/bold green]", "bold green"
                elif c.name == rnd.eliminated:
                    status, style = "[bold red]✗ ELIMINATED[/bold red]", "dim red"
                else:
                    status, style = "", ""
                row = [
                    f"[{style}]{c.name}[/{style}]" if style else c.name,
                    f"{v:g}",
                ]
                if quota:
                    diff = v - quota
                    diff_str = (
                        f"[green]+{diff:g}[/green]"
                        if diff >= 0
                        else f"[red]{diff:g}[/red]"
                    )
                    row.append(diff_str)
                row.append(status)
                tbl.add_row(*row)
            console.print(tbl)
            if rnd.note:
                console.print(f"  [dim]{rnd.note}[/dim]\n")

        if result.winners:
            seat_tbl = Table(
                title="Seat Allocation",
                box=box.ROUNDED,
                header_style="bold green",
            )
            seat_tbl.add_column("Candidate", style="bold green", min_width=18)
            seat_tbl.add_column("Party", style="dim")
            for w in result.winners:
                seat_tbl.add_row(w.name, w.party)
            console.print(seat_tbl)

    # ── Borda Count ───────────────────────────────────────────────────────────
    elif "borda" in sn:
        winner_names = {w.name for w in result.winners}
        tbl = Table(
            title="Borda Count Results",
            box=box.ROUNDED,
            header_style="bold",
        )
        tbl.add_column("Candidate", style="cyan", min_width=18)
        tbl.add_column("Party", style="dim")
        tbl.add_column("Points", justify="right")
        tbl.add_column("", justify="center", width=3)
        for c in sorted(
            system.candidates, key=lambda x: -result.vote_counts.get(x.name, 0)
        ):
            pts = result.vote_counts.get(c.name, 0)
            star = "[bold green]★[/bold green]" if c.name in winner_names else ""
            style = "bold green" if c.name in winner_names else ""
            tbl.add_row(
                f"[{style}]{c.name}[/{style}]" if style else c.name,
                c.party,
                f"{pts:g}",
                star,
            )
        console.print(tbl)

    # ── Approval Voting ───────────────────────────────────────────────────────
    elif "approval" in sn:
        winner_names = {w.name for w in result.winners}
        tbl = Table(
            title="Approval Voting Results",
            box=box.ROUNDED,
            header_style="bold",
        )
        tbl.add_column("Candidate", style="cyan", min_width=18)
        tbl.add_column("Party", style="dim")
        tbl.add_column("Approvals", justify="right")
        tbl.add_column("% of Ballots", justify="right")
        tbl.add_column("", justify="center", width=3)
        for c in sorted(
            system.candidates, key=lambda x: -result.vote_counts.get(x.name, 0)
        ):
            approvals = result.vote_counts.get(c.name, 0)
            pct = (
                f"{approvals / result.total_ballots:.1%}"
                if result.total_ballots
                else "—"
            )
            star = "[bold green]★[/bold green]" if c.name in winner_names else ""
            style = "bold green" if c.name in winner_names else ""
            tbl.add_row(
                f"[{style}]{c.name}[/{style}]" if style else c.name,
                c.party,
                f"{approvals:g}",
                pct,
                star,
            )
        console.print(tbl)

    # ── Condorcet / Schulze ───────────────────────────────────────────────────
    elif "condorcet" in sn or "schulze" in sn:
        winner_names = {w.name for w in result.winners}
        tbl = Table(
            title="Schulze Method Results",
            box=box.ROUNDED,
            header_style="bold",
        )
        tbl.add_column("Candidate", style="cyan", min_width=18)
        tbl.add_column("Party", style="dim")
        tbl.add_column("Pairwise Wins", justify="right")
        tbl.add_column("", justify="center", width=3)
        for c in sorted(
            system.candidates, key=lambda x: -result.vote_counts.get(x.name, 0)
        ):
            wins = result.vote_counts.get(c.name, 0)
            star = "[bold green]★[/bold green]" if c.name in winner_names else ""
            style = "bold green" if c.name in winner_names else ""
            tbl.add_row(
                f"[{style}]{c.name}[/{style}]" if style else c.name,
                c.party,
                f"{wins:g}",
                star,
            )
        console.print(tbl)

        # Pairwise comparison matrix
        # result.pairwise is dict[name → dict[name → count]]
        pairwise = getattr(result, "pairwise", None)
        if pairwise:
            names = [c.name for c in system.candidates]
            matrix = Table(
                title="Pairwise Comparison Matrix  (row beats column)",
                box=box.SIMPLE_HEAD,
                header_style="bold magenta",
            )
            matrix.add_column("↓ beats →", style="bold", min_width=14)
            for name in names:
                matrix.add_column(name[:14], justify="right")
            for row_name in names:
                row_data = [row_name]
                for col_name in names:
                    if row_name == col_name:
                        row_data.append("[dim]—[/dim]")
                    else:
                        v = pairwise.get(row_name, {}).get(col_name, 0)
                        row_data.append(str(v))
                matrix.add_row(*row_data)
            console.print(matrix)

    # ── Additional Member System (AMS) ────────────────────────────────────────
    elif "additional member" in sn or "ams" in sn:
        party_votes = getattr(result, "party_votes", {})
        if party_votes:
            pt = Table(title="Party Votes", box=box.ROUNDED, header_style="bold")
            pt.add_column("Party", style="cyan")
            pt.add_column("Votes", justify="right")
            pt.add_column("%", justify="right")
            for party, votes in sorted(party_votes.items(), key=lambda x: -x[1]):
                pct = (
                    f"{votes / result.total_ballots:.1%}"
                    if result.total_ballots
                    else "—"
                )
                pt.add_row(party, str(votes), pct)
            console.print(pt)

        dhondt = getattr(result, "dhondt_allocation", {})
        if dhondt:
            dt = Table(
                title="D'Hondt List Seat Allocation",
                box=box.ROUNDED,
                header_style="bold",
            )
            dt.add_column("Party", style="cyan")
            dt.add_column("List Seats", justify="right")
            for party, seats in sorted(dhondt.items(), key=lambda x: -x[1]):
                dt.add_row(party, str(seats))
            console.print(dt)

        con_winners = [
            w for w in result.winners if result.seat_types.get(w.name) == "constituency"
        ]
        list_winners = [
            w for w in result.winners if result.seat_types.get(w.name) == "list"
        ]
        other = [
            w for w in result.winners if w not in con_winners and w not in list_winners
        ]

        if con_winners:
            ct = Table(
                title="Constituency Winners", box=box.ROUNDED, header_style="bold green"
            )
            ct.add_column("Candidate", style="bold green", min_width=18)
            ct.add_column("Party", style="dim")
            for w in con_winners:
                ct.add_row(w.name, w.party)
            console.print(ct)

        if list_winners:
            lt = Table(title="List Winners", box=box.ROUNDED, header_style="bold cyan")
            lt.add_column("Candidate", style="bold cyan", min_width=18)
            lt.add_column("Party", style="dim")
            for w in list_winners:
                lt.add_row(w.name, w.party)
            console.print(lt)

        if other:
            ot = Table(title="Other Winners", box=box.ROUNDED, header_style="bold")
            ot.add_column("Candidate", style="bold green", min_width=18)
            ot.add_column("Party", style="dim")
            for w in other:
                ot.add_row(w.name, w.party)
            console.print(ot)

    # ── Fallback ──────────────────────────────────────────────────────────────
    else:
        _vote_table(
            result.vote_counts,
            system.candidates,
            result.winners,
            result.total_ballots,
        )
