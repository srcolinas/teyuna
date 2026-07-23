import random
import uuid
from typing import Annotated, Any, Literal

import pydantic

from . import entities, board


class PlayerAction(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True, arbitrary_types_allowed=True)

    kind: Literal["advance"] = "advance"
    by: str = ""
    due_to_timeout: bool = False
    rng_: Any = pydantic.Field(
        default_factory=random.Random,
        exclude=True,
    )


class FreePlacementAction(PlayerAction):
    kind: Literal["free_placement"] = "free_placement"  # type: ignore[assignment]
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


class DiscardResourcesAction(PlayerAction):
    kind: Literal["discard_resources"] = "discard_resources"  # type: ignore[assignment]
    count: dict[entities.ResourceCard, int]


class MoveConquistatorAction(PlayerAction):
    kind: Literal["move_conquistator"] = "move_conquistator"  # type: ignore[assignment]
    q: int
    r: int
    from_player: str | None = None


class PlayWisdomCardAction(PlayerAction):
    kind: Literal["play_wisdom_card"] = "play_wisdom_card"  # type: ignore[assignment]
    card: entities.WisdomCard


class PlayMamoAction(PlayerAction):
    kind: Literal["play_mamo"] = "play_mamo"  # type: ignore[assignment]
    resource: entities.ResourceCard


class PlayBlessedAction(PlayerAction):
    kind: Literal["play_blessed"] = "play_blessed"  # type: ignore[assignment]
    resources: tuple[entities.ResourceCard, entities.ResourceCard]


class PlayPathfinderAction(PlayerAction):
    kind: Literal["play_pathfinder"] = "play_pathfinder"  # type: ignore[assignment]
    paths: tuple[board.Coordinate, ...]

    @pydantic.model_validator(mode="after")
    def _canonicalize(self) -> "PlayPathfinderAction":
        object.__setattr__(
            self,
            "paths",
            tuple(board.canonical_edge(path.q, path.r, path.d) for path in self.paths),
        )
        return self


class BuildSettlementAction(PlayerAction):
    kind: Literal["build_settlement"] = "build_settlement"  # type: ignore[assignment]
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


class BuildPathAction(PlayerAction):
    kind: Literal["build_path"] = "build_path"  # type: ignore[assignment]
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


class BuyWisdomCardAction(PlayerAction):
    kind: Literal["buy_wisdom_card"] = "buy_wisdom_card"  # type: ignore[assignment]


class ProposeTradeAction(PlayerAction):
    kind: Literal["propose_trade"] = "propose_trade"  # type: ignore[assignment]
    offer: dict[entities.ResourceCard, int]
    request: dict[entities.ResourceCard, int]
    to: set[str]


class AcceptTradeAction(PlayerAction):
    kind: Literal["accept_trade"] = "accept_trade"  # type: ignore[assignment]
    id: uuid.UUID


class TradeWithSupplyAction(PlayerAction):
    kind: Literal["trade_with_supply"] = "trade_with_supply"  # type: ignore[assignment]
    offers: entities.ResourceCard
    requests: entities.ResourceCard


class SentMessageAction(PlayerAction):
    kind: Literal["sent_message"] = "sent_message"  # type: ignore[assignment]
    text: str


AnyPlayerAction = Annotated[
    FreePlacementAction
    | DiscardResourcesAction
    | MoveConquistatorAction
    | PlayWisdomCardAction
    | PlayMamoAction
    | PlayBlessedAction
    | PlayPathfinderAction
    | BuildSettlementAction
    | BuildPathAction
    | BuyWisdomCardAction
    | ProposeTradeAction
    | AcceptTradeAction
    | TradeWithSupplyAction
    | SentMessageAction
    | PlayerAction,
    pydantic.Field(discriminator="kind"),
]


class ActionExecutionResult(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)

    kind: Literal["action_result"] = "action_result"
    previous_phase: entities.GamePhaseName
    next_phase: entities.GamePhaseName
    action: AnyPlayerAction
    error: str | None = None


class PlacedBuildingsResult(ActionExecutionResult):
    kind: Literal["placed_buildings"] = "placed_buildings"  # type: ignore[assignment]
    settlement: board.Coordinate | None = None
    path: board.Coordinate | None = None
    next_player: str = ""


