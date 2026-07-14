from __future__ import annotations

import collections
import random

from .... import player
from ... import entities
from . import _errors

_RND: random.Random = random.Random()


def move_conquistator(
    game: entities.ActiveGame,
    to: player.Nickname,
    /,
    *,
    q: int,
    r: int,
    from_player: player.Nickname | None = None,
    rnd: random.Random = _RND,
) -> None:
    target = _require_new_hex(game, q=q, r=r)
    if from_player is not None:
        if not _owns_settlement_on_hex(game, from_player, q=q, r=r):
            raise _errors.InvalidStealTarget(
                f"Player {from_player} does not own a settlement on hex ({q}, {r})."
            )
        _steal_random_resource(game, to=to, from_player=from_player, rnd=rnd)
    game.conquistator_location = target


def move_conquistator_randomly(
    game: entities.ActiveGame,
    /,
    *,
    rnd: random.Random = _RND,
) -> None:
    current = game.conquistator_location
    candidates = [
        hex_tile
        for hex_tile in game.map
        if (hex_tile.q, hex_tile.r) != (current.q, current.r)
    ]
    if not candidates:
        raise _errors.InvalidConquistatorLocation(
            "No alternate hex available for conquistator."
        )
    game.conquistator_location = rnd.choice(candidates)


def _require_new_hex(game: entities.ActiveGame, *, q: int, r: int) -> entities.Hex:
    current = game.conquistator_location
    if current.q == q and current.r == r:
        raise _errors.InvalidConquistatorLocation(
            f"Conquistator is already at hex ({q}, {r})."
        )
    for hex_tile in game.map:
        if hex_tile.q == q and hex_tile.r == r:
            return hex_tile
    raise _errors.InvalidConquistatorLocation(f"Hex ({q}, {r}) is not on the map.")


def _owns_settlement_on_hex(
    game: entities.ActiveGame,
    nickname: player.Nickname,
    *,
    q: int,
    r: int,
) -> bool:
    settlements = game.players[nickname].settlements
    for direction in range(6):
        coord = entities.canonical_vertex(q, r, direction)
        if coord in settlements:
            return True
    return False


def _steal_random_resource(
    game: entities.ActiveGame,
    *,
    to: player.Nickname,
    from_player: player.Nickname,
    rnd: random.Random,
) -> None:
    hand = game.players[from_player].resources
    pool: list[entities.ResourceCard] = []
    for resource, amount in hand.items():
        pool.extend([resource] * amount)
    if not pool:
        return
    stolen = rnd.choice(pool)
    transfer = collections.Counter({stolen: 1})
    game.players[from_player].resources -= transfer
    game.players[to].resources += transfer
