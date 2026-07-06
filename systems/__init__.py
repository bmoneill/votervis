"""
Convenience re-exports for all election systems.

Each concrete class is also available under the canonical API name used
by cli.py (e.g. FPTPElection, TwoRoundElection, …).
"""

from systems.ams import AdditionalMemberSystem as AMSElection
from systems.approval import ApprovalVoting as ApprovalElection
from systems.base import BallotType, ElectionSystem
from systems.borda import BordaCount as BordaElection
from systems.condorcet import CondorcetSchulze as CondorcetElection
from systems.fptp import FirstPastThePost as FPTPElection
from systems.rcv import RankedChoiceVoting as RCVElection
from systems.stv import SingleTransferableVote as STVElection
from systems.two_round import TwoRoundSystem as TwoRoundElection

__all__ = [
    "FPTPElection",
    "TwoRoundElection",
    "RCVElection",
    "STVElection",
    "BordaElection",
    "ApprovalElection",
    "CondorcetElection",
    "AMSElection",
    "BallotType",
    "ElectionSystem",
]
