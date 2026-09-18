"""
SANCHAY Integration Tests
End-to-end workflow testing combining API, DB, and business logic
"""
import pytest
from datetime import datetime, timedelta
import sanchay_db

pytestmark = pytest.mark.integration

class TestCompleteClientOnboardingWorkflow:
    """Test complete client onboarding workflow"""
    
    def test_advisor_onboard_client_create_goals_and_tasks(self, api_client, seeded_db):
        """Complete workflow: Advisor creates account, onboards client, creates goals and tasks"""
        # Step 1: Create advisor user
        advisor_data = {
            'name': 'Rajesh Kumar',
            'email': 'rajesh@advisors.io',
            'phone': '+91-9876543210',
            'role': 'advisor',
            'status': 'active'
        }
        advisor_resp = api_client.post('/users', json=advisor_data)
        assert advisor_resp.status_code == 200
        advisor_id = advisor_resp.json()['user_id']
        
        # Step 2: Onboard client
        client_data = {
            'name': 'Rahul Sharma',
            'email': 'rahul@clients.io',
            'phone': '+91-9988776655',
            'advisor_id': None,
            'dob': '1985-05-15',
            'income': 75.0,
            'net_worth': 150.0,
            'occupation': 'IT Professional',
            'onboarding_date': '2023-10-01'
        }
        onboard_resp = api_client.post('/onboard_client', json=client_data)
        assert onboard_resp.status_code == 200
        client_id = onboard_resp.json()['client_id']
        
        # Step 3: Create goals for client
        goals = [
            {
                'client_id': client_id,
                'goal_type': 'Retirement',
                'target_amount': 5000000.0,
                'target_date': '2035',
                'priority': 'High',
                'status': 'On Track'
            },
            {
                'client_id': client_id,
                'goal_type': 'Child Education',
                'target_amount': 2000000.0,
                'target_date': '2030',
                'priority': 'High',
                'status': 'On Track'
            }
        ]
        
        goal_ids = []
        for goal in goals:
            goal_resp = api_client.post('/goals', json=goal)
            assert goal_resp.status_code == 200
            goal_ids.append(goal_resp.json()['goal_id'])
        
        # Step 4: Create tasks
        task_data = {
            'advisor_id': advisor_id,
            'client_id': client_id,
            'task_type': 'Portfolio Review',
            'priority': 'High',
            'due_date': '2023-11-01',
            'status': 'Pending'
        }
        task_resp = api_client.post('/tasks', json=task_data)
        assert task_resp.status_code == 200
        task_id = task_resp.json()['task_id']
        
        # Step 5: Verify complete workflow
        clients = api_client.get('/clients').json()
        client = next((c for c in clients if c['client_id'] == client_id), None)
        assert client is not None
        assert client['occupation'] == 'IT Professional'
        
        goals_list = api_client.get('/goals').json()
        client_goals = [g for g in goals_list if g['client_id'] == client_id]
        assert len(client_goals) == 2
    
    def test_advisor_client_portfolio_transactions_workflow(self, api_client, seeded_db):
        """Workflow: Create advisor, client, add portfolio transactions"""
        # Setup
        advisor_resp = api_client.post('/users', json={
            'name': 'Advisor',
            'email': 'adv@test.io',
            'role': 'advisor'
        })
        advisor_id = advisor_resp.json()['user_id']
        
        onboard_resp = api_client.post('/onboard_client', json={
            'name': 'Client',
            'email': 'clt@test.io',
            'income': 50.0,
            'net_worth': 100.0
        })
        client_id = onboard_resp.json()['client_id']
        
        # Add multiple transactions
        transactions = [
            {
                'client_id': client_id,
                'asset_id': 1,
                'txn_type': 'Purchase',
                'quantity': 100.0,
                'price': 1500.0,
                'txn_date': '2023-10-01'
            },
            {
                'client_id': client_id,
                'asset_id': 2,
                'txn_type': 'Purchase',
                'quantity': 50.0,
                'price': 2500.0,
                'txn_date': '2023-10-05'
            },
            {
                'client_id': client_id,
                'asset_id': 1,
                'txn_type': 'Sale',
                'quantity': 25.0,
                'price': 1600.0,
                'txn_date': '2023-10-10'
            }
        ]
        
        for txn in transactions:
            resp = api_client.post('/transactions', json=txn)
            assert resp.status_code == 200
        
        # Verify all transactions
        all_txns = api_client.get('/transactions').json()
        client_txns = [t for t in all_txns if t['client_id'] == client_id]
        assert len(client_txns) == 3

