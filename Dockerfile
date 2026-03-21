# 1. Use Bookworm (Stable Debian) to avoid 'Trixie' dependency issues
FROM python:3.11-slim-bookworm

# 2. Copy 'uv' from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# 3. Manually install ONLY the necessary Linux libraries for Chromium
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

COPY requirements.txt .

# 4. Install CPU-only Torch (MAKE SURE torch IS NOT IN requirements.txt!)
RUN uv pip install --system torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 5. Install the rest of the stack
RUN uv pip install --system -r requirements.txt

# 6. Install Chromium WITHOUT '--with-deps'
RUN playwright install chromium

# 7. Finalize and copy code
COPY . .

# 8. Set a default port for local testing, Render will override this automatically
ENV PORT=8000
EXPOSE $PORT

# 9. Use the shell form so $PORT is evaluated dynamically by Render
CMD uvicorn src.main:app --host 0.0.0.0 --port $PORT
