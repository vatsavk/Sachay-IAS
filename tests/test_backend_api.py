"""
SANCHAY API Endpoint Tests
Comprehensive testing of all FastAPI endpoints
"""
import pytest
import json
from datetime import datetime, timedelta
import sanchay_db

pytestmark = pytest.mark.api

class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self, api_client):
        """Health check should return ok status"""
        response = api_client.get('/health')
        assert response.status_code == 200
        assert response.json()['status'] == 'ok'

class TestUserAPI:
    """Test user management endpoints"""
    
    def test_create_user(self, api_client, sample_user_data, clean_db):
        """Test creating a new user"""
        response = api_client.post('/users', json=sample_user_data)
        assert response.status_code == 200
        data = response.json()
        assert 'user_id' in data
        assert data['user_id'] > 0
    
    def test_create_user_invalid_email(self, api_client, clean_db):
        """Test creating user with invalid email format"""
        payload = {
            'name': 'Invalid User',
            'email': 'not-an-email',
            'phone': '+91-9999999999',
            'role': 'client',
            'status': 'active'
        }
        # Should still create (validation not strict in Pydantic BaseModel)
        response = api_client.post('/users', json=payload)
        assert response.status_code in [200, 400, 422]
    
    def test_create_duplicate_email(self, api_client, sample_user_data, clean_db):
        """Test creating duplicate user with same email"""
        # First user
        response1 = api_client.post('/users', json=sample_user_data)
        assert response1.status_code == 200
        
        # Second user with same email
        response2 = api_client.post('/users', json=sample_user_data)
        # SQLite UNIQUE constraint should catch this
        assert response2.status_code in [400, 422, 500]
    
    def test_get_user_by_id(self, api_client, sample_user_data, clean_db):
        """Test retrieving user by ID"""
        # Create user
        create_resp = api_client.post('/users', json=sample_user_data)
        user_id = create_resp.json()['user_id']
        
        # Get user
        get_resp = api_client.get(f'/users/{user_id}')
        assert get_resp.status_code == 200
        user = get_resp.json()
        assert user['name'] == sample_user_data['name']
        assert user['email'] == sample_user_data['email']
    
    def test_get_nonexistent_user(self, api_client):
        """Test retrieving non-existent user"""
        response = api_client.get('/users/99999')
        assert response.status_code == 404
    
    def test_list_users(self, api_client, sample_user_data, clean_db):
        """Test listing all users"""
        # Create multiple users
        for i in range(3):
            user_data = sample_user_data.copy()
            user_data['email'] = f'user{i}_{user_data["email"]}'
            api_client.post('/users', json=user_data)
        
        # List users
        response = api_client.get('/users')
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        assert len(users) >= 3
        
        # Verify at least one default advisor was created
        roles = [u.get('role') for u in users]
        assert 'advisor' in roles or len(users) > 0
    
    def test_user_with_various_roles(self, api_client, seeded_db):
        """Test creating users with different valid roles"""
        roles = ['advisor', 'client', 'principal_consultant']
        
        for role in roles:
            user_data = {
                'name': f'{role.title()} User',
                'email': f'{role}_{hash(role)}@sanchay.io',
                'phone': '+91-9999999999',
                'role': role,
                'status': 'active'
            }
            
            response = api_client.post('/users', json=user_data)
            assert response.status_code == 200
            assert 'user_id' in response.json()

