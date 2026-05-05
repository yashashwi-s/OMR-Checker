FROM ubuntu:22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies for Buildozer and Android SDK
RUN dpkg --add-architecture i386 && \
    apt-get update -qq && \
    apt-get install -y -qq \
    build-essential ccache git libncurses5:i386 libstdc++6:i386 libgtk2.0-0:i386 \
    libpangox-1.0-0:i386 libpangoxft-1.0-0:i386 libidn12:i386 python3 python3-pip \
    python3-setuptools python3-venv unzip zlib1g-dev zlib1g:i386 openjdk-17-jdk \
    curl wget zip sudo cmake libffi-dev libssl-dev autoconf libtool \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install buildozer and cython globally
RUN pip3 install --no-cache-dir --upgrade pip buildozer cython virtualenv

# Create a non-root user (Buildozer heavily discourages running as root)
RUN useradd -m -s /bin/bash kivyuser && echo "kivyuser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
USER kivyuser
WORKDIR /home/kivyuser/app

# Default command
CMD ["/bin/bash"]
