git clone https://github.com/GB-AI-Tutor/gb-career-pilot-backend.git

cd gb-career-pilot-backend

python -m pip install uv 

# Create virtual environment
uv venv venv

source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

uv run uvicorn src.main:app --reload
