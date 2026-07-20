from ... import entities
from .. import _registry


class EndGameResult(_registry.ActionExecutionResult):
    pass


def handle_end_game(
    game: entities.ActiveGame, action: _registry.PlayerAction
) -> EndGameResult:
    return EndGameResult(
        succeeded=True,
        phase=_registry.GamePhaseName.END_GAME,
    )
