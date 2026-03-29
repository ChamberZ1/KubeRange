# Stage 1: start from official node.js image on Alpine (small linux distro). Name as 'build' for later reference.
# ~170MB needed to build, but final image will be smaller since we only copy built static files to nginx image.
FROM node:20-alpine AS build  
# Node provides the runtime env for the JS tools: npm, Vite, TypeScript compiler, etc.
# We use node to build the code into a servable application, and use nginx to serve it.

# Set working directory in the container to /app. All subsequent commands will run in this directory.
WORKDIR /app
COPY frontend/package*.json ./

# Install dependencies 
RUN npm ci

# copy actual source code (static HTML, CSS, JS) to container and build. Output in /app/dist
COPY frontend/ ./
RUN npm run build

# Stage 2: FRESH start from pre-built Docker nginx image. [software: variant] -  so nginx running on Alpine Linux.
# ~25MB needed to serve final image.
FROM nginx:alpine
# Copy built static files from previous stage to nginx's default html directory. 
# Also copy custom nginx config to override default. 
# Expose port 80 for HTTP traffic.
COPY --from=build /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80

# Final image is nginx + built static files.