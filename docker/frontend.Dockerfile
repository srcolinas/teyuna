# Multi-stage frontend build → static nginx image.
# Build requires VITE_API_URL (browser-reachable backend URL baked into the bundle).

ARG NODE_VERSION=22
ARG PNPM_VERSION=10.28.0

FROM node:${NODE_VERSION}-alpine AS builder

ARG PNPM_VERSION
ARG VITE_API_URL
RUN if [ -z "$VITE_API_URL" ]; then \
      echo "ERROR: VITE_API_URL build-arg is required and must be non-empty" >&2; \
      exit 1; \
    fi
ENV VITE_API_URL=$VITE_API_URL

RUN corepack enable && corepack prepare "pnpm@${PNPM_VERSION}" --activate

WORKDIR /app

COPY apps/frontend/package.json apps/frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY apps/frontend/ ./
RUN pnpm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
