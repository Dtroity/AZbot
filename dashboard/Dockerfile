FROM node:20-alpine AS build

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (dev needed for build)
RUN npm ci

# Copy source code
COPY . .

# API URL в сборке: /api — запросы идут на тот же хост (проксирует nginx)
ARG REACT_APP_API_URL=/api
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Build (limit Node heap to avoid OOM on low-RAM VPS; increase to 4096 if server has 4GB+ RAM)
RUN NODE_OPTIONS="--max-old-space-size=2048" npm run build

# Production stage
FROM nginx:alpine
RUN apk add --no-cache curl

# Copy built application
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 3000

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
