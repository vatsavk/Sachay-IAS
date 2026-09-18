# SANCHAY IAS - GETTING STARTED GUIDE

Welcome to SANCHAY IAS - your professional financial advisory operating system!

This guide will get you up and running in 5 minutes.

---

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A terminal/command prompt
- A modern web browser

**Check your Python version:**
```bash
python --version
```

Should show: `Python 3.8.0` or higher

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Dependencies (1 min)

```bash
cd E:\SANCHAY\Sanchay_IAS
pip install -r requirements.txt
```

**What this does**: Installs all required Python packages (FastAPI, SQLite, pytest, etc.)

### Step 2: Initialize Database (1 min)

```bash
python scripts/init_local_db.py
```

**What this does**: Creates the database file at `data/sanchay_local.db` with all tables

**Expected output:**
```
✓ Database initialized at: data/sanchay_local.db
```

### Step 3: Start API Server (1 min)

```bash
python -m backend.api_server
```

**What this does**: Starts the FastAPI server on http://localhost:8001

**Expected output:**
```
✓ SANCHAY API Server initialized
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**Leave this terminal open.**

### Step 4: Open Frontend (1 min)

**Option A: Using File Protocol**
1. Open your browser
2. Navigate to: `file:///E:/SANCHAY/Sanchay_IAS/frontend/index.html`

**Option B: Using HTTP Server (Recommended)**
```bash
# In a NEW terminal, navigate to project folder
cd E:\SANCHAY\Sanchay_IAS
python -m http.server 5000 --directory frontend

# Then open browser: http://localhost:5000
```

### Step 5: Verify Everything Works (1 min)

Open browser DevTools (F12) and check:
1. **Console** - Should show: `[APP] ✓ SANCHAY OS initialized successfully`
2. **Network** - Should show successful GET to `/health`

**You're done!** ✓

---

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_backend_api.py -v
```

### Run with Coverage Report
```bash
pytest --cov=backend --cov-report=html
```

---

## 📁 Project Structure

```
Sanchay_IAS/
├── backend/                    ← Python API server (FastAPI)
│   ├── api_server.py          Main API
│   ├── sanchay_db.py          Database module
│   └── ingestion_engine.py    Data ingestion
├── frontend/                   ← JavaScript UI
│   ├── index.html             Main page
│   ├── app.js                 Main engine
│   └── config.js              Configuration
├── tests/                      ← Test suite (pytest)
├── scripts/                    ← Utility scripts
├── data/                       ← Database files (auto-created)
├── docs/                       ← Documentation
├── README.md                   ← Full documentation
└── requirements.txt            ← Python dependencies
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file (copy from `.env.example`):

```bash
# Option 1: Windows PowerShell
Copy-Item .env.example .env

# Option 2: Command Prompt
copy .env.example .env

# Option 3: Manually create file and edit
```

**Common settings:**
```env
API_HOST=0.0.0.0
API_PORT=8001
DEBUG=False
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Overview and full setup guide |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | All API endpoints with examples |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment options |
| [CLEANUP_SUMMARY.md](CLEANUP_SUMMARY.md) | What was reorganized and why |

---

## 🆘 Troubleshooting

### Problem: "Module not found" error
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Problem: "Port 8001 already in use"
```bash
# Solution: Use different port
API_PORT=8002 python -m backend.api_server
```

### Problem: Frontend won't connect to API
```bash
# Check API is running
curl http://localhost:8001/health

