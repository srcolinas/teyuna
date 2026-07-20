import dataclasses

from ... import entities
from .. import _registry, _results
from . import _errors


@dataclasses.dataclass(frozen=True, slots=True)
class DiscardResourcesAction(_registry.PlayerAction):
    count: entities.ResourceCount


def handle_discard_resources(
    game: entities.ActiveGame, action: DiscardResourcesAction
) -> _registry.ActionExecutionResult:
    required = game.to_discard_resources.get(action.by)
    if required is None:
        return _results.fail(
            _errors.PlayerNotRequiredToDiscardError(
                f"Player {action.by} is not required to discard resources"
            )
        )

    if sum(action.count.values()) != required:
        return _results.fail(
            _errors.InvalidDiscardCountError(
                f"Player {action.by} must discard {required} resources"
            )
        )

    player_resources = game.players[action.by].resources
    for resource, amount in action.count.items():
        if player_resources[resource] < amount:
            return _results.fail(
                _errors.InsufficientResourcesError(
                    f"Insufficient {resource.value} to discard"
                )
            )

    game.discard_resources(action.by, action.count)
    del game.to_discard_resources[action.by]

    if game.to_discard_resources:
        return _results.ok(_registry.GamePhaseName.DISCARD_RESOURCES)
    return _results.ok(_registry.GamePhaseName.MOVE_CONQUISTATOR)