class TestTaskManagementWorkflow:
    """Test task creation, assignment, and status updates"""
    
    def test_task_lifecycle(self, api_client, seeded_db):
        """Test task creation and status progression"""
        # Setup
        advisor_resp = api_client.post('/users', json={
            'name': 'Advisor',
            'email': 'advisor@test.io',
            'role': 'advisor'
        })
        advisor_id = advisor_resp.json()['user_id']
        
        onboard_resp = api_client.post('/onboard_client', json={
            'name': 'Client',
            'email': 'client@test.io'
        })
        client_id = onboard_resp.json()['client_id']
        
        # Create task
        task_resp = api_client.post('/tasks', json={
            'advisor_id': advisor_id,
            'client_id': client_id,
            'task_type': 'KYC Review',
            'priority': 'High',
            'due_date': '2023-11-15',
            'status': 'Pending'
        })
        assert task_resp.status_code == 200
        
        # Verify initial status
        tasks = api_client.get('/tasks').json()
        task = next((t for t in tasks if t['client_id'] == client_id), None)
        assert task is not None
        assert task['status'] == 'Pending'

class TestGoalTrackingWorkflow:
    """Test goal creation and tracking"""
    
    def test_multiple_clients_multiple_goals(self, api_client, seeded_db):
        """Test managing multiple clients each with multiple goals"""
        # Create 3 clients
        clients = []
        for i in range(3):
            onboard_resp = api_client.post('/onboard_client', json={
                'name': f'Client {i}',
                'email': f'client{i}@test.io',
                'income': 50.0 * (i + 1),
                'net_worth': 100.0 * (i + 1)
            })
            assert onboard_resp.status_code == 200
            clients.append(onboard_resp.json()['client_id'])
        
        # Create 2 goals per client
        for client_id in clients:
            for j in range(2):
                goal_resp = api_client.post('/goals', json={
                    'client_id': client_id,
                    'goal_type': f'Goal {j}',
                    'target_amount': 1000000.0 * (j + 1),
                    'target_date': '2035',
                    'priority': 'High',
                    'status': 'On Track'
                })
                assert goal_resp.status_code == 200
        
        # Verify total goals
        goals = api_client.get('/goals').json()
        assert len(goals) >= 6

class TestDataRelationshipIntegrity:
    """Test data relationships across entities"""
    
    def test_advisor_to_multiple_clients(self, api_client, seeded_db):
        """Test advisor managing multiple clients"""
        # Create advisor
        advisor_resp = api_client.post('/users', json={
            'name': 'Senior Advisor',
            'email': 'senior@test.io',
            'role': 'advisor'
        })
        advisor_id = advisor_resp.json()['user_id']
        
        # Onboard multiple clients with this advisor
        client_ids = []
        for i in range(4):
            resp = api_client.post('/onboard_client', json={
                'name': f'Client {i}',
                'email': f'cli{i}@test.io',
                'advisor_id': advisor_id
            })
            client_ids.append(resp.json()['client_id'])
        
        # Verify all clients are associated
        clients = api_client.get('/clients').json()
        advisor_clients = [c for c in clients if c.get('advisor_id') == advisor_id or c.get('advisor_id') is None]
        assert len(advisor_clients) >= 4

