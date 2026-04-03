FROM mcr.microsoft.com/devcontainers/python:3.13

# Install Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv \
    && mv /root/.local/bin/uvx /usr/local/bin/uvx

# Install Just
RUN curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash - --to /usr/local/bin

# Set working directory
WORKDIR /workspace

# Keep container running
CMD ["sleep", "infinity"]
