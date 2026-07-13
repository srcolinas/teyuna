from __future__ import annotations

import abc
import dataclasses
import uuid
from enum import Enum

from .... import player
from ... import entities


@dataclasses.dataclass(frozen=True, slots=True)
class AddInitialBuildingsAction:
    terrace: entities.Coordinate
    path: entities.Coordinate


@dataclasses.dataclass(frozen=True, slots=True)
class BuildTerraceAction:
    coordinate: entities.Coordinate


@dataclasses.dataclass(frozen=True, slots=True)
class BuildGreatTerraceAction:
    coordinate: entities.Coordinate


@dataclasses.dataclass(frozen=True, slots=True)
class BuildPathAction:
    coordinate: entities.Coordinate


@dataclasses.dataclass(frozen=True, slots=True)
class ProposeTradeToPlayerInTurnAction:
    offer: entities.ResourceCount
    request: entities.ResourceCount


@dataclasses.dataclass(frozen=True, slots=True)
class AcceptTradeProposalAction:
    id: uuid.UUID


@dataclasses.dataclass(frozen=True, slots=True)
class TradeWithSupplyAction:
    offers: entities.ResourceCard
    requests: entities.ResourceCard


@dataclasses.dataclass(frozen=True, slots=True)
class AdvancePhaseAction: ...


PlayerAction = (
    BuildTerraceAction
    | BuildGreatTerraceAction
    | BuildPathAction
    | ProposeTradeToPlayerInTurnAction
    | AcceptTradeProposalAction
    | TradeWithSupplyAction
    | AddInitialBuildingsAction
    | AdvancePhaseAction
)


@dataclasses.dataclass
class PlayerRequest:
    by: player.Nickname
    action: PlayerAction


class GamePhaseName(str, Enum):
    FIRST_PLACEMENT = "first placement"
    SECOND_PLACEMENT = "second placement"
    PRE_PRODUCTION = "pre-production"
    DICE_ROLL = "dice roll"
    PRODUCTION = "production"
    CONQUEST = "conquest"
    TRADE_AND_BUILD = "trade and build"


class GamePhaseNode(abc.ABC):
    @abc.abstractmethod
    def run(self, game: entities.ActiveGame, request: PlayerRequest) -> bool:
        """Handle a player request.

        Returns True if the phase is finished and the manager should use a different
        node implementation. False if the phase is not finished.
        """

    @abc.abstractmethod
    def on_exit(self, game: entities.ActiveGame) -> GamePhaseName:
        """Return the next phase to run and perform any necessary side effects."""

    def on_enter(self, game: entities.ActiveGame) -> None:
        """
        Perform any necessary side effects when the phase is about to
        become active.
        """
