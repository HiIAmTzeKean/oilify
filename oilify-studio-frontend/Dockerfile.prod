FROM node:20-alpine AS builder

WORKDIR /app
ENV PATH=/app/node_modules/.bin:$PATH

COPY package*.json ./
RUN npm ci --silent

COPY . .
RUN npm run build

FROM nginx:stable-alpine

# Add curl for health checks
RUN apk add --no-cache curl

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
