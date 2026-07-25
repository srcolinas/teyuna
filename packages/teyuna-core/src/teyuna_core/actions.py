import random
import uuid
from typing import Annotated, Any, Literal

import pydantic

from . import entities, board


class PlayerAction(pydantic.BaseModel):
    """Advance / skip action (`kind: advance`).

    Valid phases and meaning:
    - `dice roll`: roll the dice (active player).
    - `trade and build`: end the turn (active player).
    - `first placement` / `second placement`: place a random legal terrace+path.
    - `move conquistator` and `* play warrior` / `mamo` / `blessed` / `pathfinder`:
      apply a random legal typed move for that phase.

    Not allowed during `discard resources` (submit `discard_resources` instead).
    Not useful in `lobby` or `end game`.
    """

    model_config = pydantic.ConfigDict(frozen=True, arbitrary_types_allowed=True)

    kind: Literal["advance"] = "advance"
    by: Annotated[
        str,
        pydantic.Field(
            default="",
            description="Set by the server from the authenticated player; clients should omit.",
        ),
    ] = ""
    due_to_timeout: bool = False
    rng_: Any = pydantic.Field(
        default_factory=random.Random,
        exclude=True,
    )


class FreePlacementAction(PlayerAction):
    """Place one free terrace and one adjacent path during setup.

    Valid phases: `first placement`, `second placement` (active player only).
    Omit both coordinates (or use `advance`) to let the server pick a legal placement.
    """

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
    """Discard resource cards after a 7 is rolled.

    Valid phase: `discard resources` only, and only if your nickname appears in
    `Game.to_discard_resources` with a matching total count. Not turn-ordered.
    """

    kind: Literal["discard_resources"] = "discard_resources"  # type: ignore[assignment]
    count: dict[entities.ResourceCard, int]


class MoveConquistatorAction(PlayerAction):
    """Move the conquistator to a hex and optionally steal from an adjacent player.

    Valid phases (active player): `move conquistator`, `dice play warrior`,
    `trade and build play warrior`. Use `advance` for a random legal move.
    """

    kind: Literal["move_conquistator"] = "move_conquistator"  # type: ignore[assignment]
    q: int
    r: int
    from_player: str | None = None


class PlayWisdomCardAction(PlayerAction):
    """Play a wisdom card from your hand, entering the matching resolve phase.

    Valid phases (active player): `dice roll`, `trade and build`.
    Legacy of the Elders resolves immediately; other cards enter `* play *` phases.
    """

    kind: Literal["play_wisdom_card"] = "play_wisdom_card"  # type: ignore[assignment]
    card: entities.WisdomCard


class PlayMamoAction(PlayerAction):
    """Resolve Wisdom of Mamo: monopolize one resource type from all opponents.

    Valid phases (active player): `dice play mamo`, `trade and build play mamo`.
    """

    kind: Literal["play_mamo"] = "play_mamo"  # type: ignore[assignment]
    resource: entities.ResourceCard


class PlayBlessedAction(PlayerAction):
    """Resolve Blessing of Aluna: take two resources from the bank.

    Valid phases (active player): `dice play blessed`, `trade and build play blessed`.
    """

    kind: Literal["play_blessed"] = "play_blessed"  # type: ignore[assignment]
    resources: tuple[entities.ResourceCard, entities.ResourceCard]


class PlayPathfinderAction(PlayerAction):
    """Resolve Pathfinder: place up to two free paths.

    Valid phases (active player): `dice play pathfinder`,
    `trade and build play pathfinder`.
    """

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
    """Build a terrace or upgrade to a great terrace (`item`).

    Valid phase: `trade and build` (active player). Costs and adjacency rules apply.
    """

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
    """Build a path on an edge.

    Valid phase: `trade and build` (active player).
    """

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
    """Buy a face-down wisdom card from the deck.

    Valid phase: `trade and build` (active player).
    """

    kind: Literal["buy_wisdom_card"] = "buy_wisdom_card"  # type: ignore[assignment]


class ProposeTradeAction(PlayerAction):
    """Propose a player-to-player trade.

    Valid phases:
    - `trade and build`: active player may propose to any other players.
    - `dice roll`: any player may propose only to the active player.
    """

    kind: Literal["propose_trade"] = "propose_trade"  # type: ignore[assignment]
    offer: dict[entities.ResourceCard, int]
    request: dict[entities.ResourceCard, int]
    to: set[str]


class AcceptTradeAction(PlayerAction):
    """Accept an open trade proposal by id.

    Valid phase: `trade and build` (targeted player).
    """

    kind: Literal["accept_trade"] = "accept_trade"  # type: ignore[assignment]
    id: uuid.UUID


class TradeWithSupplyAction(PlayerAction):
    """Trade with the bank / harbour at the applicable rate.

    Valid phase: `trade and build` (active player).
    """

    kind: Literal["trade_with_supply"] = "trade_with_supply"  # type: ignore[assignment]
    offers: entities.ResourceCard
    requests: entities.ResourceCard


class SentMessageAction(PlayerAction):
    """Send a chat message to the game.

    Valid in every phase except `lobby`.
    """

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
