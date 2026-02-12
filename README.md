# GB Career Pilot - Backend

FastAPI backend with Groq AI integration for university guidance.

## Setup

1. Create virtual environment:
```bash
python -m pip install uv # Windows
```

2. Install dependencies:
```bash
# 1. Force install the small CPU version of Torch first
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 2. Now install the rest of your requirements
uv pip install -r requirements.txt
```

3. Copy environment variables:
```bash
copy .env.example .env
# Edit .env with your API keys
```

4. Run development server:
```bash
uvicorn src.main:app --reload
```

API docs: http://localhost:8000/docs

## Project Structure