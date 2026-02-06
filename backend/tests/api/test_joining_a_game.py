import uuid

import pytest
import fastapi.testclient as testclient


@pytest.mark.parametrize("num_players", [1, 2, 3, 4])
def test(num_players: int, client: testclient.TestClient, game_id: uuid.UUID) -> None:
    # GIVEN: there is a game with the given id
    # WHEN: I send a POST request to join a game, as many times as the number of players

    # THEN: I should receive a 200 status code for each player joining the game
    raise NotImplementedError("Not implemented")


def test_game_joined_provides_player_jwt_token(client: testclient.TestClient, game_id: uuid.UUID) -> None:
    # GIVEN: there is a game with the given id
    # WHEN: I send a POST request to the /games/{game_id}/join endpoint

    # THEN: I should receive a jwt token in the response
    raise NotImplementedError("Not implemented")


def test_400_error_when_joining_with_already_used_username(client: testclient.TestClient, game_id: uuid.UUID) -> None:
    # GIVEN: there is a game with the given id
    # WHEN: I send a POST request to the /games/{game_id}/join endpoint with a username that is already used

    # THEN: I should receive a 400 status code
    raise NotImplementedError("Not implemented")

def tes_400_error_when_there_are_already_4_players(client: testclient.TestClient, game_id: uuid.UUID) -> None:
    # GIVEN: there is a game with the given id
    # WHEN: I send a POST request to the /games/{game_id}/join endpoint with a username that is already used

    # THEN: I should receive a 400 status code
    raise NotImplementedError("Not implemented")


@pytest.fixture
def game_id(client: testclient.TestClient) -> uuid.UUID:
    raise NotImplementedError("Not implemented")
