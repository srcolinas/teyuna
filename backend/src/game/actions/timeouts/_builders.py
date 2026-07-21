import collections
import random

from ... import entities
from .. import _registry
from ..handlers import (
    _first_placement,
    _discard_resources,
    _move_conquistator,
    _placement,
    _play_blessed,
    _play_mamo,
    _play_pathfinder,
)


def timeout_dice_roll(
    game: entities.Game, rng: random.Random
) -> _registry.PlayerAction:
    return _registry.PlayerAction(by=game.active_player, due_to_timeout=True, rng_=rng)


def timeout_trade_and_build(
    game: entities.Game, rng: random.Random
) -> _registry.PlayerAction:
    return _registry.PlayerAction(by=game.active_player, due_to_timeout=True, rng_=rng)


def timeout_first_placement(
    game: entities.Game, rng: random.Random
) -> _first_placement.FreePlacementAction:
    return _pick_free_placement(game, rng)


def timeout_second_placement(
    game: entities.Game, rng: random.Random
) -> _first_placement.FreePlacementAction:
    return _pick_free_placement(game, rng)


def timeout_move_conquistator(
    game: entities.Game, rng: random.Random
) -> _move_conquistator.MoveConquistatorAction:
    candidates = [
        entities.HexLocation(q=hex_tile.q, r=hex_tile.r)
        for hex_tile in game.map
        if entities.HexLocation(q=hex_tile.q, r=hex_tile.r)
        != game.conquistator_location
    ]
    location = rng.choice(candidates)
    victims = [
        nick
        for nick, player_state in game.players.items()
        if nick != game.active_player and sum(player_state.resources.values()) > 0
    ]
    from_player = rng.choice(victims) if victims else None
    return _move_conquistator.MoveConquistatorAction(
        by=game.active_player,
        due_to_timeout=True,
        q=location.q,
        r=location.r,
        from_player=from_player,
        rng_=rng,
    )


def timeout_discard_resources(
    game: entities.Game, rng: random.Random
) -> _discard_resources.DiscardResourcesAction:
    nick = next(iter(game.to_discard_resources))
    required = game.to_discard_resources[nick]
    count = _pick_discard(game.players[nick].resources, required, rng)
    return _discard_resources.DiscardResourcesAction(
        by=nick,
        due_to_timeout=True,
        count=count,
        rng_=rng,
    )


def timeout_lobby(game: entities.Game, rng: random.Random) -> _registry.PlayerAction:
    return _registry.PlayerAction(by="", due_to_timeout=True, rng_=rng)


def timeout_play_mamo(
    game: entities.Game, rng: random.Random
) -> _play_mamo.PlayMamoAction:
    resource = rng.choice(list(entities.ResourceCard))
    return _play_mamo.PlayMamoAction(
        by=game.active_player,
        due_to_timeout=True,
        resource=resource,
        rng_=rng,
    )


def timeout_play_blessed(
    game: entities.Game, rng: random.Random
) -> _play_blessed.PlayBlessedAction:
    pool: list[entities.ResourceCard] = [
        resource
        for resource in entities.ResourceCard
        for _ in range(game.resource_supply[resource])
    ]
    if len(pool) >= 2:
        first, second = rng.sample(pool, 2)
    else:
        resources = list(entities.ResourceCard)
        first, second = resources[0], resources[1]
    return _play_blessed.PlayBlessedAction(
        by=game.active_player,
        due_to_timeout=True,
        resources=(first, second),
        rng_=rng,
    )


def timeout_play_pathfinder(
    game: entities.Game, rng: random.Random
) -> _play_pathfinder.PlayPathfinderAction:
    player_state = game.players[game.active_player]
    remaining = entities.MAX_PATHS - len(player_state.paths)
    legal: list[entities.Coordinate] = [
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
    chosen: list[entities.Coordinate] = []
    owned_paths = set(player_state.paths)
    for edge in legal:
        if len(chosen) >= min(2, remaining):
            break
        # Re-check with paths already chosen in this timeout action.
        provisional = owned_paths | set(chosen)
        if _placement.can_add_free_path_at(
            target=edge,
            free_edges=set(game.free_edges) - set(chosen),
            existing_settlements=player_state.settlements.locations(),
            existing_paths=provisional,
            free_vertices=game.free_verticies,
        ):
            chosen.append(edge)
    return _play_pathfinder.PlayPathfinderAction(
        by=game.active_player,
        due_to_timeout=True,
        paths=tuple(chosen),
        rng_=rng,
    )


def _pick_free_placement(
    game: entities.Game, rng: random.Random
) -> _first_placement.FreePlacementAction:
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
        return _first_placement.FreePlacementAction(
            by=game.active_player,
            due_to_timeout=True,
            terrace=terrace,
            path=path,
            rng_=rng,
        )
    raise RuntimeError("No legal free placement available for timeout")


def _pick_discard(
    resources: entities.ResourceCount,
    required: int,
    rng: random.Random,
) -> entities.ResourceCount:
    pool: list[entities.ResourceCard] = [
        resource for resource, amount in resources.items() for _ in range(amount)
    ]
    rng.shuffle(pool)
    count: entities.ResourceCount = collections.Counter()
    for resource in pool[:required]:
        count[resource] += 1
    return count
