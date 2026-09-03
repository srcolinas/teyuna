# Game Rules

In Teyuna, all players play the role native south american settlers of a new land. You will need to deal with random changes in production of resource and the ocassional appearance of a conquistator.

The map of the land is a collection of hexagons put together, where most hexagones have a particular type and an associated resource:


| Resource | Type      |
| -------- | --------- |
| gold     | mountains |
| stone    | quarries  |
| cotton   | highlands |
| maize    | valleys   |
| wood     | jungle    |


Another type of hexagon is a desert, which doesn't produce any resource. Each hexagon will be assigned a number at the start of the game and will produce resources based on a dice roll on the regular turn structure (the number rolled dictates which hexagon produces resources).

The conquistator starts in the desert, but must be moved any time a 7 is rolled, the player who rolled the 7 decides in which hexagon it should go. Any hexagon with the conquistator, doesn't produce resources. Otherwise, you gain resources from the buildings you have around hexagons when they happen to produce resources.

In your turn, you can place three type of buildings, each with an associated cost and rules of placement:


| Building      | Cost                                  | Rules                                                                                                                                                                |
| ------------- | ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Path          | 1 stone + 1 wood                      | Placed on edges of the hexagons that don't already contain paths and must be next to another path, terrace or great terrace of the same player                       |
| Terrace       | 1 stone + 1 wood + 1 cotton + 1 maize | Placed on vertices of hexagons and next to an existing path and at least two vertices away from any other terrace or great terrace (of any player) in any direction. |
| Great Terrace | 3 gold + 2 maize                      | Can only be placed by replacing an existing terrace                                                                                                                  |


You will also be able to buy wisdom cards at the price of 1 gold + 1 cotton + 1 maize and they have different effects:

- **warrior** — Move the Conquistator (and steal as with a 7)
- **blessing of aluna** — Take 2 resources from the bank
- **wisdom of mamo** — Monopoly: take all cards of one resource from every opponent
- **pathfinder** — Build up to 2 free paths
- **legacy of the elders** — 1 Victory Point

Finally, you can trade resources with the supply or another player as follows (when this can happen depends on turn structure):

- Give 4 resources of a type to the supply and get 1 of your choice (if available) in return.
- If you have a terrace or great terrace in a vertex with a harbour you can trade 2:1 (of a particular resource) or 3:1 (of any resource) instead of 4:1 and depending on the vertex you occupy.
- Players can trade with each other using arbitrary rates.



## Objective

Be the first player to reach **10 Victory Points**. You are awarded points based on your buildings and wisdom cards.

- Each **Terrace** = 1 VP
- Each **Great Terrace** = 2 VP
- Longest Path (5+ continuous paths) = 2 VP
- Largest Army (3+ warriors played) = 2 VP
- **legacy of the elders** wisdom cards = 1 VP each

NOTES:

- Players can only gain victory points during their turn, so it is imposible to have ties in victory points.
- The Longest Path title is awarded to the first player who has 5 or more continous paths. If another player beats the current holder of the title, then they should get the title. If the longest road is broken by an adversary's building, then it is awarded again to the player with the longest road, as long as it has more than 5 and there are no ties. 
- The Longest Army title follows the same logic of assignment as the Longest Path one, except that it requries 3 warrior cards played and there is nothing that can break an army.



## Phases and turn structure

The following is an overview of the phases and their purpose:

1. Lobby -> Wait for players to join a the game
2. Setup -> Perform the initial setup for each player as follows:
  1. **First placement**: going clockwise from the first player, each player places one terrace and one adjacent Path for free; they are placed simultaneusly and next to each other to ensure and comply to the rules of proximity.
  2. **Second placement:** similar to first placement, but start from the last player to the first going counter-clockwise. To kickstart each player's economy, they are awarded the resources provided by the hexagons around the vertex on which the terrace was placed.
3. Regular turn order -> From the first player and going clockwise, the active player performs:
  1. **Dice roll:**
    1. Before the active player roles the dice, they can play a wisdom card, moving the system to **dice play warrior, dice play mamo, dice play blessed or dice play pathfinder**, depending on the wisdom card played.
    2. When the dice is rolled:
      1. If the number is different from 7, resources are awarded to all players who have a building in the vertex of a hex with the number that was just rolled. Then the turn goes to the trade and build phase.
      2. If the number is 7, we move to the **discard resources** phase, where players with more than 7 resource cards must discard half (rounded to the smallest number). Then the game moves to the trade and build phase.
  2. **Trade and build**:
    1. At any point, the active player can play wisdom cards, leading to **trade and build play warrior, trade and build play mamo, trade and biuld play blessed and trade and build play pathfinder**, dependening on the card played.
    2. At any point, they can place paths, terraces and great terraces, subject to the cost and placement rules mentioned above.
    3. At any point, the active palyer can trade with the supply (following the rules above), accept trade proposal from other players or make trade proposals to other players. Only trades with the active player are allowed, so if player A is active, players C and D can't propose trades to each other, nor can they accept trades not tailored to themselves.

All phases have a deadline associated and the server will take an arbitrary legal action on behalf of the player who failed to complete the action in the expected time. For example, if a player fails to define in time what the location of their first terrace and path is, the server will asigned a location at random. If a player performs the advance action, it means to stop waiting for the timelimit and just let the server perform the default action. 