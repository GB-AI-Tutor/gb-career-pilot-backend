# GB AI Tutor - Complete Backend GitHub Issues
## All Issues for Solo Backend Development

**Total Issues:** 45+
**Timeline:** 4 weeks (backend only)
**Tech Stack:** FastAPI, PostgreSQL (Supabase), Groq API

---

## 🏗️ PHASE 1: PROJECT SETUP (Week 1, Days 1-2)

### Issue #1: Initialize FastAPI Project Structure
**Priority:** 🔴 Critical
**Time:** 2 hours
**Labels:** setup, backend

**Description:**
Set up the basic FastAPI project structure with proper folder organization.

**Acceptance Criteria:**
- [ ] Create virtual environment with Python 3.11+
- [ ] Install FastAPI, uvicorn, and basic dependencies
- [ ] Create folder structure:
  ```
  backend/
  ├── src/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── config.py
  │   ├── routers/
  │   ├── models/
  │   ├── schemas/
  │   ├── database.py
  │   └── utils/
  ├── tests/
  ├── .env.example
  ├── .gitignore
  ├── requirements.txt
  └── README.md
  ```
- [ ] Create basic FastAPI app in main.py
- [ ] Add health check endpoint
- [ ] Server runs successfully

**Tasks:**
- Initialize git repository
- Create .gitignore (exclude .env, venv, __pycache__)
- Create requirements.txt with initial dependencies
- Write basic README with setup instructions

---

### Issue #2: Configure Environment Variables
**Priority:** 🔴 Critical
**Time:** 1 hour
**Labels:** setup, config

**Description:**
Set up environment configuration using python-dotenv.

**Acceptance Criteria:**
- [ ] Install python-dotenv
- [ ] Create .env.example with all required variables
- [ ] Create config.py to load environment variables
- [ ] Add validation for required env vars
- [ ] Document each environment variable

**Environment Variables:**
```
# .env.example
DATABASE_URL=postgresql://user:password@localhost:5432/gb_tutor
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_key_here
JWT_SECRET_KEY=your_secret_key
GROQ_API_KEY=your_groq_key
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:5173
```

---

### Issue #3: Set Up PostgreSQL Database Connection
**Priority:** 🔴 Critical
**Time:** 2 hours
**Labels:** database, setup

**Description:**
Connect to Supabase PostgreSQL database.

**Acceptance Criteria:**
- [ ] Create Supabase account and project
- [ ] Install supabase-py client
- [ ] Create database.py with connection logic
- [ ] Test connection with simple query
- [ ] Add connection error handling
- [ ] Create get_db() dependency function

**Files to Create:**
- src/database.py

---

### Issue #4: Set Up CORS Middleware
**Priority:** 🔴 Critical
**Time:** 30 minutes
**Labels:** security, setup

**Description:**
Configure CORS to allow frontend requests.

**Acceptance Criteria:**
- [ ] Add CORS middleware to main.py
- [ ] Allow localhost:5173 (Vite dev server)
- [ ] Configure allowed methods (GET, POST, PUT, DELETE)
- [ ] Configure allowed headers
- [ ] Test with browser fetch request

---

### Issue #5: Create API Versioning Structure
**Priority:** 🟡 Medium
**Time:** 1 hour
**Labels:** architecture

**Description:**
Set up API versioning (e.g., /api/v1/).

**Acceptance Criteria:**
- [ ] Create /api/v1 prefix
- [ ] Organize routers under versioned path
- [ ] Update health check to show API version
- [ ] Document versioning strategy in README

---

## 🔐 PHASE 2: AUTHENTICATION SYSTEM (Week 1, Days 3-5)

### Issue #6: Design User Database Schema
**Priority:** 🔴 Critical
**Time:** 2 hours
**Labels:** database, authentication

**Description:**
Design the users table schema.

**Acceptance Criteria:**
- [ ] Create SQL migration for users table
- [ ] Include fields: id, email, password_hash, full_name, phone, fsc_percentage, city, field_of_interest, created_at, updated_at
- [ ] Add unique constraint on email
- [ ] Add indexes on email and city
- [ ] Create updated_at trigger
- [ ] Run migration in Supabase

**SQL Migration:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    fsc_percentage DECIMAL(5,2) CHECK (fsc_percentage >= 0 AND fsc_percentage <= 100),
    city VARCHAR(100),
    field_of_interest VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

