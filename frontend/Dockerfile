FROM node:22-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund
COPY frontend ./
ARG AXIA_SITE_URL
ENV AXIA_SITE_URL=${AXIA_SITE_URL}
ENV AXIA_API_URL=http://api:8000
RUN npm run lint && npm run build
FROM node:22-alpine
ENV NODE_ENV=production PORT=3000 HOSTNAME=0.0.0.0
WORKDIR /app
COPY --from=builder --chown=node:node /app ./
USER node
EXPOSE 3000
CMD ["npm","run","start"]
