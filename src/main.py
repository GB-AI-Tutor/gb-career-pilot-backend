import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.api.v1.router import api_router
from src.config import settings
from src.database.database import get_supabase_client
from src.rate_limiter import limiter

# Initialize Sentry (if DSN is provided)
if settings.SENTRY_DSN:
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
            profiles_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
        )
        logger.info(f"✅ Sentry initialized for {settings.ENVIRONMENT} environment")
    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize Sentry: {e}")

app = FastAPI(
    title="GB Career Pilot API",
    description="AI-powered university guidance",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# --- LOGURU CONFIGURATION ---
# This automatically creates a 'logs' folder and writes to a file.
# The 'rotation="10 MB"' part ensures the file doesn't get massive and crash your server!
logger.add("logs/app_{time:YYYY-MM-DD}.log", rotation="10 MB", level="INFO")

# 1. --- LOGGING CONFIGURATION ---
logger.add("logs/app_{time:YYYY-MM-DD}.log", rotation="10 MB", level="INFO")


# 2. --- CUSTOM EXCEPTIONS ---
class TutorExceptionError(Exception):
    def __init__(self, status_code: int, error_type: str, message: str, details: str = None):
        self.status_code = status_code
        self.error_type = error_type
        self.message = message
        self.details = details


class DatabaseOfflineError(TutorExceptionError):
    def __init__(self, details: str = "Connection timed out."):
        super().__init__(
            503, "DatabaseError", "The university database is currently offline.", details
        )


# 3. --- EXCEPTION HANDLERS ---
@app.exception_handler(TutorExceptionError)
async def custom_tutor_exception_handler(request: Request, exc: TutorExceptionError):
    logger.warning(f"Known Error: {exc.error_type} - {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "error_type": exc.error_type,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the DANGEROUS details for you, securely in your file 📝
    logger.exception(f"CRASH on {request.url.path}")

    # Send a SAFE message to the student 🛡️
    return JSONResponse(
        status_code=500,
        content={
            "status_code": 500,
            "error_type": "InternalServerError",
            "message": "Something went wrong on our end. Please try again later.",
            "details": "An unexpected error occurred.",  # Replaced str(exc)!
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log the attempt for security monitoring
    logger.warning(f"Validation Failed on {request.url.path} - Data: {exc.errors()}")

    # Extract exactly which field failed and why (e.g., "content": "String should have at most 2000 characters")
    error_details = {str(err["loc"][-1]): err["msg"] for err in exc.errors()}

    return JSONResponse(
        status_code=422,
        content={
            "status_code": 422,
            "error_type": "ValidationError",
            "message": "The information provided was invalid.",
            "details": error_details,
        },
    )


# --- THE LOGGING MIDDLEWARE ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    try:
        # 1. Let the request pass through to your routes (like /chat)
        response = await call_next(request)

        # 2. Stop the stopwatch
        process_time = time.time() - start_time

        # 3. Log the successful request
        logger.info(
            f"[{request.method}] {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Duration: {process_time:.4f}s"
        )

        return response

    except Exception as e:
        # Stop the stopwatch if it crashes!
        process_time = time.time() - start_time

        # logger.exception automatically captures the FULL stack trace! 🐛
        logger.exception(
            f"[{request.method}] {request.url.path} | " f"FAILED after {process_time:.4f}s"
        )
        raise e  # Re-raise the error so the user gets a 500 status code


# Origins which are allowed to access backend API
origins = [
    "http://localhost:5173",
    "https://gb-ai-tutor.vercel.app",
    "https://raqeebs.app/*",
    "https://gb-career-pilot-frontend.vercel.app",
]

frontend_url = settings.FRONTEND_URL.rstrip("/")
if frontend_url and frontend_url not in origins:
    origins.append(frontend_url)

VERCEL_PREVIEW_ORIGIN_REGEX = (
    r"^https://(gb-career-pilot-frontend|gb-ai-tutor)-[a-z0-9-]+\.vercel\.app$"
)


# using Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=VERCEL_PREVIEW_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  # request send by the clients
)


@app.get("/")
async def root():
    return {"message": "GB Career Pilot API", "Status": "Healthy", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/universities")
def universites_data():
    data = get_supabase_client()
    response = data.table("universities").select("*").execute()
    universites_data = response.data

    return universites_data


# @app.get("/users")
# def users():
#     data = get_supabase_client()
#     response = data.table("users").select("*").execute()
#     users = response.data

#     return users

# Register router


app.include_router(api_router, prefix="/api/v1")

# app.include_router(universities.router, prefix="/api", tags=["universities"])
# app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])  # ADD THIS
