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
ENV NODE_ENV=development

# Run the development server
CMD ["npm", "run", "dev"]
