import random
import uuid
from typing import Any

import pydantic

from . import entities, board


class PlayerAction(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True, arbitrary_types_allowed=True)

    by: str
    due_to_timeout: bool = False
    rng_: Any = pydantic.Field(
        default_factory=random.Random,
        exclude=True,
    )


class ActionExecutionResult(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)

    previous_phase: entities.GamePhaseName
    next_phase: entities.GamePhaseName
    action: PlayerAction
    error: str | None = None


class FreePlacementAction(PlayerAction):
    terrace: board.Coordinate | None = None
    path: board.Coordinate | None = None

    @pydantic.model_validator(mode="after")
    def _canonicalize(self) -> "FreePlacementAction":
        if self.terrace is not None:
            object.__setattr__(
                self,
                "terrace",
                board.canonical_vertex(self.terrace.q, self.terrace.r, self.terrace.d),
            )
        if self.path is not None:
            object.__setattr__(
                self,
                "path",
                board.canonical_edge(self.path.q, self.path.r, self.path.d),
            )
        return self


class PlacedBuildingsResult(ActionExecutionResult):
    settlement: board.Coordinate | None = None
    path: board.Coordinate | None = None
    next_player: str = ""


class DiscardResourcesAction(PlayerAction):
    count: dict[entities.ResourceCard, int]


class DiscardedResourcesResult(ActionExecutionResult):
    count: dict[entities.ResourceCard, int] = pydantic.Field(default_factory=dict)


class MoveConquistatorAction(PlayerAction):
    q: int
    r: int
    from_player: str | None = None


class MovedConquistatorResult(ActionExecutionResult):
    q: int = -1
    r: int = -1
    from_player: str | None = None
    stolen: entities.ResourceCard | None = None


class PlayWisdomCardAction(PlayerAction):
    card: entities.WisdomCard


class PlayedWisdomCardResult(ActionExecutionResult):
    card: entities.WisdomCard | None = None


class PlayMamoAction(PlayerAction):
    resource: entities.ResourceCard


class PlayedMamoResult(ActionExecutionResult):
    resource: entities.ResourceCard | None = None


class PlayBlessedAction(PlayerAction):
    resources: tuple[entities.ResourceCard, entities.ResourceCard]


class PlayedBlessedResult(ActionExecutionResult):
    resources: tuple[entities.ResourceCard, entities.ResourceCard] | None = None


class PlayPathfinderAction(PlayerAction):
    paths: tuple[board.Coordinate, ...]

    @pydantic.model_validator(mode="after")
    def _canonicalize(self) -> "PlayPathfinderAction":
        object.__setattr__(
            self,
            "paths",
            tuple(board.canonical_edge(path.q, path.r, path.d) for path in self.paths),
        )
        return self


class PlayedPathfinderResult(ActionExecutionResult):
    paths: tuple[board.Coordinate, ...] = ()


class BuildSettlementAction(PlayerAction):
    item: entities.SettlementType
    coordinate: board.Coordinate

    @pydantic.model_validator(mode="after")
    def _canonicalize(self) -> "BuildSettlementAction":
        object.__setattr__(
            self,
            "coordinate",
            board.canonical_vertex(
                self.coordinate.q, self.coordinate.r, self.coordinate.d
            ),
        )
        return self


class BuiltSettlementResult(ActionExecutionResult):
    item: entities.SettlementType | None = None
    coordinate: board.Coordinate | None = None


class BuildPathAction(PlayerAction):
    coordinate: board.Coordinate

    @pydantic.model_validator(mode="after")
    def _canonicalize(self) -> "BuildPathAction":
        object.__setattr__(
            self,
            "coordinate",
            board.canonical_edge(
                self.coordinate.q, self.coordinate.r, self.coordinate.d
            ),
        )
        return self


class BuiltPathResult(ActionExecutionResult):
    coordinate: board.Coordinate | None = None


class EndedTradeAndBuildResult(ActionExecutionResult):
    next_player: str = ""


class BuyWisdomCardAction(PlayerAction):
    pass


class BoughtWisdomCardResult(ActionExecutionResult):
    card: entities.WisdomCard | None = None


class ProposeTradeAction(PlayerAction):
    offer: dict[entities.ResourceCard, int]
    request: dict[entities.ResourceCard, int]
    to: set[str]


class AcceptTradeAction(PlayerAction):
    id: uuid.UUID


class ProposeTradeResult(ActionExecutionResult):
    proposal_id: uuid.UUID | None = None
    offer: dict[entities.ResourceCard, int] = pydantic.Field(default_factory=dict)
    request: dict[entities.ResourceCard, int] = pydantic.Field(default_factory=dict)
    to: set[str] = pydantic.Field(default_factory=set)


class AcceptedTradeResult(ActionExecutionResult):
    proposal_id: uuid.UUID | None = None
    proposer: str = ""
    acceptor: str = ""
    offer: dict[entities.ResourceCard, int] = pydantic.Field(default_factory=dict)
    request: dict[entities.ResourceCard, int] = pydantic.Field(default_factory=dict)


class TradeWithSupplyAction(PlayerAction):
    offers: entities.ResourceCard
    requests: entities.ResourceCard


class TradedWithSupplyResult(ActionExecutionResult):
    offers: entities.ResourceCard | None = None
    requests: entities.ResourceCard | None = None
    rate: int = -1


class DiceRollResult(ActionExecutionResult):
    die_1: int = -1
    die_2: int = -1
    to_discard: dict[str, int] = pydantic.Field(default_factory=dict)
    produced: dict[str, dict[entities.ResourceCard, int]] = pydantic.Field(
        default_factory=dict
    )


class EndGameResult(ActionExecutionResult):
    pass
