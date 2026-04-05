FROM python:3.12-slim

# Install uv — copies the binary from the official image (fastest method)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# All subsequent commands happen in /app
WORKDIR /app

# Copy dependency files first — Docker caches this layer
# so dependencies only re-install when these files change, not on every code edit
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Now copy the application code
COPY . .

EXPOSE 8000

# CMD runs when the container starts (not during build)
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
