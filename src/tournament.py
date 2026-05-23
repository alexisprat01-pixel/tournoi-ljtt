"""Tournament logic: pool scheduling, cross-pool scheduling, standings."""
from __future__ import annotations

import random
from typing import Iterable, List, Optional

from .models import Match, Player, PlayerStanding


# Berger schedule for 6 players (0-indexed positions inside the pool).
# Each round is a list of (i, j) pairs covering positions 0..5 exactly once.
# Every pair (i, j) with i < j appears in exactly one of the 5 rounds.
BERGER_6 = [
    [(0, 5), (1, 4), (2, 3)],   # Round 1
    [(0, 4), (5, 3), (1, 2)],   # Round 2
    [(0, 3), (4, 2), (5, 1)],   # Round 3
    [(0, 2), (3, 1), (4, 5)],   # Round 4
    [(0, 1), (2, 5), (3, 4)],   # Round 5
]


def split_into_pools(players: List[Player], shuffle: bool = True) -> tuple[List[Player], List[Player]]:
    """Split 12 players into pools A and B (6 each)."""
    if len(players) != 12:
        raise ValueError(f"Expected 12 players, got {len(players)}")
    pool = list(players)
    if shuffle:
        random.shuffle(pool)
    pool_a = pool[:6]
    pool_b = pool[6:]
    for p in pool_a:
        p.pool = "A"
    for p in pool_b:
        p.pool = "B"
    return pool_a, pool_b


def build_pool_rounds(pool_a: List[Player], pool_b: List[Player]) -> List[Match]:
    """Generate the 5 pool rounds (Berger). Returns matches with id=0 (to be set later)."""
    matches: List[Match] = []
    for round_idx, pairs in enumerate(BERGER_6, start=1):
        for i, j in pairs:
            matches.append(Match(
                id=0,
                round_number=round_idx,
                phase="pool",
                player1_id=pool_a[i].id,
                player2_id=pool_a[j].id,
                pool="A",
            ))
            matches.append(Match(
                id=0,
                round_number=round_idx,
                phase="pool",
                player1_id=pool_b[i].id,
                player2_id=pool_b[j].id,
                pool="B",
            ))
    return matches


def build_cross_rounds(pool_a_ranked: List[Player], pool_b_ranked: List[Player]) -> List[Match]:
    """Generate the 6 cross-pool rounds (rounds 6..11).

    Round 11 (the final round) is guaranteed to pair players of the same pool rank:
    A1-B1, A2-B2, ..., A6-B6.
    Every Ai meets every Bj exactly once across the 6 rounds.
    """
    if len(pool_a_ranked) != 6 or len(pool_b_ranked) != 6:
        raise ValueError("Each pool must have exactly 6 ranked players")

    matches: List[Match] = []
    for r in range(6):           # 0..5 -> rounds 6..11
        offset = 5 - r           # last round (r=5) -> offset 0 -> Ai vs Bi
        round_number = 6 + r
        for i in range(6):
            j = (i + offset) % 6
            matches.append(Match(
                id=0,
                round_number=round_number,
                phase="cross",
                player1_id=pool_a_ranked[i].id,
                player2_id=pool_b_ranked[j].id,
            ))
    return matches


def compute_standings(
    players: Iterable[Player],
    matches: Iterable[Match],
    pool: Optional[str] = None,
    max_round: Optional[int] = None,
) -> List[PlayerStanding]:
    """Compute standings.

    - pool="A"/"B" restricts to that pool's intra-pool matches (rounds 1-5).
    - pool=None counts all matches.
    - max_round caps which rounds are considered.
    """
    by_id = {p.id: PlayerStanding(player=p) for p in players}
    if pool is not None:
        by_id = {pid: st for pid, st in by_id.items() if st.player.pool == pool}

    for m in matches:
        if not m.played:
            continue
        if max_round is not None and m.round_number > max_round:
            continue
        if pool is not None and m.pool != pool:
            continue
        if m.player1_id not in by_id or m.player2_id not in by_id:
            continue
        s1, s2 = by_id[m.player1_id], by_id[m.player2_id]
        s1.played += 1
        s2.played += 1
        s1.sets_won += m.score1
        s1.sets_lost += m.score2
        s2.sets_won += m.score2
        s2.sets_lost += m.score1
        if m.score1 > m.score2:
            s1.wins += 1
            s1.points += 2
            s2.losses += 1
            s2.points += 1
        elif m.score2 > m.score1:
            s2.wins += 1
            s2.points += 2
            s1.losses += 1
            s1.points += 1

    standings = list(by_id.values())
    standings.sort(
        key=lambda s: (-s.points, -s.set_diff, -s.sets_won, s.player.name.lower())
    )
    return standings


def is_phase_complete(matches: Iterable[Match], rounds: Iterable[int]) -> bool:
    rounds_set = set(rounds)
    relevant = [m for m in matches if m.round_number in rounds_set]
    if not relevant:
        return False
    return all(m.played for m in relevant)
