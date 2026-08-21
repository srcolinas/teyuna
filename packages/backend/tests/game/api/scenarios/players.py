import uuid

import fastapi.testclient as testclient

from src.game import entities

from .. import utils
from . import rounds
import teyuna_core


class BasePlayer:
    def __init__(
        self,
        client: testclient.TestClient,
        game_id: uuid.UUID,
        token: str,
    ) -> None:
        self._client = client
        self._game_id = game_id
        self._token = token

    def take_action(
        self, phase: teyuna_core.GamePhaseName, state: entities.Game
    ) -> None:
        rounds.advance_phase(self._client, self._game_id, self._token)


class GreedyBuilder(BasePlayer):
    def __init__(
        self,
        client: testclient.TestClient,
        game_id: uuid.UUID,
        token: str,
    ) -> None:
        super().__init__(client, game_id, token)

    def take_action(
        self, phase: teyuna_core.GamePhaseName, state: entities.Game
    ) -> None:
        match phase:
            case teyuna_core.GamePhaseName.DICE_ROLL:
                rounds.advance_phase(self._client, self._game_id, self._token)
            case teyuna_core.GamePhaseName.TRADE_AND_BUILD:
                if self._try_build_great_terrace(state.players[state.active_player]):
                    return
                if self._try_build_terrace(state):
                    return
                if self._try_build_path(state):
                    return
                rounds.advance_phase(self._client, self._game_id, self._token)

    def _try_build_great_terrace(self, state: entities.Player) -> bool:
        try:
            coordinates = next(
                location
                for location, settlement in state.settlements.items()
                if settlement is teyuna_core.SettlementType.TERRACE
            )
        except StopIteration:
            return False
        success, reason = self._post_settlement(
            teyuna_core.SettlementType.GREAT_TERRACE, coordinates
        )
        if success:
            print(f"Built great terrace at {coordinates}")
            return True
        print(f"Failed to build great terrace at {coordinates}: {reason}")
        return False

    def _try_build_terrace(self, game: entities.Game) -> bool:
        available = game.free_verticies - game.restricted_verticies
        paths = game.players[game.active_player].paths
        for location in available:
            for edge in teyuna_core.edges_adjacent_to_vertex(location):
                if edge in paths:
                    success, reason = self._post_settlement(
                        teyuna_core.SettlementType.TERRACE, location
                    )
                    if success:
                        print(f"Built terrace at {location}")
                        return True
                    print(f"Failed to build terrace at {location}: {reason}")
        print("Failed to build terrace")
        return False

    def _try_build_path(self, game: entities.Game) -> bool:
        player_ = game.players[game.active_player]
        vertices = set(player_.settlements.locations())
        for path in player_.paths:
            vertices.update(teyuna_core.vertices_of_edge(path))
        for vertex in vertices:
            for edge in teyuna_core.edges_adjacent_to_vertex(vertex):
                if edge not in player_.paths and edge in game.free_edges:
                    success, reason = self._post_path(edge)
                    if success:
                        print(f"Built path at {edge}")
                        return True
                    print(f"Failed to build path at {edge}: {reason}")
        return False

    def _post_settlement(
        self,
        item: teyuna_core.SettlementType,
        location: teyuna_core.Coordinate,
    ) -> tuple[bool, str]:
        response = utils.post_action(
            self._client,
            self._game_id,
            {
                "kind": "build_settlement",
                "item": item.value,
                "coordinate": {"q": location.q, "r": location.r, "d": location.d},
            },
            token=self._token,
        )
        if response.status_code == 200:
            return True, ""
        return False, response.text

    def _post_path(self, location: teyuna_core.Coordinate) -> tuple[bool, str]:
        response = utils.post_action(
            self._client,
            self._game_id,
            {
                "kind": "build_path",
                "coordinate": {"q": location.q, "r": location.r, "d": location.d},
            },
            token=self._token,
        )
        if response.status_code == 200:
            return True, ""
        return False, response.text
