from typing import Annotated, Literal

import pydantic

from . import actions, entities


class GameEventBase(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)


class MessageEvent(GameEventBase):
    type: Literal["message"] = "message"
    by: str
    text: str


class FailedActionEvent(GameEventBase):
    type: Literal["failed_action"] = "failed_action"
    by: str
    due_to_timeout: bool
    action: actions.AnyPlayerAction
    error: str


class SuccessfulActionEvent(GameEventBase):
    type: Literal["successful_action"] = "successful_action"
    by: str
    due_to_timeout: bool
    action: actions.AnyPlayerAction
    result: actions.AnyActionExecutionResult


class PhaseChangedEvent(GameEventBase):
    type: Literal["phase_changed"] = "phase_changed"
    previous_phase: entities.GamePhaseName
    next_phase: entities.GamePhaseName


class TurnChangedEvent(GameEventBase):
    type: Literal["turn_changed"] = "turn_changed"
    previous_player: str | None
    next_player: str | None


class BiggestArmyChangedEvent(GameEventBase):
    type: Literal["biggest_army_changed"] = "biggest_army_changed"
    previous_holder: str | None
    current_holder: str | None
    previous_size: int
    current_size: int


class LongestRoadChangedEvent(GameEventBase):
    type: Literal["longest_road_changed"] = "longest_road_changed"
    previous_holder: str | None
    current_holder: str | None
    previous_length: int
    current_length: int


class EndGameEvent(GameEventBase):
    type: Literal["end_game"] = "end_game"
    winner: str | None
    reason: str


AnyGameEvent = Annotated[
    MessageEvent
    | FailedActionEvent
    | SuccessfulActionEvent
    | PhaseChangedEvent
    | TurnChangedEvent
    | BiggestArmyChangedEvent
    | LongestRoadChangedEvent
    | EndGameEvent,
    pydantic.Field(discriminator="type"),
]
