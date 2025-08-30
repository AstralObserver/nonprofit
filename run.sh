#!/bin/bash

# Check if Hugo is installed
if ! command -v hugo &> /dev/null; then
    echo "Hugo is not installed. Please install Hugo first:"
    echo "Visit: https://gohugo.io/getting-started/installing/"
    exit 1
fi

# Create directories for images if they don't exist
mkdir -p static/images

# Create placeholder images if they don't exist
if [ ! -f static/images/protest-statue.jpg ]; then
    echo "Please add the protest statue image to static/images/protest-statue.jpg"
fi

if [ ! -f static/images/protest-books.jpg ]; then
    echo "Please add the protest books image to static/images/protest-books.jpg"
fi

# Start Hugo server
echo "Starting Take Action Tucson site at http://localhost:1313"
hugo server -D
