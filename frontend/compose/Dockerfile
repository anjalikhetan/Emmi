# Use the official Node.js image as the base image
FROM node:18-alpine

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json (if available)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application files
COPY . .

# Expose the port that the Next.js app runs on
EXPOSE 3000

# Set environment variable for development
ENV NODE_ENV=production

# Build the Next.js app
RUN npm run build

# Run the production server
CMD ["npm", "run", "start"]
