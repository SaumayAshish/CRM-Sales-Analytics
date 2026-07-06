# Multi-stage: build the Vite/React app, then serve the static output
# with nginx -- the Node toolchain never ships in the final image.
FROM node:20-slim AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
# VITE_API_BASE_URL is baked in at build time (Vite env vars are not
# runtime-configurable) -- defaults to the backend's host-published port,
# which is what a browser on the host machine can actually reach when
# running via `docker-compose up`.
ARG VITE_API_BASE_URL=http://localhost:8000/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:1.27-alpine AS runtime

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=5 \
    CMD wget -q --spider http://127.0.0.1:80/ || exit 1

EXPOSE 80
