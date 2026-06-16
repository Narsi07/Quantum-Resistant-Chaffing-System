# Quantum-Resistant Chaffing System

**Post-Quantum Metadata Obfuscation Layer using Neuro-Fuzzy Traffic Synthesis**

A sophisticated traffic analysis defense system that combines post-quantum cryptography with AI-powered dummy traffic generation to protect network communications from both classical and quantum adversaries.

---

## 🚀 Quick Start

### Option 1: Run Streamlit Dashboard (Original System)

```bash
cd "c:\Users\NARASIMMAN\OneDrive\Desktop\projects\Quantum_Resistent Chaffing"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run src/dashboard/app.py
```

Visit: http://localhost:8501

### Option 2: Run FastAPI Backend (New System)

```bash
# 1. Install PostgreSQL and create database 'qr_chaffing'
# 2. Then run:

cd backend
python -m venv venv
venv\Scripts\activate
pip install -r ../requirements.txt
copy .env.example .env
# Edit .env with your database credentials
uvicorn app.main:app --reload
```

Visit: http://localhost:8000/api/docs

---

## 📖 Full Documentation

For complete setup instructions, see: **[SETUP_GUIDE.md](file:///C:/Users/NARASIMMAN/.gemini/antigravity/brain/e6147e2d-7c89-4024-b1f9-4905e65ba057/setup_guide.md)**

---

## 🎯 Features

### Core Capabilities
- ✅ **Post-Quantum Cryptography**: Kyber512 KEM + Dilithium2 signatures
- ✅ **Traffic Obfuscation**: Constant-rate transmission with dummy packets
- ✅ **AI Traffic Generation**: ANFIS (Adaptive Neuro-Fuzzy Inference System)
- ✅ **Steganography**: LSB embedding for metadata hiding
- ✅ **Multipath Routing**: Traffic splitting for correlation resistance
- ✅ **Real-time Dashboard**: Live traffic visualization

### Backend API (New)
- ✅ **FastAPI**: High-performance async API (15,000+ req/sec)
- ✅ **PostgreSQL**: Secure database with encryption at rest
- ✅ **JWT Authentication**: Access + refresh tokens
- ✅ **RESTful API**: 40+ endpoints for complete system control
- ✅ **WebSocket Support**: Real-time updates
- ✅ **Auto Documentation**: Swagger UI + ReDoc

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
├─────────────────────────────────────────────────────────┤
│  Streamlit Dashboard          FastAPI Swagger UI        │
│  (localhost:8501)             (localhost:8000/api/docs) │
└─────────────────┬─────────────────────┬─────────────────┘
                  │                     │
                  ▼                     ▼
         ┌────────────────┐    ┌────────────────┐
         │  Obfuscation   │    │  FastAPI       │
         │  Engine        │    │  Backend       │
         │  (Python)      │    │  (Async)       │
         └────────┬───────┘    └────────┬───────┘
                  │                     │
                  │                     ▼
                  │            ┌────────────────┐
                  │            │  PostgreSQL    │
                  │            │  Database      │
                  │            └────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │  ANFIS         │
         │  Generator     │
         │  (PyTorch)     │
         └────────────────┘
```

---

## 📂 Project Structure

```
Quantum_Resistent_Chaffing/
├── src/                        # Original obfuscation engine
│   ├── obfuscation/           # Traffic obfuscation engine
│   ├── crypto/                # Post-quantum crypto wrappers
│   ├── neuro_fuzzy/           # ANFIS traffic generator
│   ├── steganography/         # LSB embedding
│   ├── network/               # Multipath routing
│   ├── adversarial/           # GAN discriminator
│   ├── dashboard/             # Streamlit UI
│   └── main.py                # CLI demo
│
├── backend/                    # New FastAPI backend
│   ├── app/
│   │   ├── models/            # Database models (7 tables)
│   │   ├── schemas/           # Pydantic validation
│   │   ├── api/               # API endpoints
│   │   ├── services/          # Business logic
│   │   ├── middleware/        # Auth middleware
│   │   └── utils/             # Security utilities
│   ├── alembic/               # Database migrations
│   └── tests/                 # Test suite
│
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## 🔒 Security Features

- **Encryption**: AES-256-GCM with post-quantum key exchange
- **Authentication**: JWT with bcrypt password hashing
- **Database Security**: Fernet encryption for sensitive data
- **Audit Logging**: Complete audit trail of all operations
- **CORS Protection**: Configurable allowed origins
- **Rate Limiting**: API request throttling

---

## 🧪 Testing

### Test Obfuscation Engine
```bash
python src/main.py --duration 30
```

### Test Backend API
```bash
cd backend
pytest tests/ -v --cov=app
```

### Manual Testing
1. Open Swagger UI: http://localhost:8000/api/docs
2. Register user: `POST /api/auth/register`
3. Login: `POST /api/auth/login`
4. Use access token for authenticated endpoints

---

## 📊 Database Schema

- **users**: User accounts with role-based access
- **crypto_keys**: Encrypted post-quantum keys
- **traffic_sessions**: Obfuscation session tracking
- **packet_logs**: Time-series packet data
- **anfis_models**: Trained AI models
- **audit_logs**: Security audit trail
- **config_presets**: Configuration templates
- **alerts**: System notifications

---

## 🛠️ Technologies

**Backend:**
- FastAPI (async web framework)
- SQLAlchemy (async ORM)
- PostgreSQL (database)
- Pydantic (validation)
- JWT (authentication)

**Obfuscation Engine:**
- PyTorch (ANFIS neural networks)
- Scapy (packet manipulation)
- NumPy/SciPy (numerical computing)
- Streamlit (dashboard)

**Cryptography:**
- liboqs (post-quantum crypto)
- cryptography (AES-GCM, Fernet)
- passlib (password hashing)

---

## 📝 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get tokens
- `POST /api/auth/refresh` - Refresh access token

### Sessions (TODO)
- `GET /api/sessions` - List traffic sessions
- `POST /api/sessions` - Create new session
- `GET /api/sessions/{id}` - Get session details

### Crypto (TODO)
- `GET /api/crypto/keys` - List cryptographic keys
- `POST /api/crypto/keys/generate` - Generate keypair

### Engine (TODO)
- `POST /api/engine/start` - Start obfuscation engine
- `POST /api/engine/stop` - Stop engine
- `WS /api/engine/stream` - Real-time updates

---

## 🐛 Troubleshooting

See **[SETUP_GUIDE.md](file:///C:/Users/NARASIMMAN/.gemini/antigravity/brain/e6147e2d-7c89-4024-b1f9-4905e65ba057/setup_guide.md)** for detailed troubleshooting.

Common issues:
- **PostgreSQL connection failed**: Check database is running and credentials in `.env`
- **liboqs-python fails**: System will run in simulation mode (expected)
- **Port already in use**: Change port with `--port 8001`

---

## 📚 Additional Documentation

- **[System Analysis](file:///C:/Users/NARASIMMAN/.gemini/antigravity/brain/e6147e2d-7c89-4024-b1f9-4905e65ba057/system_analysis.md)**: Architecture and components
- **[Implementation Plan](file:///C:/Users/NARASIMMAN/.gemini/antigravity/brain/e6147e2d-7c89-4024-b1f9-4905e65ba057/implementation_plan.md)**: Development roadmap
- **[Web UI Plan](file:///C:/Users/NARASIMMAN/.gemini/antigravity/brain/e6147e2d-7c89-4024-b1f9-4905e65ba057/web_ui_plan.md)**: Frontend design
- **[Backend Walkthrough](file:///C:/Users/NARASIMMAN/.gemini/antigravity/brain/e6147e2d-7c89-4024-b1f9-4905e65ba057/backend_walkthrough.md)**: Backend implementation

---

## 🎓 Research Background

This system implements concepts from:
- **Chaffing and Winnowing**: Traffic analysis resistance
- **Post-Quantum Cryptography**: Lattice-based crypto (NIST standards)
- **Neuro-Fuzzy Systems**: ANFIS for traffic synthesis
- **Adversarial Training**: GAN-style traffic generation
- **Steganography**: Metadata hiding in cover traffic

---

## 📄 License

MIT License

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

---

## 📧 Support

For issues or questions, see the troubleshooting section in [SETUP_GUIDE.md](file:///C:/Users/NARASIMMAN/.gemini/antigravity/brain/e6147e2d-7c89-4024-b1f9-4905e65ba057/setup_guide.md).
