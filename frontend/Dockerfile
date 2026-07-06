FROM node:24-slim AS build

WORKDIR /srv/app
COPY package.json package-lock.json ./
# npm ci fails on lockfiles generated on macOS (missing linux-only optional dep
# chains, long-standing npm bug) — npm install fills the gaps deterministically enough.
RUN npm install --no-audit --no-fund

COPY . .
# Nitro build needs >1GB heap; small VPSes hit node's default limit (OOM, exit 134).
ENV NODE_OPTIONS=--max-old-space-size=2048
RUN npm run build

FROM node:24-slim

ENV NODE_ENV=production
WORKDIR /srv/app
COPY --from=build /srv/app/.output ./.output

RUN addgroup --system habitflow && adduser --system --ingroup habitflow habitflow
USER habitflow

EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
