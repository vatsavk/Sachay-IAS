"""
SANCHAY API Server
FastAPI-based REST API for the financial advisory OS.
Loads configuration from environment variables with sensible defaults.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import os
from pathlib import Path

# Import database module
from sanchay_db import init_database, get_connection

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 8001))
API_RELOAD = os.getenv('API_RELOAD', 'True').lower() == 'true'
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5000,file://').split(',')

# ═══════════════════════════════════════════════════════════════════
# APP INITIALIZATION
# ═══════════════════════════════════════════════════════════════════

app = FastAPI(
    title='SANCHAY IAS API',
    version='2.0.0',
    description='Financial Advisory Operating System - REST API'
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[ERROR] {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "status": "error"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# ═══════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    role: str = 'advisor'
    status: str = 'active'

class ClientCreate(BaseModel):
    user_id: int
    advisor_id: Optional[int] = None
    dob: Optional[str] = None
    income: Optional[float] = 0
    net_worth: Optional[float] = 0
    occupation: Optional[str] = None
    onboarding_date: Optional[str] = None

class GoalCreate(BaseModel):
    client_id: int
    goal_type: str
    target_amount: float
    current_corpus: float = 0
    target_date: str
    monthly_sip: float = 0

class TransactionCreate(BaseModel):
    client_id: int
    asset_id: int
    transaction_type: str
    quantity: float
    price: float
    transaction_date: str

# ═══════════════════════════════════════════════════════════════════
# HEALTH & STATUS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.get('/health')
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "SANCHAY IAS API", "version": "2.0.0"}

@app.get('/status')
async def status():
    """Get API status and configuration"""
    return {
        "status": "running",
        "version": "2.0.0",
        "host": API_HOST,
        "port": API_PORT,
        "cors_origins": CORS_ORIGINS
    }

# ═══════════════════════════════════════════════════════════════════
# USER ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.post('/users')
async def create_user(user: UserCreate):
    """Create a new user"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (name, email, phone, role, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (user.name, user.email, user.phone, user.role, user.status))
            conn.commit()
            user_id = cursor.lastrowid
            return {"user_id": user_id, "message": "User created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get('/users/{user_id}')
async def get_user(user_id: int):
    """Get user by ID"""
    with get_connection() as conn:
        user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(user)

@app.get('/users')
async def list_users():
    """List all users"""
    with get_connection() as conn:
        users = conn.execute('SELECT * FROM users').fetchall()
        return [dict(u) for u in users]

# ═══════════════════════════════════════════════════════════════════
# CLIENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.get('/clients')
async def list_clients():
    """List all clients"""
    with get_connection() as conn:
        clients = conn.execute('SELECT * FROM clients').fetchall()
        return [dict(c) for c in clients]

@app.get('/clients/{client_id}')
async def get_client(client_id: int):
    """Get client details"""
    with get_connection() as conn:
        client = conn.execute('SELECT * FROM clients WHERE client_id = ?', (client_id,)).fetchone()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        return dict(client)

@app.post('/clients')
async def create_client(client: ClientCreate):
    """Create a new client"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO clients (user_id, advisor_id, dob, income, net_worth, occupation, onboarding_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (client.user_id, client.advisor_id, client.dob, client.income, 
                  client.net_worth, client.occupation, client.onboarding_date))
            conn.commit()
            client_id = cursor.lastrowid
            return {"client_id": client_id, "message": "Client created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ═══════════════════════════════════════════════════════════════════
# GOAL ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.get('/goals')
async def list_goals():
    """List all goals"""
    with get_connection() as conn:
        goals = conn.execute('SELECT * FROM goals').fetchall()
        return [dict(g) for g in goals]

@app.post('/goals')
async def create_goal(goal: GoalCreate):
    """Create a new goal"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO goals (client_id, goal_type, target_amount, current_corpus, target_date, monthly_sip)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (goal.client_id, goal.goal_type, goal.target_amount, goal.current_corpus, 
                  goal.target_date, goal.monthly_sip))
            conn.commit()
            goal_id = cursor.lastrowid
            return {"goal_id": goal_id, "message": "Goal created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ═══════════════════════════════════════════════════════════════════
# DASHBOARD & ANALYTICS
# ═══════════════════════════════════════════════════════════════════

@app.get('/dashboard')
async def get_dashboard():
    """Get dashboard summary data"""
    with get_connection() as conn:
        total_clients = conn.execute('SELECT COUNT(*) as count FROM clients').fetchone()['count']
        total_goals = conn.execute('SELECT COUNT(*) as count FROM goals').fetchone()['count']
        
        return {
            "total_clients": total_clients,
            "total_goals": total_goals,
            "total_aum": "₹0",
            "tasks_pending": 0
        }

@app.get('/tasks')
async def list_tasks():
    """List tasks"""
    return {"tasks": []}

@app.get('/compliance')
async def get_compliance():
    """Get compliance status"""
    return {"status": "compliant", "items": []}

@app.get('/reports')
async def list_reports():
    """List reports"""
    return {"reports": []}

@app.get('/team')
async def list_team():
    """List team members"""
    return {"team": []}

# ═══════════════════════════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()
    print("✓ SANCHAY API Server initialized")

if __name__ == '__main__':
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        reload=API_RELOAD,
        log_level="info"
    )
