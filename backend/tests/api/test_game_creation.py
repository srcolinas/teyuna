import fastapi.testclient as testclient


def test_game_is_created_successfully(client: testclient.TestClient) -> None:
    # GIVEN: I send a POST request to the /games endpoint

    # THEN: I should receive a 201 status code
    raise NotImplementedError("Not implemented")

def test_game_created_doesnnot_have_an_active_player(client: testclient.TestClient) -> None:
    # GIVEN: I send a POST request to the /games endpoint

    # THEN: I should receive a game with no active player
    raise NotImplementedError("Not implemented")


def test_game_created_provides_id(client: testclient.TestClient) -> None:
    # GIVEN: I send a POST request to the /games endpoint

    # THEN: I should receive a game id (using UUID4 format) in the response
    raise NotImplementedError("Not implemented")


def test_game_created_provides_hexes_with_right_locations(client: testclient.TestClient) -> None:
    # GIVEN: I send a POST request to the /games endpoint

    # THEN: I should receive a list of hexes in the response, so that
    # each has unique location within the hex grid of 25-1 non dessert hexes.
    raise NotImplementedError("Not implemented")

def test_game_created_with_right_ammount_of_hexes_per_type(client: testclient.TestClient) -> None:
    # GIVEN: I send a POST request to the /games endpoint

    # THEN: I should receive a list of hexes in the response, so that
    # there are the right amount of hexes per type.
    raise NotImplementedError("Not implemented")

def test_game_created_provides_hexes_with_right_numbers(client: testclient.TestClient) -> None:
    # GIVEN: I send a POST request to the /games endpoint

    # THEN: I should receive a list of hexes in the response, so that
    # the numbers in the hexes are correct.
    raise NotImplementedError("Not implemented")

def test_game_created_has_empty_player_list(client: testclient.TestClient) -> None:
    # GIVEN: I send a POST request to the /games endpoint

    # THEN: I should receive a game with no players
    raise NotImplementedError("Not implemented")


def test_game_created_with_conquistator_and_dessert_in_same_location(client: testclient.TestClient) -> None:
    # GIVEN: I send a POST request to the /games endpoint

    # THEN: I should receive a game with the conquistator and dessert in the same location
    raise NotImplementedError("Not implemented")


def test_game_created_with_dessert_location_different_from_any_hex_location(client: testclient.TestClient) -> None:
    # GIVEN: I send a POST request to the /games endpoint

    # THEN: I should receive a game with the dessert in a location different from any hex location
    raise NotImplementedError("Not implemented")
    
    