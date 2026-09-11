import uuid
from typing import Annotated, Literal

import pydantic

from . import entities, board


class PlayerActionBase(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)


class PlayerAction(PlayerActionBase):
    """Advance / skip action (`kind: advance`).

    Valid phases and meaning (active player):
    - `dice roll`: roll the dice.
    - `trade and build`: end the turn.
    - `first placement` / `second placement`: place a random legal terrace+path.
    - `move conquistator`, `dice play warrior`, `trade and build play warrior`:
      a random legal `move_conquistator`.
    - `dice play mamo` / `trade and build play mamo`: a random legal `play_mamo`.
    - `dice play blessed` / `trade and build play blessed`: a random legal `play_blessed`.
    - `dice play pathfinder` / `trade and build play pathfinder`: a random legal
      `play_pathfinder` (up to two paths).

    Not allowed during `discard resources` (submit `discard_resources` instead).
    Not a useful player move in `lobby` or `end game`.
    """

    kind: Literal["advance"] = "advance"


class FreePlacementAction(PlayerActionBase):
    """Place one free terrace and one adjacent path during setup.

    Valid phases: `first placement`, `second placement` (active player only).
    Omit `terrace`, `path`, or both (or use `advance`) to let the server fill in
    the missing legal coordinate(s).
    """

    kind: Literal["free_placement"] = "free_placement"
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


class DiscardResourcesAction(PlayerActionBase):
    """Discard resource cards after a 7 is rolled.

    Valid phase: `discard resources` only, and only if your nickname appears in
    `Game.to_discard_resources` with a matching total count. Not turn-ordered.
    """

    kind: Literal["discard_resources"] = "discard_resources"
    count: dict[entities.ResourceCard, int]


class MoveConquistatorAction(PlayerActionBase):
    """Move the conquistator to a different hex; optionally steal one resource.

    Valid phases (active player): `move conquistator`, `dice play warrior`,
    `trade and build play warrior`. Destination must not be the current
    conquistator hex. If `from_player` is set and they hold cards, one random
    resource is stolen. Use `advance` for a random legal move.
    """

    kind: Literal["move_conquistator"] = "move_conquistator"
    q: int
    r: int
    from_player: str | None = None


class PlayWisdomCardAction(PlayerActionBase):
    """Play a wisdom card from the playable hand (not cards bought this turn).

    Valid phases (active player): `dice roll`, `trade and build`.
    Legacy of the Elders stays in the current phase after a victory check.
    Other cards enter the matching `dice play *` / `trade and build play *` phase.
    """

    kind: Literal["play_wisdom_card"] = "play_wisdom_card"
    card: entities.WisdomCard


class PlayMamoAction(PlayerActionBase):
    """Resolve Wisdom of Mamo: monopolize one resource type from all opponents.

    Valid phases (active player): `dice play mamo`, `trade and build play mamo`.
    """

    kind: Literal["play_mamo"] = "play_mamo"
    resource: entities.ResourceCard


class PlayBlessedAction(PlayerActionBase):
    """Resolve Blessing of Aluna: take two resources from the bank.

    Valid phases (active player): `dice play blessed`, `trade and build play blessed`.
    """

    kind: Literal["play_blessed"] = "play_blessed"
    resources: tuple[entities.ResourceCard, entities.ResourceCard]


class PlayPathfinderAction(PlayerActionBase):
    """Resolve Pathfinder: place the given free paths (empty tuple allowed).

    Valid phases (active player): `dice play pathfinder`,
    `trade and build play pathfinder`. The server truncates `paths` to remaining
    path supply. Use `advance` to pick up to two legal paths.
    """

    kind: Literal["play_pathfinder"] = "play_pathfinder"
    paths: tuple[board.Coordinate, ...]

    @pydantic.model_validator(mode="after")
    def _canonicalize(self) -> "PlayPathfinderAction":
        object.__setattr__(
            self,
            "paths",
            tuple(board.canonical_edge(path.q, path.r, path.d) for path in self.paths),
        )
        return self


class BuildSettlementAction(PlayerActionBase):
    """Build a terrace or upgrade to a great terrace (`item`).

    Valid phase: `trade and build` (active player). Costs and adjacency rules apply.
    """

    kind: Literal["build_settlement"] = "build_settlement"
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


class BuildPathAction(PlayerActionBase):
    """Build a path on an edge.

    Valid phase: `trade and build` (active player).
    """

    kind: Literal["build_path"] = "build_path"
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


class BuyWisdomCardAction(PlayerActionBase):
    """Buy a face-down wisdom card from the deck.

    Valid phase: `trade and build` (active player).
    """

    kind: Literal["buy_wisdom_card"] = "buy_wisdom_card"


class ProposeTradeAction(PlayerActionBase):
    """Propose a player-to-player trade.

    Valid phases:
    - `trade and build`: the active player may propose to other players.
    - `dice roll`: non-active players may propose only to the active player;
      the active player cannot propose.
    """

    kind: Literal["propose_trade"] = "propose_trade"
    offer: dict[entities.ResourceCard, int]
    request: dict[entities.ResourceCard, int]
    to: set[str]


