# Contributing

From the repository root, install and validate everything with:

```bash
make setup
make format
make lint
make test
# or
make check
```

Those targets cover Python packages and the frontend (`apps/frontend`, pnpm).
Pre-commit runs `make format`, `make lint`, and `make test`.

Package-specific guidelines:

| Package | Guide |
| --- | --- |
| Backend | [packages/backend/README.md](packages/backend/README.md) |
| Shared core | [packages/shared-core/README.md](packages/shared-core/README.md) |
| Python SDK | [packages/sdk-python/README.md](packages/sdk-python/README.md) |
| Frontend | [apps/frontend/README.md](apps/frontend/README.md) |

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
