from __future__ import annotations

from ... import entities
from .. import actions
from . import _core, _errors
from ._trade_and_build import BiggestArmyResult, GameWonResult


class PreDiceRollPhase(
    _core.GamePhaseNode[
        entities.WisdomCard | BiggestArmyResult | GameWonResult | None,
        None,
        None,
    ]
):
    def run(
        self, game: entities.ActiveGame, request: _core.PlayerRequest
    ) -> _core.RunOutcome[
        entities.WisdomCard | BiggestArmyResult | GameWonResult | None
    ]:
        if game.active_player != request.by:
            raise _errors.PlayerNotInTurnError(f"Player {request.by} is not in turn")
        match request.action:
            case _core.PlayWisdomCardAction(card=card):
                actions.play_wisdom_card(game, request.by, card=card)
                if card is entities.WisdomCard.WARRIOR:
                    army = actions.update_biggest_army(game, request.by)
                    if actions.declare_winner_if_eligible(game, request.by):
                        return _core.RunOutcome(
                            finished=True,
                            value=GameWonResult(winner=request.by),
                        )
                    game.warrior_return_phase = _core.GamePhaseName.PRE_DICE_ROLL.value
                    if army is not None:
                        owner, count = army
                        return _core.RunOutcome(
                            finished=True,
                            value=BiggestArmyResult(owner=owner, count=count),
                        )
                    return _core.RunOutcome(finished=True, value=card)
                if card is entities.WisdomCard.BLESSING_OF_ALUNA:
                    game.blessing_return_phase = _core.GamePhaseName.PRE_DICE_ROLL.value
                    return _core.RunOutcome(finished=True, value=card)
                if card is entities.WisdomCard.WINDOM_OF_MAMO:
                    game.mamo_return_phase = _core.GamePhaseName.PRE_DICE_ROLL.value
                    return _core.RunOutcome(finished=True, value=card)
                if card is entities.WisdomCard.PATHFINDER:
                    game.pathfinder_return_phase = (
                        _core.GamePhaseName.PRE_DICE_ROLL.value
                    )
                    return _core.RunOutcome(finished=True, value=card)
                if card is entities.WisdomCard.LEGACY_OF_THE_ELDERS:
                    if actions.declare_winner_if_eligible(game, request.by):
                        return _core.RunOutcome(
                            finished=True,
                            value=GameWonResult(winner=request.by),
                        )
                    game.legacy_return_phase = _core.GamePhaseName.PRE_DICE_ROLL.value
                    return _core.RunOutcome(finished=True, value=card)
                return _core.RunOutcome(finished=False, value=card)
            case _core.AdvancePhaseAction():
                return _core.RunOutcome(finished=True, value=None)
            case _:
                raise _errors.InvalidActionError(f"Unknown action: {request.action}")

    def on_exit(self, game: entities.ActiveGame) -> _core.ExitOutcome[None]:
        if game.winner is not None:
            _clear_interrupt_return_phases(game)
            return _core.ExitOutcome(next=_core.GamePhaseName.END, value=None)
        if game.warrior_return_phase is not None:
            return _core.ExitOutcome(
                next=_core.GamePhaseName.WARRIOR_MOVE_CONQUISTATOR, value=None
            )
        if game.blessing_return_phase is not None:
            return _core.ExitOutcome(
                next=_core.GamePhaseName.BLESSING_OF_ALUNA, value=None
            )
        if game.mamo_return_phase is not None:
            return _core.ExitOutcome(
                next=_core.GamePhaseName.WISDOM_OF_THE_MAMO, value=None
            )
        if game.pathfinder_return_phase is not None:
            return _core.ExitOutcome(next=_core.GamePhaseName.PATHFINDER, value=None)
        if game.legacy_return_phase is not None:
            return _core.ExitOutcome(
                next=_core.GamePhaseName.LEGACY_OF_THE_ELDERS, value=None
            )
        return _core.ExitOutcome(next=_core.GamePhaseName.DICE_ROLL, value=None)

    def on_enter(self, game: entities.ActiveGame) -> _core.EnterOutcome[None]:
        game.players[game.active_player].cards_bought_this_turn.clear()
        return _core.EnterOutcome(value=None)


def _clear_interrupt_return_phases(game: entities.ActiveGame) -> None:
    game.warrior_return_phase = None
    game.blessing_return_phase = None
    game.mamo_return_phase = None
    game.pathfinder_return_phase = None
    game.legacy_return_phase = None
