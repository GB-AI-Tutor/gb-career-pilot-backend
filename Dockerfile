# Use a lightweight Python 3.11 base image to keep the foundation small
FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables for better performance and logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install essential system dependencies (curl for uv, plus Playwright requirements)
RUN apt-get update && apt-get install -y \
    curl \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Install 'uv' for lightning-fast package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy only requirements first to optimize Docker layer caching
COPY requirements.txt .

# --- CRITICAL: FORCE CPU-ONLY TORCH ---
# This prevents the download of 5GB+ NVIDIA drivers, keeping your image ~1.2GB
RUN uv pip install --system torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install the rest of the stack (FastAPI, Groq, LangChain, etc.)
RUN uv pip install --system -r requirements.txt

# Install Playwright browsers (required since it's in your requirements.txt)
RUN uv run playwright install chromium --with-deps

# Copy the rest of the source code
COPY . .

# Start the FastAPI server on the port Railway expects
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]