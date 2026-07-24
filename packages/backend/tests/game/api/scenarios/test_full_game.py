import pprint

import pytest
import fastapi
import fastapi.testclient as testclient

from src.game import dependencies, repository as repository_module

from .. import utils
from . import config, players, rounds
import teyuna_core


@pytest.mark.slow
def test_greedy_builder_reaches_end_game(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    good_number = 6
    repository = repository_module.InMemoryGameRepository()
    app.dependency_overrides[dependencies.get_repository] = lambda: repository
    app.dependency_overrides[dependencies.random_generator] = lambda: (
        FakeRandomGenerator(good_number // 2)
    )

    game_id, tokens = utils.create_active_game_with_tokens(
        client, nicknames=["player-0", "player-1", "player-2"]
    )
    game = repository.retrieve(game_id)
    phase = game.phase
    game.map = config.overwrite_map(
        source=game.map,
        overwrites={
            teyuna_core.HexLocation(q=0, r=0): (
                teyuna_core.HexType.MOUNTAINS,
                good_number,
            ),
            teyuna_core.HexLocation(q=-1, r=0): (
                teyuna_core.HexType.QUARRIES,
                good_number,
            ),
            teyuna_core.HexLocation(q=1, r=0): (
                teyuna_core.HexType.HIGHLANDS,
                good_number,
            ),
            teyuna_core.HexLocation(q=0, r=-1): (
                teyuna_core.HexType.VALLEYS,
                good_number,
            ),
            teyuna_core.HexLocation(q=1, r=-1): (
                teyuna_core.HexType.JUNGLE,
                good_number,
            ),
            teyuna_core.HexLocation(q=-1, r=1): (
                teyuna_core.HexType.MOUNTAINS,
                good_number,
            ),
            teyuna_core.HexLocation(q=0, r=1): (
                teyuna_core.HexType.QUARRIES,
                good_number,
            ),
            teyuna_core.HexLocation(q=0, r=-2): (teyuna_core.HexType.DESERT, 2),
            teyuna_core.HexLocation(q=-2, r=2): (teyuna_core.HexType.DESERT, 2),
            teyuna_core.HexLocation(q=0, r=2): (teyuna_core.HexType.DESERT, 2),
            teyuna_core.HexLocation(q=2, r=-2): (teyuna_core.HexType.DESERT, 2),
        },
    )
    game.conquistator_location = teyuna_core.HexLocation(q=2, r=-2)
    repository.update(game_id, game)

    first, second, third = client.get(f"/games/{game_id}").json()["turn_order"]

    rounds.add_placement_round(
        client,
        game_id,
        [
            (tokens[first], (0, 0, 0), (0, 0, 0)),
            (tokens[second], (-2, 2, 2), (-2, 2, 2)),
            (tokens[third], (0, -2, 4), (0, -2, 4)),
        ],
    )
    rounds.add_placement_round(
        client,
        game_id,
        [
            (tokens[third], (0, -2, 0), (0, -2, 5)),
            (tokens[second], (-2, 2, 4), (-2, 2, 3)),
            (tokens[first], (0, 0, 2), (0, 0, 1)),
        ],
    )

    bots: dict[str, players.BasePlayer] = {
        first: players.GreedyBuilder(client, game_id, tokens[first]),
        second: players.BasePlayer(client, game_id, tokens[second]),
        third: players.BasePlayer(client, game_id, tokens[third]),
    }
    for turn in range(20):
        game = repository.retrieve(game_id)
        phase = game.phase
        active_player = game.active_player
        while (
            active_player == game.active_player
            and phase is not teyuna_core.GamePhaseName.END_GAME
        ):
            print(f"Turn {turn} - Phase: {phase.value} - Player {active_player}")
            bots[active_player].take_action(phase, game)
            game = repository.retrieve(game_id)
            phase = game.phase

    print("--------------------------------")
    print(f"Exiting loop after {turn + 1} turns")
    pprint.pprint((first, second, third))
    pprint.pprint(phase)
    pprint.pprint(game)
    print("--------------------------------")
    game = client.get(f"/games/{game_id}").json()
    assert game["phase"] == teyuna_core.GamePhaseName.END_GAME.value


class FakeRandomGenerator:
    def __init__(self, value: int) -> None:
        self.value = value

    def randint(self, a: int, b: int) -> int:
        del a, b
        return self.value
