#!/bin/bash
# Setup script for CheckMyTex Docker deployment

set -e  # Exit on error

echo "========================================="
echo "CheckMyTex Docker Setup"
echo "========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed."
    echo "Please install Docker first: https://docs.docker.com/engine/install/"
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "ERROR: Docker Compose is not available."
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ Created .env file"
else
    echo "✓ .env file already exists"
fi

# Stop any running containers
echo ""
echo "Stopping any existing containers..."
docker compose down 2>/dev/null || true

# Build images
echo ""
echo "Building Docker images..."
echo "(This may take a few minutes on first run)"
docker compose build

# Start services
echo ""
echo "Starting services..."
docker compose up -d

# Wait for services to be healthy
echo ""
echo "Waiting for services to start..."
sleep 5

# Check if containers are running
if docker compose ps | grep -q "Up"; then
    echo ""
    echo "========================================="
    echo "✓ Setup complete!"
    echo "========================================="
    echo ""
    echo "Services are running:"
    docker compose ps
    echo ""
    echo "Access CheckMyTex at:"
    echo "  → http://localhost"
    echo ""
    echo "Useful commands:"
    echo "  View logs:        docker compose logs -f"
    echo "  Stop services:    docker compose down"
    echo "  Restart:          docker compose restart"
    echo "  Rebuild:          docker compose up -d --build"
    echo ""
else
    echo ""
    echo "========================================="
    echo "⚠ Warning: Containers may not be running properly"
    echo "========================================="
    echo ""
    echo "Check logs with: docker compose logs"
    echo ""
    docker compose ps
    exit 1
fi
