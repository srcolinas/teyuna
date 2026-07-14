from ... import entities
from .. import actions
from . import _core, _errors


class FirstPlacementPhase(_core.GamePhaseNode[None, None, None]):
    def run(
        self, game: entities.ActiveGame, request: _core.PlayerRequest
    ) -> _core.RunOutcome[None]:
        if game.active_player != request.by:
            raise _errors.PlayerNotInTurnError(f"Player {request.by} is not in turn")
        match request.action:
            case _core.AddInitialBuildingsAction(terrace=terrace, path=path):
                actions.add_free_terrace(
                    game, request.by, q=terrace.q, r=terrace.r, direction=terrace.d
                )
                actions.add_free_path(
                    game, request.by, q=path.q, r=path.r, direction=path.d
                )
            case _:
                raise _errors.InvalidActionError(f"Unknown action: {request.action}")
        game.player_idx += 1
        if game.player_idx == len(game.players):
            return _core.RunOutcome(finished=True, value=None)
        return _core.RunOutcome(finished=False, value=None)

    def on_exit(self, game: entities.ActiveGame) -> _core.ExitOutcome[None]:
        game.player_idx = len(game.players) - 1
        return _core.ExitOutcome(next=_core.GamePhaseName.SECOND_PLACEMENT, value=None)

    def on_enter(self, game: entities.ActiveGame) -> _core.EnterOutcome[None]:
        game.player_idx = 0
        return _core.EnterOutcome(value=None)
