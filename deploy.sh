#!/bin/sh

# Specify balena app name
BALENA_APP_NAME=Exoskeleton

# Go into the frontend directory and build the frontend using npm
cd frontend && npm install && npm run build

# Go back to the root directory
cd ..

# Copy the frontend build to the backend directory
cp -r frontend/build backend/www

# Build the backend using balena-cli
balena push $BALENA_APP_NAME