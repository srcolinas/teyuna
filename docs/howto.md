# How to play

The game is meant to be played through the its REST API. This document complements the API, which can be studied from `/openapi.json` and `/docs`. 

## Joining a game

Once a game is created, players wait for the expected number of players to join before they can take any action. To join a game, you send a `POST` request to `/games/{id}/players` with a nickname of choice in your payload (e.g `{"nickname": "srcolinas"}`); you will be given an object representing the state of the game and a token that you must use to identify yourself with the backend when performing an action or retrieving your hand. 

## Game state

There is a public game state that you can retrieve with a `GET` request to `/games/{id}` and it will tell you, among other things, where are the buildins already played and which vertices, the turn oder, the current phase of the game, where are some harbours, etc., you can check all returned fields from `/openapi.json` and `/docs`. 

The object will also tell you information about players, but some of that information is hiden and it is only available to them, like the specific resources they hold and the wisdom cards they have not played. Any player can keep track of their own hand based on production upon dice roll and the wisdom cards they buy, but a player can also retrieve their own hand if they make a `GET` request to `/games/{id}/hand` using the token given upon authentication.

## Board map

Read more about the board map in the [board](board.md) document.


## Phase → action map

Exact `Game.phase` strings:


| Phase                                                      | Who acts                                   | Legal `kind` values                                                                                                                                 |
| ---------------------------------------------------------- | ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `lobby`                                                    | —                                          | No player actions (join only)                                                                                                                       |
| `first placement`                                          | Active (`turn_order[0]`)                   | `free_placement`, `advance`                                                                                                                         |
| `second placement`                                         | Active                                     | `free_placement`, `advance`                                                                                                                         |
| `dice roll`                                                | Active                                     | `advance` (roll), `play_wisdom_card`                                                                                                                |
| `discard resources`                                        | Players listed in `to_discard_resources`   | `discard_resources` only                                                                                                                            |
| `move conquistator`                                        | Active                                     | `move_conquistator`, `advance`                                                                                                                      |
| `dice play warrior` / `trade and build play warrior`       | Active                                     | `move_conquistator`, `advance`                                                                                                                      |
| `dice play mamo` / `trade and build play mamo`             | Active                                     | `play_mamo`, `advance`                                                                                                                              |
| `dice play blessed` / `trade and build play blessed`       | Active                                     | `play_blessed`, `advance`                                                                                                                           |
| `dice play pathfinder` / `trade and build play pathfinder` | Active                                     | `play_pathfinder`, `advance`                                                                                                                        |
| `trade and build`                                          | Active; accept trade by target             | `build_settlement`, `build_path`, `buy_wisdom_card`, `propose_trade`, `accept_trade`, `trade_with_supply`, `play_wisdom_card`, `advance` (end turn) |
| `end game`                                                 | —                                          | Stop                                                                                                                                                |


Additionally, you can send messages to other player with a `POST` request to `/games/{id}/messages`. All effects of acctions taken by any player, as well as other sever events can be read from the stream at `/games/{id}/events`.



### Sample payloads for actions


#### advance

```json
{ "kind": "advance" }
```


#### free_placement

```json
{
  "kind": "free_placement",
  "terrace": { "q": 0, "r": -1, "d": 2 },
  "path": { "q": 0, "r": -1, "d": 2 }
}
```

Omit `terrace` / `path` (or use `advance`) for a server-chosen legal placement.

#### discard_resources

```json
{
  "kind": "discard_resources",
  "count": { "wood": 2, "gold": 2 }
}
```

Totals in `count` must equal your entry in `to_discard_resources`.

#### move_conquistator

```json
{
  "kind": "move_conquistator",
  "q": 1,
  "r": -1,
  "from_player": "bob"
}
```

`from_player` is optional (steal target adjacent to the destination hex).

#### play_wisdom_card

```json
{ "kind": "play_wisdom_card", "card": "warrior" }
```

Card strings: `warrior`, `blessing of aluna`, `wisdom of mamo`, `pathfinder`, `legacy of the elders`.

#### play_mamo / play_blessed / play_pathfinder

```json
{ "kind": "play_mamo", "resource": "wood" }
```

```json
{ "kind": "play_blessed", "resources": ["gold", "maize"] }
```

```json
{
  "kind": "play_pathfinder",
  "paths": [
    { "q": 0, "r": 0, "d": 1 },
    { "q": 0, "r": 0, "d": 2 }
  ]
}
```



#### build_settlement / build_path / buy_wisdom_card

Building types: `terrace`, `great terrace`. Paths use edges.

```json
{
  "kind": "build_settlement",
  "item": "terrace",
  "coordinate": { "q": 0, "r": 0, "d": 0 }
}
```

```json
{
  "kind": "build_path",
  "coordinate": { "q": 0, "r": 0, "d": 1 }
}
```

```json
{ "kind": "buy_wisdom_card" }
```



#### Trades

```json
{
  "kind": "propose_trade",
  "offer": { "gold": 1 },
  "request": { "stone": 1 },
  "to": ["bob"]
}
```

```json
{ "kind": "accept_trade", "id": "00000000-0000-0000-0000-000000000001" }
```

```json
{
  "kind": "trade_with_supply",
  "offers": "gold",
  "requests": "stone"
}
```
