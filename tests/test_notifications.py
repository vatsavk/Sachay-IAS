import pytest
from unittest.mock import patch, MagicMock
from notifications import _send_email_sync
import sanchay_db

def test_send_onboarding_email_mocked():
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Ensure table exists for test environment
        with sanchay_db.get_connection() as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS email_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, recipient TEXT, subject TEXT, sent_at DATETIME DEFAULT CURRENT_TIMESTAMP, status TEXT, error_message TEXT)')
        
        # Test sending
        _send_email_sync("test@example.com", "Test Subject", "Test Body")
        
        mock_server.send_message.assert_called_once()
        msg = mock_server.send_message.call_args[0][0]
        assert msg["To"] == "test@example.com"
        assert msg["Subject"] == "Test Subject"
        
        # Verify db log
        with sanchay_db.get_connection() as conn:
            log_row = conn.execute("SELECT * FROM email_logs ORDER BY id DESC LIMIT 1").fetchone()
            assert log_row is not None
            assert log_row["recipient"] == "test@example.com"
            assert log_row["subject"] == "Test Subject"
            assert log_row["status"] == "success"

from fastapi.testclient import TestClient
from api_server import app, get_current_user

client = TestClient(app)

def test_onboard_client_triggers_notification():
    with patch("notifications._send_email_sync") as mock_send:
        # Mock auth
        app.dependency_overrides[get_current_user] = lambda: {'user_id': 1, 'role': 'advisor', 'advisor_id': 1}
        
        response = client.post("/onboard_client", json={
            "name": "Integration Test Client",
            "email": "integration@test.com",
            "phone": "5555555",
            "dob": "1990-01-01",
            "income": 100000,
            "net_worth": 500000,
            "occupation": "Engineer",
            "onboarding_date": "2023-01-01",
            "advisory_fee_bps": 100,
            "risk_score": 50,
            "risk_category": "Balanced",
            "liquidity_score": 50,
            "investment_horizon": 10
        })
        
        assert response.status_code == 200
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert args[0] == "integration@test.com"
        assert "Welcome to Sanchay IAS" in args[1]
        
        app.dependency_overrides.clear()
