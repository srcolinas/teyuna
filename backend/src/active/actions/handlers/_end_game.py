from ... import entities
from .. import _registry, _results


def handle_end_game(
    game: entities.ActiveGame, action: _registry.PlayerAction
) -> _registry.ActionExecutionResult:
    return _results.ok(_registry.GamePhaseName.END_GAME)
