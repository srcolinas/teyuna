# Architecture

We want the following interaction between the client app (either AI or Human with a browser), to allow the following behavior:

```mermaid
sequenceDiagram    
    Player A->>Game Server: create game
    Game Server-->>Player A: join link for game
    Player A->>Game Server: join game 
    Game Server-->>Player A: game state + private key player A
    Note over Player A,Game Server: Player A initiaes the game and joins
    Player B->>Game Server: join game
    Game Server-->>Player B: game state + private key player B
    Game Server-->>Player A: game state 
    Note over Player B,Player A: Player B joins and Game Server updates state to player A
    Viewer->>Game Server: show game
    Game Server-->>Viewer: game state
    Note over Viewer, Game Server: any viewer gets state of the game.
```

To achieve this we need the following componts:

```mermaid
flowchart LR    
    Frontend -- Backend
    AIs -- Backend
    Backend --Database[(Database)]
```