import fastapi.testclient as testclient

from . import utils

_VALID_TERRACE = (0, -1, 2)
_VALID_PATH = (0, -1, 2)


def test_client_supplied_by_and_due_to_timeout_are_ignored(
    client: testclient.TestClient,
) -> None:
    game_id, tokens = utils.create_active_game_with_tokens(client)
    active_player = client.get(f"/games/{game_id}").json()["turn_order"][0]
    other = next(n for n in tokens if n != active_player)

    action = utils.build_free_placement_action(_VALID_TERRACE, _VALID_PATH)
    action["by"] = other
    action["due_to_timeout"] = True

    response = utils.post_action(client, game_id, action, token=tokens[active_player])

    assert response.status_code == 200, response.text
    body = response.json()
    assert "by" not in body["action"]
    assert "due_to_timeout" not in body["action"]
