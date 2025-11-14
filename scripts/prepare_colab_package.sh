#!/bin/bash
# Prepare code package for Colab upload

echo "Creating Colab package..."

# Create temporary directory
mkdir -p /tmp/libro_colab

# Copy necessary files
echo "Copying source files..."
cp -r src /tmp/libro_colab/
cp -r scripts /tmp/libro_colab/
cp -r config /tmp/libro_colab/
cp -r data /tmp/libro_colab/

# Copy specific files
cp requirements.txt /tmp/libro_colab/
cp README.md /tmp/libro_colab/

# Create necessary directories in package
mkdir -p /tmp/libro_colab/logs
mkdir -p /tmp/libro_colab/cache/generations
mkdir -p /tmp/libro_colab/results
mkdir -p /tmp/libro_colab/models

# Create empty __init__.py files
touch /tmp/libro_colab/src/__init__.py
touch /tmp/libro_colab/src/core/__init__.py
touch /tmp/libro_colab/src/utils/__init__.py

# Create zip
cd /tmp
zip -r libro_colab.zip libro_colab/

# Move to current directory
mv libro_colab.zip ~/libro_replication/libro_colab.zip

# Cleanup
rm -rf /tmp/libro_colab

echo "✓ Package created: libro_colab.zip"
echo "  Size: $(du -h ~/libro_replication/libro_colab.zip | cut -f1)"
echo ""
echo "Upload this file to Google Colab!"