### Issue #7: Create User Pydantic Models (Schemas)
**Priority:** 🔴 Critical
**Time:** 1.5 hours
**Labels:** models, authentication

**Description:**
Create Pydantic models for user registration, login, and responses.

**Acceptance Criteria:**
- [ ] Create schemas/user.py
- [ ] Define UserRegister schema (email, password, full_name, etc.)
- [ ] Define UserLogin schema (email, password)
- [ ] Define UserResponse schema (exclude password_hash)
- [ ] Define Token schema (access_token, token_type, user)
- [ ] Add field validation (email format, password strength)
- [ ] Add docstrings to all models

**Models to Create:**
- UserRegister
- UserLogin
- UserResponse
- UserUpdate
- Token

---

### Issue #8: Implement Password Hashing
**Priority:** 🔴 Critical
**Time:** 1 hour
**Labels:** security, authentication

**Description:**
Implement secure password hashing with bcrypt.

**Acceptance Criteria:**
- [ ] Install passlib[bcrypt]
- [ ] Create utils/security.py
- [ ] Implement hash_password() function
- [ ] Implement verify_password() function
- [ ] Handle bcrypt 72-byte limit
- [ ] Write unit tests for password functions

**Functions:**
```python
def hash_password(password: str) -> str:
    # Hash password with bcrypt
    pass

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Verify password against hash
    pass
```

---

### Issue #9: Implement JWT Token Generation
**Priority:** 🔴 Critical
**Time:** 2 hours
**Labels:** security, authentication

**Description:**
Implement JWT token creation and verification.

**Acceptance Criteria:**
- [ ] Install python-jose[cryptography]
- [ ] Create create_access_token() function
- [ ] Create decode_token() function
- [ ] Set token expiration (7 days)
- [ ] Include user_id in token payload
- [ ] Handle token expiration errors
- [ ] Write unit tests

**Functions:**
```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    pass

def decode_token(token: str) -> dict:
    pass
```

---

### Issue #10: Create User Registration Endpoint
**Priority:** 🔴 Critical
**Time:** 3 hours
**Labels:** authentication, endpoint

**Description:**
Implement POST /api/v1/auth/register endpoint.

**Acceptance Criteria:**
- [ ] Create routers/auth.py
- [ ] Implement registration logic
- [ ] Check if email already exists
- [ ] Hash password before storing
- [ ] Save user to database
- [ ] Generate JWT token
- [ ] Return token and user data
- [ ] Add error handling (duplicate email, validation errors)
- [ ] Write integration tests

