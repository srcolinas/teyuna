import teyuna_core

from ... import entities

_MAX_MESSAGE_LENGTH = 500


def handle_sent_message(
    game: entities.Game, action: teyuna_core.SentMessageAction
) -> teyuna_core.SentMessageResult:
    previous_phase = game.phase
    text = action.text.strip()
    if not text:
        return teyuna_core.SentMessageResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error="message text must not be empty",
        )
    if len(text) > _MAX_MESSAGE_LENGTH:
        return teyuna_core.SentMessageResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"message text must be at most {_MAX_MESSAGE_LENGTH} characters",
        )
    return teyuna_core.SentMessageResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
    )
