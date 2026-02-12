# 1. Use Bookworm (Stable Debian) to avoid 'Trixie' dependency issues
FROM python:3.11-slim-bookworm

# 2. Copy 'uv' from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# 3. Manually install ONLY the necessary Linux libraries for Chromium
# We remove the problematic fonts and replace them with standard Debian equivalents
RUN apt-get update && apt-get install -y --no-install-recommends \
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
    fonts-liberation \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy and Install CPU-only Torch
COPY requirements.txt .
RUN uv pip install --system torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 5. Install the rest of the stack
RUN uv pip install --system -r requirements.txt

# 6. Install Chromium WITHOUT '--with-deps' (We handled them in Step 3)
RUN playwright install chromium

# 7. Finalize
COPY . .
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]