**Endpoint:** `POST /api/v1/auth/register`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe",
  "phone": "+92 300 1234567",
  "fsc_percentage": 85.5,
  "city": "Islamabad",
  "field_of_interest": "Computer Science"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    ...
  }
}
```

---

### Issue #11: Create User Login Endpoint
**Priority:** 🔴 Critical
**Time:** 2 hours
**Labels:** authentication, endpoint

**Description:**
Implement POST /api/v1/auth/login endpoint.

**Acceptance Criteria:**
- [ ] Implement login logic
- [ ] Verify email exists
- [ ] Verify password matches
- [ ] Generate JWT token on success
- [ ] Return token and user data
- [ ] Add error handling (wrong credentials)
- [ ] Write integration tests

**Endpoint:** `POST /api/v1/auth/login`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

---

### Issue #12: Create Get Current User Endpoint
**Priority:** 🔴 Critical
**Time:** 2 hours
**Labels:** authentication, endpoint

**Description:**
Implement GET /api/v1/auth/me endpoint (protected route).

**Acceptance Criteria:**
- [ ] Create get_current_user() dependency
- [ ] Extract token from Authorization header
- [ ] Decode and verify token
- [ ] Fetch user from database
- [ ] Return user data
- [ ] Handle invalid/expired tokens
- [ ] Write integration tests

**Endpoint:** `GET /api/v1/auth/me`

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

### Issue #13: Create Update User Profile Endpoint
**Priority:** 🟡 Medium
**Time:** 2 hours
**Labels:** authentication, endpoint

**Description:**
Implement PUT /api/v1/auth/me endpoint.

**Acceptance Criteria:**
- [ ] Allow updating: full_name, phone, fsc_percentage, city, field_of_interest
- [ ] Do NOT allow updating email or password (separate endpoints)
- [ ] Validate updated fields
- [ ] Return updated user data
- [ ] Write tests

**Endpoint:** `PUT /api/v1/auth/me`

---

### Issue #14: Create Logout Endpoint
**Priority:** 🟢 Low
**Time:** 1 hour
**Labels:** authentication, endpoint

**Description:**
Implement POST /api/v1/auth/logout endpoint.

**Acceptance Criteria:**
- [ ] Return success message
- [ ] Document that client must delete token
- [ ] (Optional) Add token blacklist if time permits

**Endpoint:** `POST /api/v1/auth/logout`

---

### Issue #15: Write Authentication Tests
**Priority:** 🔴 Critical
**Time:** 3 hours
**Labels:** testing, authentication

**Description:**
Write comprehensive tests for all auth endpoints.

**Acceptance Criteria:**
- [ ] Test user registration (success case)
- [ ] Test registration with duplicate email (error case)
- [ ] Test login (success case)
- [ ] Test login with wrong password (error case)
- [ ] Test get current user with valid token
- [ ] Test get current user with invalid token
- [ ] Test update profile
- [ ] Achieve >80% code coverage on auth module

**Test Cases:**
- test_register_success()
- test_register_duplicate_email()
- test_register_invalid_email()
- test_login_success()
- test_login_wrong_password()
- test_login_nonexistent_user()
- test_get_current_user()
- test_update_profile()

---

## 🏫 PHASE 3: UNIVERSITIES DATABASE (Week 1-2, Days 6-10)

### Issue #16: Design Universities Database Schema
**Priority:** 🔴 Critical
**Time:** 2 hours
**Labels:** database

**Description:**
Design schema for universities, programs, and related tables.

**Acceptance Criteria:**
- [ ] Create universities table
- [ ] Create programs table (linked to universities)
- [ ] Create admission_requirements table
- [ ] Add proper foreign keys
- [ ] Add indexes for search optimization
- [ ] Run migrations in Supabase

**Schema:**
```sql
CREATE TABLE universities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    short_name VARCHAR(50),
    city VARCHAR(100) NOT NULL,
    province VARCHAR(50),
    type VARCHAR(50), -- Public/Private
    website VARCHAR(255),
    ranking INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE programs (
    id SERIAL PRIMARY KEY,
    university_id INTEGER REFERENCES universities(id),
    name VARCHAR(255) NOT NULL,
    degree_level VARCHAR(50), -- Bachelors/Masters
    field VARCHAR(100) NOT NULL,
    duration_years INTEGER,
    tuition_fee_per_year DECIMAL(10,2),
    total_seats INTEGER,
    merit_cutoff DECIMAL(5,2),
    entrance_test VARCHAR(100), -- ECAT, MDCAT, NTS, etc.
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### Issue #17: Create University Pydantic Models
**Priority:** 🔴 Critical
**Time:** 1.5 hours
**Labels:** models

**Description:**
Create Pydantic models for universities and programs.

**Acceptance Criteria:**
- [ ] Create schemas/university.py
- [ ] Define UniversityBase schema
- [ ] Define UniversityCreate schema
- [ ] Define UniversityResponse schema
- [ ] Define ProgramBase schema
- [ ] Define ProgramResponse schema
- [ ] Add validation for all fields

---

### Issue #18: Seed Universities Data (Manual Entry)
**Priority:** 🔴 Critical
**Time:** 4 hours
**Labels:** database, data

**Description:**
Manually add 20-30 universities with their programs.

**Acceptance Criteria:**
- [ ] Research and collect data for 20+ universities
- [ ] Add top universities: NUST, FAST, LUMS, COMSATS, UET, etc.
- [ ] Add 3-5 popular programs per university
- [ ] Include: name, city, tuition fees, merit cutoffs
- [ ] Create seed SQL script
- [ ] Run seed script in Supabase

**Universities to Add (Minimum 20):**
1. NUST (Islamabad)
2. FAST-NUCES (Islamabad, Lahore, Karachi)
3. LUMS (Lahore)
4. COMSATS (Multiple campuses)
5. UET (Lahore, Taxila, Peshawar)
6. PIEAS (Islamabad)
7. NED University (Karachi)
8. IBA (Karachi)
9. GIKI (Topi)
10. Air University (Islamabad)
... (10 more)

---

### Issue #19: Create Get All Universities Endpoint
**Priority:** 🔴 Critical
**Time:** 2 hours
**Labels:** endpoint, universities

**Description:**
Implement GET /api/v1/universities endpoint.

**Acceptance Criteria:**
- [ ] Return list of all universities
- [ ] Add pagination (limit, offset)
- [ ] Add sorting options
- [ ] Return total count
- [ ] Write tests

**Endpoint:** `GET /api/v1/universities?limit=10&offset=0`

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "NUST",
      "city": "Islamabad",
      "type": "Public",
      ...
    }
  ],
  "total": 25,
  "limit": 10,
  "offset": 0
}
```

---

### Issue #20: Create Get University by ID Endpoint
**Priority:** 🔴 Critical
**Time:** 1.5 hours
**Labels:** endpoint, universities

**Description:**
Implement GET /api/v1/universities/{id} endpoint.

**Acceptance Criteria:**
- [ ] Return single university details
- [ ] Include all programs offered
- [ ] Include admission requirements
- [ ] Handle university not found (404)
- [ ] Write tests

**Endpoint:** `GET /api/v1/universities/1`

---

### Issue #21: Create Get Programs by University Endpoint
**Priority:** 🟡 Medium
**Time:** 1.5 hours
**Labels:** endpoint, universities

**Description:**
Implement GET /api/v1/universities/{id}/programs endpoint.

**Acceptance Criteria:**
- [ ] Return all programs for a university
- [ ] Include program details (fees, merit, etc.)
- [ ] Add filtering by field
- [ ] Write tests

**Endpoint:** `GET /api/v1/universities/1/programs?field=Engineering`

---

## 🔍 PHASE 4: SEARCH & FILTERING (Week 2, Days 11-14)

### Issue #22: Create University Search Endpoint
**Priority:** 🔴 Critical
**Time:** 4 hours
**Labels:** endpoint, search

**Description:**
Implement smart university search with multiple filters.

**Acceptance Criteria:**
- [ ] Filter by field (Engineering, Medicine, CS, etc.)
- [ ] Filter by city
- [ ] Filter by tuition fee range (min, max)
- [ ] Filter by university type (Public/Private)
- [ ] Return matching universities with programs
- [ ] Add pagination
- [ ] Optimize database queries (use indexes)
- [ ] Write tests

**Endpoint:** `GET /api/v1/universities/search?field=Engineering&city=Islamabad&max_fee=300000`

**Query Parameters:**
- field (optional)
- city (optional)
- min_fee (optional)
- max_fee (optional)
- type (optional)
- limit (default: 10)
- offset (default: 0)

---

### Issue #23: Implement Eligibility Calculator
**Priority:** 🔴 Critical
**Time:** 3 hours
**Labels:** algorithm, endpoint

**Description:**
Calculate Safety/Target/Reach tiers for each university.

**Acceptance Criteria:**
- [ ] Compare student FSc % with program merit cutoff
- [ ] Calculate tier:
  - Safety: Student % > Merit + 10%
  - Target: Student % within ±10% of merit
  - Reach: Student % < Merit - 10%
- [ ] Include tier in search results
- [ ] Add endpoint: POST /api/v1/eligibility
- [ ] Write tests for edge cases

**Algorithm:**
```python
def calculate_tier(student_percentage: float, merit_cutoff: float) -> str:
    diff = student_percentage - merit_cutoff
    if diff > 10:
        return "Safety"
    elif diff > -10:
        return "Target"
    else:
        return "Reach"
