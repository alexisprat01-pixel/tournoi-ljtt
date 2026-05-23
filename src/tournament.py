"""Tournament logic: pool scheduling, cross-pool scheduling, standings."""
from __future__ import annotations

from itertools import permutations
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


N_TABLES = 3


def _initial_counts(player_ids: list[int]) -> tuple[dict, dict]:
    table_counts = {pid: {t: 0 for t in range(1, N_TABLES + 1)} for pid in player_ids}
    ref_counts = {pid: 0 for pid in player_ids}
    return table_counts, ref_counts


def collect_assignment_counts(matches: list[Match], player_ids: list[int]) -> tuple[dict, dict]:
    """Build the table/ref usage tally from already-assigned matches."""
    table_counts, ref_counts = _initial_counts(player_ids)
    for m in matches:
        if m.table_number and m.player1_id in table_counts:
            table_counts[m.player1_id][m.table_number] += 1
        if m.table_number and m.player2_id in table_counts:
            table_counts[m.player2_id][m.table_number] += 1
        if m.referee_id and m.referee_id in ref_counts:
            ref_counts[m.referee_id] += 1
    return table_counts, ref_counts


def group_matches_into_sessions(matches: list[Match]) -> list[list[Match]]:
    """Split matches into 3-match sessions that share the 3 physical tables.

    - Pool phase: each (round, pool) pair is one session.
    - Cross phase: each round's 6 matches are split into 2 sessions of 3
      (the first 3 in the round's match order, then the last 3). The cross
      schedule is built so the two halves never share a player, which is what
      makes them schedulable on the same 3 tables in succession.
    """
    pool_by_key: dict[tuple, list[Match]] = {}
    cross_by_round: dict[int, list[Match]] = {}
    for m in matches:
        if m.phase == "pool":
            pool_by_key.setdefault((m.round_number, m.pool), []).append(m)
        else:
            cross_by_round.setdefault(m.round_number, []).append(m)

    sessions: list[list[Match]] = []
    for round_num in sorted({m.round_number for m in matches if m.phase == "pool"}):
        for pool in ("A", "B"):
            key = (round_num, pool)
            if key in pool_by_key:
                sessions.append(pool_by_key[key])
    for round_num in sorted(cross_by_round.keys()):
        ms = cross_by_round[round_num]
        sessions.append(ms[:3])
        if len(ms) > 3:
            sessions.append(ms[3:6])
    return sessions


def _imbalance_score(
    matches_subset: list[Match],
    table_perm: tuple,
    table_counts: dict,
) -> int:
    """Sum of (max-min) table count across all players affected by this assignment."""
    affected: dict[int, dict[int, int]] = {}
    for m in matches_subset:
        for pid in (m.player1_id, m.player2_id):
            if pid not in affected:
                affected[pid] = dict(table_counts[pid])
    for m, t in zip(matches_subset, table_perm):
        affected[m.player1_id][t] += 1
        affected[m.player2_id][t] += 1
    return sum(max(c.values()) - min(c.values()) for c in affected.values())


def _assign_session(
    session: list[Match],
    table_counts: dict,
    ref_counts: dict,
    player_ids: list[int],
) -> None:
    """Assign tables (distinct in 1..3) and referees for one session of (up to 3) matches.

    Matches that already carry a non-zero table_number (resp. referee_id) are
    treated as fixed and their counts are assumed to be already reflected in
    `table_counts` (resp. `ref_counts`). Only the unset matches get assignments.
    """
    if not session:
        return

    # ----- tables -----
    fixed_matches = [m for m in session if m.table_number]
    needs_table = [m for m in session if not m.table_number]
    if needs_table:
        used = {m.table_number for m in fixed_matches}
        available = [t for t in range(1, N_TABLES + 1) if t not in used]
        if len(needs_table) > len(available):
            # Degenerate case (more matches than available tables) — fall back to
            # whatever is available, allowing repeats only if strictly necessary.
            available = available + [available[0]] * (len(needs_table) - len(available)) if available else [1, 2, 3]
        # Try each ordered selection of len(needs_table) tables among `available`
        # and keep the one minimising the resulting imbalance.
        best_perm = min(
            permutations(available, len(needs_table)),
            key=lambda perm: _imbalance_score(needs_table, perm, table_counts),
        )
        for m, t in zip(needs_table, best_perm):
            m.table_number = t
            table_counts[m.player1_id][t] += 1
            table_counts[m.player2_id][t] += 1

    # ----- referees -----
    fixed_refs = {m.referee_id for m in session if m.referee_id}
    playing_ids: set[int] = set()
    for m in session:
        playing_ids.add(m.player1_id)
        playing_ids.add(m.player2_id)
    needs_ref = [m for m in session if not m.referee_id]
    candidates = sorted(
        (pid for pid in player_ids if pid not in playing_ids and pid not in fixed_refs),
        key=lambda pid: (ref_counts[pid], pid),
    )
    for m in needs_ref:
        if not candidates:
            break
        ref = candidates.pop(0)
        m.referee_id = ref
        ref_counts[ref] += 1


def assign_tables_and_referees(
    matches: list[Match],
    player_ids: list[int],
    table_counts: dict | None = None,
    ref_counts: dict | None = None,
) -> list[Match]:
    """Session-aware fair assignment of tables and referees.

    Constraints:
      * Within a session (3 matches sharing the 3 physical tables) each table
        1, 2, 3 is used exactly once.
      * Each player ends up playing roughly the same number of times on each
        of the 3 tables.
      * Each player referees roughly the same number of matches.

    Matches that already have a non-zero `table_number` are left untouched
    (this lets us re-run the algorithm without disturbing played matches).
    Their counts must already be present in `table_counts` / `ref_counts`.
    """
    if table_counts is None or ref_counts is None:
        table_counts, ref_counts = _initial_counts(player_ids)
    for session in group_matches_into_sessions(matches):
        _assign_session(session, table_counts, ref_counts, player_ids)
    return matches


