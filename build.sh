#!/bin/bash
set -e

echo "Installing dependencies with uv..."
uv sync --package megaloader --package megaloader-api --no-dev

echo "Copying megaloader core to api directory..."
cp -r packages/core/megaloader packages/api/

echo "Build completed successfully!"
