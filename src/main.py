from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title ="GB Career Pilot API",
    description="AI-powered university guidance",
    version ="0.1.0"
)


origins = [
    "http://localhost:5173",
    "https://gb-ai-tutor.vercel.app",
    "https://gb-career-pilot-frontend.vercel.app"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message":"GB Career Pilot API",
        "Status" : "Healthy",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    return {"status":"healthy"}
