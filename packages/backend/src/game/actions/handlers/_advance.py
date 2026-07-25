import collections
import random
from collections.abc import Callable
from typing import Any

import teyuna_core

from ... import entities
from . import _placement

TypedHandler = Callable[[entities.Game, Any], teyuna_core.AnyActionExecutionResult]


def handle_advance(
    game: entities.Game, action: teyuna_core.PlayerAction
) -> teyuna_core.AnyActionExecutionResult:
    """Expand bare ``PlayerAction`` into a random legal typed move for this phase."""
    typed = random_action_for_phase(game, action)
    return _typed_handler_for(game.phase)(game, typed)


def random_action_for_phase(
    game: entities.Game, action: teyuna_core.PlayerAction
) -> teyuna_core.PlayerActionBase:
    """Build a random legal typed action for ``game.phase``, bound to ``action``."""
    by = action.by
    rng = action.rng_
    due_to_timeout = action.due_to_timeout
    phase = game.phase

    if phase in (
        teyuna_core.GamePhaseName.FIRST_PLACEMENT,
        teyuna_core.GamePhaseName.SECOND_PLACEMENT,
    ):
        return resolve_free_placement(game, rng, by=by, due_to_timeout=due_to_timeout)
    if phase in (
        teyuna_core.GamePhaseName.MOVE_CONQUISTATOR,
        teyuna_core.GamePhaseName.DICE_PLAY_WARRIOR,
        teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR,
    ):
        return random_move_conquistator(game, rng, by=by, due_to_timeout=due_to_timeout)
    if phase in (
        teyuna_core.GamePhaseName.DICE_PLAY_MAMO,
        teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO,
    ):
        return random_play_mamo(game, rng, by=by, due_to_timeout=due_to_timeout)
    if phase in (
        teyuna_core.GamePhaseName.DICE_PLAY_BLESSED,
        teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED,
    ):
        return random_play_blessed(game, rng, by=by, due_to_timeout=due_to_timeout)
    if phase in (
        teyuna_core.GamePhaseName.DICE_PLAY_PATHFINDER,
        teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER,
    ):
        return random_play_pathfinder(game, rng, by=by, due_to_timeout=due_to_timeout)
    raise KeyError(f"No random advance defined for phase: {phase.value}")


def resolve_free_placement(
    game: entities.Game,
    rng: random.Random,
    *,
    by: str,
    terrace: teyuna_core.Coordinate | None = None,
    path: teyuna_core.Coordinate | None = None,
    due_to_timeout: bool = False,
) -> teyuna_core.FreePlacementAction:
    if terrace is not None and path is not None:
        return teyuna_core.FreePlacementAction.model_construct(
            by=by,
            due_to_timeout=due_to_timeout,
            terrace=terrace,
            path=path,
            rng_=rng,
        )

    player_state = game.players[by]
    existing_settlements = set(player_state.settlements.locations())
    existing_paths = player_state.paths

    if terrace is None and path is not None:
        legal_terraces = [
            vertex
            for vertex in teyuna_core.vertices_of_edge(path)
            if _placement.can_add_free_terrace_at(
                free_verticies=game.free_verticies,
                restricted_verticies=game.restricted_verticies,
                target=vertex,
            )
        ]
        if legal_terraces:
            terrace = rng.choice(legal_terraces)
        return teyuna_core.FreePlacementAction.model_construct(
            by=by,
            due_to_timeout=due_to_timeout,
            terrace=terrace,
            path=path,
            rng_=rng,
        )

    if terrace is not None and path is None:
        legal_paths = _legal_paths_for_terrace(
            game,
            terrace=terrace,
            existing_settlements=existing_settlements,
            existing_paths=existing_paths,
        )
        if legal_paths:
            path = rng.choice(legal_paths)
        return teyuna_core.FreePlacementAction.model_construct(
            by=by,
            due_to_timeout=due_to_timeout,
            terrace=terrace,
            path=path,
            rng_=rng,
        )

    legal_terraces = [
        vertex
        for vertex in game.free_verticies
        if _placement.can_add_free_terrace_at(
            free_verticies=game.free_verticies,
            restricted_verticies=game.restricted_verticies,
            target=vertex,
        )
    ]
    rng.shuffle(legal_terraces)
    for candidate in legal_terraces:
        legal_paths = _legal_paths_for_terrace(
            game,
            terrace=candidate,
            existing_settlements=existing_settlements,
            existing_paths=existing_paths,
        )
        if not legal_paths:
            continue
        return teyuna_core.FreePlacementAction.model_construct(
            by=by,
            due_to_timeout=due_to_timeout,
            terrace=candidate,
            path=rng.choice(legal_paths),
            rng_=rng,
        )
    raise RuntimeError("No legal free placement available for timeout")


