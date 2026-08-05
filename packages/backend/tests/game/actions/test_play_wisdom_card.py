import random
from enum import Enum

import pytest

from src.game import actions, entities
import teyuna_core


@pytest.mark.parametrize(
    "card",
    [
        teyuna_core.WisdomCard.WARRIOR,
        teyuna_core.WisdomCard.WISDOM_OF_MAMO,
        teyuna_core.WisdomCard.BLESSING_OF_ALUNA,
        teyuna_core.WisdomCard.PATHFINDER,
        teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS,
    ],
)
def test_raises_when_player_does_not_have_card(
    game: entities.Game,
    card: teyuna_core.WisdomCard,
) -> None:
    player = game.active_player
    action = teyuna_core.PlayWisdomCardAction(card=card)
    result = actions.handle_play_wisdom_card(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action
    assert result.error == f"Player {player} does not have card {card.value}"
    assert result.card is None


def test_raises_when_player_not_in_turn(game: entities.Game) -> None:
    game.players[game.active_player].cards[teyuna_core.WisdomCard.WARRIOR] = 1
    other = game.turn_order[1]

    action = teyuna_core.PlayWisdomCardAction(
        card=teyuna_core.WisdomCard.WARRIOR,
    )
    result = actions.handle_play_wisdom_card(
        game,
        actions.ExecutionContext(by=other, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action
    assert result.error == f"Player {other} is not in turn"
    assert result.card is None


def test_raises_when_card_cannot_be_played(
    game: entities.Game,
) -> None:
    player = game.active_player

    class _UnplayableCard(str, Enum):
        UNKNOWN = "unknown card"

    unknown_card = _UnplayableCard.UNKNOWN
    game.players[player].cards[unknown_card] = 1  # type: ignore[index]

    action = teyuna_core.PlayWisdomCardAction.model_construct(card=unknown_card)
    result = actions.handle_play_wisdom_card(
        game,
        actions.ExecutionContext(
            by=player,
            due_to_timeout=False,
            rng=random.Random(0),
        ),
        action,
    )
    assert result.action == action
    assert (
        result.error
        == "Card 'unknown card' cannot be played during the dice roll phase."
    )
    assert result.card is None


@pytest.mark.parametrize(
    ("card", "expected_phase"),
    [
        (
            teyuna_core.WisdomCard.WARRIOR,
            teyuna_core.GamePhaseName.DICE_PLAY_WARRIOR,
        ),
        (
            teyuna_core.WisdomCard.WISDOM_OF_MAMO,
            teyuna_core.GamePhaseName.DICE_PLAY_MAMO,
        ),
        (
            teyuna_core.WisdomCard.BLESSING_OF_ALUNA,
            teyuna_core.GamePhaseName.DICE_PLAY_BLESSED,
        ),
        (
            teyuna_core.WisdomCard.PATHFINDER,
            teyuna_core.GamePhaseName.DICE_PLAY_PATHFINDER,
        ),
        (
            teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS,
            teyuna_core.GamePhaseName.DICE_ROLL,
        ),
    ],
)
def test_uses_card_and_transitions_to_expected_dice_phase(
    game: entities.Game,
    card: teyuna_core.WisdomCard,
    expected_phase: teyuna_core.GamePhaseName,
) -> None:
    player = game.active_player
    game.players[player].cards[card] = 1

    action = teyuna_core.PlayWisdomCardAction(card=card)
    result = actions.handle_play_wisdom_card(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is expected_phase
    assert result.card is card
    assert game.players[player].cards[card] == 0
    assert game.players[player].played_cards[card] == 1


def test_playing_warrior_below_min_leaves_biggest_army_unchanged(
    game: entities.Game,
) -> None:
    player = game.active_player
    game.players[player].cards[teyuna_core.WisdomCard.WARRIOR] = 1
    game.players[player].played_cards[teyuna_core.WisdomCard.WARRIOR] = 1

    action = teyuna_core.PlayWisdomCardAction(card=teyuna_core.WisdomCard.WARRIOR)
    result = actions.handle_play_wisdom_card(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.DICE_PLAY_WARRIOR
    assert result.card is teyuna_core.WisdomCard.WARRIOR
    assert game.biggest_army == (None, 0)
    assert game.players[player].played_cards[teyuna_core.WisdomCard.WARRIOR] == 2


def test_third_warrior_claims_biggest_army(game: entities.Game) -> None:
    player = game.active_player
    game.players[player].cards[teyuna_core.WisdomCard.WARRIOR] = 1
    game.players[player].played_cards[teyuna_core.WisdomCard.WARRIOR] = 2

    action = teyuna_core.PlayWisdomCardAction(card=teyuna_core.WisdomCard.WARRIOR)
    result = actions.handle_play_wisdom_card(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.DICE_PLAY_WARRIOR
    assert result.card is teyuna_core.WisdomCard.WARRIOR
    assert game.biggest_army == (player, 3)


def test_matching_stored_count_does_not_steal_biggest_army(
    game: entities.Game,
) -> None:
    player = game.active_player
    holder = game.turn_order[1]
    game.biggest_army = (holder, 3)
    game.players[player].cards[teyuna_core.WisdomCard.WARRIOR] = 1
    game.players[player].played_cards[teyuna_core.WisdomCard.WARRIOR] = 2

    action = teyuna_core.PlayWisdomCardAction(card=teyuna_core.WisdomCard.WARRIOR)
    result = actions.handle_play_wisdom_card(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.DICE_PLAY_WARRIOR
    assert result.card is teyuna_core.WisdomCard.WARRIOR
    assert game.biggest_army == (holder, 3)
    assert game.players[player].played_cards[teyuna_core.WisdomCard.WARRIOR] == 3


def test_more_warriors_than_stored_steals_biggest_army(
    game: entities.Game,
) -> None:
    player = game.active_player
    holder = game.turn_order[1]
    game.biggest_army = (holder, 3)
    game.players[player].cards[teyuna_core.WisdomCard.WARRIOR] = 1
    game.players[player].played_cards[teyuna_core.WisdomCard.WARRIOR] = 3

    action = teyuna_core.PlayWisdomCardAction(card=teyuna_core.WisdomCard.WARRIOR)
    result = actions.handle_play_wisdom_card(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.DICE_PLAY_WARRIOR
    assert result.card is teyuna_core.WisdomCard.WARRIOR
    assert game.biggest_army == (player, 4)


def test_holder_playing_another_warrior_bumps_stored_count(
    game: entities.Game,
) -> None:
    player = game.active_player
    game.biggest_army = (player, 3)
    game.players[player].cards[teyuna_core.WisdomCard.WARRIOR] = 1
    game.players[player].played_cards[teyuna_core.WisdomCard.WARRIOR] = 3

    action = teyuna_core.PlayWisdomCardAction(card=teyuna_core.WisdomCard.WARRIOR)
    result = actions.handle_play_wisdom_card(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.DICE_PLAY_WARRIOR
    assert result.card is teyuna_core.WisdomCard.WARRIOR
    assert game.biggest_army == (player, 4)


def test_playing_legacy_to_ten_vp_ends_game(game: entities.Game) -> None:
    player = game.active_player
    game.players[player].cards[teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS] = 1
    game.players[player].played_cards[teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS] = 9

    action = teyuna_core.PlayWisdomCardAction(
        card=teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS
    )
    result = actions.handle_play_wisdom_card(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.END_GAME
    assert result.card is teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS
    assert (
        game.players[player].played_cards[teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS]
        == 10
    )


def test_playing_legacy_below_ten_vp_stays_in_dice_roll(
    game: entities.Game,
) -> None:
    player = game.active_player
    game.players[player].cards[teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS] = 1
    game.players[player].played_cards[teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS] = 8

    action = teyuna_core.PlayWisdomCardAction(
        card=teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS
    )
    result = actions.handle_play_wisdom_card(
        game,
        actions.ExecutionContext(by=player, due_to_timeout=False, rng=random.Random(0)),
        action,
    )
    assert result.action == action

    assert result.error is None
    assert result.next_phase is teyuna_core.GamePhaseName.DICE_ROLL
    assert result.card is teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS
