import pydantic

from ... import entities
from .. import _registry


class DiscardResourcesAction(_registry.PlayerAction):
    count: entities.ResourceCount


class DiscardedResourcesResult(_registry.ActionExecutionResult):
    count: dict[entities.ResourceCard, int] = pydantic.Field(default_factory=dict)


def handle_discard_resources(
    game: entities.Game, action: DiscardResourcesAction
) -> DiscardedResourcesResult:
    previous_phase = game.phase
    required = game.to_discard_resources.get(action.by)
    if required is None:
        return DiscardedResourcesResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} is not required to discard resources",
        )

    if sum(action.count.values()) != required:
        return DiscardedResourcesResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} must discard {required} resources",
        )

    player_resources = game.players[action.by].resources
    for resource, amount in action.count.items():
        if player_resources[resource] < amount:
            return DiscardedResourcesResult(
                previous_phase=previous_phase,
                next_phase=game.phase,
                action=action,
                error=f"Insufficient {resource.value} to discard",
            )

    game.discard_resources(action.by, action.count)
    del game.to_discard_resources[action.by]

    if game.to_discard_resources:
        game.phase = entities.GamePhaseName.DISCARD_RESOURCES
    else:
        game.phase = entities.GamePhaseName.MOVE_CONQUISTATOR
    return DiscardedResourcesResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        count=action.count,
    )