def discard_resources_for(
    game: entities.Game,
    rng: random.Random,
    *,
    by: str,
    due_to_timeout: bool = False,
) -> teyuna_core.DiscardResourcesAction:
    required = game.to_discard_resources.get(by, 0)
    count = (
        _pick_discard(game.players[by].resources, required, rng)
        if required and by in game.players
        else {}
    )
    return teyuna_core.DiscardResourcesAction.model_construct(
        by=by,
        due_to_timeout=due_to_timeout,
        count=count,
        rng_=rng,
    )


def random_move_conquistator(
    game: entities.Game,
    rng: random.Random,
    *,
    by: str,
    due_to_timeout: bool = False,
) -> teyuna_core.MoveConquistatorAction:
    candidates = [
        teyuna_core.HexLocation(q=hex_tile.q, r=hex_tile.r)
        for hex_tile in game.map
        if teyuna_core.HexLocation(q=hex_tile.q, r=hex_tile.r)
        != game.conquistator_location
    ]
    if not candidates:
        raise RuntimeError("No legal conquistator destinations available")
    location = rng.choice(candidates)
    victims = [
        nick
        for nick, player_state in game.players.items()
        if nick != by and sum(player_state.resources.values()) > 0
    ]
    from_player = rng.choice(victims) if victims else None
    return teyuna_core.MoveConquistatorAction.model_construct(
        by=by,
        due_to_timeout=due_to_timeout,
        q=location.q,
        r=location.r,
        from_player=from_player,
        rng_=rng,
    )


def random_play_mamo(
    game: entities.Game,
    rng: random.Random,
    *,
    by: str,
    due_to_timeout: bool = False,
) -> teyuna_core.PlayMamoAction:
    resource = rng.choice(list(teyuna_core.ResourceCard))
    return teyuna_core.PlayMamoAction.model_construct(
        by=by,
        due_to_timeout=due_to_timeout,
        resource=resource,
        rng_=rng,
    )


def random_play_blessed(
    game: entities.Game,
    rng: random.Random,
    *,
    by: str,
    due_to_timeout: bool = False,
) -> teyuna_core.PlayBlessedAction:
    pool: list[teyuna_core.ResourceCard] = [
        resource
        for resource in teyuna_core.ResourceCard
        for _ in range(game.resource_supply[resource])
    ]
    if len(pool) >= 2:
        first, second = rng.sample(pool, 2)
    else:
        resources = list(teyuna_core.ResourceCard)
        first, second = resources[0], resources[1]
    return teyuna_core.PlayBlessedAction.model_construct(
        by=by,
        due_to_timeout=due_to_timeout,
        resources=(first, second),
        rng_=rng,
    )