def derive_match_result(set_scores: list[list[int]]) -> tuple[int, int, bool]:
    """Compute (sets_won_p1, sets_won_p2, played) from per-set scores.

    A set is counted for a player only if their score in that set is strictly
    greater than the opponent's. Empty (0, 0) sets are skipped. The match is
    'played' as soon as at least one set has a winner.
    """
    s1 = sum(1 for s in set_scores if len(s) >= 2 and s[0] > s[1])
    s2 = sum(1 for s in set_scores if len(s) >= 2 and s[1] > s[0])
    return s1, s2, (s1 + s2) > 0


# Fixed seeding: with players ranked 1..12 by initial points (descending),
# pool A receives ranks 1, 4, 5, 8, 9, 12 and pool B the others.
# 0-indexed positions of pool A in the sorted-by-points list.
POOL_A_SEEDS = [0, 3, 4, 7, 8, 11]
POOL_B_SEEDS = [1, 2, 5, 6, 9, 10]


def rank_by_points(players: List[Player]) -> List[Player]:
    """Return players sorted by initial points (desc), tiebreak alphabetical."""
    return sorted(players, key=lambda p: (-p.points, p.name.lower()))


def split_into_pools(players: List[Player]) -> tuple[List[Player], List[Player]]:
    """Split 12 players into pools A and B (6 each) using fixed seeding.

    Players are first ordered by initial points (desc). Ranks 1, 4, 5, 8, 9, 12
    go into pool A; the others into pool B. Within each pool, players are kept
    ordered by points (highest-ranked first).
    """
    if len(players) != 12:
        raise ValueError(f"Expected 12 players, got {len(players)}")

    ranked = rank_by_points(players)
    pool_a = [ranked[i] for i in POOL_A_SEEDS]
    pool_b = [ranked[i] for i in POOL_B_SEEDS]
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
    """Compute standings with the project's tiebreak rules.

    Filters
    -------
    - ``pool="A"``/``"B"``: only that pool's intra-pool matches are considered.
    - ``pool=None``: every played match counts.
    - ``max_round``: caps the rounds taken into account.

    Tiebreak order
    --------------
    1. Match points DESC.
    2. If **exactly 2** players are tied on points: head-to-head winner first.
    3. If **3 or more** are tied: order by set differential (sets won − sets lost).
       Within a sub-group still tied after the differential, fall back to rule 2
       if the sub-group has 2 players; otherwise alphabetical.
    """
    by_id = {p.id: PlayerStanding(player=p) for p in players}
    if pool is not None:
        by_id = {pid: st for pid, st in by_id.items() if st.player.pool == pool}

    played_matches: list[Match] = []
    for m in matches:
        if not m.played:
            continue
        if max_round is not None and m.round_number > max_round:
            continue
        if pool is not None and m.pool != pool:
            continue
        if m.player1_id not in by_id or m.player2_id not in by_id:
            continue
        played_matches.append(m)
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
    return _rank_with_tiebreaks(standings, played_matches)


def _rank_with_tiebreaks(standings: list, played_matches: list) -> list:
    """Sort by points DESC, then resolve ties group by group."""
    standings.sort(key=lambda s: -s.points)
    result: list = []
    i = 0
    while i < len(standings):
        j = i
        while j + 1 < len(standings) and standings[j + 1].points == standings[i].points:
            j += 1
        result.extend(_break_points_tie(standings[i:j + 1], played_matches))
        i = j + 1
    return result


def _break_points_tie(group: list, played_matches: list) -> list:
    """Break a tie among players with the same number of match points."""
    if len(group) <= 1:
        return list(group)
    if len(group) == 2:
        return _head_to_head_order(group, played_matches)
    # 3+ players: order by set differential, then break still-tied sub-groups.
    by_diff = sorted(group, key=lambda s: -s.set_diff)
    out: list = []
    i = 0
    while i < len(by_diff):
        j = i
        while j + 1 < len(by_diff) and by_diff[j + 1].set_diff == by_diff[i].set_diff:
            j += 1
        subgroup = by_diff[i:j + 1]
        if len(subgroup) == 1:
            out.extend(subgroup)
        elif len(subgroup) == 2:
            out.extend(_head_to_head_order(subgroup, played_matches))
        else:
            out.extend(sorted(subgroup, key=lambda s: s.player.name.lower()))
        i = j + 1
    return out


def _head_to_head_order(pair: list, played_matches: list) -> list:
    """Return [winner, loser] of the head-to-head match. Alphabetical if no match found."""
    a, b = pair
    aid, bid = a.player.id, b.player.id
    for m in played_matches:
        if {m.player1_id, m.player2_id} == {aid, bid}:
            if m.score1 > m.score2:
                winner_id = m.player1_id
            elif m.score2 > m.score1:
                winner_id = m.player2_id
            else:
                break
            return [a, b] if winner_id == aid else [b, a]
    return sorted(pair, key=lambda s: s.player.name.lower())


def is_phase_complete(matches: Iterable[Match], rounds: Iterable[int]) -> bool:
    rounds_set = set(rounds)
    relevant = [m for m in matches if m.round_number in rounds_set]
    if not relevant:
        return False
    return all(m.played for m in relevant)
