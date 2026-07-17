import collections

import pytest

from src.active import actions, entities


def test_raises_when_player_not_required_to_discard(
    game: entities.ActiveGame,
) -> None:
    player = game.turn_order[0]
    game.to_discard_resources = {game.turn_order[1]: 4}

    with pytest.raises(actions.PlayerNotRequiredToDiscardError):
        actions.handle_discard_resources(
            game,
            actions.DiscardResourcesAction(
                by=player,
                count=collections.Counter({entities.ResourceCard.WOOD: 4}),
            ),
        )


def test_raises_when_discard_count_is_wrong(game: entities.ActiveGame) -> None:
    player = game.turn_order[0]
    game.to_discard_resources = {player: 4}
    game.players[player].resources = collections.Counter(
        {entities.ResourceCard.WOOD: 9}
    )

    with pytest.raises(actions.InvalidDiscardCountError):
        actions.handle_discard_resources(
            game,
            actions.DiscardResourcesAction(
                by=player,
                count=collections.Counter({entities.ResourceCard.WOOD: 5}),
            ),
        )


def test_raises_when_insufficient_resources_of_type(
    game: entities.ActiveGame,
) -> None:
    player = game.turn_order[0]
    game.to_discard_resources = {player: 4}
    game.players[player].resources = collections.Counter(
        {
            entities.ResourceCard.WOOD: 6,
            entities.ResourceCard.GOLD: 2,
        }
    )

    with pytest.raises(actions.InsufficientResourcesError):
        actions.handle_discard_resources(
            game,
            actions.DiscardResourcesAction(
                by=player,
                count=collections.Counter({entities.ResourceCard.GOLD: 4}),
            ),
        )


def test_discard_removes_player_and_stays_in_phase_when_others_remain(
    game: entities.ActiveGame,
) -> None:
    player = game.turn_order[0]
    other = game.turn_order[1]
    game.to_discard_resources = {player: 4, other: 5}
    game.players[player].resources = collections.Counter(
        {entities.ResourceCard.WOOD: 8}
    )
    supply_before = game.resource_supply[entities.ResourceCard.WOOD]

    phase = actions.handle_discard_resources(
        game,
        actions.DiscardResourcesAction(
            by=player,
            count=collections.Counter({entities.ResourceCard.WOOD: 4}),
        ),
    )

    assert phase is actions.GamePhaseName.DISCARD_RESOURCES
    assert game.to_discard_resources == {other: 5}
    assert game.players[player].resources[entities.ResourceCard.WOOD] == 4
    assert game.resource_supply[entities.ResourceCard.WOOD] == supply_before + 4


def test_last_discard_moves_to_move_conquistator(
    game: entities.ActiveGame,
) -> None:
    player = game.turn_order[0]
    game.to_discard_resources = {player: 4}
    game.players[player].resources = collections.Counter(
        {
            entities.ResourceCard.WOOD: 5,
            entities.ResourceCard.GOLD: 4,
        }
    )

    phase = actions.handle_discard_resources(
        game,
        actions.DiscardResourcesAction(
            by=player,
            count=collections.Counter(
                {
                    entities.ResourceCard.WOOD: 2,
                    entities.ResourceCard.GOLD: 2,
                }
            ),
        ),
    )

    assert phase is actions.GamePhaseName.MOVE_CONQUISTATOR
    assert game.to_discard_resources == {}
    assert sum(game.players[player].resources.values()) == 5
