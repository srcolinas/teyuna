from ... import entities
from .. import _registry


class EndGameResult(_registry.ActionExecutionResult):
    pass


def handle_end_game(
    game: entities.Game, action: _registry.PlayerAction
) -> EndGameResult:
    game.phase = entities.GamePhaseName.END_GAME
    return EndGameResult(
        succeeded=True,
        phase=game.phase,
        by=action.by,
        due_to_timeout=action.due_to_timeout,
    )


def handle_lobby_timeout(
    game: entities.Game, action: _registry.PlayerAction
) -> EndGameResult:
    game.phase = entities.GamePhaseName.END_GAME
    return EndGameResult(
        succeeded=True,
        phase=game.phase,
        by=action.by,
        due_to_timeout=action.due_to_timeout,
    )
