import collections
import collections.abc
import random
from typing import TypeVar

import pytest

from src.active import entities
from src.active.services import actions

_T = TypeVar("_T")


def test_takes_two_resources_from_supply(game: entities.ActiveGame) -> None:
    active = game.active_player
    taken = collections.Counter(
        {
            entities.ResourceCard.GOLD: 1,
            entities.ResourceCard.WOOD: 1,
        }
    )
    gold_before = game.resource_supply[entities.ResourceCard.GOLD]
    wood_before = game.resource_supply[entities.ResourceCard.WOOD]

    result = actions.take_from_supply(game, active, resources=taken)

    assert result == taken
    assert game.players[active].resources[entities.ResourceCard.GOLD] == 1
    assert game.players[active].resources[entities.ResourceCard.WOOD] == 1
    assert game.resource_supply[entities.ResourceCard.GOLD] == gold_before - 1
    assert game.resource_supply[entities.ResourceCard.WOOD] == wood_before - 1


def test_takes_two_of_same_resource(game: entities.ActiveGame) -> None:
    active = game.active_player
    taken = collections.Counter({entities.ResourceCard.STONE: 2})

    actions.take_from_supply(game, active, resources=taken)

    assert game.players[active].resources[entities.ResourceCard.STONE] == 2
    assert game.resource_supply[entities.ResourceCard.STONE] == 17


def test_rejects_wrong_take_count(game: entities.ActiveGame) -> None:
    with pytest.raises(actions.InvalidTakeFromSupply):
        actions.take_from_supply(
            game,
            game.active_player,
            resources=collections.Counter({entities.ResourceCard.GOLD: 1}),
        )


def test_rejects_insufficient_supply(game: entities.ActiveGame) -> None:
    game.resource_supply[entities.ResourceCard.GOLD] = 0
    with pytest.raises(actions.InsufficientResources):
        actions.take_from_supply(
            game,
            game.active_player,
            resources=collections.Counter(
                {
                    entities.ResourceCard.GOLD: 1,
                    entities.ResourceCard.WOOD: 1,
                }
            ),
        )


def test_take_from_supply_randomly_grants_two(game: entities.ActiveGame) -> None:
    active = game.active_player
    game.resource_supply = collections.Counter(
        {
            entities.ResourceCard.GOLD: 1,
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.COTTON: 0,
            entities.ResourceCard.MAIZE: 0,
            entities.ResourceCard.WOOD: 0,
        }
    )
    rnd = _FixedSampleRandom([0, 1])

    result = actions.take_from_supply_randomly(game, active, rnd=rnd)

    assert result == collections.Counter(
        {
            entities.ResourceCard.GOLD: 1,
            entities.ResourceCard.STONE: 1,
        }
    )
    assert game.players[active].resources[entities.ResourceCard.GOLD] == 1
    assert game.players[active].resources[entities.ResourceCard.STONE] == 1
    assert sum(game.resource_supply.values()) == 0


def test_take_from_supply_randomly_takes_fewer_when_supply_short(
    game: entities.ActiveGame,
) -> None:
    active = game.active_player
    game.resource_supply = collections.Counter(
        {
            entities.ResourceCard.GOLD: 1,
            entities.ResourceCard.STONE: 0,
            entities.ResourceCard.COTTON: 0,
            entities.ResourceCard.MAIZE: 0,
            entities.ResourceCard.WOOD: 0,
        }
    )

    result = actions.take_from_supply_randomly(game, active, rnd=random.Random(0))

    assert result == collections.Counter({entities.ResourceCard.GOLD: 1})
    assert game.players[active].resources[entities.ResourceCard.GOLD] == 1
    assert sum(game.resource_supply.values()) == 0


def test_take_from_supply_randomly_empty_supply(game: entities.ActiveGame) -> None:
    active = game.active_player
    game.resource_supply = collections.Counter(
        {
            entities.ResourceCard.GOLD: 0,
            entities.ResourceCard.STONE: 0,
            entities.ResourceCard.COTTON: 0,
            entities.ResourceCard.MAIZE: 0,
            entities.ResourceCard.WOOD: 0,
        }
    )

    result = actions.take_from_supply_randomly(game, active)

    assert result == collections.Counter()
    assert sum(game.players[active].resources.values()) == 0


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
