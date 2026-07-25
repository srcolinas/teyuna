import random

import teyuna_core

from ... import entities
from ..handlers import _advance


def timeout_dice_roll(
    game: entities.Game, rng: random.Random
) -> teyuna_core.PlayerAction:
    return teyuna_core.PlayerAction.model_construct(
        by=game.active_player, due_to_timeout=True, rng_=rng
    )


def timeout_trade_and_build(
    game: entities.Game, rng: random.Random
) -> teyuna_core.PlayerAction:
    return teyuna_core.PlayerAction.model_construct(
        by=game.active_player, due_to_timeout=True, rng_=rng
    )


def timeout_lobby(game: entities.Game, rng: random.Random) -> teyuna_core.PlayerAction:
    return teyuna_core.PlayerAction.model_construct(
        by="", due_to_timeout=True, rng_=rng
    )


def timeout_first_placement(
    game: entities.Game, rng: random.Random
) -> teyuna_core.FreePlacementAction:
    return _advance.resolve_free_placement(
        game,
        rng,
        by=game.active_player,
        due_to_timeout=True,
    )


def timeout_second_placement(
    game: entities.Game, rng: random.Random
) -> teyuna_core.FreePlacementAction:
    return _advance.resolve_free_placement(
        game,
        rng,
        by=game.active_player,
        due_to_timeout=True,
    )


def timeout_move_conquistator(
    game: entities.Game, rng: random.Random
) -> teyuna_core.MoveConquistatorAction:
    return _advance.random_move_conquistator(
        game,
        rng,
        by=game.active_player,
        due_to_timeout=True,
    )


def timeout_discard_resources(
    game: entities.Game, rng: random.Random
) -> teyuna_core.DiscardResourcesAction:
    nick = next(iter(game.to_discard_resources))
    return _advance.discard_resources_for(game, rng, by=nick, due_to_timeout=True)


def timeout_play_mamo(
    game: entities.Game, rng: random.Random
) -> teyuna_core.PlayMamoAction:
    return _advance.random_play_mamo(
        game,
        rng,
        by=game.active_player,
        due_to_timeout=True,
    )


def timeout_play_blessed(
    game: entities.Game, rng: random.Random
) -> teyuna_core.PlayBlessedAction:
    return _advance.random_play_blessed(
        game,
        rng,
        by=game.active_player,
        due_to_timeout=True,
    )


def timeout_play_pathfinder(
    game: entities.Game, rng: random.Random
) -> teyuna_core.PlayPathfinderAction:
    return _advance.random_play_pathfinder(
        game,
        rng,
        by=game.active_player,
        due_to_timeout=True,
    )


# Re-exports so existing call sites / tests can keep importing from timeouts.
resolve_free_placement = _advance.resolve_free_placement
discard_resources_for = _advance.discard_resources_for
