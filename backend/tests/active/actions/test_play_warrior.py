from src.active import actions, entities


def test_raises_when_player_not_in_turn(game: entities.ActiveGame) -> None:
    result = actions.handle_dice_play_warrior(
        game,
        actions.MoveConquistatorAction(by=game.turn_order[1], q=1, r=0),
    )
    assert result.succeeded is False
    assert result.q == -1
    assert result.r == -1
    assert result.from_player is None
    assert result.stolen is None
    assert result.error is not None
    assert type(result.error) is actions.PlayerNotInTurnError


def test_raises_when_location_is_unchanged(game: entities.ActiveGame) -> None:
    location = game.conquistator_location
    result = actions.handle_dice_play_warrior(
        game,
        actions.MoveConquistatorAction(
            by=game.active_player, q=location.q, r=location.r
        ),
    )
    assert result.succeeded is False
    assert result.q == -1
    assert result.r == -1
    assert result.from_player is None
    assert result.stolen is None
    assert result.error is not None
    assert type(result.error) is actions.InvalidConquistatorLocation


def test_moves_conquistator_and_returns_to_dice_roll(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player

    result = actions.handle_dice_play_warrior(
        game,
        actions.MoveConquistatorAction(by=player, q=1, r=-1),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.DICE_ROLL
    assert result.q == 1
    assert result.r == -1
    assert result.from_player is None
    assert result.stolen is None
    assert game.conquistator_location == entities.HexLocation(q=1, r=-1)
    assert game.player_idx == 0


def test_moves_conquistator_and_returns_to_trade_and_build(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player

    result = actions.handle_move_conquistator(
        game,
        actions.MoveConquistatorAction(by=player, q=1, r=-1),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.TRADE_AND_BUILD
    assert result.q == 1
    assert result.r == -1
    assert result.from_player is None
    assert result.stolen is None
    assert game.conquistator_location == entities.HexLocation(q=1, r=-1)
    assert game.player_idx == 0


def test_does_not_take_resources_when_from_player_is_none(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    other = game.turn_order[1]
    game.players[other].resources[entities.ResourceCard.WOOD] = 2

    result = actions.handle_dice_play_warrior(
        game,
        actions.MoveConquistatorAction(by=player, q=1, r=0, from_player=None),
    )

    assert result.succeeded is True
    assert result.q == 1
    assert result.r == 0
    assert result.from_player is None
    assert result.stolen is None
    assert game.players[other].resources[entities.ResourceCard.WOOD] == 2
    assert game.players[player].resources[entities.ResourceCard.WOOD] == 0


def test_takes_one_resource_when_from_player_is_set(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    other = game.turn_order[1]
    game.players[other].resources[entities.ResourceCard.WOOD] = 2

    result = actions.handle_dice_play_warrior(
        game,
        actions.MoveConquistatorAction(by=player, q=1, r=0, from_player=other),
    )

    assert result.succeeded is True
    assert result.q == 1
    assert result.r == 0
    assert result.from_player == other
    assert result.stolen is entities.ResourceCard.WOOD
    assert game.players[other].resources[entities.ResourceCard.WOOD] == 1
    assert game.players[player].resources[entities.ResourceCard.WOOD] == 1
