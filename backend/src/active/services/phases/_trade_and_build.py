from __future__ import annotations

import dataclasses

from .... import player
from ... import entities
from .. import actions
from . import _core, _errors


@dataclasses.dataclass(frozen=True, slots=True)
class LongestRoadResult:
    owner: player.Nickname | None
    length: int


@dataclasses.dataclass(frozen=True, slots=True)
class BiggestArmyResult:
    owner: player.Nickname | None
    count: int


@dataclasses.dataclass(frozen=True, slots=True)
class GameWonResult:
    winner: player.Nickname


class TradeAndBuildPhase(
    _core.GamePhaseNode[
        entities.TradeProposal
        | LongestRoadResult
        | BiggestArmyResult
        | GameWonResult
        | entities.WisdomCard
        | None,
        None,
        None,
    ]
):
    def run(
        self, game: entities.ActiveGame, request: _core.PlayerRequest
    ) -> _core.RunOutcome[
        entities.TradeProposal
        | LongestRoadResult
        | BiggestArmyResult
        | GameWonResult
        | entities.WisdomCard
        | None
    ]:
        match request.action:
            case _core.ProposeTradeAction(offer=offer, request=trade_request, to=to):
                if request.by != game.active_player and to != (game.active_player,):
                    raise _errors.InvalidActionError(
                        f"Player {request.by} can only propose trades to the active player"
                    )
                actions.propose_trade(
                    game, by=request.by, offer=offer, request=trade_request, to=to
                )
                return _core.RunOutcome(finished=False, value=None)
            case _core.TradeWithSupplyAction(offers=offers, requests=requests):
                _require_active_player(game, request.by)
                actions.trade(game, by=request.by, offers=offers, requests=requests)
                return _core.RunOutcome(finished=False, value=None)
            case _core.AcceptTradeProposalAction(id=proposal_id):
                proposal = game.trade_proposals.get(proposal_id)
                if proposal is not None and request.by not in proposal.to:
                    raise _errors.InvalidActionError(
                        f"Player {request.by} cannot accept this trade proposal"
                    )
                actions.accept_trade(game, by=request.by, id=proposal_id)
                return _core.RunOutcome(finished=False, value=proposal)
            case _core.BuyAction(item=item, coordinate=coordinate):
                _require_active_player(game, request.by)
                value: LongestRoadResult | None = None
                match item:
                    case _core.Buyable.TERRACE:
                        actions.build_terrace(
                            game,
                            request.by,
                            q=coordinate.q,
                            r=coordinate.r,
                            direction=coordinate.d,
                        )
                        if game.longest_road[0] is not None:
                            vertex = entities.canonical_vertex(
                                coordinate.q, coordinate.r, coordinate.d
                            )
                            updated = actions.recompute_longest_road(
                                game, request.by, vertex=vertex
                            )
                            if updated is not None:
                                owner, length = updated
                                value = LongestRoadResult(owner=owner, length=length)
                    case _core.Buyable.GREAT_TERRACE:
                        actions.build_great_terrace(
                            game,
                            request.by,
                            q=coordinate.q,
                            r=coordinate.r,
                            direction=coordinate.d,
                        )
                    case _core.Buyable.PATH:
                        edge = entities.canonical_edge(
                            coordinate.q, coordinate.r, coordinate.d
                        )
                        actions.build_path(
                            game,
                            request.by,
                            q=coordinate.q,
                            r=coordinate.r,
                            direction=coordinate.d,
                        )
                        awarded = actions.update_longest_road(
                            game, request.by, edge=edge
                        )
                        if awarded is not None:
                            owner, length = awarded
                            value = LongestRoadResult(owner=owner, length=length)
                if actions.declare_winner_if_eligible(game, request.by):
                    return _core.RunOutcome(
                        finished=True,
                        value=GameWonResult(winner=request.by),
                    )
                return _core.RunOutcome(finished=False, value=value)
            case _core.BuyWisdomCardAction():
                _require_active_player(game, request.by)
                actions.buy_wisdom_card(game, request.by)
                return _core.RunOutcome(finished=False, value=None)
            case _core.PlayWisdomCardAction(card=card):
                _require_active_player(game, request.by)
                actions.play_wisdom_card(game, request.by, card=card)
                if card is entities.WisdomCard.WARRIOR:
                    army = actions.update_biggest_army(game, request.by)
                    if actions.declare_winner_if_eligible(game, request.by):
                        return _core.RunOutcome(
                            finished=True,
                            value=GameWonResult(winner=request.by),
                        )
                    game.warrior_return_phase = (
                        _core.GamePhaseName.TRADE_AND_BUILD.value
                    )
                    if army is not None:
                        owner, count = army
                        return _core.RunOutcome(
                            finished=True,
                            value=BiggestArmyResult(owner=owner, count=count),
                        )
                    return _core.RunOutcome(finished=True, value=card)
                if card is entities.WisdomCard.BLESSING_OF_ALUNA:
                    game.blessing_return_phase = (
                        _core.GamePhaseName.TRADE_AND_BUILD.value
                    )
                    return _core.RunOutcome(finished=True, value=card)
                if card is entities.WisdomCard.WINDOM_OF_MAMO:
                    game.mamo_return_phase = _core.GamePhaseName.TRADE_AND_BUILD.value
                    return _core.RunOutcome(finished=True, value=card)
                if card is entities.WisdomCard.PATHFINDER:
                    game.pathfinder_return_phase = (
                        _core.GamePhaseName.TRADE_AND_BUILD.value
                    )
                    return _core.RunOutcome(finished=True, value=card)
                if card is entities.WisdomCard.LEGACY_OF_THE_ELDERS:
                    if actions.declare_winner_if_eligible(game, request.by):
                        return _core.RunOutcome(
                            finished=True,
                            value=GameWonResult(winner=request.by),
                        )
                    game.legacy_return_phase = _core.GamePhaseName.TRADE_AND_BUILD.value
                    return _core.RunOutcome(finished=True, value=card)
                return _core.RunOutcome(finished=False, value=card)
            case _core.AdvancePhaseAction():
                _require_active_player(game, request.by)
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
        game.trade_proposals.clear()
        game.player_idx = (game.player_idx + 1) % len(game.turn_order)
        return _core.ExitOutcome(next=_core.GamePhaseName.PRE_DICE_ROLL, value=None)

    def on_enter(self, game: entities.ActiveGame) -> _core.EnterOutcome[None]:
        game.trade_proposals.clear()
        return _core.EnterOutcome(value=None)


def _require_active_player(game: entities.ActiveGame, by: player.Nickname) -> None:
    if game.active_player != by:
        raise _errors.PlayerNotInTurnError(f"Player {by} is not in turn")


def _clear_interrupt_return_phases(game: entities.ActiveGame) -> None:
    game.warrior_return_phase = None
    game.blessing_return_phase = None
    game.mamo_return_phase = None
    game.pathfinder_return_phase = None
    game.legacy_return_phase = None
