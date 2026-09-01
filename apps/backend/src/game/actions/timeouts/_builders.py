import random

import teyuna_core

from ... import entities
from .. import _execution, _registry
from ..handlers import _advance


def timeout_dice_roll(
    game: entities.Game, rng: random.Random
) -> _registry.TimeoutAction:
    return _registry.TimeoutAction(
        by=game.active_player,
        action=teyuna_core.PlayerAction(),
    )


def timeout_trade_and_build(
    game: entities.Game, rng: random.Random
) -> _registry.TimeoutAction:
    return _registry.TimeoutAction(
        by=game.active_player,
        action=teyuna_core.PlayerAction(),
    )


def timeout_lobby(game: entities.Game, rng: random.Random) -> _registry.TimeoutAction:
    return _registry.TimeoutAction(by="", action=teyuna_core.PlayerAction())


def timeout_first_placement(
    game: entities.Game, rng: random.Random
) -> _registry.TimeoutAction:
    by = game.active_player
    action = _advance.resolve_free_placement(
        game,
        _execution.ExecutionContext(by=by, due_to_timeout=True, rng=rng),
        teyuna_core.FreePlacementAction(),
    )
    return _registry.TimeoutAction(
        by=by,
        action=action,
    )


def timeout_second_placement(
    game: entities.Game, rng: random.Random
) -> _registry.TimeoutAction:
    return timeout_first_placement(game, rng)


def timeout_move_conquistator(
    game: entities.Game, rng: random.Random
) -> _registry.TimeoutAction:
    by = game.active_player
    action = _advance.random_move_conquistator(
        game,
        _execution.ExecutionContext(by=by, due_to_timeout=True, rng=rng),
        teyuna_core.MoveConquistatorAction(q=0, r=0),
    )
    return _registry.TimeoutAction(by=by, action=action)


def timeout_discard_resources(
    game: entities.Game, rng: random.Random
) -> _registry.TimeoutAction:
    nick = next(iter(game.to_discard_resources))
    action = _advance.discard_resources_for(
        game,
        _execution.ExecutionContext(by=nick, due_to_timeout=True, rng=rng),
        teyuna_core.DiscardResourcesAction(count={}),
    )
    return _registry.TimeoutAction(by=nick, action=action)


def timeout_play_mamo(
    game: entities.Game, rng: random.Random
) -> _registry.TimeoutAction:
    by = game.active_player
    action = _advance.random_play_mamo(
        game,
        _execution.ExecutionContext(by=by, due_to_timeout=True, rng=rng),
        teyuna_core.PlayMamoAction(resource=teyuna_core.ResourceCard.GOLD),
    )
    return _registry.TimeoutAction(by=by, action=action)


def timeout_play_blessed(
    game: entities.Game, rng: random.Random
) -> _registry.TimeoutAction:
    by = game.active_player
    action = _advance.random_play_blessed(
        game,
        _execution.ExecutionContext(by=by, due_to_timeout=True, rng=rng),
        teyuna_core.PlayBlessedAction(
            resources=(
                teyuna_core.ResourceCard.GOLD,
                teyuna_core.ResourceCard.STONE,
            )
        ),
    )
    return _registry.TimeoutAction(by=by, action=action)


def timeout_play_pathfinder(
    game: entities.Game, rng: random.Random
) -> _registry.TimeoutAction:
    by = game.active_player
    action = _advance.random_play_pathfinder(
        game,
        _execution.ExecutionContext(by=by, due_to_timeout=True, rng=rng),
        teyuna_core.PlayPathfinderAction(paths=()),
    )
    return _registry.TimeoutAction(by=by, action=action)
