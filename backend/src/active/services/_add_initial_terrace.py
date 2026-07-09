from ... import player
from .. import entities
from . import _errors


def add_initial_terrace(
    game: entities.ActiveGame,
    to: player.Nickname,
    /,
    *,
    q: int,
    r: int,
    direction: int,
) -> None:
    if game.phase is not entities.GamePhase.INITIAL:
        raise _errors.InvalidGamePhase

    if to != game.turn_order[0]:
        raise _errors.PlayerNotInTurn

    target = entities.canonical_vertex(q, r, direction)
    if target not in game.free_verticies or target in game.restricted_verticies:
        raise _errors.InvalidSettlementLocation

    game.add_terrace(to, q=q, r=r, direction=direction)
