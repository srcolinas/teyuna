import collections
import random

import teyuna_shared

from ... import entities
from ..handlers import _placement


def timeout_dice_roll(
    game: entities.Game, rng: random.Random
) -> teyuna_shared.PlayerAction:
    return teyuna_shared.PlayerAction.model_construct(
        by=game.active_player, due_to_timeout=True, rng_=rng
    )


def timeout_trade_and_build(
    game: entities.Game, rng: random.Random
) -> teyuna_shared.PlayerAction:
    return teyuna_shared.PlayerAction.model_construct(
        by=game.active_player, due_to_timeout=True, rng_=rng
    )


def timeout_first_placement(
    game: entities.Game, rng: random.Random
) -> teyuna_shared.FreePlacementAction:
    return _pick_free_placement(game, rng)


def timeout_second_placement(
    game: entities.Game, rng: random.Random
) -> teyuna_shared.FreePlacementAction:
    return _pick_free_placement(game, rng)


def timeout_move_conquistator(
    game: entities.Game, rng: random.Random
) -> teyuna_shared.MoveConquistatorAction:
    candidates = [
        teyuna_shared.HexLocation(q=hex_tile.q, r=hex_tile.r)
        for hex_tile in game.map
        if teyuna_shared.HexLocation(q=hex_tile.q, r=hex_tile.r)
        != game.conquistator_location
    ]
    location = rng.choice(candidates)
    victims = [
        nick
        for nick, player_state in game.players.items()
        if nick != game.active_player and sum(player_state.resources.values()) > 0
    ]
    from_player = rng.choice(victims) if victims else None
    return teyuna_shared.MoveConquistatorAction.model_construct(
        by=game.active_player,
        due_to_timeout=True,
        q=location.q,
        r=location.r,
        from_player=from_player,
        rng_=rng,
    )


def timeout_discard_resources(
    game: entities.Game, rng: random.Random
) -> teyuna_shared.DiscardResourcesAction:
    nick = next(iter(game.to_discard_resources))
    required = game.to_discard_resources[nick]
    count = _pick_discard(game.players[nick].resources, required, rng)
    return teyuna_shared.DiscardResourcesAction.model_construct(
        by=nick,
        due_to_timeout=True,
        count=count,
        rng_=rng,
    )


def timeout_lobby(
    game: entities.Game, rng: random.Random
) -> teyuna_shared.PlayerAction:
    return teyuna_shared.PlayerAction.model_construct(
        by="", due_to_timeout=True, rng_=rng
    )


def timeout_play_mamo(
    game: entities.Game, rng: random.Random
) -> teyuna_shared.PlayMamoAction:
    resource = rng.choice(list(teyuna_shared.ResourceCard))
    return teyuna_shared.PlayMamoAction.model_construct(
        by=game.active_player,
        due_to_timeout=True,
        resource=resource,
        rng_=rng,
    )


def timeout_play_blessed(
    game: entities.Game, rng: random.Random
) -> teyuna_shared.PlayBlessedAction:
    pool: list[teyuna_shared.ResourceCard] = [
        resource
        for resource in teyuna_shared.ResourceCard
        for _ in range(game.resource_supply[resource])
    ]
    if len(pool) >= 2:
        first, second = rng.sample(pool, 2)
    else:
        resources = list(teyuna_shared.ResourceCard)
        first, second = resources[0], resources[1]
    return teyuna_shared.PlayBlessedAction.model_construct(
        by=game.active_player,
        due_to_timeout=True,
        resources=(first, second),
        rng_=rng,
    )


def timeout_play_pathfinder(
    game: entities.Game, rng: random.Random
) -> teyuna_shared.PlayPathfinderAction:
    player_state = game.players[game.active_player]
    remaining = teyuna_shared.MAX_PATHS - len(player_state.paths)
    legal: list[teyuna_shared.Coordinate] = [
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
    chosen: list[teyuna_shared.Coordinate] = []
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
    return teyuna_shared.PlayPathfinderAction.model_construct(
        by=game.active_player,
        due_to_timeout=True,
        paths=tuple(chosen),
        rng_=rng,
    )


def _pick_free_placement(
    game: entities.Game, rng: random.Random
) -> teyuna_shared.FreePlacementAction:
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
    for terrace in legal_terraces:
        legal_paths = [
            edge
            for edge in game.free_edges
            if _placement.can_add_free_path_at(
                target=edge,
                free_edges=game.free_edges,
                existing_settlements=game.players[
                    game.active_player
                ].settlements.locations(),
                existing_paths=game.players[game.active_player].paths,
                free_vertices=game.free_verticies,
                new_settlement=terrace,
            )
        ]
        if not legal_paths:
            continue
        path = rng.choice(legal_paths)
        return teyuna_shared.FreePlacementAction.model_construct(
            by=game.active_player,
            due_to_timeout=True,
            terrace=terrace,
            path=path,
            rng_=rng,
        )
    raise RuntimeError("No legal free placement available for timeout")


def _pick_discard(
    resources: teyuna_shared.ResourceCount,
    required: int,
    rng: random.Random,
) -> dict[teyuna_shared.ResourceCard, int]:
    pool: list[teyuna_shared.ResourceCard] = [
        resource for resource, amount in resources.items() for _ in range(amount)
    ]
    rng.shuffle(pool)
    count: collections.Counter[teyuna_shared.ResourceCard] = collections.Counter()
    for resource in pool[:required]:
        count[resource] += 1
    return dict(count)
