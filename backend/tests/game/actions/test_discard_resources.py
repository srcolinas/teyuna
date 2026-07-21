import collections

from src.game import actions, entities


def test_raises_when_player_not_required_to_discard(
    game: entities.Game,
) -> None:
    player = game.turn_order[0]
    game.to_discard_resources = {game.turn_order[1]: 4}

    result = actions.handle_discard_resources(
        game,
        actions.DiscardResourcesAction(
            by=player,
            count=collections.Counter({entities.ResourceCard.WOOD: 4}),
        ),
    )
    assert result.succeeded is False
    assert result.count == collections.Counter()
    assert result.error is not None
    assert type(result.error) is actions.PlayerNotRequiredToDiscardError


def test_raises_when_discard_count_is_wrong(game: entities.Game) -> None:
    player = game.turn_order[0]
    game.to_discard_resources = {player: 4}
    game.players[player].resources = collections.Counter(
        {entities.ResourceCard.WOOD: 9}
    )

    result = actions.handle_discard_resources(
        game,
        actions.DiscardResourcesAction(
            by=player,
            count=collections.Counter({entities.ResourceCard.WOOD: 5}),
        ),
    )
    assert result.succeeded is False
    assert result.count == collections.Counter()
    assert result.error is not None
    assert type(result.error) is actions.InvalidDiscardCountError


def test_raises_when_insufficient_resources_of_type(
    game: entities.Game,
) -> None:
    player = game.turn_order[0]
    game.to_discard_resources = {player: 4}
    game.players[player].resources = collections.Counter(
        {
            entities.ResourceCard.WOOD: 6,
            entities.ResourceCard.GOLD: 2,
        }
    )

    result = actions.handle_discard_resources(
        game,
        actions.DiscardResourcesAction(
            by=player,
            count=collections.Counter({entities.ResourceCard.GOLD: 4}),
        ),
    )
    assert result.succeeded is False
    assert result.count == collections.Counter()
    assert result.error is not None
    assert type(result.error) is actions.InsufficientResourcesError


def test_discard_removes_player_and_stays_in_phase_when_others_remain(
    game: entities.Game,
) -> None:
    player = game.turn_order[0]
    other = game.turn_order[1]
    game.to_discard_resources = {player: 4, other: 5}
    game.players[player].resources = collections.Counter(
        {entities.ResourceCard.WOOD: 8}
    )
    supply_before = game.resource_supply[entities.ResourceCard.WOOD]

    count = collections.Counter({entities.ResourceCard.WOOD: 4})
    result = actions.handle_discard_resources(
        game,
        actions.DiscardResourcesAction(
            by=player,
            count=count,
        ),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is entities.GamePhaseName.DISCARD_RESOURCES
    assert result.count == count
    assert game.to_discard_resources == {other: 5}
    assert game.players[player].resources[entities.ResourceCard.WOOD] == 4
    assert game.resource_supply[entities.ResourceCard.WOOD] == supply_before + 4


def test_last_discard_moves_to_move_conquistator(
    game: entities.Game,
) -> None:
    player = game.turn_order[0]
    game.to_discard_resources = {player: 4}
    game.players[player].resources = collections.Counter(
        {
            entities.ResourceCard.WOOD: 5,
            entities.ResourceCard.GOLD: 4,
        }
    )

    count = collections.Counter(
        {
            entities.ResourceCard.WOOD: 2,
            entities.ResourceCard.GOLD: 2,
        }
    )
    result = actions.handle_discard_resources(
        game,
        actions.DiscardResourcesAction(
            by=player,
            count=count,
        ),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is entities.GamePhaseName.MOVE_CONQUISTATOR
    assert result.count == count
    assert game.to_discard_resources == {}
    assert sum(game.players[player].resources.values()) == 5