class AcceptTradeAction(PlayerActionBase):
    """Accept an open trade proposal by id.

    Valid phase: `trade and build` (targeted player).
    """

    kind: Literal["accept_trade"] = "accept_trade"
    id: uuid.UUID


class TradeWithSupplyAction(PlayerActionBase):
    """Trade with the bank / harbour at the applicable rate.

    Valid phase: `trade and build` (active player).
    """

    kind: Literal["trade_with_supply"] = "trade_with_supply"
    offers: entities.ResourceCard
    requests: entities.ResourceCard


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
    | PlayerAction,
    pydantic.Field(discriminator="kind"),
]


class ActionExecutionResultBase(pydantic.BaseModel):
    """Shared fields for every action result (no ``kind`` discriminant)."""

    model_config = pydantic.ConfigDict(frozen=True)

    previous_phase: entities.GamePhaseName
    next_phase: entities.GamePhaseName
    action: AnyPlayerAction
    error: str | None = None


class ActionExecutionResult(ActionExecutionResultBase):
    kind: Literal["action_result"] = "action_result"


class PlacedBuildingsResult(ActionExecutionResultBase):
    kind: Literal["placed_buildings"] = "placed_buildings"
    settlement: board.Coordinate | None = None
    path: board.Coordinate | None = None
    next_player: str = ""


class DiscardedResourcesResult(ActionExecutionResultBase):
    kind: Literal["discarded_resources"] = "discarded_resources"
    count: dict[entities.ResourceCard, int] = pydantic.Field(default_factory=dict)


class MovedConquistatorResult(ActionExecutionResultBase):
    kind: Literal["moved_conquistator"] = "moved_conquistator"
    q: int = -1
    r: int = -1
    from_player: str | None = None
    stolen: entities.ResourceCard | None = None


class PlayedWisdomCardResult(ActionExecutionResultBase):
    kind: Literal["played_wisdom_card"] = "played_wisdom_card"
    card: entities.WisdomCard | None = None


class PlayedMamoResult(ActionExecutionResultBase):
    kind: Literal["played_mamo"] = "played_mamo"
    resource: entities.ResourceCard | None = None


class PlayedBlessedResult(ActionExecutionResultBase):
    kind: Literal["played_blessed"] = "played_blessed"
    resources: tuple[entities.ResourceCard, entities.ResourceCard] | None = None


class PlayedPathfinderResult(ActionExecutionResultBase):
    kind: Literal["played_pathfinder"] = "played_pathfinder"
    paths: tuple[board.Coordinate, ...] = ()


class BuiltSettlementResult(ActionExecutionResultBase):
    kind: Literal["built_settlement"] = "built_settlement"
    item: entities.SettlementType | None = None
    coordinate: board.Coordinate | None = None


class BuiltPathResult(ActionExecutionResultBase):
    kind: Literal["built_path"] = "built_path"
    coordinate: board.Coordinate | None = None


class EndedTradeAndBuildResult(ActionExecutionResultBase):
    kind: Literal["ended_trade_and_build"] = "ended_trade_and_build"
    next_player: str = ""


class BoughtWisdomCardResult(ActionExecutionResultBase):
    kind: Literal["bought_wisdom_card"] = "bought_wisdom_card"
    card: entities.WisdomCard | None = None


class ProposeTradeResult(ActionExecutionResultBase):
    kind: Literal["proposed_trade"] = "proposed_trade"
    proposal_id: uuid.UUID | None = None


class AcceptedTradeResult(ActionExecutionResultBase):
    kind: Literal["accepted_trade"] = "accepted_trade"
    proposal_id: uuid.UUID | None = None
    proposer: str = ""
    acceptor: str = ""
    offer: dict[entities.ResourceCard, int] = pydantic.Field(default_factory=dict)
    request: dict[entities.ResourceCard, int] = pydantic.Field(default_factory=dict)


class TradedWithSupplyResult(ActionExecutionResultBase):
    kind: Literal["traded_with_supply"] = "traded_with_supply"
    offers: entities.ResourceCard | None = None
    requests: entities.ResourceCard | None = None
    rate: int = -1


class DiceRollResult(ActionExecutionResultBase):
    kind: Literal["dice_roll"] = "dice_roll"
    die_1: int = -1
    die_2: int = -1
    to_discard: dict[str, int] = pydantic.Field(default_factory=dict)
    produced: dict[str, dict[entities.ResourceCard, int]] = pydantic.Field(
        default_factory=dict
    )


class EndGameResult(ActionExecutionResultBase):
    kind: Literal["end_game"] = "end_game"


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
    | AcceptedTradeResult
    | TradedWithSupplyResult
    | DiceRollResult
    | EndGameResult
    | ActionExecutionResult,
    pydantic.Field(discriminator="kind"),
]