# Should return:
# {"status":"ok","service":"SANCHAY IAS API","version":"2.0.0"}
```

### Problem: Database file not found
```bash
# Reinitialize database
python scripts/init_local_db.py --fresh
```

---

## 💡 Common Tasks

### Check API Status
```bash
curl http://localhost:8001/health
curl http://localhost:8001/status
```

### List All Clients
```bash
curl http://localhost:8001/clients
```

### Create a User
```bash
curl -X POST http://localhost:8001/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com","role":"advisor","status":"active"}'
```

### View Database
```bash
sqlite3 data/sanchay_local.db
# Then at sqlite> prompt:
# .tables
# SELECT * FROM users;
# .quit
```

---

## 📊 API Quick Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| GET | `/status` | Server status |
| GET | `/users` | List all users |
| POST | `/users` | Create user |
| GET | `/clients` | List all clients |
| POST | `/clients` | Create client |
| GET | `/dashboard` | Dashboard data |
| GET | `/goals` | List goals |
| POST | `/goals` | Create goal |

See [API_REFERENCE.md](docs/API_REFERENCE.md) for full documentation.

---

## 🎯 Next Steps

### For Developers
1. ✓ Verify structure: `python verify_structure.py`
2. ✓ Read the full [README.md](README.md)
3. ✓ Explore test files in `tests/`
4. ✓ Review API code in `backend/api_server.py`

### For DevOps/Deployment
1. Read [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
2. Choose deployment option (Docker, Systemd, etc.)
3. Follow production checklist

### For Contributing
1. Create a feature branch
2. Make changes
3. Run tests: `pytest`
4. Commit and push

---

## 📞 Getting Help

### Before asking for help:
1. Check the **Console** tab in DevTools (F12)
2. Check the **Network** tab for failed requests
3. Check terminal for error messages
4. Read the relevant documentation

### Common Issues & Solutions

**API won't start?**
- Is Python installed? → `python --version`
- Are dependencies installed? → `pip install -r requirements.txt`
- Is port 8001 available? → Check with `lsof -i :8001`

**Frontend won't load?**
- Try accessing via http://localhost:5000 instead of file://
- Check browser console (F12) for errors
- Verify API is running → `curl http://localhost:8001/health`

**Tests failing?**
- Clear cache: `rm -rf .pytest_cache __pycache__`
- Reinstall dependencies: `pip install -r requirements.txt`
- Run with verbose: `pytest -vv`

---

## 📈 Project Status

| Component | Status | Notes |
|-----------|--------|-------|
| Backend API | ✅ Ready | FastAPI, fully functional |
| Frontend | ✅ Ready | Vanilla JS, no dependencies |
| Database | ✅ Ready | SQLite, schema included |
| Testing | ✅ Ready | pytest configured |
| Documentation | ✅ Complete | README + 3 guides |
| Configuration | ✅ Complete | Environment-based |
| Structure | ✅ Professional | Organized folders |

---

## 🎓 Learning Resources

### Understanding the Project

**Backend (Python/FastAPI):**
- `backend/api_server.py` - Main REST API
- `backend/sanchay_db.py` - Database connections
- `backend/ingestion_engine.py` - Data fetching

**Frontend (Vanilla JavaScript):**
- `frontend/config.js` - Configuration
- `frontend/app.js` - Main application logic
- `frontend/index.html` - UI structure

**Testing:**
- `tests/conftest.py` - pytest setup
- `tests/test_backend_api.py` - API tests

### FastAPI Documentation
- Official: https://fastapi.tiangolo.com
- Tutorial: https://fastapi.tiangolo.com/tutorial/

### SQLite Documentation
- Official: https://www.sqlite.org/docs.html

### pytest Documentation
- Official: https://docs.pytest.org

---

## ✨ Pro Tips

1. **Use VS Code** - Great for Python development
2. **Enable auto-reload** - Edit code and see changes instantly
3. **Use curl or Postman** - Test APIs easily
4. **Check logs** - Always check console for errors
5. **Read docstrings** - Code is documented inline

---

## 🚀 You're Ready!

Your SANCHAY IAS environment is now set up and ready for development!

### Current Status:
✓ Folder structure organized  
✓ Code improved and modularized  
✓ Configuration management set up  
✓ Documentation complete  
✓ Testing ready  
✓ Ready for production  

### What's Next?
1. Explore the API endpoints
2. Understand the database schema
3. Read the full documentation
4. Start developing features

**Happy coding! 🎉**

---

*Last Updated: 2024*  
*Version: 2.0.0*  
*Status: Production Ready*
