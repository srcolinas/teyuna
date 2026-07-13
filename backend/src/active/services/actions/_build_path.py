from .... import player
from ... import entities
from . import _add_free_path, _errors


def build_path(
    game: entities.ActiveGame,
    to: player.Nickname,
    /,
    *,
    q: int,
    r: int,
    direction: int,
) -> None:
    if len(game.players[to].paths) >= entities.MAX_PATHS:
        raise _errors.InsufficientResources

    resources = game.players[to].resources
    if resources[entities.ResourceCard.STONE] < 1:
        raise _errors.InsufficientResources

    if resources[entities.ResourceCard.WOOD] < 1:
        raise _errors.InsufficientResources

    _add_free_path.add_free_path(game, to, q=q, r=r, direction=direction)
    game.players[to].resources.update(
        {
            entities.ResourceCard.STONE: -1,
            entities.ResourceCard.WOOD: -1,
        }
    )
