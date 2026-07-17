import pytest

from src.active import actions, entities


@pytest.mark.parametrize(
    "card",
    [
        entities.WisdomCard.WARRIOR,
        entities.WisdomCard.WINDOM_OF_MAMO,
        entities.WisdomCard.BLESSING_OF_ALUNA,
        entities.WisdomCard.PATHFINDER,
        entities.WisdomCard.LEGACY_OF_THE_ELDERS,
    ],
)
def test_raises_when_player_does_not_have_card(
    game: entities.ActiveGame,
    card: entities.WisdomCard,
) -> None:
    with pytest.raises(actions.PlayerDoesNotHaveCardError):
        actions.handle_play_wisdom_card(
            game,
            actions.PlayWisdomCardAction(by=game.active_player, card=card),
        )


def test_raises_when_player_not_in_turn(game: entities.ActiveGame) -> None:
    game.players[game.active_player].cards[entities.WisdomCard.WARRIOR] = 1

    with pytest.raises(actions.PlayerNotInTurnError):
        actions.handle_play_wisdom_card(
            game,
            actions.PlayWisdomCardAction(
                by=game.turn_order[1],
                card=entities.WisdomCard.WARRIOR,
            ),
        )


@pytest.mark.parametrize(
    ("card", "expected_phase"),
    [
        (entities.WisdomCard.WARRIOR, actions.GamePhaseName.DICE_PLAY_WARRIOR),
        (entities.WisdomCard.WINDOM_OF_MAMO, actions.GamePhaseName.DICE_PLAY_MAMO),
        (
            entities.WisdomCard.BLESSING_OF_ALUNA,
            actions.GamePhaseName.DICE_PLAY_BLESSED,
        ),
        (
            entities.WisdomCard.PATHFINDER,
            actions.GamePhaseName.DICE_PLAY_PATHFINDER,
        ),
        (entities.WisdomCard.LEGACY_OF_THE_ELDERS, actions.GamePhaseName.DICE_ROLL),
    ],
)
def test_uses_card_and_transitions_to_expected_phase(
    game: entities.ActiveGame,
    card: entities.WisdomCard,
    expected_phase: actions.GamePhaseName,
) -> None:
    player = game.active_player
    game.players[player].cards[card] = 1

    phase = actions.handle_play_wisdom_card(
        game,
        actions.PlayWisdomCardAction(by=player, card=card),
    )

    assert phase is expected_phase
    assert game.players[player].cards[card] == 0
    assert game.players[player].played_cards[card] == 1
