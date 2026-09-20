import pytest
from fastapi.testclient import TestClient
from api_server import app, get_current_user
import sanchay_db

client = TestClient(app)

def test_reports_empty_holdings():
    # Setup dummy client with no holdings
    adv_user_id = sanchay_db.ensure_user('Dummy Adv', 'dummy_adv@test.com', '777', 'advisor')
    with sanchay_db.get_connection() as conn:
        conn.execute("INSERT INTO advisors (user_id, firm_name) VALUES (?, ?)", (adv_user_id, 'Dummy Firm'))
        adv_id = conn.execute("SELECT advisor_id FROM advisors WHERE user_id=?", (adv_user_id,)).fetchone()['advisor_id']
        
    user_id = sanchay_db.ensure_user('Empty Holdings Client', 'empty@test.com', '666', 'client')
    client_id = sanchay_db.create_client(user_id, adv_id, '1990-01-01', 50000, 100000, 'Test', '2023-01-01')
        
    app.dependency_overrides[get_current_user] = lambda: {'user_id': user_id, 'role': 'client', 'client_id': client_id}
    
    try:
        response = client.post(f"/reports?client_id={client_id}")
        # Should return a graceful error (e.g. 400 Bad Request or a message)
        assert response.status_code == 400 
        assert "No holdings available" in response.text
    finally:
        app.dependency_overrides.clear()
        with sanchay_db.get_connection() as conn:
            conn.execute("DELETE FROM clients WHERE client_id=?", (client_id,))
            conn.execute("DELETE FROM users WHERE user_id=?", (user_id,))
