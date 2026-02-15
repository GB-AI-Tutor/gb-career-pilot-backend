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

# For local key accessing from .env
uv pip install python-dotenv
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

5. pre commit tester :
```bash

uv pip install pre-commit

```
create file .pre-commit-config.yaml in root of this folder and add this:
```bash
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace  # Cleans up messy spaces
      - id: end-of-file-fixer    # Ensures files end with a newline
      - id: check-yaml           # Validates your .yml files
      - id: check-added-large-files # Prevents pushing huge images

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff                 # Runs the linter
        args: [ --fix ]          # Automatically fixes what it can
      - id: ruff-format          # Runs the formatter
```

Run this:
```bash
uv run pre-commit install
```

This make sure all tests passes everytime you commit locally.

## Project Structure