def random_play_pathfinder(
    game: entities.Game,
    rng: random.Random,
    *,
    by: str,
    due_to_timeout: bool = False,
) -> teyuna_core.PlayPathfinderAction:
    player_state = game.players[by]
    remaining = teyuna_core.MAX_PATHS - len(player_state.paths)
    legal: list[teyuna_core.Coordinate] = [
        edge
        for edge in game.free_edges
        if _placement.can_add_free_path_at(
            target=edge,
            free_edges=game.free_edges,
            existing_settlements=player_state.settlements.locations(),
            existing_paths=player_state.paths,
            free_vertices=game.free_verticies,
        )
    ]
    rng.shuffle(legal)
    chosen: list[teyuna_core.Coordinate] = []
    owned_paths = set(player_state.paths)
    for edge in legal:
        if len(chosen) >= min(2, remaining):
            break
        provisional = owned_paths | set(chosen)
        if _placement.can_add_free_path_at(
            target=edge,
            free_edges=set(game.free_edges) - set(chosen),
            existing_settlements=player_state.settlements.locations(),
            existing_paths=provisional,
            free_vertices=game.free_verticies,
        ):
            chosen.append(edge)
    return teyuna_core.PlayPathfinderAction.model_construct(
        by=by,
        due_to_timeout=due_to_timeout,
        paths=tuple(chosen),
        rng_=rng,
    )


def _legal_paths_for_terrace(
    game: entities.Game,
    *,
    terrace: teyuna_core.Coordinate,
    existing_settlements: set[teyuna_core.Coordinate],
    existing_paths: set[teyuna_core.Coordinate],
) -> list[teyuna_core.Coordinate]:
    adjacent = teyuna_core.edges_adjacent_to_vertex(terrace.q, terrace.r, terrace.d)
    return [
        edge
        for edge in adjacent
        if _placement.can_add_free_path_at(
            target=edge,
            free_edges=game.free_edges,
            existing_settlements=existing_settlements,
            existing_paths=existing_paths,
            free_vertices=game.free_verticies,
            new_settlement=terrace,
        )
    ]


def _pick_discard(
    resources: teyuna_core.ResourceCount,
    required: int,
    rng: random.Random,
) -> dict[teyuna_core.ResourceCard, int]:
    pool: list[teyuna_core.ResourceCard] = [
        resource for resource, amount in resources.items() for _ in range(amount)
    ]
    rng.shuffle(pool)
    count: collections.Counter[teyuna_core.ResourceCard] = collections.Counter()
    for resource in pool[:required]:
        count[resource] += 1
    return dict(count)


def _typed_handler_for(phase: teyuna_core.GamePhaseName) -> TypedHandler:
    # Lazy imports avoid a cycle with placement handlers that call resolve_free_placement.
    from . import (
        _first_placement,
        _move_conquistator,
        _play_blessed,
        _play_mamo,
        _play_pathfinder,
        _second_placement,
    )

    handlers: dict[teyuna_core.GamePhaseName, TypedHandler] = {
        teyuna_core.GamePhaseName.FIRST_PLACEMENT: (
            _first_placement.handle_first_placement
        ),
        teyuna_core.GamePhaseName.SECOND_PLACEMENT: (
            _second_placement.handle_second_placement
        ),
        teyuna_core.GamePhaseName.MOVE_CONQUISTATOR: (
            _move_conquistator.handle_move_conquistator
        ),
        teyuna_core.GamePhaseName.DICE_PLAY_WARRIOR: (
            _move_conquistator.handle_dice_play_warrior
        ),
        teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_WARRIOR: (
            _move_conquistator.handle_move_conquistator
        ),
        teyuna_core.GamePhaseName.DICE_PLAY_MAMO: _play_mamo.handle_dice_play_mamo,
        teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_MAMO: (
            _play_mamo.handle_trade_and_build_play_mamo
        ),
        teyuna_core.GamePhaseName.DICE_PLAY_BLESSED: (
            _play_blessed.handle_dice_play_blessed
        ),
        teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_BLESSED: (
            _play_blessed.handle_trade_and_build_play_blessed
        ),
        teyuna_core.GamePhaseName.DICE_PLAY_PATHFINDER: (
            _play_pathfinder.handle_dice_play_pathfinder
        ),
        teyuna_core.GamePhaseName.TRADE_AND_BUILD_PLAY_PATHFINDER: (
            _play_pathfinder.handle_trade_and_build_play_pathfinder
        ),
    }
    return handlers[phase]
