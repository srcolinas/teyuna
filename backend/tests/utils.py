import contextlib
import datetime
import uuid
from typing import cast

from src import active, player, proposed
from src.active import entities
from src.active.services import phases


def create_game_and_add_players(
    *,
    game_manager: active.services.GameManager | None = None,
    max_players: int = 3,
    players_to_add: int = 3,
    nicknames: list[player.Nickname] | None = None,
) -> uuid.UUID:
    auth = player.PlayerAuthenticationService()
    proposed_repository = proposed.InMemoryProposedGameRepository()
    if game_manager is None:
        game_manager = _stub_game_manager()

    proposed_game_id = proposed_repository.add(
        num_players=max_players,
        expires_at=datetime.datetime.now() + datetime.timedelta(seconds=1),
    ).id

    if nicknames is None:
        nicknames = [f"srcolinas-{i}" for i in range(players_to_add)]

    for i in range(players_to_add - 1):
        proposed.add_player(
            game_id=proposed_game_id,
            nickname=nicknames[i],
            repository=proposed_repository,
            game_manager=game_manager,
            auth=auth,
        )

    result, _ = proposed.add_player(
        game_id=proposed_game_id,
        nickname=nicknames[players_to_add - 1],
        repository=proposed_repository,
        game_manager=game_manager,
        auth=auth,
    )
    result = cast(proposed.PlayerAddedResult, result)
    game = cast(uuid.UUID, result.game)
    return game


@contextlib.contextmanager
def assert_not_raises(ExpectedException):
    try:
        yield

    except ExpectedException:
        raise AssertionError(
            "Did raise exception {0} when it should not!".format(
                repr(ExpectedException)
            )
        )

    except Exception as e:
        raise AssertionError("An unexpected exception {0} raised.".format(repr(e)))


def _stub_game_manager() -> active.services.GameManager:
    class FirstNode(phases.GamePhaseNode):
        def run(self, game: entities.ActiveGame, request: phases.PlayerRequest) -> bool:
            return False

        def on_exit(self, game: entities.ActiveGame) -> phases.GamePhaseName:
            return phases.GamePhaseName.FIRST_PLACEMENT

    return active.services.GameManager(
        {phases.GamePhaseName.FIRST_PLACEMENT: FirstNode()}
    )
