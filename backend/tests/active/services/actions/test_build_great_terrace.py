import pytest

from src.active import entities
from src.active.services import actions

from .... import utils

_GREAT_TERRACE_COST = {
    entities.ResourceCard.GOLD: 3,
    entities.ResourceCard.MAIZE: 2,
}


def test_cannot_build_great_terrace_if_terrace_not_placed_before(
    game: entities.ActiveGame,
) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.resources.update(_GREAT_TERRACE_COST)
    with pytest.raises(
        actions.InvalidSettlementLocation,
        match="You must first build a terrace at specified location.",
    ):
        actions.build_great_terrace(game, game.active_player, q=0, r=0, direction=2)


def test_can_build_great_terrace_with_sufficient_resources(
    game: entities.ActiveGame,
) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.resources.update(_GREAT_TERRACE_COST)
    with utils.assert_not_raises(actions.InsufficientResources):
        actions.build_great_terrace(game, game.active_player, q=0, r=0, direction=0)


@pytest.mark.parametrize(
    "resources",
    [
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 1,
        },
        {
            entities.ResourceCard.GOLD: 2,
            entities.ResourceCard.MAIZE: 2,
        },
    ],
)
def test_cannot_build_great_terrace_with_insufficient_resources(
    resources: dict[entities.ResourceCard, int], game: entities.ActiveGame
) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.resources.update(resources)
    with pytest.raises(actions.InsufficientResources):
        actions.build_great_terrace(game, game.active_player, q=0, r=0, direction=0)


def test_great_terrace_is_added_to_game_object(game: entities.ActiveGame) -> None:
    player = game.players[game.active_player]
    target = entities.canonical_vertex(0, 0, 2)
    player.settlements[target] = entities.SettlementType.TERRACE
    player.resources.update(_GREAT_TERRACE_COST)
    actions.build_great_terrace(game, game.active_player, q=0, r=0, direction=2)
    assert player.settlements[target] is entities.SettlementType.GREAT_TERRACE


def test_resources_are_removed_from_player(game: entities.ActiveGame) -> None:
    player = game.players[game.active_player]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.resources.update(_GREAT_TERRACE_COST)
    actions.build_great_terrace(game, game.active_player, q=0, r=0, direction=0)
    assert player.resources[entities.ResourceCard.GOLD] == 0
    assert player.resources[entities.ResourceCard.MAIZE] == 0


def test_cannot_build_great_terrace_if_not_enough_great_terraces_available(
    game: entities.ActiveGame,
) -> None:
    player = game.players[game.active_player]
    for i in range(entities.MAX_GREAT_TERRACES):
        player.settlements[entities.Coordinate(q=0, r=0, d=i)] = (
            entities.SettlementType.GREAT_TERRACE
        )
    player.settlements[entities.canonical_vertex(0, 0, 5)] = (
        entities.SettlementType.TERRACE
    )
    player.resources.update(_GREAT_TERRACE_COST)
    with pytest.raises(actions.InsufficientResources):
        actions.build_great_terrace(game, game.active_player, q=0, r=0, direction=5)
