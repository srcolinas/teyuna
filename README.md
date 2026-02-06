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
- 👥 **Multiplayer Support** - Play with 3-4 players
- 🌐 **Web-Based** - Play in your browser with a beautiful, responsive UI oir simply watch a game in progress.
- 🤖 **AI Opponents** - Challenge AI players powered by LLMs.
- 🔐 **User Accounts** - Track your stats and game history
- 📱 **Real-time Updates** - WebSocket-powered live game state

The AI player is simulated by an AI client (powered by Pydantic AI) written in Python that interacts with the game server via its API, just as the web browser client does. From the server point of view, there is no difference between a human player and an AI player, it is just another client connected to it.

## Playing the game

Start playing the game locally with
```bash
podman compose up
```
It should start a game server and 3 AI clients playing against each other and a web browser for you to sit and watch the game.

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting a pull request.
