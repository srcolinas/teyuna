# Backend

If you haven't contriubuted in a while, you may want to run `make clean` and then `make setup` to get the project up and running.

Always validate code changes with the following three commands:

- `make format`
- `make lint`
- `make test`

Always run `make coverage` to see the test coverage, we should aim for 100% coverage on functions and classes that do not perform IO bound tasks.


## Extra guidelines:

* Don't call directly internal functions from another module or package, if needed we should update the public API to expose the functionality.
* Don't use monkey patching or magic mocks for testing. Use fixtures and dependency injection instead.
* Keep public and main functionality at the top of the module and private functionality at the bottom.