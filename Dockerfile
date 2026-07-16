FROM debian:bookworm-slim AS builder

LABEL description="410stick unified build environment (qhypstub + lk1st + kernel + pmOS)"

RUN apt-get update && apt-get install -y --no-install-recommends \
    # 鈹€鈹€ lk1st toolchain (arm32 cross-gcc) 鈹€鈹€
    gcc-arm-none-eabi \
    # 鈹€鈹€ qhypstub + kernel toolchain (aarch64 cross-gcc, includes as/ld/objcopy) 鈹€鈹€
    gcc-aarch64-linux-gnu \
    make \
    device-tree-compiler \
    flex \
    bison \
    bc \
    libelf-dev \
    # 鈹€鈹€ pmOS / initramfs 鈹€鈹€
    cpio \
    xz-utils \
    python3 \
    python3-pip \
    # 鈹€鈹€ pmbootstrap extras 鈹€鈹€
    sudo \
    openssh-client \
    ccache \
    patch \
    # 鈹€鈹€ kernel host tools 鈹€鈹€
    gcc \
    libssl-dev \
    # 鈹€鈹€ common 鈹€鈹€
    git \
    wget \
    curl \
    openssl \
    ca-certificates \
    file \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth=1 https://gitlab.com/postmarketOS/pmbootstrap.git /opt/pmbootstrap \
    && ln -s /opt/pmbootstrap/pmbootstrap.py /usr/local/bin/pmbootstrap

WORKDIR /build
