# Backend

If you haven't contributed in a while, you may want to run `make clean` and then `make setup` to get the project up and running.

Always validate code changes with the following three commands:

- `make format`
- `make lint`
- `make test`

Always run `make coverage` to see the test coverage, we should aim for 100% coverage on functions and classes that do not perform IO bound tasks.

## API

The FastAPI server exposes interactive OpenAPI docs when running:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

A short HTTP/SSE overview for agent authors is in [`docs/api-reference.md`](../../docs/api-reference.md). Game rules are documented in the root [`rulebook.md`](../../rulebook.md).

## Extra guidelines:

* Don't call directly internal functions from another module or package, if needed we should update the public API to expose the functionality.
* Don't use monkey patching or magic mocks for testing. Use fixtures and dependency injection instead.
* Keep public and main functionality at the top of the module and private functionality at the bottom.
