#!/bin/bash
# Build the multiboot-usb live ISO
# Usage: bash deploy/build-iso.sh [source_url] [source_ref]
set -euo pipefail

SOURCE_URL="${1:-https://github.com/mrmichaelmoro/multiboot-usb.git}"
SOURCE_REF="${2:-main}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_FILE="${SCRIPT_DIR}/../multiboot-usb-live.iso"

echo "=== multiboot-usb ISO Builder ==="
echo "Source: ${SOURCE_URL}@${SOURCE_REF}"
echo "Output: ${OUTPUT_FILE}"
echo ""

# Check Docker is available
if ! command -v docker &>/dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker first."
    exit 1
fi

# Build the Docker image
echo "[1/3] Building Docker image..."
docker build \
    --build-arg SOURCE_URL="${SOURCE_URL}" \
    --build-arg SOURCE_REF="${SOURCE_REF}" \
    -t multiboot-usb-iso \
    -f "${SCRIPT_DIR}/Dockerfile" \
    "${SCRIPT_DIR}/.."

# Run container to extract ISO
echo "[2/3] Extracting ISO from container..."
CONTAINER_ID=$(docker create multiboot-usb-iso)
docker cp "${CONTAINER_ID}:/build/multiboot-usb-live.iso" "${OUTPUT_FILE}"
docker rm "${CONTAINER_ID}" >/dev/null

echo "[3/3] Done!"
echo ""
echo "ISO built successfully:"
ls -lh "${OUTPUT_FILE}"
echo ""
echo "To test in VM:"
echo "  qemu-system-x86_64 -cdrom ${OUTPUT_FILE} -m 512M -boot d"
echo ""
echo "To write to USB:"
echo "  sudo dd if=${OUTPUT_FILE} of=/dev/sdX bs=4M status=progress conv=fsync"
