# Use Node.js 18+ for development
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install git for better development experience
RUN apk add --no-cache git

# Copy package files
COPY package*.json ./

# Install dependencies (including dev dependencies for development)
RUN npm ci

# Copy source code
COPY . .

# Expose the development port
EXPOSE 3000

# Set environment to development
ENV NODE_ENV=development

# Default command for development with hot reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]