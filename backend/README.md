# FastAPI Backend - Quantum-Resistant Chaffing System

Backend API for the Post-Quantum Metadata Obfuscation Layer.

## Features

- 🔐 JWT Authentication with refresh tokens
- 🗄️ PostgreSQL database with async SQLAlchemy
- 🔒 Post-quantum cryptography key management
- 📊 Traffic session and packet logging
- 🤖 ANFIS model management
- 📝 Comprehensive audit logging
- 🚀 High-performance async API (FastAPI)

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 14+

### Installation

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

2. Install dependencies:
```bash
pip install -r ../requirements.txt
```

3. Set up environment variables:
```bash
copy .env.example .env
# Edit .env with your configuration
```

4. Create PostgreSQL database:
```sql
CREATE DATABASE qr_chaffing;
```

5. Run database migrations:
```bash
# Initialize Alembic (first time only)
alembic init alembic

# Generate migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

### Running the Server

Development mode:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Production mode:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuration
│   ├── database.py          # Database connection
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── api/                 # API routes
│   ├── services/            # Business logic
│   ├── middleware/          # Auth middleware
│   └── utils/               # Utilities
├── alembic/                 # Database migrations
├── tests/                   # Tests
├── .env.example             # Environment template
└── README.md
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token

### Sessions (TODO)
- `GET /api/sessions` - List sessions
- `POST /api/sessions` - Create session
- `GET /api/sessions/{id}` - Get session details

### Crypto (TODO)
- `GET /api/crypto/keys` - List keys
- `POST /api/crypto/keys/generate` - Generate keypair

### Engine (TODO)
- `POST /api/engine/start` - Start engine
- `POST /api/engine/stop` - Stop engine
- `WS /api/engine/stream` - WebSocket stream

## Testing

```bash
pytest tests/ -v --cov=app
```

## Security

- Passwords hashed with bcrypt (cost factor 12)
- JWT tokens with short expiry (15 min access, 7 day refresh)
- Database keys encrypted with Fernet
- CORS configured for frontend origins
- SQL injection prevention via SQLAlchemy ORM

## License

MIT
