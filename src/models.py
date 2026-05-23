"""Data models for the Top12 tournament."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Tournament:
    id: int
    name: str
    event_date: str = ""    # ISO format "YYYY-MM-DD" or ""
    notes: str = ""
    created_at: str = ""    # ISO datetime
    updated_at: str = ""


@dataclass
class Player:
    id: int
    name: str
    points: int = 0      # initial ranking points (replaces "club")
    pool: str = ""       # "A", "B", or "" before assignment


@dataclass
class Match:
    id: int
    round_number: int          # 1..11
    phase: str                 # "pool" or "cross"
    player1_id: int
    player2_id: int
    score1: int = 0            # sets won by player1 (derived from set_scores)
    score2: int = 0            # sets won by player2 (derived from set_scores)
    played: bool = False
    pool: str = ""             # "A"/"B" for pool matches, "" for cross
    set_scores: list = field(default_factory=list)  # [[p1, p2], ...] up to 5 sets
    table_number: int = 0      # 1..3, 0 if not yet assigned
    referee_id: int = 0        # player id, 0 if none

    def winner_id(self) -> Optional[int]:
        if not self.played:
            return None
        if self.score1 > self.score2:
            return self.player1_id
        if self.score2 > self.score1:
            return self.player2_id
        return None


@dataclass
class PlayerStanding:
    """Computed standing for a player."""
    player: Player
    played: int = 0
    wins: int = 0
    losses: int = 0
    points: int = 0          # 2 per win, 1 per loss
    sets_won: int = 0
    sets_lost: int = 0

    @property
    def set_diff(self) -> int:
        return self.sets_won - self.sets_lost
