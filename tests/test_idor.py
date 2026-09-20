import pytest
from fastapi.testclient import TestClient
import sanchay_db
from api_server import app, get_current_user
import pytest_asyncio


client = TestClient(app)

def test_client_portal_idor_protection():
    # We will mock the get_current_user dependency to pretend to be an advisor
    # First, let's create two advisors and two clients in a fresh DB state
    
    # In Sanchay IAS testing, we usually create a real DB state or mock the DB connection.
    # We will use the existing DB by creating a temporary advisor and client.
    
    # Create Advisor A
    adv_a_user = sanchay_db.ensure_user('Test Advisor A', 'adv_a@test.com', '111', 'advisor')
    with sanchay_db.get_connection() as conn:
        conn.execute("INSERT INTO advisors (user_id, firm_name) VALUES (?, ?)", (adv_a_user, 'Firm A'))
        adv_a_id = conn.execute("SELECT advisor_id FROM advisors WHERE user_id=?", (adv_a_user,)).fetchone()['advisor_id']
        
    # Create Advisor B
    adv_b_user = sanchay_db.ensure_user('Test Advisor B', 'adv_b@test.com', '222', 'advisor')
    with sanchay_db.get_connection() as conn:
        conn.execute("INSERT INTO advisors (user_id, firm_name) VALUES (?, ?)", (adv_b_user, 'Firm B'))
        adv_b_id = conn.execute("SELECT advisor_id FROM advisors WHERE user_id=?", (adv_b_user,)).fetchone()['advisor_id']
        
    # Create Client for Advisor B
    client_b_user = sanchay_db.ensure_user('Test Client B', 'client_b@test.com', '333', 'client')
    client_b_id = sanchay_db.create_client(client_b_user, adv_b_id, '1990-01-01', 50000, 100000, 'Test', '2023-01-01')

    # Mock Advisor A's token
    def override_get_current_user():
        return {
            'user_id': adv_a_user,
            'role': 'advisor',
            'advisor_id': adv_a_id
        }
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    try:
        # Advisor A tries to access Client B's portfolio
        response = client.get(f"/my/portfolio?client_id={client_b_id}")
        assert response.status_code == 403
        assert response.json()['detail'] == "Unauthorized: You do not manage this client"
        
        # Advisor A tries to access Client B's analytics
        response_analytics = client.get(f"/my/dashboard/analytics?client_id={client_b_id}")
        assert response_analytics.status_code == 403
        assert response_analytics.json()['detail'] == "Unauthorized: You do not manage this client"
    finally:
        # Cleanup
        app.dependency_overrides.clear()
        with sanchay_db.get_connection() as conn:
            conn.execute("DELETE FROM clients WHERE client_id=?", (client_b_id,))
            conn.execute("DELETE FROM advisors WHERE advisor_id IN (?, ?)", (adv_a_id, adv_b_id))
            conn.execute("DELETE FROM users WHERE user_id IN (?, ?, ?)", (adv_a_user, adv_b_user, client_b_user))
