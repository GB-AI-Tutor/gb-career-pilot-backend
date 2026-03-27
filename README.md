# 🎓 GB Career Pilot - Backend

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

[![License: Dual](https://img.shields.io/badge/License-Dual%20(MIT%2FCommercial)-blue.svg)](./LICENSE.md)
[![CI/CD](https://github.com/GB-AI-Tutor/gb-career-pilot-backend/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/GB-AI-Tutor/gb-career-pilot-backend/actions)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](./CONTRIBUTING.md)

**AI-powered university counseling platform backend for Pakistani students**

[Live API](https://gb-career-pilot-api.onrender.com) · [Frontend Repo](https://github.com/GB-AI-Tutor/gb-career-pilot-frontend) · [Report Bug](https://github.com/GB-AI-Tutor/gb-career-pilot-backend/issues) · [Request Feature](https://github.com/GB-AI-Tutor/gb-career-pilot-backend/issues)

</div>

---

## 🎯 About

GB Career Pilot Backend is a production-ready FastAPI application powering an AI-driven university counseling platform. It helps students in Gilgit-Baltistan, Pakistan discover universities, programs, and career paths using Groq's Llama 3.3 70B.

**Live API:** [https://gb-career-pilot-api.onrender.com](https://gb-career-pilot-backend.onrender.com/)
**Frontend:** https://raqeebs.app

---

## ✨ Features

- 🤖 **AI Counseling** - Groq's Llama 3.3 70B with streaming (500+ tokens/sec)
- 🔐 **Authentication** - JWT with access/refresh tokens, bcrypt hashing
- 📧 **Email Verification** - Multi-provider (Resend, Brevo)
- 🚦 **Rate Limiting** - Redis-backed distributed rate limiting
- 🗄️ **Database** - PostgreSQL with Supabase hosting
- ⚡ **Caching** - Redis for performance
- 🎓 **University Database** - 200+ institutions and programs
- 💬 **Conversation History** - Persistent AI chat history
- 🔒 **Security** - Input validation, CORS, error monitoring
- 📚 **API Docs** - Auto-generated Swagger/ReDoc

---

## 🛠️ Tech Stack

| Category | Technologies |
|----------|-------------|
| **Framework** | FastAPI 0.109+ |
| **Language** | Python 3.11+ |
| **Database** | PostgreSQL 15 (Supabase) |
| **Cache** | Redis 7+ (Upstash) |
| **AI/ML** | Groq API (Llama 3.3 70B), LangChain |
| **Auth** | JWT (PyJWT), bcrypt |
| **Email** | Resend, Brevo |
| **Testing** | pytest, pytest-asyncio |
| **CI/CD** | GitHub Actions |
| **Deployment** | Docker, Render |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or Supabase account)
- Redis (or Upstash account)
- API Keys: Groq, Resend/Brevo

### Installation

1. **Clone & install**
   ```bash
   git clone https://github.com/GB-AI-Tutor/gb-career-pilot-backend.git
   cd gb-career-pilot-backend

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Run server**
   ```bash
   uvicorn src.main:app --reload --port 8000
   ```

4. **Visit docs**
   - Swagger: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Environment Setup

See `.env.example` for all required variables:

```env
# Database (Supabase)
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_key

# AI (Groq)
GROQ_API_KEY=your_groq_key

# Redis (Upstash)
UPSTASH_REDIS_URL=your_redis_url
UPSTASH_REDIS_TOKEN=your_token

# JWT
JWT_SECRET_KEY=your_secret  # Generate: openssl rand -hex 32
JWT_REFRESH_SECRET_KEY=your_refresh_secret
ALGORITHM=HS256

# Email
RESEND_API_KEY=your_resend_key
BREVO_API=your_brevo_key

# Frontend
FRONTEND_URL=http://localhost:5173
```

---

## 📚 API Documentation

### Base URL
- **Production:** `https://gb-career-pilot-api.onrender.com`
- **Local:** `http://localhost:8000`

### Key Endpoints

**Authentication**
```
POST   /api/v1/auth/register          # Register user
POST   /api/v1/auth/login             # Login
POST   /api/v1/auth/refresh           # Refresh token
GET    /api/v1/auth/verify            # Verify email
```

**AI Chat**
```
POST   /api/v1/ai/chat                # AI counseling
POST   /api/v1/ai/chat/stream         # Streaming response
GET    /api/v1/ai/conversation-history # Chat history
```

**Universities & Programs**
```
GET    /api/v1/universities           # List universities
GET    /api/v1/universities/{id}      # Get details
GET    /api/v1/programs               # List programs
GET    /api/v1/programs/search        # Search programs
```

**Interactive docs:** `/docs` (Swagger UI)

---

## 📁 Project Structure

```
gb-career-pilot-backend/
├── src/
│   ├── api/v1/endpoints/      # API routes
│   ├── auth/                  # Authentication logic
│   ├── cache/                 # Redis client
│   ├── database/              # DB connection
│   ├── models/                # Data models
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # Business logic
│   ├── utils/                 # Utilities
│   ├── config.py              # Configuration
│   └── main.py                # FastAPI app
├── tests/                     # Test suite
├── .github/workflows/         # CI/CD
├── requirements.txt           # Dependencies
└── Dockerfile                 # Docker config
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Specific test
pytest tests/test_auth.py -v
```

---

## 🚢 Deployment

### Render (Production)

Automatic deployment from `main` branch.

**URL:** https://gb-career-pilot-api.onrender.com

1. Push to `main`
2. GitHub Actions runs tests
3. Render auto-deploys if tests pass

### Docker

```bash
docker build -t gb-backend .
docker run -p 8000:8000 --env-file .env gb-backend
```

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

**Quick start:**
1. Fork the repo
2. Create branch: `git checkout -b feature/amazing`
3. Make changes & add tests
4. Commit: `git commit -m 'feat: add amazing feature'`
5. Push: `git push origin feature/amazing`
6. Open Pull Request

**Good first issues:** [Look here](https://github.com/GB-AI-Tutor/gb-career-pilot-backend/labels/good%20first%20issue)

---

## 📜 License

**Dual-license model:**
- ✅ Free for non-profit (students, NGOs, education)
- 💼 Commercial license required for businesses

See [LICENSE.md](./LICENSE.md)

---

## 🔒 Security

Found a vulnerability? **Don't open a public issue!**

📧 Email: security@feelandsupport.org

See [SECURITY.md](./SECURITY.md)

---

## 📞 Contact

- 🌐 Website: [raqeebs.app](https://raqeebs.app)
- 💬 Discord: *Coming soon*
- 📧 Email: contact@feelandsupport.org
- 🐛 Issues: [GitHub Issues](https://github.com/GB-AI-Tutor/gb-career-pilot-backend/issues)

---

<div align="center">

**Built with ❤️ by Feel and Support**

[⭐ Star](https://github.com/GB-AI-Tutor/gb-career-pilot-backend) · [🍴 Fork](https://github.com/GB-AI-Tutor/gb-career-pilot-backend/fork) · [🐛 Report](https://github.com/GB-AI-Tutor/gb-career-pilot-backend/issues)

</div>
