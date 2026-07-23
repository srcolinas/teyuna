.PHONY: clean setup format lint test check coverage

clean:
	rm -rf node_modules dist coverage
	rm -rf node_modules/.vite node_modules/.tmp
	rm -rf *.tsbuildinfo

setup:
	pnpm install --frozen-lockfile

format:
	pnpm run format
	pnpm run lint

lint:
	pnpm run format:check
	pnpm run lint:check
	pnpm run typecheck

test:
	pnpm run test

check: lint test
	@echo "All checks passed!"

coverage:
	pnpm run coverage