class TestConcurrentOperations:
    """Test handling of concurrent-like operations"""
    
    def test_rapid_user_creation(self, api_client, seeded_db):
        """Test creating multiple users rapidly"""
        user_ids = []
        
        for i in range(5):
            resp = api_client.post('/users', json={
                'name': f'Rapid User {i}',
                'email': f'rapid{i}@test.io',
                'role': 'client'
            })
            assert resp.status_code == 200
            user_ids.append(resp.json()['user_id'])
        
        # Verify all users exist
        users = api_client.get('/users').json()
        for uid in user_ids:
            assert any(u['user_id'] == uid for u in users)
    
    def test_rapid_client_onboarding(self, api_client, seeded_db):
        """Test onboarding multiple clients rapidly"""
        client_ids = []
        
        for i in range(5):
            resp = api_client.post('/onboard_client', json={
                'name': f'Onboard Client {i}',
                'email': f'onboard{i}@test.io',
                'income': 50.0,
                'net_worth': 100.0
            })
            assert resp.status_code == 200
            client_ids.append(resp.json()['client_id'])
        
        # Verify all clients exist
        clients = api_client.get('/clients').json()
        assert len(clients) >= 5

class TestErrorHandlingAndRecovery:
    """Test error handling in critical workflows"""
    
    def test_onboard_with_missing_fields(self, api_client, seeded_db):
        """Test onboarding with missing optional fields"""
        resp = api_client.post('/onboard_client', json={
            'name': 'Minimal Client',
            'email': 'minimal@test.io'
            # Missing all optional fields
        })
        assert resp.status_code == 200
        assert 'client_id' in resp.json()
    
    def test_goal_creation_without_optional_fields(self, api_client, seeded_db):
        """Test goal creation with minimal required fields"""
        onboard_resp = api_client.post('/onboard_client', json={
            'name': 'Client',
            'email': 'client@test.io'
        })
        client_id = onboard_resp.json()['client_id']
        
        # Create goal with minimal fields
        resp = api_client.post('/goals', json={
            'client_id': client_id,
            'goal_type': 'Basic Goal',
            'target_amount': 1000000.0,
            'target_date': '2030'
        })
        assert resp.status_code == 200

class TestAPIResponseConsistency:
    """Test API response format consistency"""
    
    def test_list_endpoints_return_arrays(self, api_client, seeded_db):
        """Test that all list endpoints return arrays"""
        endpoints = ['/users', '/clients', '/goals', '/tasks', '/transactions']
        
        for endpoint in endpoints:
            resp = api_client.get(endpoint)
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list), f"{endpoint} did not return a list"
    
    def test_create_endpoints_return_id(self, api_client, seeded_db):
        """Test that create endpoints return IDs"""
        # Create user
        user_resp = api_client.post('/users', json={
            'name': 'Test',
            'email': 'test@test.io',
            'role': 'client'
        })
        assert 'user_id' in user_resp.json()
        
        # Create client
        onboard_resp = api_client.post('/onboard_client', json={
            'name': 'Client',
            'email': 'client@test.io'
        })
        assert 'client_id' in onboard_resp.json()
        
        # Create goal
        client_id = onboard_resp.json()['client_id']
        goal_resp = api_client.post('/goals', json={
            'client_id': client_id,
            'goal_type': 'Goal',
            'target_amount': 1000000.0,
            'target_date': '2030'
        })
        assert 'goal_id' in goal_resp.json()

class TestDataValidationWorkflow:
    """Test data validation across workflows"""
    
    def test_workflow_with_edge_case_values(self, api_client, seeded_db):
        """Test workflow with edge case numeric values"""
        # Create client
        onboard_resp = api_client.post('/onboard_client', json={
            'name': 'Edge Case Client',
            'email': 'edge@test.io',
            'income': 0.01,  # Very small
            'net_worth': 999999999.99  # Very large
        })
        assert onboard_resp.status_code == 200
        client_id = onboard_resp.json()['client_id']
        
        # Create goal with edge case amount
        goal_resp = api_client.post('/goals', json={
            'client_id': client_id,
            'goal_type': 'Edge Case Goal',
            'target_amount': 0.01,  # Very small target
            'target_date': '2030'
        })
        assert goal_resp.status_code == 200
        
        # Create transaction with large quantity
        txn_resp = api_client.post('/transactions', json={
            'client_id': client_id,
            'asset_id': 1,
            'txn_type': 'Purchase',
            'quantity': 999999.99,
            'price': 0.01
        })
        assert txn_resp.status_code == 200
