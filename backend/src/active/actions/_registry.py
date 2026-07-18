import dataclasses
import inspect
import random
from enum import Enum
from collections.abc import Callable
from typing import Any

from ... import player
from .. import entities


class GamePhaseName(str, Enum):
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


@dataclasses.dataclass(frozen=True, slots=True)
class PlayerAction:
    by: player.Nickname
    rng_: random.Random = dataclasses.field(default_factory=random.Random, kw_only=True)


class GamePhaseHanlderNotImplementedError(Exception):
    pass


class ActionNotAllowedError(Exception):
    pass


class ActionsRegistry:
    def __init__(self) -> None:
        self._registry: dict[
            GamePhaseName,
            dict[
                type[PlayerAction], Callable[[entities.ActiveGame, Any], GamePhaseName]
            ],
        ] = {}

    def register[ActionT: PlayerAction](
        self,
        phase: GamePhaseName,
    ) -> Callable[
        [Callable[[entities.ActiveGame, ActionT], GamePhaseName]],
        Callable[[entities.ActiveGame, ActionT], GamePhaseName],
    ]:
        def decorator(
            handler: Callable[[entities.ActiveGame, ActionT], GamePhaseName],
        ) -> Callable[[entities.ActiveGame, ActionT], GamePhaseName]:
            sig = inspect.signature(handler)
            params = list(sig.parameters.values())

            if len(params) < 2:
                raise ValueError(
                    f"Handler '{handler.__name__}' must accept at least two parameters: (game, action)."
                )

            action_param_name = params[1].name

            annotations = inspect.get_annotations(handler)
            action_type = annotations.get(action_param_name)

            if not isinstance(action_type, type) or not issubclass(
                action_type, PlayerAction
            ):
                raise TypeError(
                    f"The second parameter '{action_param_name}' of handler '{handler.__name__}' "
                    f"must be annotated with a subclass of PlayerAction (got {action_type})."
                )

            if phase not in self._registry:
                self._registry[phase] = {}

            self._registry[phase][action_type] = handler

            return handler

        return decorator

    def execute(
        self, phase: GamePhaseName, game: entities.ActiveGame, action: PlayerAction
    ) -> GamePhaseName:
        if phase is GamePhaseName.END_GAME:
            raise ActionNotAllowedError("Game has ended; no actions are allowed")

        phase_handlers = self._registry.get(phase)
        if not phase_handlers:
            raise GamePhaseHanlderNotImplementedError(
                f"No handlers defined for game phase: {phase.value}"
            )

        action_type = type(action)
        handler = phase_handlers.get(action_type)

        if not handler:
            raise ActionNotAllowedError(
                f"Action '{action_type.__name__}' is not allowed during the '{phase.value}' phase."
            )

        return handler(game, action)
