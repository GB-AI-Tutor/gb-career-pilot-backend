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

## Docker Deployment

### Prerequisites
- Docker and Docker Compose installed ([Download](https://www.docker.com/products/docker-desktop))

### Quick Start with Docker

1. Clone environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

2. Build and run with Docker Compose:
```bash
docker-compose up --build
```

The application will be available at: http://localhost:8000

API docs: http://localhost:8000/docs

3. View logs:
```bash
docker-compose logs -f backend
```

4. Stop containers:
```bash
docker-compose down
```

### Docker Commands Reference

**Build image:**
```bash
docker-compose build
```

**Run in background:**
```bash
docker-compose up -d
```

**Run specific service:**
```bash
docker-compose up backend
docker-compose up postgres
```

**Access PostgreSQL:**
```bash
docker-compose exec postgres psql -U postgres -d gb_career_db
```

**Rebuild and restart:**
```bash
docker-compose up --build --force-recreate
```

**Remove everything (including volumes):**
```bash
docker-compose down -v
```

### Environment Variables for Docker

All environment variables should be set in `.env` file. Key variables:
- `GROQ_API_KEY`: Your Groq API key (required)
- `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_ADMIN_KEY`: Supabase credentials (required)
- `BRAVE_SEARCH_API_KEY`: Brave Search API key (for university searches)
- `SECRET_KEY`: JWT secret key (change in production)
- `DB_USER`, `DB_PASSWORD`: PostgreSQL credentials

### Production Deployment

For production:
1. Update `SECRET_KEY` to a strong random value
2. Set `DEBUG=False` in production environment
3. Use environment-specific `.env` files
4. Consider using a reverse proxy (Nginx) in front of the FastAPI app
5. Use managed database services instead of containerized PostgreSQL

## Project Structure