class DiscardedResourcesResult(ActionExecutionResult):
    kind: Literal["discarded_resources"] = "discarded_resources"  # type: ignore[assignment]
    count: dict[entities.ResourceCard, int] = pydantic.Field(default_factory=dict)


class MovedConquistatorResult(ActionExecutionResult):
    kind: Literal["moved_conquistator"] = "moved_conquistator"  # type: ignore[assignment]
    q: int = -1
    r: int = -1
    from_player: str | None = None
    stolen: entities.ResourceCard | None = None


class PlayedWisdomCardResult(ActionExecutionResult):
    kind: Literal["played_wisdom_card"] = "played_wisdom_card"  # type: ignore[assignment]
    card: entities.WisdomCard | None = None


class PlayedMamoResult(ActionExecutionResult):
    kind: Literal["played_mamo"] = "played_mamo"  # type: ignore[assignment]
    resource: entities.ResourceCard | None = None


class PlayedBlessedResult(ActionExecutionResult):
    kind: Literal["played_blessed"] = "played_blessed"  # type: ignore[assignment]
    resources: tuple[entities.ResourceCard, entities.ResourceCard] | None = None


class PlayedPathfinderResult(ActionExecutionResult):
    kind: Literal["played_pathfinder"] = "played_pathfinder"  # type: ignore[assignment]
    paths: tuple[board.Coordinate, ...] = ()


class BuiltSettlementResult(ActionExecutionResult):
    kind: Literal["built_settlement"] = "built_settlement"  # type: ignore[assignment]
    item: entities.SettlementType | None = None
    coordinate: board.Coordinate | None = None


class BuiltPathResult(ActionExecutionResult):
    kind: Literal["built_path"] = "built_path"  # type: ignore[assignment]
    coordinate: board.Coordinate | None = None


class EndedTradeAndBuildResult(ActionExecutionResult):
    kind: Literal["ended_trade_and_build"] = "ended_trade_and_build"  # type: ignore[assignment]
    next_player: str = ""


class BoughtWisdomCardResult(ActionExecutionResult):
    kind: Literal["bought_wisdom_card"] = "bought_wisdom_card"  # type: ignore[assignment]
    card: entities.WisdomCard | None = None


class ProposeTradeResult(ActionExecutionResult):
    kind: Literal["proposed_trade"] = "proposed_trade"  # type: ignore[assignment]
    proposal_id: uuid.UUID | None = None


class SentMessageResult(ActionExecutionResult):
    kind: Literal["sent_message"] = "sent_message"  # type: ignore[assignment]


class AcceptedTradeResult(ActionExecutionResult):
    kind: Literal["accepted_trade"] = "accepted_trade"  # type: ignore[assignment]
    proposal_id: uuid.UUID | None = None
    proposer: str = ""
    acceptor: str = ""
    offer: dict[entities.ResourceCard, int] = pydantic.Field(default_factory=dict)
    request: dict[entities.ResourceCard, int] = pydantic.Field(default_factory=dict)


class TradedWithSupplyResult(ActionExecutionResult):
    kind: Literal["traded_with_supply"] = "traded_with_supply"  # type: ignore[assignment]
    offers: entities.ResourceCard | None = None
    requests: entities.ResourceCard | None = None
    rate: int = -1


class DiceRollResult(ActionExecutionResult):
    kind: Literal["dice_roll"] = "dice_roll"  # type: ignore[assignment]
    die_1: int = -1
    die_2: int = -1
    to_discard: dict[str, int] = pydantic.Field(default_factory=dict)
    produced: dict[str, dict[entities.ResourceCard, int]] = pydantic.Field(
        default_factory=dict
    )


class EndGameResult(ActionExecutionResult):
    kind: Literal["end_game"] = "end_game"  # type: ignore[assignment]


AnyActionExecutionResult = Annotated[
    PlacedBuildingsResult
    | DiscardedResourcesResult
    | MovedConquistatorResult
    | PlayedWisdomCardResult
    | PlayedMamoResult
    | PlayedBlessedResult
    | PlayedPathfinderResult
    | BuiltSettlementResult
    | BuiltPathResult
    | EndedTradeAndBuildResult
    | BoughtWisdomCardResult
    | ProposeTradeResult
    | SentMessageResult
    | AcceptedTradeResult
    | TradedWithSupplyResult
    | DiceRollResult
    | EndGameResult
    | ActionExecutionResult,
    pydantic.Field(discriminator="kind"),
]
