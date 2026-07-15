from src.active import entities
from src.active.services import actions


def test_first_award_at_three_warriors(game: entities.ActiveGame) -> None:
    by = game.active_player
    game.players[by].played_cards[entities.WisdomCard.WARRIOR] = 3

    result = actions.update_biggest_army(game, by)

    assert result == (by, 3)
    assert game.biggest_army == (by, 3)


def test_below_threshold_does_not_award(game: entities.ActiveGame) -> None:
    by = game.active_player
    game.players[by].played_cards[entities.WisdomCard.WARRIOR] = 2

    result = actions.update_biggest_army(game, by)

    assert result is None
    assert game.biggest_army == (None, 0)


def test_steal_when_strictly_more(game: entities.ActiveGame) -> None:
    holder = game.turn_order[1]
    stealer = game.active_player
    game.biggest_army = (holder, 3)
    game.players[stealer].played_cards[entities.WisdomCard.WARRIOR] = 4

    result = actions.update_biggest_army(game, stealer)

    assert result == (stealer, 4)
    assert game.biggest_army == (stealer, 4)


def test_equal_count_does_not_steal(game: entities.ActiveGame) -> None:
    holder = game.turn_order[1]
    challenger = game.active_player
    game.biggest_army = (holder, 3)
    game.players[challenger].played_cards[entities.WisdomCard.WARRIOR] = 3

    result = actions.update_biggest_army(game, challenger)

    assert result is None
    assert game.biggest_army == (holder, 3)


def test_same_holder_count_growth_is_silent(game: entities.ActiveGame) -> None:
    holder = game.active_player
    game.biggest_army = (holder, 3)
    game.players[holder].played_cards[entities.WisdomCard.WARRIOR] = 4

    result = actions.update_biggest_army(game, holder)

    assert result is None
    assert game.biggest_army == (holder, 4)