```

**Endpoint:** `POST /api/v1/eligibility`

**Request:**
```json
{
  "student_percentage": 85.5,
  "universities": [1, 2, 3]  // university IDs
}
```

**Response:**
```json
{
  "results": [
    {
      "university_id": 1,
      "university_name": "NUST",
      "programs": [
        {
          "name": "BS Computer Science",
          "merit_cutoff": 88.0,
          "tier": "Reach",
          "difference": -2.5
        }
      ]
    }
  ]
}
```

---

### Issue #24: Add Search Filters Validation
**Priority:** 🟡 Medium
**Time:** 1.5 hours
**Labels:** validation

**Description:**
Validate all search query parameters.

**Acceptance Criteria:**
- [ ] Validate fee range (min < max)
- [ ] Validate field is from allowed list
- [ ] Validate city name format
- [ ] Return clear error messages for invalid params
- [ ] Write tests

---

### Issue #25: Optimize Search Queries
**Priority:** 🟡 Medium
**Time:** 2 hours
**Labels:** performance, database

**Description:**
Optimize database queries for fast search.

**Acceptance Criteria:**
- [ ] Add database indexes on searchable fields
- [ ] Use query optimization techniques
- [ ] Measure query performance
- [ ] Aim for <100ms response time
- [ ] Write performance tests

---

## 🤖 PHASE 5: AI INTEGRATION (Week 3, Days 15-21)

### Issue #26: Set Up Groq API Client
**Priority:** 🔴 Critical
**Time:** 1.5 hours
**Labels:** ai, setup

**Description:**
Integrate Groq API for LLM access.

**Acceptance Criteria:**
- [ ] Install groq SDK
- [ ] Create utils/ai_client.py
- [ ] Initialize Groq client with API key
- [ ] Test basic completion request
- [ ] Handle API errors (rate limits, timeouts)
- [ ] Write unit tests

---

### Issue #27: Create AI Chat Endpoint (Basic)
**Priority:** 🔴 Critical
**Time:** 3 hours
**Labels:** ai, endpoint

**Description:**
Implement basic chat endpoint with Groq.

**Acceptance Criteria:**
- [ ] Create POST /api/v1/chat endpoint
- [ ] Accept user message
- [ ] Send to Groq API
- [ ] Return AI response
- [ ] Add streaming support (optional)
- [ ] Write tests

**Endpoint:** `POST /api/v1/chat`

**Request:**
```json
{
  "message": "Which universities offer CS in Islamabad?",
  "user_id": 1
}
```

**Response:**
```json
{
  "message": "Here are the top universities offering CS in Islamabad: NUST, FAST-NUCES, Air University...",
  "conversation_id": "abc123"
}
```

---

### Issue #28: Connect AI to University Database (Function Calling)
**Priority:** 🔴 Critical
**Time:** 4 hours
**Labels:** ai, integration

**Description:**
Give AI access to university search API.

**Acceptance Criteria:**
- [ ] Define search function for AI to call
- [ ] Implement function calling with Groq
- [ ] AI decides when to search database
- [ ] AI uses real data in responses
- [ ] Test with various questions
- [ ] Write integration tests

**How it works:**
1. User asks: "Which universities in Lahore offer Engineering under 200k?"
2. AI recognizes need to search database
3. AI calls search_universities(city="Lahore", field="Engineering", max_fee=200000)
4. AI receives search results
5. AI formats response for user

---

### Issue #29: Implement Conversation History
**Priority:** 🟡 Medium
**Time:** 3 hours
**Labels:** ai, database

**Description:**
Store and retrieve conversation history.

**Acceptance Criteria:**
- [ ] Create conversations table
- [ ] Create messages table
- [ ] Store each message (user + AI)
- [ ] Retrieve conversation by ID
- [ ] Link conversations to users
- [ ] Add endpoint: GET /api/v1/conversations
- [ ] Write tests

**Schema:**
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR(20), -- 'user' or 'assistant'
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### Issue #30: Add Streaming Chat Response
**Priority:** 🟢 Low
**Time:** 2 hours
**Labels:** ai, enhancement

**Description:**
Implement streaming for real-time chat feel.

**Acceptance Criteria:**
- [ ] Use Server-Sent Events (SSE) or WebSocket
- [ ] Stream AI response word-by-word
- [ ] Handle connection errors
- [ ] Write tests

**Endpoint:** `POST /api/v1/chat/stream`

---

### Issue #31: Implement AI Rate Limiting
**Priority:** 🟡 Medium
**Time:** 2 hours
**Labels:** ai, security

**Description:**
Limit AI requests per user to prevent abuse.

**Acceptance Criteria:**
- [ ] Track AI requests per user
- [ ] Limit to X requests per hour (e.g., 20)
- [ ] Return clear error when limit exceeded
- [ ] Reset counter after time window
- [ ] Write tests

---

### Issue #32: Create AI Prompt Templates
**Priority:** 🟡 Medium
**Time:** 2 hours
**Labels:** ai

**Description:**
Create reusable prompt templates for AI.

**Acceptance Criteria:**
- [ ] Create system prompt for university counselor role
- [ ] Create prompt for analyzing student profile
- [ ] Create prompt for recommendation generation
- [ ] Store templates in config file
- [ ] Write tests

**Example System Prompt:**
```
You are an expert university admission counselor in Pakistan.
You help students find suitable universities based on their FSc percentage, budget, and interests.
Always provide specific, actionable advice.
Use the search_universities function when needed to get real data.
```

---

## 📊 PHASE 6: ANALYTICS & EXTRAS (Week 4, Days 22-28)

### Issue #33: Create Dashboard Stats Endpoint
**Priority:** 🟡 Medium
**Time:** 2 hours
**Labels:** endpoint, analytics

**Description:**
Provide stats for user dashboard.

**Acceptance Criteria:**
- [ ] Total universities in database
- [ ] Total programs available
- [ ] User's saved universities count
- [ ] User's conversation count
- [ ] Write tests

**Endpoint:** `GET /api/v1/stats`

---

### Issue #34: Implement University Favorites (Bookmarking)
**Priority:** 🟡 Medium
**Time:** 3 hours
**Labels:** feature, endpoint

**Description:**
Allow users to save/favorite universities.

**Acceptance Criteria:**
- [ ] Create user_favorites table
- [ ] POST /api/v1/favorites/{university_id} (add favorite)
- [ ] DELETE /api/v1/favorites/{university_id} (remove)
- [ ] GET /api/v1/favorites (get all favorites)
- [ ] Write tests

---

### Issue #35: Create Comparison Endpoint
**Priority:** 🟢 Low
**Time:** 3 hours
**Labels:** feature, endpoint

**Description:**
Compare multiple universities side-by-side.

**Acceptance Criteria:**
- [ ] Accept list of university IDs
- [ ] Return comparison data (fees, programs, merit, etc.)
- [ ] Format for easy frontend display
- [ ] Write tests

**Endpoint:** `POST /api/v1/universities/compare`

**Request:**
```json
{
  "university_ids": [1, 2, 3]
}
```

---

### Issue #36: Add Request Logging
**Priority:** 🟡 Medium
**Time:** 2 hours
**Labels:** logging, monitoring

**Description:**
Log all API requests for debugging.

**Acceptance Criteria:**
- [ ] Install logging library
- [ ] Log request method, path, status, duration
- [ ] Log errors with stack traces
- [ ] Don't log sensitive data (passwords, tokens)
- [ ] Write logs to file

---

### Issue #37: Implement Error Handling Middleware
**Priority:** 🔴 Critical
**Time:** 2 hours
**Labels:** error-handling

**Description:**
Centralized error handling for consistent responses.

**Acceptance Criteria:**
- [ ] Create custom exception classes
- [ ] Add global exception handler
- [ ] Return consistent error format:
  ```json
  {
    "error": "Error message",
    "detail": "Detailed explanation",
    "status_code": 400
  }
  ```
- [ ] Handle common errors (404, 401, 500)
- [ ] Write tests

---

### Issue #38: Add Input Validation Middleware
**Priority:** 🟡 Medium
**Time:** 1.5 hours
**Labels:** validation

**Description:**
Validate all request inputs.

**Acceptance Criteria:**
- [ ] Use Pydantic models for validation
- [ ] Return clear validation errors
- [ ] Sanitize inputs (SQL injection prevention)
- [ ] Write tests

---

### Issue #39: Create API Documentation
**Priority:** 🔴 Critical
**Time:** 3 hours
**Labels:** documentation

**Description:**
Comprehensive API documentation.

**Acceptance Criteria:**
- [ ] Add descriptions to all endpoints
- [ ] Add request/response examples
- [ ] Add error response examples
- [ ] Group endpoints by category
- [ ] Test all examples work
- [ ] FastAPI auto-docs should be complete

---

### Issue #40: Write Integration Tests
**Priority:** 🔴 Critical
**Time:** 4 hours
**Labels:** testing

**Description:**
End-to-end integration tests.

**Acceptance Criteria:**
- [ ] Test complete user journey:
  - Register → Login → Search → Chat → Get recommendations
- [ ] Test with real database (test database)
- [ ] Achieve >70% overall code coverage
- [ ] All tests pass

---

## 🚀 PHASE 7: DEPLOYMENT PREP (Week 4, Days 29-30)

### Issue #41: Create Docker Configuration
**Priority:** 🟡 Medium
**Time:** 2 hours
**Labels:** deployment

**Description:**
Dockerize the application.

**Acceptance Criteria:**
- [ ] Create Dockerfile
- [ ] Create docker-compose.yml (with PostgreSQL)
- [ ] Test local Docker deployment
- [ ] Update README with Docker instructions

---

### Issue #42: Set Up Railway Deployment
**Priority:** 🔴 Critical
**Time:** 2 hours
**Labels:** deployment

**Description:**
Deploy backend to Railway.

**Acceptance Criteria:**
- [ ] Connect GitHub repo to Railway
- [ ] Configure environment variables
- [ ] Test deployment
- [ ] API accessible at public URL
- [ ] Update README with deployment URL

---

### Issue #43: Add Health Check & Monitoring
**Priority:** 🟡 Medium
**Time:** 1.5 hours
**Labels:** monitoring

**Description:**
Monitoring endpoints for uptime checks.

**Acceptance Criteria:**
- [ ] Enhance health check endpoint
- [ ] Check database connection
- [ ] Check Groq API connection
- [ ] Return detailed status
- [ ] Write tests

**Endpoint:** `GET /api/v1/health`

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "ai_api": "connected",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

---

### Issue #44: Security Hardening
**Priority:** 🔴 Critical
**Time:** 2 hours
**Labels:** security

**Description:**
Final security checks before production.

**Acceptance Criteria:**
- [ ] Remove debug mode in production
- [ ] Set secure JWT secret
- [ ] Configure CORS properly
- [ ] Add rate limiting (SlowAPI or similar)
- [ ] Remove any test/demo credentials
- [ ] Scan for vulnerabilities

---

### Issue #45: Performance Optimization
**Priority:** 🟡 Medium
**Time:** 2 hours
**Labels:** performance

**Description:**
Optimize API performance.

**Acceptance Criteria:**
- [ ] Add database connection pooling
- [ ] Add response caching where appropriate
- [ ] Optimize slow queries
- [ ] Load test with 100 concurrent requests
- [ ] Ensure <200ms average response time

---

## 📝 BONUS ISSUES (If Time Permits)

### Issue #46: Email Verification
**Priority:** 🟢 Low
**Time:** 4 hours
**Labels:** authentication, enhancement

**Description:**
Send verification email on registration.

---

### Issue #47: Password Reset
**Priority:** 🟢 Low
**Time:** 4 hours
**Labels:** authentication, enhancement

**Description:**
Implement "Forgot Password" flow.

---

### Issue #48: Admin Panel Endpoints
**Priority:** 🟢 Low
**Time:** 6 hours
**Labels:** admin, enhancement

**Description:**
Create admin endpoints to manage universities.

---

### Issue #49: Data Export Endpoint
**Priority:** 🟢 Low
**Time:** 2 hours
**Labels:** feature

**Description:**
Allow users to export their data (GDPR compliance).

---

### Issue #50: Scheduled Jobs (Web Crawler)
**Priority:** 🟢 Low
**Time:** 8+ hours
**Labels:** crawler, automation

**Description:**
Automate university data updates (future enhancement).

---

## 📊 Issue Summary

**By Priority:**
- 🔴 Critical: 25 issues (must complete)
- 🟡 Medium: 15 issues (should complete)
- 🟢 Low: 10 issues (nice to have)

**By Phase:**
- Phase 1 (Setup): 5 issues
- Phase 2 (Auth): 10 issues
- Phase 3 (Universities): 6 issues
- Phase 4 (Search): 4 issues
- Phase 5 (AI): 7 issues
- Phase 6 (Analytics): 8 issues
- Phase 7 (Deployment): 5 issues
- Bonus: 5 issues

**Total Estimated Time:** 120-150 hours (4 weeks at 30-40 hours/week)

---

## 🎯 Recommended Order

**Week 1:**
- Issues #1-15 (Setup + Authentication)

**Week 2:**
- Issues #16-25 (Universities + Search)

**Week 3:**
- Issues #26-32 (AI Integration)

**Week 4:**
- Issues #33-45 (Analytics + Deployment)

---

## 💡 Issue Creation Tips

**For each issue, include:**
1. Clear title (e.g., "Implement User Registration Endpoint")
2. Priority label (🔴🟡🟢)
3. Time estimate
4. Detailed description
5. Acceptance criteria (checklist)
6. Related files/endpoints
7. Testing requirements

**Labels to use:**
- backend
- frontend
- authentication
- database
- ai
- testing
- documentation
- deployment
- enhancement
- bug
- security
- performance

---

## ✅ Getting Started

**Create issues in GitHub:**
1. Go to your repo → Issues → New Issue
2. Copy the issue content above
3. Add appropriate labels
4. Assign to yourself
5. Add to project board (optional)

**Then work through them one by one!**

Start with Issue #1 tomorrow and work your way through systematically.

Good luck! 🚀
