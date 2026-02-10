# Increase timeout for the first run just in case
export UV_HTTP_TIMEOUT=300

# Step 1: Install the lightweight CPU-only Torch ecosystem
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Step 2: Install the rest of the GB Career Pilot stack
uv pip install -r requirements.txt