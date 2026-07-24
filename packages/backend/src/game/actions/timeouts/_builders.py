import collections
import random

import teyuna_core

from ... import entities
from ..handlers import _placement


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


def timeout_first_placement(
    game: entities.Game, rng: random.Random
) -> teyuna_core.FreePlacementAction:
    return resolve_free_placement(
        game,
        rng,
        by=game.active_player,
        due_to_timeout=True,
    )


def timeout_second_placement(
    game: entities.Game, rng: random.Random
) -> teyuna_core.FreePlacementAction:
    return resolve_free_placement(
        game,
        rng,
        by=game.active_player,
        due_to_timeout=True,
    )


def timeout_move_conquistator(
    game: entities.Game, rng: random.Random
) -> teyuna_core.MoveConquistatorAction:
    candidates = [
        teyuna_core.HexLocation(q=hex_tile.q, r=hex_tile.r)
        for hex_tile in game.map
        if teyuna_core.HexLocation(q=hex_tile.q, r=hex_tile.r)
        != game.conquistator_location
    ]
    location = rng.choice(candidates)
    victims = [
        nick
        for nick, player_state in game.players.items()
        if nick != game.active_player and sum(player_state.resources.values()) > 0
    ]
    from_player = rng.choice(victims) if victims else None
    return teyuna_core.MoveConquistatorAction.model_construct(
        by=game.active_player,
        due_to_timeout=True,
        q=location.q,
        r=location.r,
        from_player=from_player,
        rng_=rng,
    )


def timeout_discard_resources(
    game: entities.Game, rng: random.Random
) -> teyuna_core.DiscardResourcesAction:
    nick = next(iter(game.to_discard_resources))
    required = game.to_discard_resources[nick]
    count = _pick_discard(game.players[nick].resources, required, rng)
    return teyuna_core.DiscardResourcesAction.model_construct(
        by=nick,
        due_to_timeout=True,
        count=count,
        rng_=rng,
    )


def timeout_lobby(game: entities.Game, rng: random.Random) -> teyuna_core.PlayerAction:
    return teyuna_core.PlayerAction.model_construct(
        by="", due_to_timeout=True, rng_=rng
    )


def timeout_play_mamo(
    game: entities.Game, rng: random.Random
) -> teyuna_core.PlayMamoAction:
    resource = rng.choice(list(teyuna_core.ResourceCard))
    return teyuna_core.PlayMamoAction.model_construct(
        by=game.active_player,
        due_to_timeout=True,
        resource=resource,
        rng_=rng,
    )


def timeout_play_blessed(
    game: entities.Game, rng: random.Random
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
        by=game.active_player,
        due_to_timeout=True,
        resources=(first, second),
        rng_=rng,
    )


def timeout_play_pathfinder(
    game: entities.Game, rng: random.Random
) -> teyuna_core.PlayPathfinderAction:
    player_state = game.players[game.active_player]
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
        by=game.active_player,
        due_to_timeout=True,
        paths=tuple(chosen),
        rng_=rng,
    )


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


def _legal_paths_for_terrace(
    game: entities.Game,
    *,
    terrace: teyuna_core.Coordinate,
    existing_settlements: set[teyuna_core.Coordinate],
    existing_paths: set[teyuna_core.Coordinate],
) -> list[teyuna_core.Coordinate]:
    return [
        edge
        for edge in game.free_edges
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
