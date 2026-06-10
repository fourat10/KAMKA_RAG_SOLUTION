# Use Python 3.12 slim for a smaller image
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies required by PyMuPDF (fitz)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    dumb-init \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first — Docker caches this layer
# so deps are only reinstalled when pyproject.toml changes
COPY pyproject.toml uv.lock ./

# Install all dependencies into the system Python
# --no-cache keeps the image smaller
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy the rest of the backend source code
COPY . .

# Create a non-root user for security
RUN addgroup --gid 1001 --system appgroup && \
    adduser --uid 1001 --system --ingroup appgroup appuser

USER appuser

# Tell HuggingFace to never reach the internet at startup
# The model is served from the mounted cache volume
# ENV TRANSFORMERS_OFFLINE=1
# ENV HF_DATASETS_OFFLINE=1

# Expose the port uvicorn runs on
EXPOSE 8000

# Use dumb-init to handle signals properly (same pattern as your frontend)
ENTRYPOINT ["dumb-init", "--"]

# Start FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
