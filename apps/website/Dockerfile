# Production Dockerfile for Clerk Frontend
# Multi-stage build: build React app, then serve with nginx

# Build stage
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files for dependency installation
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source files
COPY . .

# Build the React application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
