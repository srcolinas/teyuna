from ... import entities
from .. import actions
from . import _core, _errors


class ProductionPhase(_core.GamePhaseNode[None, None, None]):
    def run(
        self, game: entities.ActiveGame, request: _core.PlayerRequest
    ) -> _core.RunOutcome[None]:
        if game.active_player != request.by:
            raise _errors.PlayerNotInTurnError(f"Player {request.by} is not in turn")
        match request.action:
            case _core.AdvancePhaseAction():
                return _core.RunOutcome(finished=True, value=None)
            case _:
                raise _errors.InvalidActionError(f"Unknown action: {request.action}")

    def on_exit(self, game: entities.ActiveGame) -> _core.ExitOutcome[None]:
        return _core.ExitOutcome(next=_core.GamePhaseName.TRADE_AND_BUILD, value=None)

    def on_enter(self, game: entities.ActiveGame) -> _core.EnterOutcome[None]:
        actions.produce_resources(game, roll=game.last_dice_roll)
        return _core.EnterOutcome(value=None)
