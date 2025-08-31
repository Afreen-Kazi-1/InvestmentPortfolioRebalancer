# Use an official Node.js runtime as a parent image
FROM node:18-alpine

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json (if available)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the React app for production
RUN npm run build

# Serve the app with Nginx or a simple static server (for production)
# For development, we rely on the `npm start` command in docker-compose.yml
# For a production build, you might use a multi-stage build with Nginx:
# FROM nginx:stable-alpine
# COPY --from=builder /app/build /usr/share/nginx/html
# EXPOSE 80
# CMD ["nginx", "-g", "daemon off;"]

# Expose the port the app runs on
EXPOSE 3000

# Command to run the application in development mode
CMD ["npm", "start"]