# SANCHAY IAS
## Financial Advisory Operating System

A comprehensive, production-ready financial advisory management system built with FastAPI (backend) and vanilla JavaScript (frontend).

---

## 📋 Project Structure

```
sanchay_ias/
├── backend/                    # Python FastAPI backend
│   ├── api_server.py          # Main API server
│   ├── sanchay_db.py          # Database module
│   ├── ingestion_engine.py    # Data ingestion service
│   └── __init__.py
├── frontend/                   # JavaScript frontend
│   ├── index.html             # Main UI
│   ├── config.js              # Configuration management
│   ├── app.js                 # Main app engine
│   ├── app_ext.js             # App extensions
│   ├── engines.js             # Computation engines
│   ├── sentinel.js            # Monitoring
│   ├── data.js                # Fallback data
│   ├── styles.css             # Styling
│   ├── assets/                # Static assets
│   └── test_render.js         # Test utilities
├── tests/                      # Test suite
│   ├── conftest.py            # pytest configuration
│   ├── test_backend_api.py    # API tests
│   ├── test_database_operations.py
│   ├── test_integration.py
│   └── test_runner.py
├── scripts/                    # Utility scripts
│   └── init_local_db.py       # Database initialization
├── data/                       # Database & data files
│   └── sanchay_local.db       # SQLite database
├── config/                     # Configuration files
│   └── [environment configs]
├── docs/                       # Documentation
│   ├── README.md
│   ├── API_REFERENCE.md
│   └── DEPLOYMENT.md
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip or poetry
- SQLite3

### Installation

1. **Clone & Setup**
   ```bash
   cd sanchay_ias
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Database**
   ```bash
   python scripts/init_local_db.py
   ```

5. **Start API Server**
   ```bash
   python -m backend.api_server
   ```

   The API will be available at: `http://localhost:8001`

6. **Open Frontend**
   ```bash
   # Open in browser:
   file:///path/to/frontend/index.html
   # OR use a simple HTTP server:
   python -m http.server 5000 --directory frontend
   # Then open: http://localhost:5000
   ```

---

## 📚 API Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /status` - Server status

### Users
- `GET /users` - List all users
- `GET /users/{user_id}` - Get user by ID
- `POST /users` - Create new user

### Clients
- `GET /clients` - List all clients
- `GET /clients/{client_id}` - Get client details
- `POST /clients` - Create new client

### Goals
- `GET /goals` - List all goals
- `POST /goals` - Create new goal

### Dashboard
- `GET /dashboard` - Get dashboard summary
- `GET /tasks` - List tasks
- `GET /compliance` - Get compliance status
- `GET /reports` - List reports
- `GET /team` - List team members

See [docs/API_REFERENCE.md](docs/API_REFERENCE.md) for complete API documentation.

---

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and adjust:

```bash
cp .env.example .env
```

Key settings:
- `API_HOST` - API server host (default: 0.0.0.0)
- `API_PORT` - API server port (default: 8001)
- `CORS_ORIGINS` - Allowed CORS origins
- `DATA_REFRESH_INTERVAL` - Data sync interval (seconds)

### Frontend Configuration

Edit `frontend/config.js`:
- API base URL
- UI theme
- Refresh intervals
- Feature flags

---

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test Suite
```bash
pytest tests/test_backend_api.py -v
```

### Run with Coverage
```bash
pytest --cov=backend tests/
```

### Run Integration Tests
```bash
pytest tests/test_integration.py -v
```

---

## 📊 Database

### Database Location
- **Development**: `data/sanchay_local.db`
- **Production**: Configure via environment

### Schema
The database includes tables for:
- **users** - User accounts and roles
- **advisors** - Advisor information
- **clients** - Client details
- **goals** - Financial goals
- **transactions** - Transaction history
- **asset_master** - Asset registry
- **price_history** - Historical price data

### Initialize Fresh Database
```bash
python scripts/init_local_db.py --fresh
```

---

## 🎨 Frontend Architecture

### Core Modules
- **config.js** - Centralized configuration
- **app.js** - Main application engine
- **engines.js** - Computation engines
- **sentinel.js** - Monitoring & alerts
- **data.js** - Fallback data (when API offline)

### Key Features
- ✅ Responsive UI with Flexbox layout
- ✅ API fallback to local data
- ✅ Auto-refresh with configurable intervals
- ✅ Dark theme with CSS variables
- ✅ Real-time error handling
- ✅ Offline-first architecture

---

## 🔌 Backend Architecture

### API Framework
Built with **FastAPI** for:
- High performance async operations
- Automatic API documentation
- Built-in validation via Pydantic
- CORS middleware pre-configured

### Database
- **SQLite** for development/deployment
- **Context managers** for safe connections
- **Foreign keys** enabled for referential integrity

### Data Ingestion
- Background service for market data
- Free data sources (Yahoo Finance)
- Configurable refresh intervals

---

## 📝 Common Tasks

### Add a New API Endpoint
1. Define Pydantic model in `backend/api_server.py`
2. Create endpoint function
3. Add to test suite
4. Document in `docs/API_REFERENCE.md`

### Add New Database Table
1. Add CREATE TABLE statement to `backend/sanchay_db.py`
2. Run `python scripts/init_local_db.py --fresh`
3. Create ORM model if needed

### Update Frontend UI
1. Edit `frontend/index.html` for structure
2. Update `frontend/styles.css` for styling
3. Add logic to `frontend/app.js`
4. Test in browser

---

## 🚨 Troubleshooting

### API Server Won't Start
```bash
# Check if port is in use
lsof -i :8001

# Use different port
API_PORT=8002 python -m backend.api_server
```

### Database Locked Error
```bash
# Restart API server
# Or delete data/sanchay_local.db and reinitialize
```

### Frontend Can't Connect to API
- Verify API server is running (`curl http://localhost:8001/health`)
- Check `CORS_ORIGINS` configuration
- Check browser console for errors
- Frontend should fallback to local data automatically

### Tests Failing
```bash
# Clear cache
rm -rf .pytest_cache __pycache__

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Run with verbose output
pytest -vv
```

---

## 📋 Production Checklist

- [ ] Copy `.env.example` to `.env` and update values
- [ ] Set `API_RELOAD=False` in production
- [ ] Set `DEBUG=False`
- [ ] Run full test suite: `pytest`
- [ ] Test all API endpoints
- [ ] Verify database backups
- [ ] Configure proper CORS origins
- [ ] Set up error logging/monitoring
- [ ] Update documentation

---

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/name`
2. Make changes and add tests
3. Run tests: `pytest`
4. Commit: `git commit -m "feat: description"`
5. Push: `git push origin feature/name`
6. Create Pull Request

---

## 📄 License

[Specify your license here]

---

## 📧 Support

For issues or questions:
1. Check `docs/` folder for documentation
2. Review test files for usage examples
3. Check GitHub Issues
4. Contact: [support email]

---

## 🗺️ Roadmap

- [ ] User authentication & authorization
- [ ] Advanced portfolio analytics
- [ ] Machine learning recommendations
- [ ] Mobile app
- [ ] Advanced reporting

---

**Last Updated**: 2024
**Version**: 2.0.0
