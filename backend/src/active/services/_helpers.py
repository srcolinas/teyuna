import collections

from ... import player
from .. import entities


def discount_resources(
    game: entities.ActiveGame,
    to: player.Nickname,
    resources: collections.Counter[entities.ResourceCard],
) -> None:
    game.players[to].resources -= resources
    game.resource_supply += resources


def grant_resources(
    game: entities.ActiveGame,
    to: player.Nickname,
    resources: collections.Counter[entities.ResourceCard],
) -> None:
    game.players[to].resources += resources
    game.resource_supply -= resources
