from .... import player
from ... import entities
from . import _errors


def play_wisdom_card(
    game: entities.ActiveGame,
    to: player.Nickname,
    /,
    *,
    card: entities.WisdomCard,
) -> None:
    player_state = game.players[to]
    playable = player_state.cards[card] - player_state.cards_bought_this_turn[card]
    if playable < 1:
        raise _errors.WisdomCardNotPlayable

    player_state.cards[card] -= 1
    player_state.played_cards[card] += 1
