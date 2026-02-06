# Contributing Guidelines

The project is composed of three main parts (each a folder under the root directory):

* The game server `/backend`, written in Python using FastAPI.
* The web browser client `/frontend`, written in TypeScript using React.
* The AI client `/ai_client`, written in Python using Pydantic AI.


Note that we use two languages, make sure you follow the guides for each language.

## Package management

* Use UV (https://docs.astral.sh/uv/) for Python.
* Use NPM (https://docs.npmjs.com/) for TypeScript.

## Quality checks

* For Python, use [mypy](https://mypy.readthedocs.io/en/stable/), [ruff](https://ruff.rs/) and [pytest](https://docs.pytest.org/en/stable/).
* For TypeScript, use [prettier](https://prettier.io/), [eslint](https://eslint.org/) and [jest](https://jestjs.io/).

Code should always pass all quality checks. They can be run with the  `make format`, `make lint`, `make test` and `make check` commands.

## Style guides

Basic style guides:

* For Python: https://google.github.io/styleguide/pyguide.html
* For TypeScript: https://google.github.io/styleguide/tsguide.html

However, anything pointed out by the linters takes precedence.

In addition, we use dependency inversion and dependency injection to allow for easy testing and future extensibility in pieces of code that require connection to external services like databases or APIs.

### Testing

Make sure to isolate testable code (e.g. logic to validate an input or how we extract information from an object to buid another object) as much as possible from non-testable code (e.g. code that makes an API call to OpenAI, a database or a service). Unit tests should be created for every exposed testable code, but make sure you only expose what is really necessary, On the other hand, we write integration tests for non testable code. 