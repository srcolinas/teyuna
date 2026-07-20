from enum import Enum

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
    result = actions.handle_play_wisdom_card(
        game,
        actions.PlayWisdomCardAction(by=game.active_player, card=card),
    )
    assert result.succeeded is False
    assert result.error is not None
    assert type(result.error) is actions.PlayerDoesNotHaveCardError


def test_raises_when_player_not_in_turn(game: entities.ActiveGame) -> None:
    game.players[game.active_player].cards[entities.WisdomCard.WARRIOR] = 1

    result = actions.handle_play_wisdom_card(
        game,
        actions.PlayWisdomCardAction(
            by=game.turn_order[1],
            card=entities.WisdomCard.WARRIOR,
        ),
    )
    assert result.succeeded is False
    assert result.error is not None
    assert type(result.error) is actions.PlayerNotInTurnError


def test_raises_when_card_cannot_be_played(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player

    class _UnplayableCard(str, Enum):
        UNKNOWN = "unknown card"

    unknown_card = _UnplayableCard.UNKNOWN
    game.players[player].cards[unknown_card] = 1  # type: ignore[index]

    result = actions.handle_play_wisdom_card(
        game,
        actions.PlayWisdomCardAction(by=player, card=unknown_card),  # type: ignore[arg-type]
    )
    assert result.succeeded is False
    assert result.error is not None
    assert type(result.error) is actions.ActionNotAllowedError


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
def test_uses_card_and_transitions_to_expected_dice_phase(
    game: entities.ActiveGame,
    card: entities.WisdomCard,
    expected_phase: actions.GamePhaseName,
) -> None:
    player = game.active_player
    game.players[player].cards[card] = 1

    result = actions.handle_play_wisdom_card(
        game,
        actions.PlayWisdomCardAction(by=player, card=card),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is expected_phase
    assert game.players[player].cards[card] == 0
    assert game.players[player].played_cards[card] == 1


def test_playing_warrior_below_min_leaves_biggest_army_unchanged(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    game.players[player].cards[entities.WisdomCard.WARRIOR] = 1
    game.players[player].played_cards[entities.WisdomCard.WARRIOR] = 1

    actions.handle_play_wisdom_card(
        game,
        actions.PlayWisdomCardAction(by=player, card=entities.WisdomCard.WARRIOR),
    )

    assert game.biggest_army == (None, 0)
    assert game.players[player].played_cards[entities.WisdomCard.WARRIOR] == 2


def test_third_warrior_claims_biggest_army(game: entities.ActiveGame) -> None:
    player = game.active_player
    game.players[player].cards[entities.WisdomCard.WARRIOR] = 1
    game.players[player].played_cards[entities.WisdomCard.WARRIOR] = 2

    actions.handle_play_wisdom_card(
        game,
        actions.PlayWisdomCardAction(by=player, card=entities.WisdomCard.WARRIOR),
    )

    assert game.biggest_army == (player, 3)


def test_matching_stored_count_does_not_steal_biggest_army(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    holder = game.turn_order[1]
    game.biggest_army = (holder, 3)
    game.players[player].cards[entities.WisdomCard.WARRIOR] = 1
    game.players[player].played_cards[entities.WisdomCard.WARRIOR] = 2

    actions.handle_play_wisdom_card(
        game,
        actions.PlayWisdomCardAction(by=player, card=entities.WisdomCard.WARRIOR),
    )

    assert game.biggest_army == (holder, 3)
    assert game.players[player].played_cards[entities.WisdomCard.WARRIOR] == 3


def test_more_warriors_than_stored_steals_biggest_army(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    holder = game.turn_order[1]
    game.biggest_army = (holder, 3)
    game.players[player].cards[entities.WisdomCard.WARRIOR] = 1
    game.players[player].played_cards[entities.WisdomCard.WARRIOR] = 3

    actions.handle_play_wisdom_card(
        game,
        actions.PlayWisdomCardAction(by=player, card=entities.WisdomCard.WARRIOR),
    )

    assert game.biggest_army == (player, 4)


def test_holder_playing_another_warrior_bumps_stored_count(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    game.biggest_army = (player, 3)
    game.players[player].cards[entities.WisdomCard.WARRIOR] = 1
    game.players[player].played_cards[entities.WisdomCard.WARRIOR] = 3

    actions.handle_play_wisdom_card(
        game,
        actions.PlayWisdomCardAction(by=player, card=entities.WisdomCard.WARRIOR),
    )

    assert game.biggest_army == (player, 4)


def test_playing_legacy_to_ten_vp_ends_game(game: entities.ActiveGame) -> None:
    player = game.active_player
    game.players[player].cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS] = 1
    game.players[player].played_cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS] = 9

    result = actions.handle_play_wisdom_card(
        game,
        actions.PlayWisdomCardAction(
            by=player, card=entities.WisdomCard.LEGACY_OF_THE_ELDERS
        ),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.END_GAME
    assert (
        game.players[player].played_cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS]
        == 10
    )


def test_playing_legacy_below_ten_vp_stays_in_dice_roll(
    game: entities.ActiveGame,
) -> None:
    player = game.active_player
    game.players[player].cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS] = 1
    game.players[player].played_cards[entities.WisdomCard.LEGACY_OF_THE_ELDERS] = 8

    result = actions.handle_play_wisdom_card(
        game,
        actions.PlayWisdomCardAction(
            by=player, card=entities.WisdomCard.LEGACY_OF_THE_ELDERS
        ),
    )

    assert result.succeeded is True
    assert result.error is None
    assert result.phase is actions.GamePhaseName.DICE_ROLL
