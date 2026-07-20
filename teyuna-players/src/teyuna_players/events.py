import enum

import pydantic


class GamePhaseName(str, enum.Enum):
    FIRST_PLACEMENT = "first placement"
    SECOND_PLACEMENT = "second placement"
    DICE_ROLL = "dice roll"
    DISCARD_RESOURCES = "discard resources"
    DICE_PLAY_WARRIOR = "dice play warrior"
    DICE_PLAY_MAMO = "dice play mamo"
    DICE_PLAY_BLESSED = "dice play blessed"
    DICE_PLAY_PATHFINDER = "dice play pathfinder"
    MOVE_CONQUISTATOR = "move conquistator"
    TRADE_AND_BUILD = "trade and build"
    TRADE_AND_BUILD_PLAY_WARRIOR = "trade and build play warrior"
    TRADE_AND_BUILD_PLAY_MAMO = "trade and build play mamo"
    TRADE_AND_BUILD_PLAY_BLESSED = "trade and build play blessed"
    TRADE_AND_BUILD_PLAY_PATHFINDER = "trade and build play pathfinder"
    END_GAME = "end game"


class ActionExecutionResult(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True, arbitrary_types_allowed=True)

    succeeded: bool
    phase: GamePhaseName
    by: str | None = None
    error: str | None = None


class DiceRollResult(ActionExecutionResult):
    die_1: int = -1
    die_2: int = -1
    to_discard: dict[str, int] = pydantic.Field(default_factory=dict)
