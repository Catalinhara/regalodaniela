FROM node:18-slim

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install --verbose

# Copy source
COPY . .

# Expose port
EXPOSE 5173

# Build and serve
RUN npm run build
RUN npm install -g serve
CMD ["serve", "-s", "dist", "-l", "5173"]
