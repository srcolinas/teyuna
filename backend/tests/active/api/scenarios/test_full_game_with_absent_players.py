import os
import time
import pprint

import pytest
import fastapi
import fastapi.testclient as testclient

from src import main, settings
from src.active import actions, dependencies, entities, repository as repository_module

from .. import utils
from . import config, players, rounds


@pytest.mark.slow
def test_greedy_builder_reaches_end_game(
    app: fastapi.FastAPI,
    client: testclient.TestClient,
) -> None:
    good_number = 6
    repository = repository_module.InMemoryActiveGameRepository()
    app.dependency_overrides[dependencies.get_repository] = lambda: repository
    app.dependency_overrides[dependencies.random_generator] = (
        lambda: FakeRandomGenerator(good_number // 2)
    )

    game_id, tokens = utils.create_active_game_with_tokens(
        client, nicknames=["player-0", "player-1", "player-2"]
    )
    stored = repository.retrieve(game_id)
    game, phase = stored.game, stored.phase
    game.map = config.overwrite_map(
        source=game.map,
        overwrites={
            entities.HexLocation(q=0, r=0): (entities.HexType.MOUNTAINS, good_number),
            entities.HexLocation(q=-1, r=0): (entities.HexType.QUARRIES, good_number),
            entities.HexLocation(q=1, r=0): (entities.HexType.HIGHLANDS, good_number),
            entities.HexLocation(q=0, r=-1): (entities.HexType.VALLEYS, good_number),
            entities.HexLocation(q=1, r=-1): (entities.HexType.JUNGLE, good_number),
            entities.HexLocation(q=-1, r=1): (entities.HexType.MOUNTAINS, good_number),
            entities.HexLocation(q=0, r=1): (entities.HexType.QUARRIES, good_number),
            entities.HexLocation(q=0, r=-2): (entities.HexType.DESERT, 2),
            entities.HexLocation(q=-2, r=2): (entities.HexType.DESERT, 2),
            entities.HexLocation(q=0, r=2): (entities.HexType.DESERT, 2),
            entities.HexLocation(q=2, r=-2): (entities.HexType.DESERT, 2),
        },
    )
    game.conquistator_location = entities.HexLocation(q=2, r=-2)
    repository.update(game_id, game, phase, phase_deadline=stored.phase_deadline)

    first, second, third = client.get(f"/active-games/{game_id}").json()["turn_order"]

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
    bot = players.GreedyBuilder(client, game_id, tokens[first])

    for turn in range(20):
        stored = repository.retrieve(game_id)
        while (
            first != stored.game.active_player
            and stored.phase is not actions.GamePhaseName.END_GAME
        ):
            print(
                f"Turn {turn} - Phase: {stored.phase.value} - "
                f"Player {stored.game.active_player} - Waiting for {first}"
            )
            time.sleep(0.05)
            stored = repository.retrieve(game_id)

        while (
            first == stored.game.active_player
            and stored.phase is not actions.GamePhaseName.END_GAME
        ):
            print(
                f"Turn {turn} - Phase: {stored.phase.value} - "
                f"Player {stored.game.active_player}"
            )
            bot.take_action(stored.phase, stored.game)
            stored = repository.retrieve(game_id)
        if stored.phase is actions.GamePhaseName.END_GAME:
            break

    print("--------------------------------")
    print(f"Exiting loop after {turn + 1} turns")
    pprint.pprint((first, second, third))
    pprint.pprint(stored.phase)
    pprint.pprint(stored.game)
    print("--------------------------------")
    game = client.get(f"/active-games/{game_id}").json()
    assert game["phase"] == actions.GamePhaseName.END_GAME.value


_TIMEOUT_ENV = {
    "TEYUNA_FIRST_PLACEMENT_TIMEOUT": "PT0.2S",
    "TEYUNA_SECOND_PLACEMENT_TIMEOUT": "PT0.2S",
    "TEYUNA_DICE_ROLL_TIMEOUT": "PT0.2S",
    "TEYUNA_DISCARD_RESOURCES_TIMEOUT": "PT0.2S",
    "TEYUNA_MOVE_CONQUISTATOR_TIMEOUT": "PT0.2S",
    "TEYUNA_DICE_PLAY_WARRIOR_TIMEOUT": "PT0.2S",
    "TEYUNA_DICE_PLAY_MAMO_TIMEOUT": "PT0.2S",
    "TEYUNA_DICE_PLAY_BLESSED_TIMEOUT": "PT0.2S",
    "TEYUNA_DICE_PLAY_PATHFINDER_TIMEOUT": "PT0.2S",
    "TEYUNA_TRADE_AND_BUILD_TIMEOUT": "PT0.2S",
    "TEYUNA_TRADE_AND_BUILD_PLAY_WARRIOR_TIMEOUT": "PT0.2S",
    "TEYUNA_TRADE_AND_BUILD_PLAY_MAMO_TIMEOUT": "PT0.2S",
    "TEYUNA_TRADE_AND_BUILD_PLAY_BLESSED_TIMEOUT": "PT0.2S",
    "TEYUNA_TRADE_AND_BUILD_PLAY_PATHFINDER_TIMEOUT": "PT0.2S",
    "TEYUNA_TIMEOUT_POLL_INTERVAL": "PT0.05S",
}


@pytest.fixture
def setupenvars():
    previous = {key: os.environ.get(key) for key in _TIMEOUT_ENV}
    os.environ.update(_TIMEOUT_ENV)
    settings.settings.cache_clear()
    dependencies.get_actions_registry.cache_clear()
    yield
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    settings.settings.cache_clear()
    dependencies.get_actions_registry.cache_clear()


@pytest.fixture
def app(setupenvars) -> fastapi.FastAPI:
    return main.create_app()


class FakeRandomGenerator:
    def __init__(self, value: int) -> None:
        self.value = value

    def randint(self, a: int, b: int) -> int:
        del a, b
        return self.value
