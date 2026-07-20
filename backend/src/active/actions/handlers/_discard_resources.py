import collections
import dataclasses

from ... import entities
from .. import _registry
from . import _errors


@dataclasses.dataclass(frozen=True, slots=True)
class DiscardResourcesAction(_registry.PlayerAction):
    count: entities.ResourceCount


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class DiscardedResourcesResult(_registry.ActionExecutionResult):
    count: entities.ResourceCount = dataclasses.field(
        default_factory=collections.Counter
    )


def handle_discard_resources(
    game: entities.ActiveGame, action: DiscardResourcesAction
) -> DiscardedResourcesResult:
    required = game.to_discard_resources.get(action.by)
    if required is None:
        return DiscardedResourcesResult(
            succeeded=False,
            phase=_registry.GamePhaseName.END_GAME,
            error=_errors.PlayerNotRequiredToDiscardError(
                f"Player {action.by} is not required to discard resources"
            ),
        )

    if sum(action.count.values()) != required:
        return DiscardedResourcesResult(
            succeeded=False,
            phase=_registry.GamePhaseName.END_GAME,
            error=_errors.InvalidDiscardCountError(
                f"Player {action.by} must discard {required} resources"
            ),
        )

    player_resources = game.players[action.by].resources
    for resource, amount in action.count.items():
        if player_resources[resource] < amount:
            return DiscardedResourcesResult(
                succeeded=False,
                phase=_registry.GamePhaseName.END_GAME,
                error=_errors.InsufficientResourcesError(
                    f"Insufficient {resource.value} to discard"
                ),
            )

    game.discard_resources(action.by, action.count)
    del game.to_discard_resources[action.by]

    if game.to_discard_resources:
        return DiscardedResourcesResult(
            succeeded=True,
            phase=_registry.GamePhaseName.DISCARD_RESOURCES,
            count=action.count,
        )
    return DiscardedResourcesResult(
        succeeded=True,
        phase=_registry.GamePhaseName.MOVE_CONQUISTATOR,
        count=action.count,
    )