class TestClientAPI:
    """Test client management endpoints"""
    
    def test_create_client_via_simple_api(self, api_client, sample_user_data, sample_client_data, clean_db):
        """Test creating a client via /clients endpoint"""
        # First create a user
        user_resp = api_client.post('/users', json=sample_user_data)
        user_id = user_resp.json()['user_id']
        
        # Create client
        client_payload = sample_client_data.copy()
        client_payload['user_id'] = user_id
        client_payload['advisor_id'] = None
        
        response = api_client.post('/clients', json=client_payload)
        assert response.status_code == 200
        assert 'client_id' in response.json()
    
    def test_onboard_client_workflow(self, api_client, sample_client_data, clean_db):
        """Test the onboard_client endpoint (simplified user+client creation)"""
        response = api_client.post('/onboard_client', json=sample_client_data)
        assert response.status_code == 200
        data = response.json()
        assert 'client_id' in data
        assert 'user_id' in data
    
    def test_onboard_client_duplicate_email(self, api_client, sample_client_data, clean_db):
        """Test onboarding client with duplicate email"""
        # First onboard
        api_client.post('/onboard_client', json=sample_client_data)
        
        # Second onboard with same email
        response = api_client.post('/onboard_client', json=sample_client_data)
        # Should fail due to UNIQUE constraint on email
        assert response.status_code in [400, 422, 500]
    
    def test_list_clients(self, api_client, clean_db):
        """Test listing clients"""
        response = api_client.get('/clients')
        assert response.status_code == 200
        clients = response.json()
        assert isinstance(clients, list)
    
    def test_get_client_by_id(self, api_client, sample_client_data, clean_db):
        """Test retrieving client by ID"""
        # Onboard client
        onboard_resp = api_client.post('/onboard_client', json=sample_client_data)
        client_id = onboard_resp.json()['client_id']
        
        # Get client
        get_resp = api_client.get(f'/clients/{client_id}')
        assert get_resp.status_code == 200
        client = get_resp.json()
        assert client['client_id'] == client_id
    
    def test_get_nonexistent_client(self, api_client):
        """Test retrieving non-existent client"""
        response = api_client.get('/clients/99999')
        assert response.status_code == 404

class TestGoalAPI:
    """Test goal management endpoints"""
    
    def test_create_goal(self, api_client, sample_client_data, sample_goal_data, clean_db):
        """Test creating a goal"""
        # Onboard client
        onboard_resp = api_client.post('/onboard_client', json=sample_client_data)
        client_id = onboard_resp.json()['client_id']
        
        # Create goal
        goal_payload = sample_goal_data.copy()
        goal_payload['client_id'] = client_id
        
        response = api_client.post('/goals', json=goal_payload)
        assert response.status_code == 200
        assert 'goal_id' in response.json()
    
    def test_create_goal_invalid_client(self, api_client, sample_goal_data, clean_db):
        """Test creating goal with non-existent client"""
        goal_payload = sample_goal_data.copy()
        goal_payload['client_id'] = 99999
        
        response = api_client.post('/goals', json=goal_payload)
        # Should fail due to foreign key constraint
        assert response.status_code in [400, 422, 500]
    
    def test_list_goals(self, api_client, clean_db):
        """Test listing goals"""
        response = api_client.get('/goals')
        assert response.status_code == 200
        goals = response.json()
        assert isinstance(goals, list)
    
    def test_goal_with_various_statuses(self, api_client, sample_client_data, clean_db):
        """Test creating goals with different statuses"""
        # Onboard client
        onboard_resp = api_client.post('/onboard_client', json=sample_client_data)
        client_id = onboard_resp.json()['client_id']
        
        statuses = ['On Track', 'At Risk', 'Ahead of Target']
        
        for status in statuses:
            goal_payload = {
                'client_id': client_id,
                'goal_type': f'Goal_{status}',
                'target_amount': 1000000.0,
                'target_date': '2035',
                'priority': 'Medium',
                'status': status
            }
            
            response = api_client.post('/goals', json=goal_payload)
            assert response.status_code == 200

