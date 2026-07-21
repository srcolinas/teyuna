from ... import entities
from .. import _registry


class EndGameResult(_registry.ActionExecutionResult):
    pass


def handle_end_game(
    game: entities.Game, action: _registry.PlayerAction
) -> EndGameResult:
    previous_phase = game.phase
    game.phase = entities.GamePhaseName.END_GAME
    return EndGameResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
    )


def handle_lobby_timeout(
    game: entities.Game, action: _registry.PlayerAction
) -> EndGameResult:
    previous_phase = game.phase
    game.phase = entities.GamePhaseName.END_GAME
    return EndGameResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
    )
