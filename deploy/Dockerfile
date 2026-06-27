FROM debian:bookworm-slim AS builder

# Install live-build and build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    live-build \
    git \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
    python3-cryptography \
    python3-prompt-toolkit \
    isolinux \
    syslinux-utils \
    xorriso \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Clone the multiboot-usb source
ARG SOURCE_URL=https://github.com/mrmichaelmoro/multiboot-usb.git
ARG SOURCE_REF=main
RUN git clone --depth 1 --branch ${SOURCE_REF} ${SOURCE_URL} multiboot-usb

# Install multiboot-usb into the live system
RUN cd multiboot-usb && \
    python3 -m pip install --no-cache-dir -e . && \
    cp -r multiboot_usb/grub /usr/share/multiboot-usb/grub

# Copy live-build config
COPY live-build-config/ config/

# Copy first-boot hook
COPY hooks/normal/ config/hooks/normal/

# Copy custom package list
COPY package-lists/ config/package-lists/

# Build the ISO
RUN lb build 2>&1 | tee /build/build.log

# Extract the ISO to a known location for easy retrieval
RUN cp live-image-amd64.hybrid.iso /build/multiboot-usb-live.iso

# Final stage — just the ISO
FROM scratch AS export
COPY --from=builder /build/multiboot-usb-live.iso /