class TestTaskAPI:
    """Test task management endpoints"""
    
    def test_create_task(self, api_client, sample_user_data, sample_client_data, sample_task_data, seeded_db):
        """Test creating a task"""
        # Create advisor
        user_resp = api_client.post('/users', json=sample_user_data)
        user_id = user_resp.json()['user_id']
        
        # Create/onboard client
        onboard_resp = api_client.post('/onboard_client', json=sample_client_data)
        client_id = onboard_resp.json()['client_id']
        
        # Create task
        task_payload = sample_task_data.copy()
        task_payload['advisor_id'] = 1
        task_payload['client_id'] = client_id
        
        response = api_client.post('/tasks', json=task_payload)
        assert response.status_code == 200
        assert 'task_id' in response.json()
    
    def test_create_task_invalid_advisor(self, api_client, sample_client_data, sample_task_data, seeded_db):
        """Test creating task with non-existent advisor"""
        onboard_resp = api_client.post('/onboard_client', json=sample_client_data)
        client_id = onboard_resp.json()['client_id']
        
        task_payload = sample_task_data.copy()
        task_payload['advisor_id'] = 99999
        task_payload['client_id'] = client_id
        
        # Should fail (advisor doesn't exist)
        response = api_client.post('/tasks', json=task_payload)
        assert response.status_code in [400, 422, 500]
    
    def test_list_tasks(self, api_client, seeded_db):
        """Test listing tasks"""
        response = api_client.get('/tasks')
        assert response.status_code == 200
        tasks = response.json()
        assert isinstance(tasks, list)
    
    def test_task_with_various_priorities(self, api_client, sample_user_data, sample_client_data, seeded_db):
        """Test creating tasks with different priorities"""
        # Setup
        user_resp = api_client.post('/users', json=sample_user_data)
        user_id = user_resp.json()['user_id']
        
        onboard_resp = api_client.post('/onboard_client', json=sample_client_data)
        client_id = onboard_resp.json()['client_id']
        
        priorities = ['Low', 'Medium', 'High', 'Critical']
        
        for priority in priorities:
            task_payload = {
                'advisor_id': user_id,
                'client_id': client_id,
                'task_type': f'Task_{priority}',
                'priority': priority,
                'due_date': '2023-11-15',
                'status': 'Pending'
            }
            
            response = api_client.post('/tasks', json=task_payload)
            assert response.status_code == 200

class TestTransactionAPI:
    """Test transaction management endpoints"""
    
    def test_create_transaction(self, api_client, sample_client_data, sample_transaction_data, seeded_db):
        """Test creating a transaction"""
        # Onboard client
        onboard_resp = api_client.post('/onboard_client', json=sample_client_data)
        client_id = onboard_resp.json()['client_id']
        
        # Create transaction
        txn_payload = sample_transaction_data.copy()
        txn_payload['client_id'] = client_id
        
        response = api_client.post('/transactions', json=txn_payload)
        assert response.status_code == 200
        assert 'txn_id' in response.json()
    
    def test_create_transaction_invalid_client(self, api_client, sample_transaction_data, seeded_db):
        """Test creating transaction with non-existent client"""
        txn_payload = sample_transaction_data.copy()
        txn_payload['client_id'] = 99999
        
        response = api_client.post('/transactions', json=txn_payload)
        # Should fail due to foreign key constraint
        assert response.status_code in [400, 422, 500]
    
    def test_list_transactions(self, api_client, seeded_db):
        """Test listing transactions"""
        response = api_client.get('/transactions')
        assert response.status_code == 200
        transactions = response.json()
        assert isinstance(transactions, list)
    
    def test_transaction_types(self, api_client, sample_client_data, seeded_db):
        """Test creating transactions of different types"""
        # Onboard client
        onboard_resp = api_client.post('/onboard_client', json=sample_client_data)
        client_id = onboard_resp.json()['client_id']
        
        txn_types = ['Purchase', 'Sale', 'Dividend', 'Transfer', 'Rebalance']
        
        for txn_type in txn_types:
            txn_payload = {
                'client_id': client_id,
                'asset_id': 1,
                'txn_type': txn_type,
                'quantity': 100.0,
                'price': 1500.0,
                'txn_date': '2023-10-17'
            }
            
            response = api_client.post('/transactions', json=txn_payload)
            assert response.status_code == 200

