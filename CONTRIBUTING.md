# Contributing

From the repository root, install and validate everything with:

```bash
task setup
task format
task lint
task test
# or
task check
```

Those tasks cover Python packages and the frontend (`apps/frontend`, pnpm).
Pre-commit runs `task format`, `task lint`, and `task test`.

Package-specific guidelines:

| Package | Guide |
| --- | --- |
| Backend | [apps/backend/README.md](apps/backend/README.md) |
| Teyuna core | [packages/teyuna-core/README.md](packages/teyuna-core/README.md) |
| Python SDK | [packages/sdk-python/README.md](packages/sdk-python/README.md) |
| Frontend | [apps/frontend/README.md](apps/frontend/README.md) |

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
