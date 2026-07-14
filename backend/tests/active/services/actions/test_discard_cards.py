import collections
import collections.abc
import random
from typing import TypeVar

import pytest

from src.active import entities
from src.active.services import actions

_T = TypeVar("_T")


def test_discards_half_of_eight_cards_and_returns_to_supply(
    game: entities.ActiveGame,
) -> None:
    player = game.players[game.active_player]
    player.resources = collections.Counter(
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.STONE: 3,
            entities.ResourceCard.WOOD: 2,
        }
    )
    supply_before = game.resource_supply[entities.ResourceCard.GOLD]
    discarded = collections.Counter(
        {
            entities.ResourceCard.GOLD: 2,
            entities.ResourceCard.STONE: 2,
        }
    )

    actions.discard_cards(game, game.active_player, resources=discarded)

    assert sum(player.resources.values()) == 4
    assert player.resources[entities.ResourceCard.GOLD] == 1
    assert player.resources[entities.ResourceCard.STONE] == 1
    assert player.resources[entities.ResourceCard.WOOD] == 2
    assert game.resource_supply[entities.ResourceCard.GOLD] == supply_before + 2
    assert game.resource_supply[entities.ResourceCard.STONE] == 19 + 2


def test_discards_four_when_total_is_odd_nine(
    game: entities.ActiveGame,
) -> None:
    player = game.players[game.active_player]
    player.resources = collections.Counter(
        {
            entities.ResourceCard.GOLD: 5,
            entities.ResourceCard.MAIZE: 4,
        }
    )
    discarded = collections.Counter({entities.ResourceCard.GOLD: 4})

    actions.discard_cards(game, game.active_player, resources=discarded)

    assert sum(player.resources.values()) == 5
    assert player.resources[entities.ResourceCard.GOLD] == 1
    assert player.resources[entities.ResourceCard.MAIZE] == 4


def test_rejects_when_player_has_seven_or_fewer_cards(
    game: entities.ActiveGame,
) -> None:
    game.players[game.active_player].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 7}
    )
    with pytest.raises(actions.InvalidDiscard):
        actions.discard_cards(
            game,
            game.active_player,
            resources=collections.Counter({entities.ResourceCard.GOLD: 3}),
        )


def test_rejects_wrong_discard_count(
    game: entities.ActiveGame,
) -> None:
    game.players[game.active_player].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 8}
    )
    with pytest.raises(actions.InvalidDiscard):
        actions.discard_cards(
            game,
            game.active_player,
            resources=collections.Counter({entities.ResourceCard.GOLD: 3}),
        )


def test_rejects_over_selecting_a_type(
    game: entities.ActiveGame,
) -> None:
    game.players[game.active_player].resources = collections.Counter(
        {
            entities.ResourceCard.GOLD: 2,
            entities.ResourceCard.STONE: 6,
        }
    )
    with pytest.raises(actions.InsufficientResources):
        actions.discard_cards(
            game,
            game.active_player,
            resources=collections.Counter({entities.ResourceCard.GOLD: 4}),
        )


def test_discard_random_half_reduces_by_half(
    game: entities.ActiveGame,
) -> None:
    player = game.players[game.active_player]
    player.resources = collections.Counter(
        {
            entities.ResourceCard.GOLD: 4,
            entities.ResourceCard.STONE: 4,
        }
    )
    actions.discard_random_half(
        game, game.active_player, rnd=_FixedSampleRandom([0, 1, 2, 3])
    )
    assert sum(player.resources.values()) == 4


class _FixedSampleRandom(random.Random):
    def __init__(self, indexes: list[int]) -> None:
        super().__init__()
        self._indexes = indexes

    def sample(
        self,
        population: collections.abc.Sequence[_T],
        k: int,
        *,
        counts: collections.abc.Iterable[int] | None = None,
    ) -> list[_T]:
        del counts
        return [population[i] for i in self._indexes[:k]]