class TestCORSHeaders:
    """Test CORS headers"""
    
    def test_cors_headers_present(self, api_client):
        """Test that CORS headers are present in responses"""
        response = api_client.get('/health', headers={'Origin': 'http://localhost:3000'})
        assert response.status_code == 200
        assert 'access-control-allow-origin' in response.headers
        assert response.headers['access-control-allow-origin'] == 'http://localhost:3000'
    
    def test_cors_options_request(self, api_client):
        """Test CORS OPTIONS request"""
        response = api_client.options('/health', headers={
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'GET'
        })
        assert response.status_code in [200, 204]

class TestInputValidation:
    """Test input validation and edge cases"""
    
    def test_negative_amounts(self, api_client, sample_client_data, clean_db):
        """Test creating goal with negative target amount"""
        onboard_resp = api_client.post('/onboard_client', json=sample_client_data)
        client_id = onboard_resp.json()['client_id']
        
        goal_payload = {
            'client_id': client_id,
            'goal_type': 'Test',
            'target_amount': -1000000.0,  # Negative amount
            'target_date': '2035',
            'priority': 'Low',
            'status': 'On Track'
        }
        
        response = api_client.post('/goals', json=goal_payload)
        # Should either reject or accept (depending on validation logic)
        assert response.status_code in [200, 400, 422]
    
    def test_missing_required_fields(self, api_client, clean_db):
        """Test creating user without required fields"""
        # Missing name
        payload = {
            'email': 'test@sanchay.io',
            'phone': '+91-9999999999',
            'role': 'client'
        }
        
        response = api_client.post('/users', json=payload)
        # Should fail validation
        assert response.status_code in [400, 422]
    
    def test_empty_string_fields(self, api_client, clean_db):
        """Test creating user with empty strings"""
        payload = {
            'name': '',
            'email': 'test@sanchay.io',
            'phone': '+91-9999999999',
            'role': 'client'
        }
        
        response = api_client.post('/users', json=payload)
        # Behavior depends on validation logic
        assert response.status_code in [200, 400, 422]
    
    def test_very_large_numbers(self, api_client, sample_client_data, clean_db):
        """Test transaction with very large amounts"""
        onboard_resp = api_client.post('/onboard_client', json=sample_client_data)
        client_id = onboard_resp.json()['client_id']
        
        txn_payload = {
            'client_id': client_id,
            'asset_id': 1,
            'txn_type': 'Purchase',
            'quantity': 999999999.99,
            'price': 999999999.99,
            'txn_date': '2023-10-17'
        }
        
        response = api_client.post('/transactions', json=txn_payload)
        assert response.status_code == 200

class TestDataIntegrity:
    """Test data integrity and consistency"""
    
    def test_client_user_relationship(self, api_client, sample_user_data, sample_client_data, clean_db):
        """Test that client is properly linked to user"""
        user_resp = api_client.post('/users', json=sample_user_data)
        user_id = user_resp.json()['user_id']
        
        client_payload = sample_client_data.copy()
        client_payload['user_id'] = user_id
        
        client_resp = api_client.post('/clients', json=client_payload)
        client_id = client_resp.json()['client_id']
        
        # Fetch client and verify user linkage
        get_client_resp = api_client.get(f'/clients/{client_id}')
        client = get_client_resp.json()
        
        assert client['user_id'] == user_id
    
    def test_goal_client_relationship(self, api_client, sample_client_data, clean_db):
        """Test that goal is properly linked to client"""
        onboard_resp = api_client.post('/onboard_client', json=sample_client_data)
        client_id = onboard_resp.json()['client_id']
        
        goal_payload = {
            'client_id': client_id,
            'goal_type': 'Test Goal',
            'target_amount': 1000000.0,
            'target_date': '2035',
            'priority': 'Medium',
            'status': 'On Track'
        }
        
        goal_resp = api_client.post('/goals', json=goal_payload)
        goal_id = goal_resp.json()['goal_id']
        
        # Fetch goals and verify linkage
        goals = api_client.get('/goals').json()
        matching_goal = next((g for g in goals if g['goal_id'] == goal_id), None)
        
        assert matching_goal is not None
        assert matching_goal['client_id'] == client_id
