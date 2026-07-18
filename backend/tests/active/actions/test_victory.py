from src.active import actions, entities


def test_terraces_and_great_terraces(game: entities.ActiveGame) -> None:
    by = game.active_player
    player = game.players[by]
    player.settlements[entities.canonical_vertex(0, 0, 0)] = (
        entities.SettlementType.TERRACE
    )
    player.settlements[entities.canonical_vertex(0, 0, 2)] = (
        entities.SettlementType.GREAT_TERRACE
    )

    assert actions.victory_points(game, by) == 3


def test_longest_road_and_biggest_army_bonuses(game: entities.ActiveGame) -> None:
    by = game.active_player
    game.longest_road = (by, 5)
    game.biggest_army = (by, 3)

    assert actions.victory_points(game, by) == 4


def test_legacy_cards_count(game: entities.ActiveGame) -> None:
    by = game.active_player
    game.players[by].played_cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS] = 2

    assert actions.victory_points(game, by) == 2


def test_bonuses_do_not_apply_for_other_players(game: entities.ActiveGame) -> None:
    by = game.active_player
    other = game.turn_order[1]
    game.longest_road = (other, 5)
    game.biggest_army = (other, 3)
    game.players[other].played_cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS] = 1

    assert actions.victory_points(game, by) == 0


def test_phase_after_victory_check_returns_end_game_when_at_least_ten(
    game: entities.ActiveGame,
) -> None:
    by = game.active_player
    game.players[by].played_cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS] = 10

    assert (
        actions.phase_after_victory_check(
            game, by, actions.GamePhaseName.TRADE_AND_BUILD
        )
        is actions.GamePhaseName.END_GAME
    )


def test_phase_after_victory_check_returns_fallback_when_below_ten(
    game: entities.ActiveGame,
) -> None:
    by = game.active_player
    game.players[by].played_cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS] = 9

    assert (
        actions.phase_after_victory_check(
            game, by, actions.GamePhaseName.TRADE_AND_BUILD
        )
        is actions.GamePhaseName.TRADE_AND_BUILD
    )
