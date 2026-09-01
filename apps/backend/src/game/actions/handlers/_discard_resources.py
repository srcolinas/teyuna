import teyuna_core

from ... import entities
from .. import _execution


def handle_discard_resources(
    game: entities.Game,
    context: _execution.ExecutionContext,
    action: teyuna_core.DiscardResourcesAction,
) -> teyuna_core.DiscardedResourcesResult:
    previous_phase = game.phase
    required = game.to_discard_resources.get(context.by)
    if required is None:
        return teyuna_core.DiscardedResourcesResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {context.by} is not required to discard resources",
        )

    if sum(action.count.values()) != required:
        return teyuna_core.DiscardedResourcesResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {context.by} must discard {required} resources",
        )

    player_resources = game.players[context.by].resources
    for resource, amount in action.count.items():
        if player_resources[resource] < amount:
            return teyuna_core.DiscardedResourcesResult(
                previous_phase=previous_phase,
                next_phase=game.phase,
                action=action,
                error=f"Insufficient {resource.value} to discard",
            )

    game.discard_resources(context.by, action.count)
    del game.to_discard_resources[context.by]

    if game.to_discard_resources:
        game.phase = teyuna_core.GamePhaseName.DISCARD_RESOURCES
    else:
        game.phase = teyuna_core.GamePhaseName.MOVE_CONQUISTATOR
    return teyuna_core.DiscardedResourcesResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        count=action.count,
    )
