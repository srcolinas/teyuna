from __future__ import annotations

import abc
import dataclasses
import uuid
from enum import Enum
from typing import Generic, TypeVar

from .... import player
from ... import entities

TRun = TypeVar("TRun")
TExit = TypeVar("TExit")
TEnter = TypeVar("TEnter")


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


@dataclasses.dataclass(frozen=True, slots=True)
class BuyWisdomCardAction: ...


PlayerAction = (
    BuildTerraceAction
    | BuildGreatTerraceAction
    | BuildPathAction
    | ProposeTradeToPlayerInTurnAction
    | AcceptTradeProposalAction
    | TradeWithSupplyAction
    | AddInitialBuildingsAction
    | AdvancePhaseAction
    | BuyWisdomCardAction
)


@dataclasses.dataclass
class PlayerRequest:
    by: player.Nickname
    action: PlayerAction


class GamePhaseName(str, Enum):
    FIRST_PLACEMENT = "first placement"
    SECOND_PLACEMENT = "second placement"
    PRE_DICE_ROLL = "pre-dice roll"
    DICE_ROLL = "dice roll"
    PRODUCTION = "production"
    CONQUEST = "conquest"
    TRADE_AND_BUILD = "trade and build"


@dataclasses.dataclass(frozen=True, slots=True)
class RunOutcome(Generic[TRun]):
    finished: bool
    value: TRun


@dataclasses.dataclass(frozen=True, slots=True)
class ExitOutcome(Generic[TExit]):
    next: GamePhaseName
    value: TExit


@dataclasses.dataclass(frozen=True, slots=True)
class EnterOutcome(Generic[TEnter]):
    value: TEnter


class GamePhaseNode(abc.ABC, Generic[TRun, TExit, TEnter]):
    @abc.abstractmethod
    def run(
        self, game: entities.ActiveGame, request: PlayerRequest
    ) -> RunOutcome[TRun]:
        """Handle a player request.

        Returns whether the phase is finished (manager should advance) and an
        optional phase-specific value to report to callers.
        """

    @abc.abstractmethod
    def on_exit(self, game: entities.ActiveGame) -> ExitOutcome[TExit]:
        """Return the next phase, optional report value, and any side effects."""

    @abc.abstractmethod
    def on_enter(self, game: entities.ActiveGame) -> EnterOutcome[TEnter]:
        """Perform side effects when the phase is about to become active."""
