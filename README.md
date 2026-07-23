# 🏔️ Teyuna - The Lost City

A multiplayer strategy board game celebrating the ancient **Tayrona civilization** of Colombia's Sierra Nevada de Santa Marta.

![Teyuna Banner](https://img.shields.io/badge/Teyuna-The%20Lost%20City-gold?style=for-the-badge)

## 🎮 About the Game

**Teyuna** is a strategy board game inspired by Settlers of Catan, but themed around the Tayrona people who built the magnificent city of Teyuna (Ciudad Perdida) around 800 CE. Compete with 3-4 players to build the most prosperous settlement by gathering resources, constructing buildings, and earning victory points.

### The Tayrona Legacy

The Tayrona were master builders who created an extensive network of stone-paved paths, terraces, and settlements throughout the Sierra Nevada mountains. Their descendants—the Kogi, Arhuaco, Wiwa, and Kankuamo peoples—still inhabit this region, which they consider the "Heart of the World."

Learn the rules of the game in the [rulebook](rulebook.md).

## ✨ Features

- 🎲 **Classic Strategy Gameplay** - Familiar mechanics with original Tayrona theming
- 👥 **Multiplayer Support** - Play with 3-4 players, through UI for humans and API for AIs.
- 📱 **Real-time Updates** - Watch any live game in real time.

From the server point of view, there is no difference between a human player and an AI player, it is just another client connected to it.

## Documentation

| Guide | Description |
| --- | --- |
| [Getting started](docs/getting-started.md) | Run the server and simulate a game |
| [Writing agents](docs/writing-agents.md) | Build and test your own AI agent |
| [SDK reference](docs/sdk-reference.md) | Public Python SDK API |
| [API reference](docs/api-reference.md) | HTTP/SSE overview (details in OpenAPI) |

Interactive OpenAPI docs (when the server is running): http://127.0.0.1:8000/docs

## Playing the game

Assuming you have Docker installed, you can run the game server with:

```bash
docker compose up -d backend
```

This will start the game server.

You can then play against some dummy players or your own AI agents using the `teyuna-simulate` CLI (see below).

## Python SDK

Build AI agents or other clients against the game server with [`teyuna-sdk`](packages/sdk-python/):

```bash
pip install teyuna-sdk
```

See the [SDK README](packages/sdk-python/README.md) for usage, sample agents, and the `teyuna-simulate` CLI.

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting a pull request.
