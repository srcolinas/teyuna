import collections

from src.game import actions, entities
import teyuna_shared


def test_raises_when_player_not_required_to_discard(
    game: entities.Game,
) -> None:
    player = game.turn_order[0]
    game.to_discard_resources = {game.turn_order[1]: 4}

    result = actions.handle_discard_resources(
        game,
        teyuna_shared.DiscardResourcesAction(
            by=player,
            count=collections.Counter({teyuna_shared.ResourceCard.WOOD: 4}),
        ),
    )
    assert result.error == f"Player {player} is not required to discard resources"
    assert result.count == collections.Counter()


def test_raises_when_discard_count_is_wrong(game: entities.Game) -> None:
    player = game.turn_order[0]
    game.to_discard_resources = {player: 4}
    game.players[player].resources = collections.Counter(
        {teyuna_shared.ResourceCard.WOOD: 9}
    )

    result = actions.handle_discard_resources(
        game,
        teyuna_shared.DiscardResourcesAction(
            by=player,
            count=collections.Counter({teyuna_shared.ResourceCard.WOOD: 5}),
        ),
    )
    assert result.error == f"Player {player} must discard 4 resources"
    assert result.count == collections.Counter()


def test_raises_when_insufficient_resources_of_type(
    game: entities.Game,
) -> None:
    player = game.turn_order[0]
    game.to_discard_resources = {player: 4}
    game.players[player].resources = collections.Counter(
        {
            teyuna_shared.ResourceCard.WOOD: 6,
            teyuna_shared.ResourceCard.GOLD: 2,
        }
    )

    result = actions.handle_discard_resources(
        game,
        teyuna_shared.DiscardResourcesAction(
            by=player,
            count=collections.Counter({teyuna_shared.ResourceCard.GOLD: 4}),
        ),
    )
    assert result.error == "Insufficient gold to discard"
    assert result.count == collections.Counter()


def test_discard_removes_player_and_stays_in_phase_when_others_remain(
    game: entities.Game,
) -> None:
    player = game.turn_order[0]
    other = game.turn_order[1]
    game.to_discard_resources = {player: 4, other: 5}
    game.players[player].resources = collections.Counter(
        {teyuna_shared.ResourceCard.WOOD: 8}
    )
    supply_before = game.resource_supply[teyuna_shared.ResourceCard.WOOD]

    count = collections.Counter({teyuna_shared.ResourceCard.WOOD: 4})
    result = actions.handle_discard_resources(
        game,
        teyuna_shared.DiscardResourcesAction(
            by=player,
            count=count,
        ),
    )

    assert result.error is None
    assert result.next_phase is teyuna_shared.GamePhaseName.DISCARD_RESOURCES
    assert result.count == count
    assert game.to_discard_resources == {other: 5}
    assert game.players[player].resources[teyuna_shared.ResourceCard.WOOD] == 4
    assert game.resource_supply[teyuna_shared.ResourceCard.WOOD] == supply_before + 4


def test_last_discard_moves_to_move_conquistator(
    game: entities.Game,
) -> None:
    player = game.turn_order[0]
    game.to_discard_resources = {player: 4}
    game.players[player].resources = collections.Counter(
        {
            teyuna_shared.ResourceCard.WOOD: 5,
            teyuna_shared.ResourceCard.GOLD: 4,
        }
    )

    count = collections.Counter(
        {
            teyuna_shared.ResourceCard.WOOD: 2,
            teyuna_shared.ResourceCard.GOLD: 2,
        }
    )
    result = actions.handle_discard_resources(
        game,
        teyuna_shared.DiscardResourcesAction(
            by=player,
            count=count,
        ),
    )

    assert result.error is None
    assert result.next_phase is teyuna_shared.GamePhaseName.MOVE_CONQUISTATOR
    assert result.count == count
    assert game.to_discard_resources == {}
    assert sum(game.players[player].resources.values()) == 5
