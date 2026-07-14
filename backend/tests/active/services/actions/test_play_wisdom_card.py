import pytest

from src.active import entities
from src.active.services import actions


def test_cannot_play_wisdom_card_if_not_owned(
    game: entities.ActiveGame,
) -> None:
    with pytest.raises(actions.WisdomCardNotPlayable):
        actions.play_wisdom_card(
            game, game.active_player, card=entities.WisdomCard.WARRIOR
        )


def test_cannot_play_wisdom_card_bought_this_turn(
    game: entities.ActiveGame,
) -> None:
    player = game.players[game.active_player]
    player.cards[entities.WisdomCard.WARRIOR] = 1
    player.cards_bought_this_turn[entities.WisdomCard.WARRIOR] = 1
    with pytest.raises(actions.WisdomCardNotPlayable):
        actions.play_wisdom_card(
            game, game.active_player, card=entities.WisdomCard.WARRIOR
        )


def test_play_wisdom_card_moves_card_to_played_cards(
    game: entities.ActiveGame,
) -> None:
    player = game.players[game.active_player]
    player.cards[entities.WisdomCard.WARRIOR] = 1

    actions.play_wisdom_card(game, game.active_player, card=entities.WisdomCard.WARRIOR)

    assert player.cards[entities.WisdomCard.WARRIOR] == 0
    assert player.played_cards[entities.WisdomCard.WARRIOR] == 1


def test_can_play_wisdom_card_bought_on_a_previous_turn(
    game: entities.ActiveGame,
) -> None:
    player = game.players[game.active_player]
    player.cards[entities.WisdomCard.WARRIOR] = 1
    player.cards_bought_this_turn[entities.WisdomCard.WARRIOR] = 1
    player.cards_bought_this_turn.clear()

    actions.play_wisdom_card(game, game.active_player, card=entities.WisdomCard.WARRIOR)

    assert player.cards[entities.WisdomCard.WARRIOR] == 0
    assert player.played_cards[entities.WisdomCard.WARRIOR] == 1
