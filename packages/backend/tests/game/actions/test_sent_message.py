from src.game import actions, entities
import teyuna_core


def test_sends_message(game: entities.Game) -> None:
    player = game.active_player
    action = teyuna_core.SentMessageAction(by=player, text="hello")
    result = actions.handle_sent_message(game, action)

    assert result.action == action
    assert result.error is None
    assert result.previous_phase is game.phase
    assert result.next_phase is game.phase


def test_rejects_empty_text(game: entities.Game) -> None:
    player = game.active_player
    action = teyuna_core.SentMessageAction(by=player, text="   ")
    result = actions.handle_sent_message(game, action)

    assert result.action == action
    assert result.error == "message text must not be empty"
    assert result.next_phase is game.phase


def test_rejects_too_long_text(game: entities.Game) -> None:
    player = game.active_player
    action = teyuna_core.SentMessageAction(by=player, text="x" * 501)
    result = actions.handle_sent_message(game, action)

    assert result.action == action
    assert result.error == "message text must be at most 500 characters"
    assert result.next_phase is game.phase
