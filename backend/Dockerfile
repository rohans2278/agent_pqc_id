# One image, two services (uvicorn :8000 and mcp_server.py :8001 — see compose).
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Build toolchain for liboqs (the C library ML-DSA-65 needs).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake git libssl-dev ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Compile and install liboqs (pinned) as a shared library, then refresh the
# linker cache so the `oqs` Python binding can load it at runtime.
RUN git clone --depth 1 --branch 0.15.0 \
        https://github.com/open-quantum-safe/liboqs /tmp/liboqs \
    && cmake -S /tmp/liboqs -B /tmp/liboqs/build \
        -DBUILD_SHARED_LIBS=ON -DOQS_BUILD_ONLY_LIB=ON \
    && cmake --build /tmp/liboqs/build --parallel \
    && cmake --install /tmp/liboqs/build \
    && ldconfig \
    && rm -rf /tmp/liboqs

WORKDIR /app
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Install the pure-Python runtime deps with uv (creates /app/.venv).
COPY pyproject.toml ./
RUN uv sync --no-dev

# The liboqs Python binding (`oqs`), pinned — installed separately because it
# depends on the liboqs C library built above, so it's intentionally not in
# pyproject. Don't re-run `uv sync` after this; it would drop oqs from the venv.
RUN uv pip install git+https://github.com/open-quantum-safe/liboqs-python@0.12.0

COPY . .

EXPOSE 8000 8001
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
