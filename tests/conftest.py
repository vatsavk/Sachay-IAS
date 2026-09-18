"""
Pytest Configuration and Fixtures for SANCHAY Testing Suite
Pre-Production Testing Framework v1.0
"""
import pytest
import sqlite3
import os
import tempfile
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sanchay_db
from fastapi.testclient import TestClient

# Global test database path
TEST_DB_PATH = None

@pytest.fixture(scope='session')
def test_db_path():
    """Create a temporary test database for the entire test session"""
    global TEST_DB_PATH
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    TEST_DB_PATH = temp_db.name
    temp_db.close()
    
    # Patch it globally for all tests
    original_db = sanchay_db.DB_PATH
    sanchay_db.DB_PATH = TEST_DB_PATH
    
    # Initialize test database
    sanchay_db.init_database(TEST_DB_PATH)
    yield TEST_DB_PATH
    
    # Cleanup
    sanchay_db.DB_PATH = original_db
    try:
        os.unlink(TEST_DB_PATH)
    except:
        pass

@pytest.fixture
def db_connection(test_db_path):
    """Provide a fresh database connection for each test"""
    # Use the test database instead of production
    original_db = sanchay_db.DB_PATH
    sanchay_db.DB_PATH = test_db_path
    
    conn = sqlite3.connect(test_db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON;')
    
    yield conn
    
    conn.close()
    sanchay_db.DB_PATH = original_db

@pytest.fixture
def clean_db(test_db_path):
    """Provide a clean database by resetting tables before each test"""
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    # Disable foreign key constraints temporarily
    cursor.execute('PRAGMA foreign_keys=OFF;')
    
    # Clear all tables
    cursor.execute('DELETE FROM transactions;')
    cursor.execute('DELETE FROM tasks;')
    cursor.execute('DELETE FROM goals;')
    cursor.execute('DELETE FROM clients;')
    cursor.execute('DELETE FROM advisors;')
    cursor.execute('DELETE FROM users;')
    
    cursor.execute('PRAGMA foreign_keys=ON;')
    conn.commit()
    conn.close()
    
    yield test_db_path
    
    # Cleanup again
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys=OFF;')
    cursor.execute('DELETE FROM transactions;')
    cursor.execute('DELETE FROM tasks;')
    cursor.execute('DELETE FROM goals;')
    cursor.execute('DELETE FROM clients;')
    cursor.execute('DELETE FROM advisors;')
    cursor.execute('DELETE FROM users;')
    cursor.execute('PRAGMA foreign_keys=ON;')
    conn.commit()
    conn.close()

@pytest.fixture
def seeded_db(clean_db):
    """Clean DB with one default advisor pre-seeded for FK-dependent tests."""
    import sanchay_db
    original = sanchay_db.DB_PATH
    sanchay_db.DB_PATH = clean_db
    sanchay_db.ensure_advisor(
        "Test Advisor", "advisor@test.io", "Test Firm", "LIC-TEST-001"
    )
    sanchay_db.DB_PATH = original
    yield clean_db

@pytest.fixture
def api_client():
    """Provide a FastAPI test client"""
    from api_server import app, get_current_user, require_write
    
    # Mock auth dependencies for testing
    app.dependency_overrides[get_current_user] = lambda: {'user_id': 1, 'role': 'principal_consultant', 'advisor_id': 1}
    app.dependency_overrides[require_write] = lambda: {'user_id': 1, 'role': 'principal_consultant', 'advisor_id': 1}
    
    # Monkey patch the database path for testing
    original_db = sanchay_db.DB_PATH
    sanchay_db.DB_PATH = TEST_DB_PATH
    
    client = TestClient(app)
    yield client
    
    sanchay_db.DB_PATH = original_db
    app.dependency_overrides.clear()

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        'name': 'Test User',
        'email': f'test_{os.urandom(4).hex()}@sanchay.io',
        'phone': '+91-9999999999',
        'role': 'advisor',
        'status': 'active'
    }

@pytest.fixture
def sample_client_data():
    """Sample client data for testing"""
    return {
        'name': 'Test Client',
        'email': f'client_{os.urandom(4).hex()}@sanchay.io',
        'phone': '+91-8888888888',
        'dob': '1990-01-01',
        'income': 50.0,
        'net_worth': 100.0,
        'occupation': 'Business Owner',
        'onboarding_date': '2023-01-01'
    }

@pytest.fixture
def sample_goal_data():
    """Sample goal data for testing"""
    return {
        'goal_type': 'Retirement',
        'target_amount': 5000000.0,
        'target_date': '2035',
        'priority': 'High',
        'status': 'On Track'
    }

@pytest.fixture
def sample_task_data():
    """Sample task data for testing"""
    return {
        'task_type': 'Portfolio Review',
        'priority': 'High',
        'due_date': '2023-11-01',
        'status': 'Pending'
    }

@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing"""
    return {
        'asset_id': 1,
        'txn_type': 'BUY',
        'quantity': 100.0,
        'price': 1500.0,
        'txn_date': '2023-10-17'
    }

def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line('markers', 'unit: Unit tests')
    config.addinivalue_line('markers', 'integration: Integration tests')
    config.addinivalue_line('markers', 'database: Database operation tests')
    config.addinivalue_line('markers', 'api: API endpoint tests')
    config.addinivalue_line('markers', 'ui: UI/UX tests')
    config.addinivalue_line('markers', 'performance: Performance tests')
    config.addinivalue_line('markers', 'security: Security tests')
